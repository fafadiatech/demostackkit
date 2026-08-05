"""
Seeder: Operations for Chemical Manufacturing.

Creates manufacturing operations linked to workstations.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


OPERATIONS = [
    {"name": "Raw Material Dosing",   "workstation": "Mixing Tank",         "description": "Weigh and dose raw materials into vessel", "operating_cost": 60.0},
    {"name": "Mixing & Blending",     "workstation": "Mixing Tank",         "description": "Agitate and blend raw material charge", "operating_cost": 80.0},
    {"name": "Chemical Reaction",     "workstation": "Reaction Vessel",     "description": "Controlled exothermic/endothermic reaction", "operating_cost": 150.0},
    {"name": "Distillation",          "workstation": "Distillation Column", "description": "Separate product by fractional distillation", "operating_cost": 180.0},
    {"name": "Filtration",            "workstation": "Filtration Unit",     "description": "Remove solids and clarify product", "operating_cost": 100.0},
    {"name": "Filling & Packaging",   "workstation": "Filling Station",     "description": "Fill product into containers and seal", "operating_cost": 70.0},
    {"name": "Quality Testing",       "workstation": "QC Lab",              "description": "Analytical testing for purity and compliance", "operating_cost": 120.0},
]


class OperationSeeder(BaseMasterSeeder):
    label = "Operations"
    priority = 50

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
