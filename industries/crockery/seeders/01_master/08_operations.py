"""
Seeder: Operations for Crockery Manufacturing.

Creates manufacturing operations linked to workstations.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


OPERATIONS = [
    {"name": "Clay Preparation & Wedging", "workstation": "Throwing & Casting Station", "description": "Weigh, blend and wedge clay to remove air pockets", "operating_cost": 60.0},
    {"name": "Throwing or Casting", "workstation": "Throwing & Casting Station", "description": "Throw on wheel or pour slip into moulds", "operating_cost": 90.0},
    {"name": "Trimming & Drying", "workstation": "Trimming & Finishing Bench", "description": "Trim foot ring, smooth surface and air dry greenware", "operating_cost": 45.0},
    {"name": "Bisque Firing", "workstation": "Bisque Kiln", "description": "First fire at 1000°C to harden greenware to bisqueware", "operating_cost": 120.0},
    {"name": "Glazing", "workstation": "Glazing Station", "description": "Apply food-safe glaze by dipping or pouring", "operating_cost": 70.0},
    {"name": "Glaze Firing", "workstation": "Glaze Kiln", "description": "Final fire at 1220°C to mature glaze and vitrify clay", "operating_cost": 150.0},
    {"name": "QC Inspection", "workstation": "QC Inspection Table", "description": "Inspect glaze finish, dimensions and structural integrity", "operating_cost": 40.0},
    {"name": "Packing & Labelling", "workstation": "Packaging Station", "description": "Wrap, box and label finished crockery pieces", "operating_cost": 30.0},
]


class OperationSeeder(BaseMasterSeeder):
    label = "Operations"
    priority = 50

    def run(self) -> None:
        ops_json = json.dumps(OPERATIONS)
        script = f"""
import frappe, json
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()

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
