"""
Seeder: Staff for FMCG Distribution.

Creates warehouse, dispatch and sales staff for demo payroll and HRMS.
Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

DESIGNATIONS = [
    "Warehouse Manager",
    "Dispatch Supervisor",
    "Warehouse Picker",
    "Delivery Driver",
    "Sales Representative",
    "Accounts Executive",
]

EMPLOYEES = [
    {
        "first_name": "Harish",
        "last_name": "Reddy",
        "gender": "Male",
        "designation": "Warehouse Manager",
        "department": "Warehouse",
        "date_of_birth": "1980-01-22",
        "date_of_joining": "2013-06-03",
    },
    {
        "first_name": "Manoj",
        "last_name": "Verma",
        "gender": "Male",
        "designation": "Dispatch Supervisor",
        "department": "Warehouse",
        "date_of_birth": "1986-07-11",
        "date_of_joining": "2015-11-18",
    },
    {
        "first_name": "Ravi",
        "last_name": "Kumar",
        "gender": "Male",
        "designation": "Warehouse Picker",
        "department": "Warehouse",
        "date_of_birth": "1992-03-05",
        "date_of_joining": "2018-04-09",
    },
    {
        "first_name": "Sunil",
        "last_name": "Pandey",
        "gender": "Male",
        "designation": "Delivery Driver",
        "department": "Warehouse",
        "date_of_birth": "1989-10-28",
        "date_of_joining": "2017-02-14",
    },
    {
        "first_name": "Neha",
        "last_name": "Kapoor",
        "gender": "Female",
        "designation": "Sales Representative",
        "department": "Sales",
        "date_of_birth": "1991-05-16",
        "date_of_joining": "2019-08-01",
    },
    {
        "first_name": "Pooja",
        "last_name": "Sharma",
        "gender": "Female",
        "designation": "Accounts Executive",
        "department": "Accounts",
        "date_of_birth": "1993-12-08",
        "date_of_joining": "2020-01-06",
    },
]


class EmployeeSeeder(BaseMasterSeeder):
    label = "Distribution Staff"
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
