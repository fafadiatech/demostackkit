"""
Seeder: Production Employees for Drone Manufacturing.

Creates the shop-floor workforce that Job Cards are allocated to — PCB and
frame assembly technicians, avionics and firmware engineers, flight test
pilots and QC inspectors. Job Card assigns work via its `employee` table
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
    "Assembly Supervisor",
    "PCB Assembly Technician",
    "Frame Assembly Technician",
    "Avionics Technician",
    "Firmware Calibration Engineer",
    "Flight Test Pilot",
    "QC Inspector",
    "Packaging Operator",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Karthik",
        "last_name": "Menon",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1982-02-19",
        "date_of_joining": "2015-01-12",
    },
    {
        "first_name": "Divya",
        "last_name": "Raghavan",
        "gender": "Female",
        "designation": "Assembly Supervisor",
        "department": "Production",
        "date_of_birth": "1988-06-30",
        "date_of_joining": "2017-05-22",
    },
    {
        "first_name": "Arjun",
        "last_name": "Nambiar",
        "gender": "Male",
        "designation": "PCB Assembly Technician",
        "department": "Production",
        "date_of_birth": "1993-11-15",
        "date_of_joining": "2019-08-05",
    },
    {
        "first_name": "Sanjay",
        "last_name": "Bhat",
        "gender": "Male",
        "designation": "PCB Assembly Technician",
        "department": "Production",
        "date_of_birth": "1987-04-03",
        "date_of_joining": "2016-03-07",
    },
    {
        "first_name": "Sneha",
        "last_name": "Pillai",
        "gender": "Female",
        "designation": "Frame Assembly Technician",
        "department": "Production",
        "date_of_birth": "1994-03-08",
        "date_of_joining": "2020-06-15",
    },
    {
        "first_name": "Vishal",
        "last_name": "Rane",
        "gender": "Male",
        "designation": "Avionics Technician",
        "department": "Production",
        "date_of_birth": "1991-07-27",
        "date_of_joining": "2018-09-03",
    },
    {
        "first_name": "Nikhil",
        "last_name": "Joshi",
        "gender": "Male",
        "designation": "Firmware Calibration Engineer",
        "department": "Production",
        "date_of_birth": "1990-05-12",
        "date_of_joining": "2018-01-29",
    },
    {
        "first_name": "Aditi",
        "last_name": "Sharma",
        "gender": "Female",
        "designation": "Flight Test Pilot",
        "department": "Production",
        "date_of_birth": "1992-12-04",
        "date_of_joining": "2019-04-08",
    },
    {
        "first_name": "Rahul",
        "last_name": "Verma",
        "gender": "Male",
        "designation": "QC Inspector",
        "department": "Quality Management",
        "date_of_birth": "1989-09-21",
        "date_of_joining": "2017-11-13",
    },
    {
        "first_name": "Pooja",
        "last_name": "Naik",
        "gender": "Female",
        "designation": "Packaging Operator",
        "department": "Dispatch",
        "date_of_birth": "1996-01-17",
        "date_of_joining": "2021-07-19",
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
