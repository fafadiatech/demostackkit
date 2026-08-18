"""
Seeder: Production Employees for Electrical Equipment Manufacturing.

Creates the shop-floor workforce that Job Cards are allocated to — coil
winding and core assembly technicians, tank fabricators, HV test engineers
and switchgear assemblers. Job Card assigns work via its `employee` table
(Job Card Time Log rows), so without these records no Job Card can be
allocated to anyone.

Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

# Designations created on demand — ERPNext's standard set has no shop-floor roles.
DESIGNATIONS = [
    "Production Manager",
    "Shop Floor Supervisor",
    "Coil Winding Technician",
    "Core Assembly Technician",
    "Tank Fabricator",
    "Oil Filling Operator",
    "HV Test Engineer",
    "Switchgear Assembler",
    "QC Inspector",
    "Dispatch Operator",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Mohan",
        "last_name": "Kulkarni",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1977-08-25",
        "date_of_joining": "2012-05-14",
    },
    {
        "first_name": "Vaishali",
        "last_name": "Deshmukh",
        "gender": "Female",
        "designation": "Shop Floor Supervisor",
        "department": "Production",
        "date_of_birth": "1985-01-11",
        "date_of_joining": "2015-09-01",
    },
    {
        "first_name": "Ravi",
        "last_name": "Bhosale",
        "gender": "Male",
        "designation": "Coil Winding Technician",
        "department": "Production",
        "date_of_birth": "1990-06-19",
        "date_of_joining": "2017-03-20",
    },
    {
        "first_name": "Sadhana",
        "last_name": "Pawar",
        "gender": "Female",
        "designation": "Core Assembly Technician",
        "department": "Production",
        "date_of_birth": "1992-10-07",
        "date_of_joining": "2018-12-10",
    },
    {
        "first_name": "Ashok",
        "last_name": "Jagtap",
        "gender": "Male",
        "designation": "Tank Fabricator",
        "department": "Production",
        "date_of_birth": "1986-03-29",
        "date_of_joining": "2015-11-16",
    },
    {
        "first_name": "Prashant",
        "last_name": "Kale",
        "gender": "Male",
        "designation": "Oil Filling Operator",
        "department": "Production",
        "date_of_birth": "1991-12-23",
        "date_of_joining": "2019-01-21",
    },
    {
        "first_name": "Neelam",
        "last_name": "Joshi",
        "gender": "Female",
        "designation": "HV Test Engineer",
        "department": "Quality Management",
        "date_of_birth": "1989-05-05",
        "date_of_joining": "2016-08-08",
    },
    {
        "first_name": "Sachin",
        "last_name": "Mane",
        "gender": "Male",
        "designation": "Switchgear Assembler",
        "department": "Production",
        "date_of_birth": "1993-09-14",
        "date_of_joining": "2020-02-17",
    },
    {
        "first_name": "Rupali",
        "last_name": "Salunkhe",
        "gender": "Female",
        "designation": "QC Inspector",
        "department": "Quality Management",
        "date_of_birth": "1994-07-02",
        "date_of_joining": "2020-10-05",
    },
    {
        "first_name": "Ganesh",
        "last_name": "Phadke",
        "gender": "Male",
        "designation": "Dispatch Operator",
        "department": "Dispatch",
        "date_of_birth": "1995-11-28",
        "date_of_joining": "2021-06-14",
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
