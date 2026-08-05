"""
Seeder: Workstations for Solar System Assembly.

Creates manufacturing workstations used in solar system assembly and commissioning.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


WORKSTATIONS = [
    {"workstation_name": "Panel Assembly Bay",        "description": "Bay for panel unboxing, inspection and layout planning", "hour_rate": 150.0},
    {"workstation_name": "Cable Management Station",  "description": "DC/AC cable cutting, crimping and routing station", "hour_rate": 120.0},
    {"workstation_name": "Inverter Mounting Bay",     "description": "Inverter and electrical panel installation bay", "hour_rate": 180.0},
    {"workstation_name": "System Testing Bay",        "description": "String testing, commissioning and grid synchronisation", "hour_rate": 250.0},
    {"workstation_name": "QC Inspection Station",     "description": "Pre-handover quality and safety inspection station", "hour_rate": 200.0},
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
