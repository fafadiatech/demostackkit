"""
Seeder: Staff for Ingredient Trading & Distribution.

Creates warehouse, procurement and dispatch staff for demo payroll and HRMS.
Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

DESIGNATIONS = [
    "Warehouse Manager",
    "Procurement Executive",
    "Dispatch Supervisor",
    "Quality & Compliance Coordinator",
    "Sales Executive",
    "Accounts Executive",
]

EMPLOYEES = [
    {
        "first_name": "Deepak",
        "last_name": "Chauhan",
        "gender": "Male",
        "designation": "Warehouse Manager",
        "department": "Warehouse",
        "date_of_birth": "1979-04-14",
        "date_of_joining": "2012-09-02",
    },
    {
        "first_name": "Suresh",
        "last_name": "Iyer",
        "gender": "Male",
        "designation": "Procurement Executive",
        "department": "Buying",
        "date_of_birth": "1987-02-19",
        "date_of_joining": "2016-05-23",
    },
    {
        "first_name": "Ramesh",
        "last_name": "Naik",
        "gender": "Male",
        "designation": "Dispatch Supervisor",
        "department": "Warehouse",
        "date_of_birth": "1990-08-07",
        "date_of_joining": "2018-01-15",
    },
    {
        "first_name": "Farida",
        "last_name": "Shaikh",
        "gender": "Female",
        "designation": "Quality & Compliance Coordinator",
        "department": "Quality",
        "date_of_birth": "1988-11-30",
        "date_of_joining": "2017-07-10",
    },
    {
        "first_name": "Ananya",
        "last_name": "Rao",
        "gender": "Female",
        "designation": "Sales Executive",
        "department": "Sales",
        "date_of_birth": "1992-06-21",
        "date_of_joining": "2019-10-01",
    },
    {
        "first_name": "Karan",
        "last_name": "Mehta",
        "gender": "Male",
        "designation": "Accounts Executive",
        "department": "Accounts",
        "date_of_birth": "1994-01-09",
        "date_of_joining": "2020-03-16",
    },
]


class EmployeeSeeder(BaseMasterSeeder):
    label = "Ingredient Trading Staff"
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
