"""
Shared seeder: Timesheets logged against seeded project tasks.

Tasks alone give a demo a plan but no actuals — `actual_time` stays zero, the
project's costing panel is blank, and Project Profitability has nothing to
report. Submitting a Timesheet is what writes `actual_time`, `act_start_date`
and `act_end_date` back onto the Task and refreshes the Project's costing.

Two ERPNext behaviours shape this seeder:

    Overlap validation
        Two time logs for the same employee may not overlap, drafts included,
        and an identical or fully enclosing interval counts as an overlap. The
        slot allocation in `demostackkit.seeder.projects.timesheet_entries`
        hands out each (employee, day, slot) triple at most once, which is what
        keeps that check quiet.

    Open -> Working
        `Task.update_time_and_costing` silently promotes an Open task to Working
        on submit. That is why this runs at 250, ahead of the status pass in
        `260_task_finalize.py`, rather than after it.

Rates are seeded onto the Activity Type masters rather than onto each row: it is
how a real deployment is configured, and `update_cost` only falls back to the
master when the row's own rate is zero.

Runs for every industry; no-ops when no projects were seeded.
"""

from __future__ import annotations

import json
from datetime import date

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.project_seeders import PROJECT_PLAN_CACHE_KEY
from demostackkit.seeder.projects import activity_rates, timesheet_entries


class ProjectTimesheetSeeder(BaseTransactionSeeder):
    label = "Project Timesheets"
    priority = 250
    _volume_attr = "timesheets"
    default_volume = 40

    def run(self) -> None:
        cfg = self.ctx.industry_config
        plans = self.ctx.cache_get(PROJECT_PLAN_CACHE_KEY) or []
        if not plans:
            return

        entries = timesheet_entries(plans, date.today(), self.ctx.random, limit=self.volume)
        if not entries:
            return

        # Resolve subjects to the docnames the Projects seeder actually created.
        docnames = {plan["name"]: plan.get("docnames", {}).get("tasks", {}) for plan in plans}
        projects = {plan["name"]: plan.get("docnames", {}).get("project") for plan in plans}

        rows = []
        for entry in entries:
            task = docnames.get(entry["project"], {}).get(entry["task_subject"])
            project = projects.get(entry["project"])
            if not task or not project:
                continue
            rows.append({**entry, "task": task, "project_name": project})

        if not rows:
            return

        payload = {
            "company": self.ctx.cache_get("company_name", cfg.company.name),
            "currency": cfg.company.currency,
            "rates": activity_rates(cfg.company.currency),
            "rows": rows,
        }
        payload_json = json.dumps(payload)

        script = f"""
import json
from collections import defaultdict

from frappe.utils import getdate

payload = json.loads('''{payload_json}''')
company = payload['company']

if not frappe.db.exists('DocType', 'Timesheet'):
    print('Timesheets: doctype not available on this site, nothing to seed')
    raise SystemExit(0)

# ── Activity Type rates ──────────────────────────────────────────────────────
# update_cost only reads these when the timesheet row's own rate is zero, so
# setting them here prices every seeded row without touching any of them.
rated = 0
for name, rate in payload['rates'].items():
    if not frappe.db.exists('Activity Type', name):
        frappe.get_doc({{'doctype': 'Activity Type', 'activity_type': name}}).insert(
            ignore_permissions=True
        )
    if not frappe.db.get_value('Activity Type', name, 'costing_rate'):
        frappe.db.set_value('Activity Type', name, {{
            'costing_rate': rate['costing_rate'],
            'billing_rate': rate['billing_rate'],
        }})
        rated += 1
frappe.db.commit()
print(f'Activity Types: priced={{rated}}')

# ── Timesheets ───────────────────────────────────────────────────────────────
# One document per employee per ISO week: a single timesheet spanning months
# reads wrong, and one per row would bury the list view.
buckets = defaultdict(list)
for row in payload['rows']:
    year, week, _ = getdate(row['from_time'][:10]).isocalendar()
    buckets[(row['employee'], year, week)].append(row)

created = errors = 0

for (employee, year, week), rows in sorted(buckets.items()):
    try:
        ts = frappe.get_doc({{
            'doctype': 'Timesheet',
            'company': company,
            'employee': employee,
            'currency': payload['currency'],
            'time_logs': [
                {{
                    'activity_type': r['activity_type'],
                    'from_time': r['from_time'],
                    # to_time is recomputed from from_time + hours in validate,
                    # so supplying hours alone is both sufficient and safer.
                    'hours': r['hours'],
                    # billing_hours has to be explicit: billing_amount is
                    # computed before update_billing_hours defaults it, so
                    # leaving it blank zeroes the amount on the first pass.
                    'billing_hours': r['billing_hours'],
                    'is_billable': r['is_billable'],
                    'project': r['project_name'],
                    'task': r['task'],
                    'description': r['description'],
                }}
                for r in rows
            ],
        }})
        ts.insert(ignore_permissions=True)
        ts.submit()
        created += 1
    except Exception as ex:
        print(f'WARN Timesheet {{employee}} {{year}}-W{{week}}: {{ex}}')
        errors += 1

frappe.db.commit()
print(f'Timesheets: created={{created}}, failed={{errors}}')
"""
        self._exec(script, timeout=600)
