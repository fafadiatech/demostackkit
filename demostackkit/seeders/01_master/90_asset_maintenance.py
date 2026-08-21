"""
Shared seeder: Asset Maintenance for every maintenance-required Asset.

Needs no per-industry data — it reads the ``asset_names`` cache left by each
industry's ``14_assets.py`` (built on ``demostackkit.seeder.asset_seeder``)
and no-ops if the industry seeded no Assets or the Assets module is absent.

Runs at priority 90 — after the shared ``84_employee_users.py`` — because
``Asset Maintenance Task.assign_to`` is enforced server-side
(``asset_maintenance.py``'s ``validate()`` throws "Please assign task to a
member" otherwise) and, unlike a plain Link field, resolving it walks
``frappe.desk.form.assign_to``, which needs a real User whose docname is its
own email. ``Administrator`` fails that with a cryptic "Could not find
Allocated To" because its docname and email differ, so tasks are assigned to
a seeded employee login instead. No-ops if the industry seeded no employee
logins either.

The Asset Maintenance Team's own member field is a plain Link (never touches
the assignment path above), so it can safely be Administrator.

Getting one Completed log in the past and one Planned log in the future
means working with ERPNext's own state machine rather than hand-inserting
both: ``Asset Maintenance Log.due_date`` is ``fetch_from: task.next_due_date``
and read-only, so a manually-set ``due_date`` is silently overwritten on
insert. Instead: the task starts with ``next_due_date`` in the past, which
makes ``Asset Maintenance``'s own ``on_update()`` auto-create one Planned log
there (see ``sync_maintenance_tasks()`` in ERPNext's ``asset_maintenance.py``);
marking that log Completed and submitting it runs
``AssetMaintenanceLog.on_submit()``, which advances the task's
``next_due_date`` by one periodicity and re-saves it — which in turn
triggers ``on_update()`` again and auto-creates the next Planned log, now
due in the future.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from demostackkit.seeder.base import BaseMasterSeeder


class AssetMaintenanceSeeder(BaseMasterSeeder):
    """Asset Maintenance schedules and logs for every maintained Asset."""

    label = "Asset Maintenance"
    priority = 90

    def run(self) -> None:
        cfg = self.ctx.industry_config
        asset_names = self.ctx.cache_get("asset_names", [])
        directory = self.ctx.cache_get("employee_directory", [])
        if "Assets" not in cfg.modules or not asset_names or not directory:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        today = date.today()
        past_due = today - timedelta(days=45)
        rng = self.ctx.random

        payload = {
            "company": company,
            "assets": [
                {"asset_name": name, "assign_to": rng.choice(directory)["user"]}
                for name in asset_names
            ],
            "past_due": past_due.isoformat(),
            "completion_date": (today - timedelta(days=42)).isoformat(),
        }
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']

if not frappe.db.exists('DocType', 'Asset Maintenance'):
    print('Assets: the Assets module is not available on this site, nothing to seed')
    raise SystemExit(0)

team_name = f'Maintenance Team - {{company}}'
if not frappe.db.exists('Asset Maintenance Team', team_name):
    frappe.get_doc({{
        'doctype': 'Asset Maintenance Team',
        'maintenance_team_name': team_name,
        'company': company,
        'maintenance_team_members': [{{
            'team_member': 'Administrator',
            'maintenance_role': 'System Manager',
        }}],
    }}).insert(ignore_permissions=True)
    frappe.db.commit()

created = skipped = errors = 0
for entry in payload['assets']:
    asset = frappe.db.get_value(
        'Asset', {{'asset_name': entry['asset_name'], 'company': company}}, 'name'
    )
    if not asset:
        continue
    if frappe.db.exists('Asset Maintenance', asset):
        skipped += 1
        continue
    try:
        doc = frappe.get_doc({{
            'doctype': 'Asset Maintenance',
            'asset_name': asset,
            'company': company,
            'maintenance_team': team_name,
            'asset_maintenance_tasks': [{{
                'maintenance_task': 'Preventive Maintenance Inspection',
                'maintenance_type': 'Preventive Maintenance',
                'maintenance_status': 'Planned',
                'periodicity': 'Quarterly',
                'start_date': payload['past_due'],
                'certificate_required': 0,
                'assign_to': entry['assign_to'],
                # Due in the past so the auto-created log below is ready to be
                # marked Completed straight away.
                'next_due_date': payload['past_due'],
            }}],
        }})
        doc.insert(ignore_permissions=True)

        # on_update() -> sync_maintenance_tasks() just auto-created one Planned
        # log at the task's next_due_date (see module docstring). Complete and
        # submit it: on_submit() advances the task to its next due date and
        # re-saves it, which auto-creates the next Planned log — now due in
        # the future — without us having to compute that date ourselves.
        task_name = doc.asset_maintenance_tasks[0].name
        log_name = frappe.db.get_value(
            'Asset Maintenance Log',
            {{'task': task_name, 'maintenance_status': ('in', ('Planned', 'Overdue'))}},
            'name',
        )
        log = frappe.get_doc('Asset Maintenance Log', log_name)
        log.maintenance_status = 'Completed'
        log.completion_date = payload['completion_date']
        log.save(ignore_permissions=True)
        log.submit()

        frappe.db.commit()
        created += 1
        print(f'CREATED: Asset Maintenance for {{asset}}')
    except Exception as ex:
        frappe.db.rollback()
        print(f'ERROR Asset Maintenance {{asset}}: {{ex}}')
        errors += 1

frappe.db.commit()
print(f'Asset Maintenance: created={{created}}, skipped={{skipped}}, errors={{errors}}')
if errors:
    raise SystemExit(f'{{errors}} asset maintenance record(s) failed')
"""
        self._exec(script, timeout=300)
