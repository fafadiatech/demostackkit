"""
Seeder: Operations for Jewellery Manufacturing.

Creates manufacturing operations linked to workstations.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

OPERATIONS = [
    {
        "name": "Metal Melting",
        "workstation": "Melting Furnace",
        "description": "Melt and alloy precious metals to required karat",
        "operating_cost": 200.0,
    },
    {
        "name": "Rolling & Drawing",
        "workstation": "Rolling Mill",
        "description": "Roll metal into sheets or draw into wire",
        "operating_cost": 120.0,
    },
    {
        "name": "Wax Casting",
        "workstation": "Casting Machine",
        "description": "Investment casting from wax model",
        "operating_cost": 160.0,
    },
    {
        "name": "Filing & Shaping",
        "workstation": "Filing Bench",
        "description": "Hand file, shape and assemble components",
        "operating_cost": 140.0,
    },
    {
        "name": "Stone Setting",
        "workstation": "Stone Setting Bench",
        "description": "Set gemstones using prong, bezel or pave technique",
        "operating_cost": 250.0,
    },
    {
        "name": "Polishing & Finishing",
        "workstation": "Polishing Machine",
        "description": "Polish, buff and rhodium plate finished piece",
        "operating_cost": 100.0,
    },
    {
        "name": "Quality Hallmarking",
        "workstation": "QC Station",
        "description": "Inspect, weigh, hallmark and certify finished jewellery",
        "operating_cost": 80.0,
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
