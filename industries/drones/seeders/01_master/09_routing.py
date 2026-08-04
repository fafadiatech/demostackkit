"""
Seeder: Routing for Drones Manufacturing.

Creates the standard drone production routing (sequence of operations).
Idempotent — skips if routing already exists.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


ROUTING_NAME = "Drone Standard Route"

ROUTING_OPERATIONS = [
    {"operation": "PCB Soldering & Testing",   "workstation": "PCB Assembly Station",        "time_in_mins": 45},
    {"operation": "Frame Assembly",             "workstation": "Frame Assembly Bench",         "time_in_mins": 60},
    {"operation": "Motor & ESC Integration",   "workstation": "Motor & ESC Integration",      "time_in_mins": 30},
    {"operation": "Firmware Flash & Calibration", "workstation": "Firmware & Calibration Desk", "time_in_mins": 40},
    {"operation": "Test Flight & Tuning",      "workstation": "Flight Test Bay",              "time_in_mins": 30},
    {"operation": "QC Final Inspection",       "workstation": "QC Inspection Table",          "time_in_mins": 20},
    {"operation": "Packaging & Documentation", "workstation": "Packaging & Labelling Station", "time_in_mins": 10},
]


class RoutingSeeder(BaseMasterSeeder):
    label = "Routing"
    priority = 60

    def run(self) -> None:
        ops_json = json.dumps(ROUTING_OPERATIONS)
        script = f"""
import frappe, json
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()

routing_name = '{ROUTING_NAME}'
if frappe.db.exists('Routing', routing_name):
    print(f'Routing already exists: {{routing_name}}')
else:
    ops = json.loads('''{ops_json}''')
    frappe.get_doc({{
        'doctype': 'Routing',
        'routing_name': routing_name,
        'operations': [
            {{
                'operation': op['operation'],
                'workstation': op['workstation'],
                'time_in_mins': op['time_in_mins'],
            }}
            for op in ops
        ],
    }}).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f'Routing created: {{routing_name}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("routing_name", ROUTING_NAME)
