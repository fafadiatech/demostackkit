"""
Seeder: Staff for Hobby Shop & TCG Retailer.

Creates retail store staff for demo payroll and HRMS (US hourly payroll).
Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

DESIGNATIONS = [
    "Store Manager",
    "Assistant Manager",
    "Sales Associate",
    "Inventory Specialist",
    "Events Coordinator",
]

EMPLOYEES = [
    {
        "first_name": "Marcus",
        "last_name": "Chen",
        "gender": "Male",
        "designation": "Store Manager",
        "department": "Sales",
        "date_of_birth": "1985-04-18",
        "date_of_joining": "2016-03-14",
    },
    {
        "first_name": "Emily",
        "last_name": "Rodriguez",
        "gender": "Female",
        "designation": "Assistant Manager",
        "department": "Sales",
        "date_of_birth": "1990-08-02",
        "date_of_joining": "2019-06-03",
    },
    {
        "first_name": "Jake",
        "last_name": "Thompson",
        "gender": "Male",
        "designation": "Sales Associate",
        "department": "Sales",
        "date_of_birth": "1998-11-25",
        "date_of_joining": "2021-09-07",
    },
    {
        "first_name": "Sarah",
        "last_name": "Kim",
        "gender": "Female",
        "designation": "Inventory Specialist",
        "department": "Stores",
        "date_of_birth": "1992-02-11",
        "date_of_joining": "2018-01-22",
    },
    {
        "first_name": "David",
        "last_name": "Nguyen",
        "gender": "Male",
        "designation": "Events Coordinator",
        "department": "Marketing",
        "date_of_birth": "1994-06-30",
        "date_of_joining": "2020-04-13",
    },
]


class EmployeeSeeder(BaseMasterSeeder):
    label = "Retail Staff"
    priority = 80

    def run(self) -> None:
        company = self.ctx.industry_config.company
        employees_json = json.dumps(EMPLOYEES)
        designations_json = json.dumps(DESIGNATIONS)
        script = f"""
import json

company_name = '{company.name}'
company_abbr = '{company.abbr}'
employees = json.loads('''{employees_json}''')

for d in json.loads('''{designations_json}'''):
    if not frappe.db.exists('Designation', d):
        frappe.get_doc({{'doctype': 'Designation', 'designation_name': d}}).insert(ignore_permissions=True)
frappe.db.commit()

def resolve_department(bare):
    scoped = bare + ' - ' + company_abbr
    if frappe.db.exists('Department', scoped):
        return scoped
    if frappe.db.exists('Department', bare):
        return bare
    return None

created = skipped = errors = 0
names = []

for e in employees:
    full_name = e['first_name'] + ' ' + e['last_name']
    existing = frappe.db.get_value(
        'Employee', {{'employee_name': full_name, 'company': company_name}}, 'name'
    )
    if existing:
        names.append(existing)
        skipped += 1
        continue
    try:
        doc = frappe.get_doc({{
            'doctype': 'Employee',
            'first_name': e['first_name'],
            'last_name': e['last_name'],
            'company': company_name,
            'gender': e['gender'],
            'date_of_birth': e['date_of_birth'],
            'date_of_joining': e['date_of_joining'],
            'designation': e['designation'],
            'department': resolve_department(e['department']),
            'employment_type': 'Full-time',
            'status': 'Active',
        }})
        doc.insert(ignore_permissions=True)
        names.append(doc.name)
        created += 1
    except Exception as ex:
        print(f'ERROR Employee {{full_name}}: {{ex}}')
        errors += 1

frappe.db.commit()
print(f'Employees: created={{created}}, skipped={{skipped}}, errors={{errors}}')
print('EMPLOYEE_IDS=' + json.dumps(names))
if errors:
    raise SystemExit(f'{{errors}} employee(s) failed to create')
"""
        self._exec(script, timeout=180)
        self.ctx.cache_set(
            "employee_names", [f"{e['first_name']} {e['last_name']}" for e in EMPLOYEES]
        )
