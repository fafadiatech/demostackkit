"""
Seeder: Production Employees for EV Manufacturing.

Creates the shop-floor workforce that Job Cards are allocated to — battery
pack and motor assembly technicians, chassis welders, EV electrical
technicians and PDI test engineers. Job Card assigns work via its `employee`
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
    "Line Supervisor",
    "Battery Assembly Technician",
    "Pack Integration Engineer",
    "Motor Assembly Technician",
    "Chassis Welder",
    "Body Fitment Technician",
    "EV Electrical Technician",
    "PDI Test Engineer",
    "QC Inspector",
    "Dispatch Operator",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Anand",
        "last_name": "Krishnan",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1980-03-08",
        "date_of_joining": "2014-02-03",
    },
    {
        "first_name": "Shweta",
        "last_name": "Iyer",
        "gender": "Female",
        "designation": "Line Supervisor",
        "department": "Production",
        "date_of_birth": "1987-07-16",
        "date_of_joining": "2016-06-20",
    },
    {
        "first_name": "Imran",
        "last_name": "Shaikh",
        "gender": "Male",
        "designation": "Battery Assembly Technician",
        "department": "Production",
        "date_of_birth": "1992-02-11",
        "date_of_joining": "2019-03-11",
    },
    {
        "first_name": "Ritu",
        "last_name": "Malhotra",
        "gender": "Female",
        "designation": "Pack Integration Engineer",
        "department": "Production",
        "date_of_birth": "1991-08-24",
        "date_of_joining": "2018-07-09",
    },
    {
        "first_name": "Dinesh",
        "last_name": "Yadav",
        "gender": "Male",
        "designation": "Motor Assembly Technician",
        "department": "Production",
        "date_of_birth": "1989-11-05",
        "date_of_joining": "2017-04-24",
    },
    {
        "first_name": "Sunil",
        "last_name": "Chauhan",
        "gender": "Male",
        "designation": "Chassis Welder",
        "department": "Production",
        "date_of_birth": "1986-12-30",
        "date_of_joining": "2015-10-12",
    },
    {
        "first_name": "Priyanka",
        "last_name": "Deshpande",
        "gender": "Female",
        "designation": "Body Fitment Technician",
        "department": "Production",
        "date_of_birth": "1993-05-18",
        "date_of_joining": "2020-01-06",
    },
    {
        "first_name": "Vikram",
        "last_name": "Sethi",
        "gender": "Male",
        "designation": "EV Electrical Technician",
        "department": "Production",
        "date_of_birth": "1990-09-02",
        "date_of_joining": "2018-02-19",
    },
    {
        "first_name": "Anjali",
        "last_name": "Rao",
        "gender": "Female",
        "designation": "PDI Test Engineer",
        "department": "Quality Management",
        "date_of_birth": "1994-01-25",
        "date_of_joining": "2020-08-17",
    },
    {
        "first_name": "Harish",
        "last_name": "Nadar",
        "gender": "Male",
        "designation": "QC Inspector",
        "department": "Quality Management",
        "date_of_birth": "1988-06-13",
        "date_of_joining": "2017-01-16",
    },
    {
        "first_name": "Meera",
        "last_name": "Joshi",
        "gender": "Female",
        "designation": "Dispatch Operator",
        "department": "Dispatch",
        "date_of_birth": "1995-10-09",
        "date_of_joining": "2021-05-24",
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
