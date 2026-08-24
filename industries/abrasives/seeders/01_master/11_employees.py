"""
Seeder: Production & Trading Employees for Alpha Abrasives.

Creates the shop-floor workforce that Job Cards are allocated to (mixing,
pressing, curing, QC and packing technicians) alongside the traded-line
roles that keep the imported machines/tools business running (procurement,
traded goods warehousing, dispatch). Job Card assigns work via its
`employee` table, so without these records no Job Card can be allocated.

Idempotent — skips employees that already exist for the company.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

DESIGNATIONS = [
    "Production Manager",
    "Shop Floor Supervisor",
    "Mixing & Bonding Technician",
    "Press Operator",
    "Curing Oven Operator",
    "QC Inspector",
    "Packing Operator",
    "Import & Procurement Executive",
    "Traded Goods Warehouse Executive",
    "Dispatch Operator",
]

# department is the bare name; the seeder resolves it to '<name> - <abbr>'.
EMPLOYEES = [
    {
        "first_name": "Anand",
        "last_name": "Deshpande",
        "gender": "Male",
        "designation": "Production Manager",
        "department": "Production",
        "date_of_birth": "1978-04-12",
        "date_of_joining": "2013-06-10",
    },
    {
        "first_name": "Sunita",
        "last_name": "Kamble",
        "gender": "Female",
        "designation": "Shop Floor Supervisor",
        "department": "Production",
        "date_of_birth": "1986-02-18",
        "date_of_joining": "2016-03-05",
    },
    {
        "first_name": "Ravindra",
        "last_name": "Naik",
        "gender": "Male",
        "designation": "Mixing & Bonding Technician",
        "department": "Production",
        "date_of_birth": "1990-09-24",
        "date_of_joining": "2017-08-14",
    },
    {
        "first_name": "Geeta",
        "last_name": "Shinde",
        "gender": "Female",
        "designation": "Press Operator",
        "department": "Production",
        "date_of_birth": "1991-11-03",
        "date_of_joining": "2018-05-21",
    },
    {
        "first_name": "Vijay",
        "last_name": "Chavan",
        "gender": "Male",
        "designation": "Curing Oven Operator",
        "department": "Production",
        "date_of_birth": "1988-07-15",
        "date_of_joining": "2016-11-02",
    },
    {
        "first_name": "Pooja",
        "last_name": "Kulkarni",
        "gender": "Female",
        "designation": "QC Inspector",
        "department": "Quality Management",
        "date_of_birth": "1993-01-27",
        "date_of_joining": "2019-09-16",
    },
    {
        "first_name": "Santosh",
        "last_name": "Gaikwad",
        "gender": "Male",
        "designation": "Packing Operator",
        "department": "Production",
        "date_of_birth": "1994-05-09",
        "date_of_joining": "2020-04-06",
    },
    {
        "first_name": "Nikhil",
        "last_name": "Merchant",
        "gender": "Male",
        "designation": "Import & Procurement Executive",
        "department": "Purchase",
        "date_of_birth": "1987-03-30",
        "date_of_joining": "2015-10-19",
    },
    {
        "first_name": "Farida",
        "last_name": "Sheikh",
        "gender": "Female",
        "designation": "Traded Goods Warehouse Executive",
        "department": "Stock",
        "date_of_birth": "1992-06-22",
        "date_of_joining": "2019-02-11",
    },
    {
        "first_name": "Deepak",
        "last_name": "Wagh",
        "gender": "Male",
        "designation": "Dispatch Operator",
        "department": "Dispatch",
        "date_of_birth": "1995-08-17",
        "date_of_joining": "2021-07-12",
    },
]


class EmployeeSeeder(BaseMasterSeeder):
    label = "Production & Trading Employees"
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
