"""
Seeder: Payroll setup for Chemical Manufacturing.

Turns the shop-floor workforce created by the Employee seeder into a payable
one, in the order HRMS needs:

    Holiday List                  — set as the company default; a Salary Slip
                                    cannot be raised without one, and its days
                                    decide the payment days every prorated
                                    component is scaled by
    Salary Component              — the earnings and deductions a payslip is
                                    built from (HRMS ships most of these; the
                                    seeder adds whatever is missing)
    Salary Structure              — one structure, submitted, whose rows are
                                    formulas over `base`
    Salary Structure Assignment   — one per active employee, submitted, whose
                                    `base` is that employee's monthly cost to
                                    company

Without the assignment nothing downstream works: Payroll Entry finds no
employees, and a hand-raised Salary Slip has no structure to read.

The component and structure shapes come from `demostackkit.seeder.payroll`, so
this file only carries what is genuinely industry data — what a chemical plant
pays each role. That module also decides monthly-vs-hourly from the company's
country, which is why a US plant would come out timesheet-based off the same
table.

Idempotent — existing components, structures and assignments are left alone.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder
from demostackkit.seeder.payroll import (
    period_base,
    salary_components,
    structure_plan,
    weekly_offs,
)
from demostackkit.seeder.utils import parse_relative_date

#: Annual cost to company, in the company's currency, for every designation the
#: Employee seeder creates. Mid-market Indian speciality chemicals rates.
ANNUAL_CTC = {
    "Production Manager": 1_140_000,
    "Production Supervisor": 660_000,
    "Shift Supervisor": 576_000,
    "Maintenance Technician": 420_000,
    "Quality Analyst": 456_000,
    "Plant Operator": 384_000,
    "Process Operator": 336_000,
    "Machine Operator": 312_000,
    "Packaging Operator": 264_000,
}

#: Covers an employee hired into a designation this table has not priced — a
#: seeded site should never leave someone unassigned and unpayable.
FALLBACK_CTC = 300_000


class PayrollSeeder(BaseMasterSeeder):
    label = "Payroll Setup"
    priority = 82

    def run(self) -> None:
        cfg = self.ctx.industry_config
        company = self.ctx.cache_get("company_name", cfg.company.name)
        abbr = self.ctx.cache_get("company_abbr", cfg.company.abbr)
        country = cfg.company.country

        plans = structure_plan(country, cfg.company.currency, abbr, ANNUAL_CTC)
        base_by_designation = {
            designation: period_base(ctc, country) for designation, ctc in ANNUAL_CTC.items()
        }

        # Payroll opens with the seeded transaction window rather than today, so
        # the assignments already cover the demo's own date range.
        payroll_start = parse_relative_date(cfg.seed.date_range.start).replace(day=1)

        payload = {
            "company": company,
            "abbr": abbr,
            "currency": cfg.company.currency,
            "country": country,
            "from_date": payroll_start.isoformat(),
            # A year either side of the seeded window, so slips can be raised for
            # any month of the demo and for the year ahead of it.
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
            "fallback_base": period_base(FALLBACK_CTC, country),
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
        # ISO code, which is what the `holidays` package behind get_local_holidays wants.
        'country': (frappe.db.get_value('Country', payload['country'], 'code') or '').upper(),
    }})
    for off in hl['weekly_offs']:
        doc.weekly_off = off
        doc.get_weekly_off_dates()
    # Public holidays are a bonus, not a requirement: an unsupported country or a
    # missing holidays package must not cost the demo its payroll.
    try:
        doc.get_local_holidays()
    except Exception as ex:
        print(f'WARN public holidays skipped for {{payload["country"]}}: {{ex}}')
    doc.insert(ignore_permissions=True)
    print(f'Holiday List: created {{doc.name}} with {{doc.total_holidays}} day(s) off')
else:
    print(f'Holiday List: {{hl["name"]}} already exists')

# Employees inherit the company's list unless they carry their own, so setting it
# here is what makes every seeded employee payable.
if not frappe.db.get_value('Company', company, 'default_holiday_list'):
    frappe.db.set_value('Company', company, 'default_holiday_list', hl['name'])
frappe.db.commit()

# ── Salary Components ────────────────────────────────────────────────────────
# HRMS creates Basic, House Rent Allowance, Provident Fund, Professional Tax and
# Income Tax at install; only the rest are ours to add. Existing components are
# left exactly as they are — the structure's formulas read `base`, never another
# component, so their flags cannot break this structure.
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

    # An assignment cannot start before the employee joined.
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
