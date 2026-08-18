"""
Seeder: Staff for Automobile Dealership & Service.

Creates the sales, service and parts workforce for demo payroll and HRMS.
Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

DESIGNATIONS = [
    "Service Manager",
    "Sales Executive",
    "Service Advisor",
    "Senior Mechanic",
    "Mechanic",
    "Parts Executive",
    "Receptionist",
]

EMPLOYEES = [
    {
        "first_name": "Rajesh",
        "last_name": "Malhotra",
        "gender": "Male",
        "designation": "Service Manager",
        "department": "Service",
        "date_of_birth": "1979-06-14",
        "date_of_joining": "2012-04-01",
    },
    {
        "first_name": "Priya",
        "last_name": "Nair",
        "gender": "Female",
        "designation": "Sales Executive",
        "department": "Sales",
        "date_of_birth": "1990-02-28",
        "date_of_joining": "2018-07-16",
    },
    {
        "first_name": "Suresh",
        "last_name": "Patil",
        "gender": "Male",
        "designation": "Service Advisor",
        "department": "Service",
        "date_of_birth": "1988-11-03",
        "date_of_joining": "2016-09-12",
    },
    {
        "first_name": "Dinesh",
        "last_name": "Yadav",
        "gender": "Male",
        "designation": "Senior Mechanic",
        "department": "Service",
        "date_of_birth": "1985-08-19",
        "date_of_joining": "2014-03-24",
    },
    {
        "first_name": "Imran",
        "last_name": "Shaikh",
        "gender": "Male",
        "designation": "Mechanic",
        "department": "Service",
        "date_of_birth": "1993-04-07",
        "date_of_joining": "2019-01-08",
    },
    {
        "first_name": "Kavita",
        "last_name": "Desai",
        "gender": "Female",
        "designation": "Parts Executive",
        "department": "Spare Parts",
        "date_of_birth": "1991-12-15",
        "date_of_joining": "2017-05-22",
    },
    {
        "first_name": "Anjali",
        "last_name": "Mehta",
        "gender": "Female",
        "designation": "Receptionist",
        "department": "Administration",
        "date_of_birth": "1996-09-30",
        "date_of_joining": "2021-02-01",
    },
]


class EmployeeSeeder(BaseMasterSeeder):
    label = "Dealership Staff"
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
