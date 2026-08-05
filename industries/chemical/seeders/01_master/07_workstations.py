"""
Seeder: Workstations for Chemical Manufacturing.

Creates manufacturing workstations used in chemical production.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


WORKSTATIONS = [
    {"workstation_name": "Mixing Tank",          "description": "Agitated mixing vessel for blending raw materials", "hour_rate": 200.0},
    {"workstation_name": "Reaction Vessel",      "description": "Jacketed reactor for chemical synthesis", "hour_rate": 350.0},
    {"workstation_name": "Distillation Column",  "description": "Fractional distillation unit", "hour_rate": 400.0},
    {"workstation_name": "Filtration Unit",      "description": "Pressure filtration and centrifuge station", "hour_rate": 250.0},
    {"workstation_name": "Filling Station",      "description": "Automated filling and capping line", "hour_rate": 180.0},
    {"workstation_name": "QC Lab",               "description": "Quality control and analytical testing laboratory", "hour_rate": 300.0},
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
