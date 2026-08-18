"""
Seeder: Production Employees for Chemical Manufacturing.

Creates the shop-floor workforce that Job Cards are allocated to — plant and
process operators, shift supervisors, maintenance and QC analysts. Job Card
assigns work via its `employee` table (Job Card Time Log rows), so without
these records no Job Card can be allocated to anyone.

Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

# Designations created on demand — ERPNext's standard set has no shop-floor roles.
DESIGNATIONS = [
    "Production Manager",
    "Production Supervisor",
    "Shift Supervisor",
    "Plant Operator",
    "Process Operator",
    "Machine Operator",
    "Packaging Operator",
    "Maintenance Technician",
    "Quality Analyst",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Ramesh",
        "last_name": "Deshpande",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1978-04-12",
        "date_of_joining": "2014-06-02",
    },
    {
        "first_name": "Sunita",
        "last_name": "Kulkarni",
        "gender": "Female",
        "designation": "Production Supervisor",
        "department": "Production",
        "date_of_birth": "1985-09-23",
        "date_of_joining": "2017-02-15",
    },
    {
        "first_name": "Vijay",
        "last_name": "Sawant",
        "gender": "Male",
        "designation": "Shift Supervisor",
        "department": "Production",
        "date_of_birth": "1988-11-30",
        "date_of_joining": "2016-11-21",
    },
    {
        "first_name": "Anil",
        "last_name": "Pawar",
        "gender": "Male",
        "designation": "Plant Operator",
        "department": "Production",
        "date_of_birth": "1990-01-08",
        "date_of_joining": "2018-07-10",
    },
    {
        "first_name": "Prakash",
        "last_name": "Jadhav",
        "gender": "Male",
        "designation": "Process Operator",
        "department": "Production",
        "date_of_birth": "1992-03-17",
        "date_of_joining": "2019-04-01",
    },
    {
        "first_name": "Deepa",
        "last_name": "Bhosale",
        "gender": "Female",
        "designation": "Process Operator",
        "department": "Production",
        "date_of_birth": "1993-06-05",
        "date_of_joining": "2020-01-13",
    },
    {
        "first_name": "Mahesh",
        "last_name": "Gaikwad",
        "gender": "Male",
        "designation": "Machine Operator",
        "department": "Production",
        "date_of_birth": "1991-08-19",
        "date_of_joining": "2019-09-02",
    },
    {
        "first_name": "Kiran",
        "last_name": "More",
        "gender": "Female",
        "designation": "Packaging Operator",
        "department": "Production",
        "date_of_birth": "1995-02-27",
        "date_of_joining": "2021-08-09",
    },
    {
        "first_name": "Nitin",
        "last_name": "Shinde",
        "gender": "Male",
        "designation": "Maintenance Technician",
        "department": "Production",
        "date_of_birth": "1987-02-25",
        "date_of_joining": "2016-03-14",
    },
    {
        "first_name": "Shalini",
        "last_name": "Rane",
        "gender": "Female",
        "designation": "Quality Analyst",
        "department": "Quality Management",
        "date_of_birth": "1994-12-02",
        "date_of_joining": "2021-05-17",
    },
    {
        "first_name": "Amit",
        "last_name": "Chavan",
        "gender": "Male",
        "designation": "Quality Analyst",
        "department": "Quality Management",
        "date_of_birth": "1989-07-11",
        "date_of_joining": "2018-02-05",
    },
]


class EmployeeSeeder(BaseMasterSeeder):
    label = "Production Employees"
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
    # ERPNext creates departments suffixed with the company abbr.
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
