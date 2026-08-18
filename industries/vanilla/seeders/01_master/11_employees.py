"""
Seeder: Staff for Vanilla demo company.

Creates a minimal workforce for demo payroll and HRMS (US hourly payroll).
Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

DESIGNATIONS = [
    "General Manager",
    "Accountant",
    "Sales Representative",
    "Warehouse Associate",
]

EMPLOYEES = [
    {
        "first_name": "John",
        "last_name": "Smith",
        "gender": "Male",
        "designation": "General Manager",
        "department": "Management",
        "date_of_birth": "1978-03-15",
        "date_of_joining": "2015-01-05",
    },
    {
        "first_name": "Lisa",
        "last_name": "Johnson",
        "gender": "Female",
        "designation": "Accountant",
        "department": "Accounts",
        "date_of_birth": "1986-07-22",
        "date_of_joining": "2017-04-10",
    },
    {
        "first_name": "Mike",
        "last_name": "Williams",
        "gender": "Male",
        "designation": "Sales Representative",
        "department": "Sales",
        "date_of_birth": "1991-11-08",
        "date_of_joining": "2019-08-19",
    },
    {
        "first_name": "Amy",
        "last_name": "Brown",
        "gender": "Female",
        "designation": "Warehouse Associate",
        "department": "Stores",
        "date_of_birth": "1994-05-03",
        "date_of_joining": "2020-02-24",
    },
]


class EmployeeSeeder(BaseMasterSeeder):
    label = "Company Staff"
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
