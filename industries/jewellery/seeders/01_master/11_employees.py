"""
Seeder: Production Employees for Jewellery Manufacturing.

Creates the shop-floor workforce that Job Cards are allocated to — melting
and casting operators, filing and stone-setting artisans, polishers and
hallmarking technicians. Job Card assigns work via its `employee` table (Job
Card Time Log rows), so without these records no Job Card can be allocated
to anyone.

Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

# Designations created on demand — ERPNext's standard set has no shop-floor roles.
DESIGNATIONS = [
    "Production Manager",
    "Karigar Supervisor",
    "Melting Furnace Operator",
    "Rolling Mill Operator",
    "Casting Technician",
    "Filing & Shaping Artisan",
    "Stone Setter",
    "Polishing Artisan",
    "Hallmarking Technician",
    "QC Inspector",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Mahendra",
        "last_name": "Soni",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1976-06-11",
        "date_of_joining": "2012-01-09",
    },
    {
        "first_name": "Kavita",
        "last_name": "Verma",
        "gender": "Female",
        "designation": "Karigar Supervisor",
        "department": "Production",
        "date_of_birth": "1985-02-27",
        "date_of_joining": "2014-08-18",
    },
    {
        "first_name": "Jitendra",
        "last_name": "Sonkar",
        "gender": "Male",
        "designation": "Melting Furnace Operator",
        "department": "Production",
        "date_of_birth": "1988-10-05",
        "date_of_joining": "2016-05-23",
    },
    {
        "first_name": "Ramesh",
        "last_name": "Vishwakarma",
        "gender": "Male",
        "designation": "Rolling Mill Operator",
        "department": "Production",
        "date_of_birth": "1990-01-16",
        "date_of_joining": "2017-09-11",
    },
    {
        "first_name": "Sunil",
        "last_name": "Zaveri",
        "gender": "Male",
        "designation": "Casting Technician",
        "department": "Production",
        "date_of_birth": "1991-07-03",
        "date_of_joining": "2018-06-04",
    },
    {
        "first_name": "Asha",
        "last_name": "Panchal",
        "gender": "Female",
        "designation": "Filing & Shaping Artisan",
        "department": "Production",
        "date_of_birth": "1993-12-12",
        "date_of_joining": "2019-10-21",
    },
    {
        "first_name": "Deepak",
        "last_name": "Meena",
        "gender": "Male",
        "designation": "Stone Setter",
        "department": "Production",
        "date_of_birth": "1989-04-19",
        "date_of_joining": "2017-02-06",
    },
    {
        "first_name": "Poonam",
        "last_name": "Jain",
        "gender": "Female",
        "designation": "Polishing Artisan",
        "department": "Production",
        "date_of_birth": "1994-09-08",
        "date_of_joining": "2020-05-11",
    },
    {
        "first_name": "Alok",
        "last_name": "Bhandari",
        "gender": "Male",
        "designation": "Hallmarking Technician",
        "department": "Quality Management",
        "date_of_birth": "1992-03-23",
        "date_of_joining": "2019-01-14",
    },
    {
        "first_name": "Snehal",
        "last_name": "Thakkar",
        "gender": "Female",
        "designation": "QC Inspector",
        "department": "Quality Management",
        "date_of_birth": "1995-11-01",
        "date_of_joining": "2021-04-12",
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
