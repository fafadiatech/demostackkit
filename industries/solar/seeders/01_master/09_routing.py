"""
Seeder: Routing for Solar System Assembly.

Creates the standard solar system assembly routing (sequence of operations).
Idempotent — skips if routing already exists.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


ROUTING_NAME = "Solar System Assembly Route"

ROUTING_OPERATIONS = [
    {"operation": "Panel Layout Planning",          "workstation": "Panel Assembly Bay",       "time_in_mins": 60},
    {"operation": "Panel Mounting",                 "workstation": "Panel Assembly Bay",       "time_in_mins": 180},
    {"operation": "Cable Routing & Crimping",       "workstation": "Cable Management Station", "time_in_mins": 120},
    {"operation": "Inverter Installation",          "workstation": "Inverter Mounting Bay",    "time_in_mins": 90},
    {"operation": "System Commissioning & Testing", "workstation": "System Testing Bay",       "time_in_mins": 120},
    {"operation": "Solar QC Sign-off",              "workstation": "QC Inspection Station",    "time_in_mins": 60},
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
