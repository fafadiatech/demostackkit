"""
Seeder: Routings for PowerTech Electrical Manufacturing.

Creates two standard routings in a single script:
- Transformer Manufacturing Route: full transformer production sequence from
  coil winding through core lamination, core-and-coil assembly, tank
  fabrication, vacuum oil filling, HV testing, and final packing.
- Switchgear Manufacturing Route: streamlined panel assembly sequence covering
  switchgear panel assembly, HV testing, and final inspection and packing.

Both routings share the High Voltage Testing and Final Inspection & Packing
operations — demonstrating the common testing infrastructure across product
families. Both are cached for reference by the BOM seeder.
Idempotent — skips routings that already exist.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

TRANSFORMER_ROUTING = "Transformer Manufacturing Route"
SWITCHGEAR_ROUTING = "Switchgear Manufacturing Route"

TRANSFORMER_OPERATIONS = [
    {
        "operation": "Coil Winding",
        "workstation": "Coil Winding Station",
        "time_in_mins": 480,
    },
    {
        "operation": "Core Lamination & Stacking",
        "workstation": "Core Lamination Station",
        "time_in_mins": 360,
    },
    {
        "operation": "Core & Coil Assembly",
        "workstation": "Core & Coil Assembly Bay",
        "time_in_mins": 300,
    },
    {
        "operation": "Tank Fabrication & Fitting",
        "workstation": "Tank Fabrication Bay",
        "time_in_mins": 480,
    },
    {
        "operation": "Vacuum Oil Filling",
        "workstation": "Oil Filling Station",
        "time_in_mins": 240,
    },
    {
        "operation": "High Voltage Testing",
        "workstation": "HV Testing Lab",
        "time_in_mins": 120,
    },
    {
        "operation": "Final Inspection & Packing",
        "workstation": "Packing & Dispatch Area",
        "time_in_mins": 60,
    },
]

SWITCHGEAR_OPERATIONS = [
    {
        "operation": "Switchgear Panel Assembly",
        "workstation": "Switchgear Assembly Bay",
        "time_in_mins": 480,
    },
    {
        "operation": "High Voltage Testing",
        "workstation": "HV Testing Lab",
        "time_in_mins": 60,
    },
    {
        "operation": "Final Inspection & Packing",
        "workstation": "Packing & Dispatch Area",
        "time_in_mins": 30,
    },
]


class RoutingSeeder(BaseMasterSeeder):
    label = "Routings (Transformer & Switchgear)"
    priority = 90

    def run(self) -> None:
        trans_ops_json = json.dumps(TRANSFORMER_OPERATIONS)
        swgr_ops_json = json.dumps(SWITCHGEAR_OPERATIONS)

        script = f"""
import json

trans_routing_name = '{TRANSFORMER_ROUTING}'
swgr_routing_name  = '{SWITCHGEAR_ROUTING}'

# Transformer Manufacturing Route
if frappe.db.exists('Routing', trans_routing_name):
    print(f'Routing already exists: {{trans_routing_name}}')
else:
    trans_ops = json.loads('''{trans_ops_json}''')
    frappe.get_doc({{
        'doctype': 'Routing',
        'routing_name': trans_routing_name,
        'operations': [
            {{
                'operation': op['operation'],
                'workstation': op['workstation'],
                'time_in_mins': op['time_in_mins'],
            }}
            for op in trans_ops
        ],
    }}).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f'Routing created: {{trans_routing_name}}')

# Switchgear Manufacturing Route
if frappe.db.exists('Routing', swgr_routing_name):
    print(f'Routing already exists: {{swgr_routing_name}}')
else:
    swgr_ops = json.loads('''{swgr_ops_json}''')
    frappe.get_doc({{
        'doctype': 'Routing',
        'routing_name': swgr_routing_name,
        'operations': [
            {{
                'operation': op['operation'],
                'workstation': op['workstation'],
                'time_in_mins': op['time_in_mins'],
            }}
            for op in swgr_ops
        ],
    }}).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f'Routing created: {{swgr_routing_name}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("transformer_routing", TRANSFORMER_ROUTING)
        self.ctx.cache_set("switchgear_routing", SWITCHGEAR_ROUTING)
