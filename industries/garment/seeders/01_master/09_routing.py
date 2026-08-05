"""
Seeder: Routing for Garment Manufacturing.

Creates the standard garment production routing (sequence of operations).
Idempotent — skips if routing already exists.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Garment Standard Route"

ROUTING_OPERATIONS = [
    {"operation": "Fabric Cutting", "workstation": "Cutting Table", "time_in_mins": 30},
    {"operation": "Sewing Assembly", "workstation": "Sewing Machine", "time_in_mins": 60},
    {"operation": "Overlocking", "workstation": "Overlock Machine", "time_in_mins": 20},
    {"operation": "Button Attachment", "workstation": "Button Machine", "time_in_mins": 15},
    {"operation": "Pressing & Ironing", "workstation": "Pressing Station", "time_in_mins": 10},
    {"operation": "QC Inspection", "workstation": "QC Table", "time_in_mins": 10},
    {"operation": "Garment Packaging", "workstation": "Packaging Station", "time_in_mins": 5},
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
