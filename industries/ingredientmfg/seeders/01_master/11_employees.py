"""
Seeder: Production Employees for Ingredient Manufacturing.

Creates the shop-floor workforce that Job Cards are allocated to — plant and
extraction operators, shift supervisors, maintenance staff and QC chemists.
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
    "Production Supervisor",
    "Shift Supervisor",
    "Plant Operator",
    "Extraction Operator",
    "Packaging Operator",
    "Maintenance Technician",
    "QC Chemist",
    "Microbiologist",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Suresh",
        "last_name": "Naidu",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1977-05-18",
        "date_of_joining": "2013-08-11",
    },
    {
        "first_name": "Lakshmi",
        "last_name": "Rao",
        "gender": "Female",
        "designation": "Production Supervisor",
        "department": "Production",
        "date_of_birth": "1986-02-09",
        "date_of_joining": "2016-04-04",
    },
    {
        "first_name": "Dinesh",
        "last_name": "Kamble",
        "gender": "Male",
        "designation": "Shift Supervisor",
        "department": "Production",
        "date_of_birth": "1989-10-14",
        "date_of_joining": "2017-09-19",
    },
    {
        "first_name": "Ravindra",
        "last_name": "Patil",
        "gender": "Male",
        "designation": "Plant Operator",
        "department": "Production",
        "date_of_birth": "1991-06-22",
        "date_of_joining": "2018-11-05",
    },
    {
        "first_name": "Suman",
        "last_name": "Reddy",
        "gender": "Female",
        "designation": "Extraction Operator",
        "department": "Production",
        "date_of_birth": "1992-12-01",
        "date_of_joining": "2019-06-17",
    },
    {
        "first_name": "Manoj",
        "last_name": "Yadav",
        "gender": "Male",
        "designation": "Extraction Operator",
        "department": "Production",
        "date_of_birth": "1993-03-27",
        "date_of_joining": "2020-02-10",
    },
    {
        "first_name": "Pooja",
        "last_name": "Nair",
        "gender": "Female",
        "designation": "Packaging Operator",
        "department": "Production",
        "date_of_birth": "1995-08-06",
        "date_of_joining": "2021-07-01",
    },
    {
        "first_name": "Ashok",
        "last_name": "Waghmare",
        "gender": "Male",
        "designation": "Maintenance Technician",
        "department": "Production",
        "date_of_birth": "1987-01-16",
        "date_of_joining": "2015-12-08",
    },
    {
        "first_name": "Divya",
        "last_name": "Krishnan",
        "gender": "Female",
        "designation": "QC Chemist",
        "department": "Quality Management",
        "date_of_birth": "1994-11-20",
        "date_of_joining": "2021-03-15",
    },
    {
        "first_name": "Arvind",
        "last_name": "Bose",
        "gender": "Male",
        "designation": "QC Chemist",
        "department": "Quality Management",
        "date_of_birth": "1990-04-03",
        "date_of_joining": "2017-10-23",
    },
    {
        "first_name": "Neha",
        "last_name": "Iyer",
        "gender": "Female",
        "designation": "Microbiologist",
        "department": "Quality Management",
        "date_of_birth": "1993-09-12",
        "date_of_joining": "2020-05-26",
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
