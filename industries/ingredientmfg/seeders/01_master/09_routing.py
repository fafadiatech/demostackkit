"""
Seeder: Routing for Ingredient Manufacturing.

Creates the standard batch-process ingredient production routing
(sequence of operations): dosing, extraction, filtration, drying and
standardisation, QC testing, packing. ~7 hour total cycle time.
Idempotent — skips if routing already exists.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Ingredient Manufacturing Standard Route"

ROUTING_OPERATIONS = [
    {
        "operation": "Raw Material Weighing & Dosing",
        "workstation": "Weighing & Dosing Station",
        "time_in_mins": 30,
    },
    {"operation": "Solvent Extraction", "workstation": "Extraction Vessel", "time_in_mins": 150},
    {
        "operation": "Filtration & Clarification",
        "workstation": "Filtration Unit",
        "time_in_mins": 60,
    },
    {
        "operation": "Drying & Standardization",
        "workstation": "Drying & Standardization Unit",
        "time_in_mins": 90,
    },
    {"operation": "Quality Testing", "workstation": "QC Lab", "time_in_mins": 60},
    {"operation": "Filling & Packing", "workstation": "Packing Line", "time_in_mins": 30},
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
