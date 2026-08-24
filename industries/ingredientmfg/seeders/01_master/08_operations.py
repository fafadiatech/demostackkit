"""
Seeder: Operations for Ingredient Manufacturing.

Creates manufacturing operations linked to workstations.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

OPERATIONS = [
    {
        "name": "Raw Material Weighing & Dosing",
        "workstation": "Weighing & Dosing Station",
        "description": "Weigh and dose raw botanicals and chemicals into the batch",
        "operating_cost": 50.0,
    },
    {
        "name": "Solvent Extraction",
        "workstation": "Extraction Vessel",
        "description": "Extract actives from botanical or protein raw material",
        "operating_cost": 160.0,
    },
    {
        "name": "Filtration & Clarification",
        "workstation": "Filtration Unit",
        "description": "Remove spent solids and clarify the extract",
        "operating_cost": 100.0,
    },
    {
        "name": "Drying & Standardization",
        "workstation": "Drying & Standardization Unit",
        "description": "Dry and standardise the extract to target potency",
        "operating_cost": 140.0,
    },
    {
        "name": "Quality Testing",
        "workstation": "QC Lab",
        "description": "Analytical testing for purity, potency and safety",
        "operating_cost": 120.0,
    },
    {
        "name": "Filling & Packing",
        "workstation": "Packing Line",
        "description": "Fill product into containers and seal",
        "operating_cost": 70.0,
    },
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
