"""
Seeder: Routing for Crockery Manufacturing.

Creates the standard crockery production routing (sequence of operations).
Idempotent — skips if routing already exists.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Crockery Standard Route"

ROUTING_OPERATIONS = [
    {
        "operation": "Clay Preparation & Wedging",
        "workstation": "Throwing & Casting Station",
        "time_in_mins": 20,
    },
    {
        "operation": "Throwing or Casting",
        "workstation": "Throwing & Casting Station",
        "time_in_mins": 45,
    },
    {
        "operation": "Trimming & Drying",
        "workstation": "Trimming & Finishing Bench",
        "time_in_mins": 30,
    },
    {"operation": "Bisque Firing", "workstation": "Bisque Kiln", "time_in_mins": 480},
    {"operation": "Glazing", "workstation": "Glazing Station", "time_in_mins": 30},
    {"operation": "Glaze Firing", "workstation": "Glaze Kiln", "time_in_mins": 480},
    {"operation": "QC Inspection", "workstation": "QC Inspection Table", "time_in_mins": 15},
    {"operation": "Packing & Labelling", "workstation": "Packaging Station", "time_in_mins": 10},
]


class RoutingSeeder(BaseMasterSeeder):
    label = "Routing"
    priority = 60

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
