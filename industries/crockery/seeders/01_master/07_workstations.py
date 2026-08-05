"""
Seeder: Workstations for Crockery Manufacturing.

Creates manufacturing workstations used in crockery and ceramics production.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


WORKSTATIONS = [
    {"workstation_name": "Throwing & Casting Station", "description": "Pottery wheel throwing and slip casting workstation", "hour_rate": 180.0},
    {"workstation_name": "Trimming & Finishing Bench", "description": "Greenware trimming, smoothing and handle attachment bench", "hour_rate": 150.0},
    {"workstation_name": "Bisque Kiln", "description": "Electric kiln for first bisque firing at 1000°C", "hour_rate": 200.0},
    {"workstation_name": "Glazing Station", "description": "Glaze dipping, pouring and brushing station", "hour_rate": 160.0},
    {"workstation_name": "Glaze Kiln", "description": "Electric kiln for final glaze firing at 1220°C", "hour_rate": 220.0},
    {"workstation_name": "QC Inspection Table", "description": "Quality inspection and dimensional measurement table", "hour_rate": 120.0},
    {"workstation_name": "Packaging Station", "description": "Crockery wrapping, boxing and labelling station", "hour_rate": 80.0},
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
