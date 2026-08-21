"""
Shared seeder: Maintenance Schedules (submitted) and their Visits.

Needs no per-industry data — it auto-pairs the ``customer_names`` and
``item_codes`` / ``fg_item_codes`` caches (the same way ``ProjectSeeder``
auto-pairs ``customers[index % len(customers)]`` in
``demostackkit/seeder/project_seeders.py``) and no-ops when either cache is
empty, which is what lets ``vanilla`` skip this cleanly: it seeds no
customers or items.

Turns two of each Schedule's generated rows into Maintenance Visits — one
Completed in the past, one still-open in the future — using ERPNext's own
``make_maintenance_visit`` mapper so the Visit inherits the Schedule's
customer/company/item context correctly.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import resolve_saleable_items

#: A span comfortably above ERPNext's validate_dates_with_periodicity floor
#: (90 days for Quarterly, 180 for Half Yearly), so either periodicity validates.
_SCHEDULE_SPAN_DAYS = 370


class MaintenanceContractSeeder(BaseTransactionSeeder):
    """Maintenance Schedules (submitted) and their Visits, for sold goods."""

    label = "Maintenance Contracts"
    priority = 245
    _volume_attr = "maintenance_contracts"
    default_volume = 4

    def run(self) -> None:
        cfg = self.ctx.industry_config
        customers = self.ctx.cache_get("customer_names", [])
        items = resolve_saleable_items(self.ctx)
        if not customers or not items:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        today = date.today()
        rng = self.ctx.random
        periodicities = ["Quarterly", "Half Yearly"]

        start = today - timedelta(days=200)
        end = start + timedelta(days=_SCHEDULE_SPAN_DAYS)

        contracts = []
        for i in range(self.volume):
            periodicity = periodicities[i % len(periodicities)]
            no_of_visits = 4 if periodicity == "Quarterly" else 2
            contracts.append(
                {
                    "customer": customers[i % len(customers)],
                    "item_code": items[rng.randrange(len(items))],
                    "transaction_date": (today - timedelta(days=210)).isoformat(),
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "periodicity": periodicity,
                    "no_of_visits": no_of_visits,
                }
            )

        payload = {"company": company, "today": today.isoformat(), "contracts": contracts}
        payload_json = json.dumps(payload)

        script = f"""
import json
from frappe.utils import getdate

payload = json.loads('''{payload_json}''')
company = payload['company']
today = getdate(payload['today'])

if not frappe.db.exists('DocType', 'Maintenance Schedule'):
    print('Maintenance: doctype not available, nothing to seed')
    raise SystemExit(0)

from erpnext.maintenance.doctype.maintenance_schedule.maintenance_schedule import (
    make_maintenance_visit,
)

sales_person = frappe.db.exists('Sales Person', 'Sales Team')
if not sales_person:
    sales_person = frappe.get_doc({{
        'doctype': 'Sales Person', 'sales_person_name': 'Sales Team', 'is_group': 0,
    }}).insert(ignore_permissions=True).name


def make_visit(schedule_name, row, *, completed):
    visit = make_maintenance_visit(schedule_name, s_id=row.name)
    visit.mntc_date = row.scheduled_date
    visit.status = 'Draft'
    visit.company = company
    visit.customer = frappe.db.get_value('Maintenance Schedule', schedule_name, 'customer')
    for purpose in visit.purposes:
        purpose.work_done = (
            'Routine preventive maintenance completed; unit inspected and serviced.'
            if completed else
            'Visit scheduled; service not yet performed.'
        )
    visit.completion_status = 'Fully Completed' if completed else 'Partially Completed'
    visit.insert(ignore_permissions=True)
    if completed:
        visit.submit()
    frappe.db.commit()


created = visits_created = errors = 0
for c in payload['contracts']:
    try:
        ms = frappe.get_doc({{
            'doctype': 'Maintenance Schedule',
            'customer': c['customer'],
            'company': company,
            'transaction_date': c['transaction_date'],
            'items': [{{
                'item_code': c['item_code'],
                'start_date': c['start_date'],
                'end_date': c['end_date'],
                'periodicity': c['periodicity'],
                'no_of_visits': c['no_of_visits'],
                'sales_person': sales_person,
            }}],
        }})
        ms.insert(ignore_permissions=True)
        ms.submit()
        frappe.db.commit()
        created += 1

        rows = sorted(ms.schedules, key=lambda r: getdate(r.scheduled_date))
        past_rows = [r for r in rows if getdate(r.scheduled_date) <= today]
        future_rows = [r for r in rows if getdate(r.scheduled_date) > today]

        if past_rows:
            make_visit(ms.name, past_rows[-1], completed=True)
            visits_created += 1
        if future_rows:
            make_visit(ms.name, future_rows[0], completed=False)
            visits_created += 1
        print(f'CREATED: Maintenance Schedule {{ms.name}} for {{c["customer"]}}')
    except Exception as ex:
        frappe.db.rollback()
        print(f"ERROR Maintenance Schedule for {{c['customer']}}: {{ex}}")
        errors += 1

frappe.db.commit()
print(f'Maintenance Schedules: created={{created}}, visits={{visits_created}}, errors={{errors}}')
if errors:
    raise SystemExit(f'{{errors}} maintenance schedule(s) failed')
"""
        self._exec(script, timeout=300)
