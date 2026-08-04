"""
Seeder: Operations for Drones Manufacturing.

Creates manufacturing operations linked to workstations.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


OPERATIONS = [
    {"name": "PCB Soldering & Testing", "workstation": "PCB Assembly Station", "description": "Solder and test all PCB assemblies and electronics", "operating_cost": 120.0},
    {"name": "Frame Assembly", "workstation": "Frame Assembly Bench", "description": "Assemble drone frame, arms and structural components", "operating_cost": 100.0},
    {"name": "Motor & ESC Integration", "workstation": "Motor & ESC Integration", "description": "Mount motors and wire electronic speed controllers", "operating_cost": 110.0},
    {"name": "Firmware Flash & Calibration", "workstation": "Firmware & Calibration Desk", "description": "Flash flight controller firmware and calibrate all sensors", "operating_cost": 150.0},
    {"name": "Test Flight & Tuning", "workstation": "Flight Test Bay", "description": "Conduct test flights and tune PID parameters", "operating_cost": 200.0},
    {"name": "QC Final Inspection", "workstation": "QC Inspection Table", "description": "Final quality inspection of completed drone", "operating_cost": 80.0},
    {"name": "Packaging & Documentation", "workstation": "Packaging & Labelling Station", "description": "Pack drone with accessories and prepare documentation", "operating_cost": 50.0},
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
