"""
Seeder: Routing for Alpha Abrasives.

Creates a single "Abrasive Product Manufacturing Route" shared by every
bonded wheel, disc and coated belt SKU: mixing/bonding, pressing/moulding,
curing, grading/QC, and packing — a short routing, comparable in length to
crockery's multi-stage kiln routing.
Idempotent — skips if the routing already exists.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Abrasive Product Manufacturing Route"

ROUTING_OPERATIONS = [
    {
        "operation": "Raw Material Mixing & Bonding",
        "workstation": "Mixing & Bonding Station",
        "time_in_mins": 45,
    },
    {
        "operation": "Pressing & Moulding",
        "workstation": "Press & Mould Station",
        "time_in_mins": 30,
    },
    {"operation": "Curing", "workstation": "Curing Oven", "time_in_mins": 600},
    {
        "operation": "Grading & Quality Check",
        "workstation": "Grading & QC Bench",
        "time_in_mins": 20,
    },
    {
        "operation": "Packing & Labelling",
        "workstation": "Packing Station",
        "time_in_mins": 15,
    },
]


class RoutingSeeder(BaseMasterSeeder):
    label = "Routing"
    priority = 90

    def run(self) -> None:
        ops_json = json.dumps(ROUTING_OPERATIONS)
        script = f"""
import json

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
