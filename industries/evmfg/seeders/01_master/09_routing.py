"""
Seeder: Routings for Voltara EV Manufacturing.

Creates two standard finished-good routings, plus one narrow single-step
routing for the brake-disc sub-assembly BOM, in a single script:
- EV Car Manufacturing Route: full car production sequence from chassis welding
  through battery assembly, motor fitment, body panels, electrical integration,
  final trim, PDI road test, and dispatch.
- EV Bike Manufacturing Route: streamlined two-wheeler sequence covering frame
  welding, battery assembly, motor fitment, electrical integration, final
  assembly, PDI, and dispatch.
- Brake Disc Assembly Route: single operation, used only by the `MAT-BRAKE-DISC`
  sub-assembly BOM (see `10_bom.py`) instead of the full car routing. A
  sub-assembly BOM that reused the full car routing would carry its own
  independent copy of every operation starting sequence_id back at 1; when a
  multi-level Work Order concatenates operations across BOM levels, that reset
  collides with ERPNext's sequence_id validation
  (`Work Order.validate_operations_sequence`) and the Work Order fails to
  submit (e.g. "Row #N: Sequence ID must be X or Y for Operation ..."). Giving
  the sub-assembly only the single operation it actually performs avoids the
  collision and is more accurate.

Both full routings share the same underlying operations — the same battery,
motor, electrical, and packing steps run on shared workstations. Only the car
route adds body panel fitting (not needed for bikes). All three are cached
for reference by the BOM seeder.
Idempotent — skips routings that already exist.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

CAR_ROUTING = "EV Car Manufacturing Route"
BIKE_ROUTING = "EV Bike Manufacturing Route"
BRAKE_DISC_ROUTING = "Brake Disc Assembly Route"

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

#: Single-step routing for the brake-disc sub-assembly BOM (see module
#: docstring for why this can't just reuse EV Car Manufacturing Route).
BRAKE_DISC_OPERATIONS = [
    {
        "operation": "Brake Disc Assembly",
        "workstation": "Motor Assembly Bay",
        "time_in_mins": 60,
    },
]


class RoutingSeeder(BaseMasterSeeder):
    label = "Routings (Car & Bike)"
    priority = 60

    def run(self) -> None:
        routings = [
            (CAR_ROUTING, CAR_OPERATIONS),
            (BIKE_ROUTING, BIKE_OPERATIONS),
            (BRAKE_DISC_ROUTING, BRAKE_DISC_OPERATIONS),
        ]
        routings_json = json.dumps(routings)

        script = f"""
import json

routings = json.loads('''{routings_json}''')

for routing_name, ops in routings:
    if frappe.db.exists('Routing', routing_name):
        print(f'Routing already exists: {{routing_name}}')
        continue
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
        self.ctx.cache_set("car_routing", CAR_ROUTING)
        self.ctx.cache_set("bike_routing", BIKE_ROUTING)
        self.ctx.cache_set("brake_disc_routing", BRAKE_DISC_ROUTING)
