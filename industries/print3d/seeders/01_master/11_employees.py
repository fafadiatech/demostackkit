"""
Seeder: Production Employees for 3D Printing Services.

Creates the shop-floor workforce that Job Cards are allocated to — FDM and
SLA print technicians, post-processing and finishing staff, QC inspectors
and shipping associates. Job Card assigns work via its `employee` table (Job
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
    "Print Floor Supervisor",
    "FDM Print Technician",
    "SLA Print Technician",
    "Post-Processing Technician",
    "Finishing Technician",
    "QC Inspector",
    "Shipping Associate",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Daniel",
        "last_name": "Reyes",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1981-05-09",
        "date_of_joining": "2014-09-15",
    },
    {
        "first_name": "Megan",
        "last_name": "Foster",
        "gender": "Female",
        "designation": "Print Floor Supervisor",
        "department": "Production",
        "date_of_birth": "1988-01-24",
        "date_of_joining": "2017-03-06",
    },
    {
        "first_name": "Tyler",
        "last_name": "Brooks",
        "gender": "Male",
        "designation": "FDM Print Technician",
        "department": "Production",
        "date_of_birth": "1994-06-17",
        "date_of_joining": "2020-02-10",
    },
    {
        "first_name": "Andre",
        "last_name": "Jackson",
        "gender": "Male",
        "designation": "FDM Print Technician",
        "department": "Production",
        "date_of_birth": "1991-12-21",
        "date_of_joining": "2018-10-15",
    },
    {
        "first_name": "Priya",
        "last_name": "Raman",
        "gender": "Female",
        "designation": "SLA Print Technician",
        "department": "Production",
        "date_of_birth": "1992-11-29",
        "date_of_joining": "2019-05-20",
    },
    {
        "first_name": "Marcus",
        "last_name": "Webb",
        "gender": "Male",
        "designation": "Post-Processing Technician",
        "department": "Production",
        "date_of_birth": "1990-08-13",
        "date_of_joining": "2018-01-08",
    },
    {
        "first_name": "Chloe",
        "last_name": "Bennett",
        "gender": "Female",
        "designation": "Finishing Technician",
        "department": "Production",
        "date_of_birth": "1995-03-02",
        "date_of_joining": "2021-06-07",
    },
    {
        "first_name": "Rachel",
        "last_name": "Kim",
        "gender": "Female",
        "designation": "QC Inspector",
        "department": "Quality Management",
        "date_of_birth": "1993-04-05",
        "date_of_joining": "2019-11-04",
    },
    {
        "first_name": "Owen",
        "last_name": "Delgado",
        "gender": "Male",
        "designation": "Shipping Associate",
        "department": "Dispatch",
        "date_of_birth": "1996-02-18",
        "date_of_joining": "2022-01-10",
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
