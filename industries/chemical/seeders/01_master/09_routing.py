"""
Seeder: Routing for Chemical Manufacturing.

Creates the standard chemical production routing (sequence of operations).
Idempotent — skips if routing already exists.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


ROUTING_NAME = "Chemical Standard Route"

ROUTING_OPERATIONS = [
    {"operation": "Raw Material Dosing", "workstation": "Mixing Tank",         "time_in_mins": 30},
    {"operation": "Mixing & Blending",   "workstation": "Mixing Tank",         "time_in_mins": 60},
    {"operation": "Chemical Reaction",   "workstation": "Reaction Vessel",     "time_in_mins": 120},
    {"operation": "Distillation",        "workstation": "Distillation Column", "time_in_mins": 90},
    {"operation": "Filtration",          "workstation": "Filtration Unit",     "time_in_mins": 45},
    {"operation": "Filling & Packaging", "workstation": "Filling Station",     "time_in_mins": 30},
    {"operation": "Quality Testing",     "workstation": "QC Lab",              "time_in_mins": 60},
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
