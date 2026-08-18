"""
Seeder: Production Employees for Ceramics Manufacturing.

Creates the shop-floor workforce that Job Cards are allocated to — throwing
and casting artisans, kiln operators, glazing technicians and QC inspectors.
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
    "Kiln Supervisor",
    "Throwing Artisan",
    "Casting Operator",
    "Trimming & Finishing Artisan",
    "Glazing Technician",
    "Kiln Operator",
    "QC Inspector",
    "Packaging Operator",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Suresh",
        "last_name": "Prajapati",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1979-05-14",
        "date_of_joining": "2013-07-01",
    },
    {
        "first_name": "Latika",
        "last_name": "Chitnis",
        "gender": "Female",
        "designation": "Kiln Supervisor",
        "department": "Production",
        "date_of_birth": "1986-10-02",
        "date_of_joining": "2016-04-11",
    },
    {
        "first_name": "Ganesh",
        "last_name": "Kumbhar",
        "gender": "Male",
        "designation": "Throwing Artisan",
        "department": "Production",
        "date_of_birth": "1989-03-21",
        "date_of_joining": "2017-08-16",
    },
    {
        "first_name": "Rohini",
        "last_name": "Salvi",
        "gender": "Female",
        "designation": "Casting Operator",
        "department": "Production",
        "date_of_birth": "1993-07-09",
        "date_of_joining": "2019-11-04",
    },
    {
        "first_name": "Dattatray",
        "last_name": "More",
        "gender": "Male",
        "designation": "Trimming & Finishing Artisan",
        "department": "Production",
        "date_of_birth": "1990-12-18",
        "date_of_joining": "2018-05-21",
    },
    {
        "first_name": "Sneha",
        "last_name": "Wagh",
        "gender": "Female",
        "designation": "Glazing Technician",
        "department": "Production",
        "date_of_birth": "1994-04-26",
        "date_of_joining": "2020-09-14",
    },
    {
        "first_name": "Anita",
        "last_name": "Kadam",
        "gender": "Female",
        "designation": "Glazing Technician",
        "department": "Production",
        "date_of_birth": "1991-09-25",
        "date_of_joining": "2018-10-22",
    },
    {
        "first_name": "Balaji",
        "last_name": "Shelke",
        "gender": "Male",
        "designation": "Kiln Operator",
        "department": "Production",
        "date_of_birth": "1988-08-07",
        "date_of_joining": "2016-12-05",
    },
    {
        "first_name": "Manisha",
        "last_name": "Patil",
        "gender": "Female",
        "designation": "QC Inspector",
        "department": "Quality Management",
        "date_of_birth": "1992-01-30",
        "date_of_joining": "2019-02-18",
    },
    {
        "first_name": "Yogesh",
        "last_name": "Thorat",
        "gender": "Male",
        "designation": "Packaging Operator",
        "department": "Dispatch",
        "date_of_birth": "1995-06-11",
        "date_of_joining": "2021-03-08",
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
