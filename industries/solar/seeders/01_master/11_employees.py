"""
Seeder: Production Employees for Solar Installation.

Creates the shop-floor workforce that Job Cards are allocated to — panel
assembly and cable technicians, inverter technicians, commissioning
engineers and site safety officers. Job Card assigns work via its `employee`
table (Job Card Time Log rows), so without these records no Job Card can be
allocated to anyone.

Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

# Designations created on demand — ERPNext's standard set has no shop-floor roles.
DESIGNATIONS = [
    "Production Manager",
    "Installation Supervisor",
    "Panel Assembly Technician",
    "Cable Technician",
    "Inverter Technician",
    "Commissioning Engineer",
    "QC Inspector",
    "Site Safety Officer",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Vikas",
        "last_name": "Chandra",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1980-11-06",
        "date_of_joining": "2014-04-21",
    },
    {
        "first_name": "Preeti",
        "last_name": "Saxena",
        "gender": "Female",
        "designation": "Installation Supervisor",
        "department": "Production",
        "date_of_birth": "1987-03-15",
        "date_of_joining": "2016-09-12",
    },
    {
        "first_name": "Sandeep",
        "last_name": "Rathore",
        "gender": "Male",
        "designation": "Panel Assembly Technician",
        "department": "Production",
        "date_of_birth": "1991-09-28",
        "date_of_joining": "2018-08-06",
    },
    {
        "first_name": "Neha",
        "last_name": "Agarwal",
        "gender": "Female",
        "designation": "Panel Assembly Technician",
        "department": "Production",
        "date_of_birth": "1993-02-08",
        "date_of_joining": "2019-12-02",
    },
    {
        "first_name": "Manoj",
        "last_name": "Tiwari",
        "gender": "Male",
        "designation": "Cable Technician",
        "department": "Production",
        "date_of_birth": "1989-07-20",
        "date_of_joining": "2017-06-19",
    },
    {
        "first_name": "Kiran",
        "last_name": "Bhatt",
        "gender": "Male",
        "designation": "Inverter Technician",
        "department": "Production",
        "date_of_birth": "1990-04-11",
        "date_of_joining": "2018-03-05",
    },
    {
        "first_name": "Swati",
        "last_name": "Mishra",
        "gender": "Female",
        "designation": "Commissioning Engineer",
        "department": "Production",
        "date_of_birth": "1992-08-25",
        "date_of_joining": "2019-07-15",
    },
    {
        "first_name": "Rajiv",
        "last_name": "Khanna",
        "gender": "Male",
        "designation": "QC Inspector",
        "department": "Quality Management",
        "date_of_birth": "1988-12-14",
        "date_of_joining": "2017-05-08",
    },
    {
        "first_name": "Farida",
        "last_name": "Sheikh",
        "gender": "Female",
        "designation": "Site Safety Officer",
        "department": "Operations",
        "date_of_birth": "1994-10-30",
        "date_of_joining": "2020-11-16",
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
