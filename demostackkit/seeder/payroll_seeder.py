"""
Shared PayrollSeeder base for every industry.

Each industry supplies only ``ANNUAL_CTC`` (and optionally ``FALLBACK_CTC``) in its
``12_payroll.py``; this module carries the Frappe script and run logic.
"""

from __future__ import annotations

import json
from collections.abc import Mapping

from demostackkit.seeder.base import BaseMasterSeeder
from demostackkit.seeder.payroll import (
    period_base,
    salary_components,
    structure_plan,
    weekly_offs,
)
from demostackkit.seeder.utils import parse_relative_date

#: Default annual CTC when a designation is not priced — India mid-market operator.
DEFAULT_FALLBACK_CTC = 300_000


class PayrollSeeder(BaseMasterSeeder):
    """Create Holiday List, Salary Components, Structure, and Assignments."""

    label = "Payroll Setup"
    priority = 82

    #: Annual cost to company per designation — set in each industry's ``12_payroll.py``.
    ANNUAL_CTC: Mapping[str, float]
    FALLBACK_CTC: float = DEFAULT_FALLBACK_CTC

    def run(self) -> None:
        cfg = self.ctx.industry_config
        company = self.ctx.cache_get("company_name", cfg.company.name)
        abbr = self.ctx.cache_get("company_abbr", cfg.company.abbr)
        country = cfg.company.country

        plans = structure_plan(country, cfg.company.currency, abbr, self.ANNUAL_CTC)
        base_by_designation = {
            designation: period_base(ctc, country) for designation, ctc in self.ANNUAL_CTC.items()
        }

        payroll_start = parse_relative_date(cfg.seed.date_range.start).replace(day=1)

        payload = {
            "company": company,
            "abbr": abbr,
            "currency": cfg.company.currency,
            "country": country,
            "from_date": payroll_start.isoformat(),
            "holiday_list": {
                "name": f"Demo Holidays - {abbr}",
                "from_date": payroll_start.replace(month=1, day=1).isoformat(),
                "to_date": payroll_start.replace(
                    year=payroll_start.year + 1, month=12, day=31
                ).isoformat(),
                "weekly_offs": weekly_offs(country),
            },
            "components": salary_components(country),
            "structures": plans,
            "base_by_designation": base_by_designation,
            "fallback_base": period_base(self.FALLBACK_CTC, country),
        }
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']

if not frappe.db.exists('DocType', 'Salary Component'):
    print('Payroll: hrms is not installed on this site, nothing to seed')
    raise SystemExit(0)

# ── Holiday List ─────────────────────────────────────────────────────────────
hl = payload['holiday_list']
if not frappe.db.exists('Holiday List', hl['name']):
    doc = frappe.get_doc({{
        'doctype': 'Holiday List',
        'holiday_list_name': hl['name'],
        'from_date': hl['from_date'],
        'to_date': hl['to_date'],
        'country': (frappe.db.get_value('Country', payload['country'], 'code') or '').upper(),
    }})
    for off in hl['weekly_offs']:
        doc.weekly_off = off
        doc.get_weekly_off_dates()
    try:
        doc.get_local_holidays()
    except Exception as ex:
        print(f'WARN public holidays skipped for {{payload["country"]}}: {{ex}}')
    doc.insert(ignore_permissions=True)
    print(f'Holiday List: created {{doc.name}} with {{doc.total_holidays}} day(s) off')
else:
    print(f'Holiday List: {{hl["name"]}} already exists')

if not frappe.db.get_value('Company', company, 'default_holiday_list'):
    frappe.db.set_value('Company', company, 'default_holiday_list', hl['name'])
frappe.db.commit()

# ── Salary Components ────────────────────────────────────────────────────────
comp_created = comp_skipped = 0
for c in payload['components']:
    if frappe.db.exists('Salary Component', c['salary_component']):
        comp_skipped += 1
        continue
    frappe.get_doc(dict(c, doctype='Salary Component')).insert(ignore_permissions=True)
    comp_created += 1
frappe.db.commit()
print(f'Salary Components: created={{comp_created}}, skipped={{comp_skipped}}')

# ── Salary Structures ────────────────────────────────────────────────────────
structure_by_designation = {{}}
default_structure = None
str_created = str_skipped = 0

for s in payload['structures']:
    designations = s.pop('designations')
    if not frappe.db.exists('Salary Structure', s['name']):
        doc = frappe.get_doc(dict(s, doctype='Salary Structure', company=company))
        doc.insert(ignore_permissions=True)
        doc.submit()
        str_created += 1
    else:
        str_skipped += 1
    default_structure = default_structure or s['name']
    for designation in designations:
        structure_by_designation[designation] = s['name']

frappe.db.commit()
print(f'Salary Structures: created={{str_created}}, skipped={{str_skipped}}')

# ── Salary Structure Assignments ─────────────────────────────────────────────
from frappe.utils import getdate

assigned = ssa_skipped = errors = 0

for emp in frappe.get_all(
    'Employee',
    filters={{'company': company, 'status': 'Active'}},
    fields=['name', 'employee_name', 'designation', 'date_of_joining'],
    order_by='name',
):
    structure = structure_by_designation.get(emp.designation, default_structure)
    base = payload['base_by_designation'].get(emp.designation, payload['fallback_base'])
    if emp.designation not in payload['base_by_designation']:
        print(f'WARN {{emp.employee_name}}: designation {{emp.designation!r}} is not priced, using the fallback base')

    if frappe.db.exists(
        'Salary Structure Assignment',
        {{'employee': emp.name, 'salary_structure': structure, 'docstatus': 1}},
    ):
        ssa_skipped += 1
        continue

    from_date = max(getdate(payload['from_date']), getdate(emp.date_of_joining))

    try:
        doc = frappe.get_doc({{
            'doctype': 'Salary Structure Assignment',
            'employee': emp.name,
            'salary_structure': structure,
            'company': company,
            'currency': payload['currency'],
            'from_date': from_date,
            'base': base,
        }})
        doc.insert(ignore_permissions=True)
        doc.submit()
        assigned += 1
    except Exception as ex:
        print(f'ERROR Salary Structure Assignment {{emp.employee_name}}: {{ex}}')
        errors += 1

frappe.db.commit()
print(f'Salary Structure Assignments: created={{assigned}}, skipped={{ssa_skipped}}, errors={{errors}}')
if errors:
    raise SystemExit(f'{{errors}} salary structure assignment(s) failed')
"""
        self._exec(script, timeout=300)
        self.ctx.cache_set("salary_structures", [s["name"] for s in plans])
