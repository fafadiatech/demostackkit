"""
Seeder: Production Employees for Garment Manufacturing.

Creates the shop-floor workforce that Job Cards are allocated to — cutting
masters, sewing and overlock operators, pressing operators and QC checkers.
Job Card assigns work via its `employee` table (Job Card Time Log rows), so
without these records no Job Card can be allocated to anyone.

Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

# Designations created on demand — ERPNext's standard set has no shop-floor roles.
DESIGNATIONS = [
    "Production Manager",
    "Floor Supervisor",
    "Cutting Master",
    "Sewing Operator",
    "Overlock Operator",
    "Button Machine Operator",
    "Pressing Operator",
    "QC Checker",
    "Packaging Operator",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Ashok",
        "last_name": "Gupta",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1978-09-17",
        "date_of_joining": "2013-03-04",
    },
    {
        "first_name": "Rekha",
        "last_name": "Sharma",
        "gender": "Female",
        "designation": "Floor Supervisor",
        "department": "Production",
        "date_of_birth": "1984-04-22",
        "date_of_joining": "2015-07-13",
    },
    {
        "first_name": "Iqbal",
        "last_name": "Ansari",
        "gender": "Male",
        "designation": "Cutting Master",
        "department": "Production",
        "date_of_birth": "1987-11-08",
        "date_of_joining": "2016-02-15",
    },
    {
        "first_name": "Sarita",
        "last_name": "Devi",
        "gender": "Female",
        "designation": "Sewing Operator",
        "department": "Production",
        "date_of_birth": "1993-01-19",
        "date_of_joining": "2019-06-10",
    },
    {
        "first_name": "Pushpa",
        "last_name": "Yadav",
        "gender": "Female",
        "designation": "Sewing Operator",
        "department": "Production",
        "date_of_birth": "1994-08-30",
        "date_of_joining": "2020-03-16",
    },
    {
        "first_name": "Lakshmi",
        "last_name": "Nair",
        "gender": "Female",
        "designation": "Overlock Operator",
        "department": "Production",
        "date_of_birth": "1992-05-07",
        "date_of_joining": "2018-11-05",
    },
    {
        "first_name": "Ramkumar",
        "last_name": "Singh",
        "gender": "Male",
        "designation": "Button Machine Operator",
        "department": "Production",
        "date_of_birth": "1990-10-14",
        "date_of_joining": "2018-04-02",
    },
    {
        "first_name": "Shabana",
        "last_name": "Qureshi",
        "gender": "Female",
        "designation": "Pressing Operator",
        "department": "Production",
        "date_of_birth": "1991-03-26",
        "date_of_joining": "2017-12-11",
    },
    {
        "first_name": "Nandini",
        "last_name": "Rao",
        "gender": "Female",
        "designation": "QC Checker",
        "department": "Quality Management",
        "date_of_birth": "1995-07-21",
        "date_of_joining": "2021-01-18",
    },
    {
        "first_name": "Vinod",
        "last_name": "Kamble",
        "gender": "Male",
        "designation": "Packaging Operator",
        "department": "Dispatch",
        "date_of_birth": "1989-12-02",
        "date_of_joining": "2017-08-21",
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
