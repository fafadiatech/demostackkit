"""
Seeder: Routings for Voltara EV Manufacturing.

Creates two standard routings in a single script:
- EV Car Manufacturing Route: full car production sequence from chassis welding
  through battery assembly, motor fitment, body panels, electrical integration,
  final trim, PDI road test, and dispatch.
- EV Bike Manufacturing Route: streamlined two-wheeler sequence covering frame
  welding, battery assembly, motor fitment, electrical integration, final
  assembly, PDI, and dispatch.

Both routings share the same underlying operations — the same battery, motor,
electrical, and packing steps run on shared workstations. Only the car route
adds body panel fitting (not needed for bikes). Both are cached for reference
by the BOM seeder.
Idempotent — skips routings that already exist.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

CAR_ROUTING = "EV Car Manufacturing Route"
BIKE_ROUTING = "EV Bike Manufacturing Route"

CAR_OPERATIONS = [
    {
        "operation": "Chassis & Frame Welding",
        "workstation": "Chassis Welding Station",
        "time_in_mins": 480,
    },
    {
        "operation": "Battery Cell Assembly",
        "workstation": "Battery Assembly Station",
        "time_in_mins": 300,
    },
    {
        "operation": "Battery Pack Integration",
        "workstation": "Pack Integration Bay",
        "time_in_mins": 120,
    },
    {"operation": "Motor Assembly", "workstation": "Motor Assembly Bay", "time_in_mins": 240},
    {"operation": "Body Panel Fitting", "workstation": "Body Assembly Line", "time_in_mins": 360},
    {
        "operation": "Electrical Systems Integration",
        "workstation": "Electrical Integration Bay",
        "time_in_mins": 300,
    },
    {
        "operation": "Final Assembly & Trim",
        "workstation": "Final Assembly Bay",
        "time_in_mins": 480,
    },
    {"operation": "PDI & Road Test", "workstation": "PDI & Testing Bay", "time_in_mins": 120},
    {"operation": "EV Packing & Dispatch", "workstation": "EV Packing Station", "time_in_mins": 30},
]

BIKE_OPERATIONS = [
    {
        "operation": "Chassis & Frame Welding",
        "workstation": "Chassis Welding Station",
        "time_in_mins": 60,
    },
    {
        "operation": "Battery Cell Assembly",
        "workstation": "Battery Assembly Station",
        "time_in_mins": 90,
    },
    {
        "operation": "Battery Pack Integration",
        "workstation": "Pack Integration Bay",
        "time_in_mins": 45,
    },
    {"operation": "Motor Assembly", "workstation": "Motor Assembly Bay", "time_in_mins": 60},
    {
        "operation": "Electrical Systems Integration",
        "workstation": "Electrical Integration Bay",
        "time_in_mins": 90,
    },
    {"operation": "Final Assembly & Trim", "workstation": "Final Assembly Bay", "time_in_mins": 60},
    {"operation": "PDI & Road Test", "workstation": "PDI & Testing Bay", "time_in_mins": 30},
    {"operation": "EV Packing & Dispatch", "workstation": "EV Packing Station", "time_in_mins": 15},
]


class RoutingSeeder(BaseMasterSeeder):
    label = "Routings (Car & Bike)"
    priority = 60

    def run(self) -> None:
        car_ops_json = json.dumps(CAR_OPERATIONS)
        bike_ops_json = json.dumps(BIKE_OPERATIONS)

        script = f"""
import json

car_routing_name  = '{CAR_ROUTING}'
bike_routing_name = '{BIKE_ROUTING}'

# EV Car Manufacturing Route
if frappe.db.exists('Routing', car_routing_name):
    print(f'Routing already exists: {{car_routing_name}}')
else:
    car_ops = json.loads('''{car_ops_json}''')
    frappe.get_doc({{
        'doctype': 'Routing',
        'routing_name': car_routing_name,
        'operations': [
            {{
                'operation': op['operation'],
                'workstation': op['workstation'],
                'time_in_mins': op['time_in_mins'],
            }}
            for op in car_ops
        ],
    }}).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f'Routing created: {{car_routing_name}}')

# EV Bike Manufacturing Route
if frappe.db.exists('Routing', bike_routing_name):
    print(f'Routing already exists: {{bike_routing_name}}')
else:
    bike_ops = json.loads('''{bike_ops_json}''')
    frappe.get_doc({{
        'doctype': 'Routing',
        'routing_name': bike_routing_name,
        'operations': [
            {{
                'operation': op['operation'],
                'workstation': op['workstation'],
                'time_in_mins': op['time_in_mins'],
            }}
            for op in bike_ops
        ],
    }}).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f'Routing created: {{bike_routing_name}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("car_routing", CAR_ROUTING)
        self.ctx.cache_set("bike_routing", BIKE_ROUTING)
