"""
Seeder: Operations for 3D Printing Services.

Creates manufacturing operations covering both FDM and SLA print
workflows: printing, support removal, washing, UV curing, surface
finishing, quality inspection, and packing.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

OPERATIONS = [
    {
        "name": "FDM Printing",
        "workstation": "FDM Printer Bank",
        "description": "Print part layer-by-layer using fused deposition modeling",
        "operating_cost": 15.0,
    },
    {
        "name": "SLA Printing",
        "workstation": "SLA Printer Bank",
        "description": "Print high-detail part using stereolithography resin",
        "operating_cost": 30.0,
    },
    {
        "name": "Support Removal",
        "workstation": "Post-Processing Bench",
        "description": "Remove support structures from printed part",
        "operating_cost": 8.0,
    },
    {
        "name": "IPA Washing",
        "workstation": "Washing Station",
        "description": "Wash SLA part in isopropyl alcohol to remove uncured resin",
        "operating_cost": 5.0,
    },
    {
        "name": "UV Curing",
        "workstation": "UV Curing Chamber",
        "description": "Post-cure SLA part under UV light for full strength",
        "operating_cost": 5.0,
    },
    {
        "name": "Sanding & Finishing",
        "workstation": "Post-Processing Bench",
        "description": "Sand and smooth part surface to required finish",
        "operating_cost": 8.0,
    },
    {
        "name": "Print QC Inspection",
        "workstation": "QC Inspection Desk",
        "description": "Dimensional check and visual inspection of finished part",
        "operating_cost": 8.0,
    },
    {
        "name": "Packing & Dispatch",
        "workstation": "Packing Station",
        "description": "Wrap, box and label part for customer dispatch",
        "operating_cost": 5.0,
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
