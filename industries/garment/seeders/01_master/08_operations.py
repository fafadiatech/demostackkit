"""
Seeder: Operations for Garment Manufacturing.

Creates manufacturing operations linked to workstations.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


OPERATIONS = [
    {"name": "Fabric Cutting", "workstation": "Cutting Table", "description": "Spread and cut fabric to pattern", "operating_cost": 50.0},
    {"name": "Sewing Assembly", "workstation": "Sewing Machine", "description": "Stitch fabric panels together", "operating_cost": 80.0},
    {"name": "Overlocking", "workstation": "Overlock Machine", "description": "Finish seam edges with overlock stitch", "operating_cost": 60.0},
    {"name": "Button Attachment", "workstation": "Button Machine", "description": "Attach buttons and make button-holes", "operating_cost": 40.0},
    {"name": "Pressing & Ironing", "workstation": "Pressing Station", "description": "Steam press finished garment", "operating_cost": 30.0},
    {"name": "QC Inspection", "workstation": "QC Table", "description": "Inspect dimensions, stitching and finish", "operating_cost": 25.0},
    {"name": "Garment Packaging", "workstation": "Packaging Station", "description": "Fold, tag, and bag finished garment", "operating_cost": 20.0},
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
