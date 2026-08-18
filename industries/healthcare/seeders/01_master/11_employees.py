"""
Seeder: Staff for Healthcare & Pharma.

Creates clinical and administrative staff for demo payroll and HRMS.
Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

DESIGNATIONS = [
    "Hospital Administrator",
    "Pharmacist",
    "Lab Technician",
    "Staff Nurse",
    "Store Manager",
    "Billing Executive",
]

EMPLOYEES = [
    {
        "first_name": "Dr. Anita",
        "last_name": "Desai",
        "gender": "Female",
        "designation": "Hospital Administrator",
        "department": "Administration",
        "date_of_birth": "1976-05-20",
        "date_of_joining": "2010-01-04",
    },
    {
        "first_name": "Vikram",
        "last_name": "Pillai",
        "gender": "Male",
        "designation": "Pharmacist",
        "department": "Pharmacy",
        "date_of_birth": "1987-09-12",
        "date_of_joining": "2015-06-15",
    },
    {
        "first_name": "Sneha",
        "last_name": "Rao",
        "gender": "Female",
        "designation": "Lab Technician",
        "department": "Laboratory",
        "date_of_birth": "1991-03-28",
        "date_of_joining": "2018-02-19",
    },
    {
        "first_name": "Lakshmi",
        "last_name": "Iyer",
        "gender": "Female",
        "designation": "Staff Nurse",
        "department": "Nursing",
        "date_of_birth": "1990-11-07",
        "date_of_joining": "2016-08-08",
    },
    {
        "first_name": "Rahul",
        "last_name": "Menon",
        "gender": "Male",
        "designation": "Store Manager",
        "department": "Stores",
        "date_of_birth": "1984-07-03",
        "date_of_joining": "2014-04-21",
    },
    {
        "first_name": "Divya",
        "last_name": "Krishnan",
        "gender": "Female",
        "designation": "Billing Executive",
        "department": "Accounts",
        "date_of_birth": "1993-01-14",
        "date_of_joining": "2019-10-01",
    },
]


class EmployeeSeeder(BaseMasterSeeder):
    label = "Healthcare Staff"
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
