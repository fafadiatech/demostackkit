"""
Seeder: Operations for Alpha Abrasives.

Creates the five manufacturing operations shared by every bonded wheel,
disc and coated belt SKU: mixing/bonding, pressing/moulding, curing,
grading/QC, and packing.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

_QC_INSPECTION_PARAMETERS = [
    ("Grit Consistency (%)", 92.0, 100.0),
    ("Wheel Balance (g.mm)", 0.0, 15.0),
    ("Burst/RPM Safety Test Pass (0/1)", 0.9, 1.0),
    ("Bond Hardness (Shore)", 40.0, 70.0),
]

OPERATIONS = [
    {
        "name": "Raw Material Mixing & Bonding",
        "workstation": "Mixing & Bonding Station",
        "description": "Blend abrasive grain with resin/rubber bond and fillers to a uniform mix",
        "operating_cost": 450.0,
    },
    {
        "name": "Pressing & Moulding",
        "workstation": "Press & Mould Station",
        "description": "Hydraulic press moulds the mix into the target wheel, disc or belt form",
        "operating_cost": 550.0,
    },
    {
        "name": "Curing",
        "workstation": "Curing Oven",
        "description": "Oven-cure pressed product to fully set the bond",
        "operating_cost": 400.0,
    },
    {
        "name": "Grading & Quality Check",
        "workstation": "Grading & QC Bench",
        "description": "Grit consistency, wheel balance, burst/RPM safety and bond hardness checks",
        "operating_cost": 350.0,
    },
    {
        "name": "Packing & Labelling",
        "workstation": "Packing Station",
        "description": "Label, box and stretch wrap finished product for dispatch",
        "operating_cost": 250.0,
    },
]


class OperationSeeder(BaseMasterSeeder):
    label = "Operations"
    priority = 64

    def run(self) -> None:
        ops_json = json.dumps(OPERATIONS)
        script = f"""
import json

operations = json.loads('''{ops_json}''')
created = skipped = 0
for op in operations:
    if frappe.db.exists('Operation', op['name']):
        skipped += 1
        continue
    frappe.get_doc({{
        'doctype': 'Operation',
        'name': op['name'],
        'workstation': op['workstation'],
        'description': op.get('description', ''),
        'operating_cost': op.get('operating_cost', 0),
    }}).insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Operations: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("operation_names", [op["name"] for op in OPERATIONS])
        self.ctx.cache_set("qc_operation_name", "Grading & Quality Check")
        self.ctx.cache_set("qc_inspection_parameters", _QC_INSPECTION_PARAMETERS)
