"""
Seeder: Workstations for Voltara EV Manufacturing.

Creates manufacturing workstations representing the full EV production floor:
battery cell assembly and pack integration bays, motor assembly, chassis
welding, body panel fitting, electrical integration, final assembly and trim,
pre-delivery inspection and road test, and EV packing and dispatch.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


WORKSTATIONS = [
    {"workstation_name": "Battery Assembly Station",   "description": "Cell sorting, spot welding and module assembly",             "hour_rate": 800.0},
    {"workstation_name": "Pack Integration Bay",       "description": "Module stacking, BMS wiring and pack sealing",              "hour_rate": 650.0},
    {"workstation_name": "Motor Assembly Bay",         "description": "Motor rotor-stator assembly and bearing press-fit",         "hour_rate": 1000.0},
    {"workstation_name": "Chassis Welding Station",    "description": "MIG and spot welding of steel monocoque and bike frames",   "hour_rate": 700.0},
    {"workstation_name": "Body Assembly Line",         "description": "Panel fitting, hemming and body-in-white assembly",         "hour_rate": 800.0},
    {"workstation_name": "Electrical Integration Bay", "description": "Harness routing, connector crimping and HV system wiring",  "hour_rate": 750.0},
    {"workstation_name": "PDI & Testing Bay",          "description": "Pre-delivery inspection, software flashing and road test",  "hour_rate": 600.0},
    {"workstation_name": "Final Assembly Bay",         "description": "Trim, glass, seats and final mechanical assembly",          "hour_rate": 900.0},
    {"workstation_name": "EV Packing Station",         "description": "Protective wrap, crating and dispatch labelling",           "hour_rate": 300.0},
]


class WorkstationSeeder(BaseMasterSeeder):
    label = "Workstations"
    priority = 40

    def run(self) -> None:
        ws_json = json.dumps(WORKSTATIONS)
        script = f"""
import frappe, json
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()

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
