"""
Seeder: Staff for EPC (Engineering, Procurement & Construction).

Creates project and site workforce for demo payroll and HRMS.
Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

DESIGNATIONS = [
    "Project Manager",
    "Site Engineer",
    "Quantity Surveyor",
    "Safety Officer",
    "Foreman",
    "Electrician",
    "Plumber",
    "Carpenter",
]

EMPLOYEES = [
    {
        "first_name": "Arun",
        "last_name": "Bhatia",
        "gender": "Male",
        "designation": "Project Manager",
        "department": "Projects",
        "date_of_birth": "1977-04-09",
        "date_of_joining": "2011-08-15",
    },
    {
        "first_name": "Rohit",
        "last_name": "Saxena",
        "gender": "Male",
        "designation": "Site Engineer",
        "department": "Projects",
        "date_of_birth": "1988-06-21",
        "date_of_joining": "2016-03-07",
    },
    {
        "first_name": "Meera",
        "last_name": "Joshi",
        "gender": "Female",
        "designation": "Quantity Surveyor",
        "department": "Projects",
        "date_of_birth": "1990-11-14",
        "date_of_joining": "2018-01-22",
    },
    {
        "first_name": "Sanjay",
        "last_name": "Thakur",
        "gender": "Male",
        "designation": "Safety Officer",
        "department": "Projects",
        "date_of_birth": "1985-02-03",
        "date_of_joining": "2015-09-10",
    },
    {
        "first_name": "Balwant",
        "last_name": "Singh",
        "gender": "Male",
        "designation": "Foreman",
        "department": "Projects",
        "date_of_birth": "1983-08-27",
        "date_of_joining": "2014-05-19",
    },
    {
        "first_name": "Ramesh",
        "last_name": "Yadav",
        "gender": "Male",
        "designation": "Electrician",
        "department": "Projects",
        "date_of_birth": "1991-01-18",
        "date_of_joining": "2019-07-01",
    },
    {
        "first_name": "Mohan",
        "last_name": "Prasad",
        "gender": "Male",
        "designation": "Plumber",
        "department": "Projects",
        "date_of_birth": "1989-09-06",
        "date_of_joining": "2017-11-13",
    },
    {
        "first_name": "Ganesh",
        "last_name": "Mistry",
        "gender": "Male",
        "designation": "Carpenter",
        "department": "Projects",
        "date_of_birth": "1992-12-30",
        "date_of_joining": "2020-04-06",
    },
]


class EmployeeSeeder(BaseMasterSeeder):
    label = "EPC Site Staff"
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
