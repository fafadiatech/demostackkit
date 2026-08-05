"""
Seeder: Workstations for Drones Manufacturing.

Creates manufacturing workstations used in drone production.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

WORKSTATIONS = [
    {
        "workstation_name": "PCB Assembly Station",
        "description": "PCB soldering and electronics assembly workstation",
        "hour_rate": 250.0,
    },
    {
        "workstation_name": "Frame Assembly Bench",
        "description": "Drone frame assembly and structural integration bench",
        "hour_rate": 200.0,
    },
    {
        "workstation_name": "Motor & ESC Integration",
        "description": "Motor mounting and ESC wiring workstation",
        "hour_rate": 220.0,
    },
    {
        "workstation_name": "Firmware & Calibration Desk",
        "description": "Flight controller firmware flashing and sensor calibration desk",
        "hour_rate": 300.0,
    },
    {
        "workstation_name": "Flight Test Bay",
        "description": "Indoor flight test bay for tuning and validation",
        "hour_rate": 350.0,
    },
    {
        "workstation_name": "QC Inspection Table",
        "description": "Quality inspection and measurement table",
        "hour_rate": 150.0,
    },
    {
        "workstation_name": "Packaging & Labelling Station",
        "description": "Drone packaging, documentation and labelling station",
        "hour_rate": 100.0,
    },
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
