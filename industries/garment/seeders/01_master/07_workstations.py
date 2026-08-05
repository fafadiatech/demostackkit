"""
Seeder: Workstations for Garment Manufacturing.

Creates manufacturing workstations used in garment production.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


WORKSTATIONS = [
    {"workstation_name": "Cutting Table", "description": "Fabric spreading and cutting workstation", "hour_rate": 150.0},
    {"workstation_name": "Sewing Machine", "description": "Industrial lockstitch sewing machine", "hour_rate": 200.0},
    {"workstation_name": "Overlock Machine", "description": "Industrial overlock / serger machine", "hour_rate": 180.0},
    {"workstation_name": "Button Machine", "description": "Button attaching and button-hole machine", "hour_rate": 120.0},
    {"workstation_name": "Pressing Station", "description": "Steam pressing and ironing table", "hour_rate": 100.0},
    {"workstation_name": "QC Table", "description": "Quality inspection and measurement table", "hour_rate": 120.0},
    {"workstation_name": "Packaging Station", "description": "Folding, tagging and poly-bagging station", "hour_rate": 80.0},
]


class WorkstationSeeder(BaseMasterSeeder):
    label = "Workstations"
    priority = 40

    def run(self) -> None:
        ws_json = json.dumps(WORKSTATIONS)
        script = f"""
import json

workstations = json.loads('''{ws_json}''')
created = skipped = 0
for ws in workstations:
    if frappe.db.exists('Workstation', ws['workstation_name']):
        skipped += 1
        continue
    frappe.get_doc({{
        'doctype': 'Workstation',
        'workstation_name': ws['workstation_name'],
        'description': ws.get('description', ''),
        'hour_rate': ws.get('hour_rate', 0),
    }}).insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Workstations: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("workstation_names", [ws["workstation_name"] for ws in WORKSTATIONS])
