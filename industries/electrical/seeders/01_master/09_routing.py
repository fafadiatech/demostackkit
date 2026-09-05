"""
Seeder: Routings for PowerTech Electrical Manufacturing.

Creates two standard finished-good routings, plus three narrow single-step
routings for sub-assembly BOMs, in a single script:
- Transformer Manufacturing Route: full transformer production sequence from
  coil winding through core lamination, core-and-coil assembly, tank
  fabrication, vacuum oil filling, HV testing, and final packing.
- Switchgear Manufacturing Route: streamlined panel assembly sequence covering
  switchgear panel assembly, HV testing, and final inspection and packing.
- Coil Winding Route / Core Lamination Route / Busbar Assembly Route: each a
  single operation, used only by the sub-assembly BOMs (`ESA-COIL-LV`,
  `ESA-COIL-HV`, `ESA-CORE`, `ESA-SWGR-BUS` — see `10_bom.py`) instead of the
  full finished-good routing. A sub-assembly BOM that reused the full 7-step
  routing would carry its own independent copy of every operation (including
  "Coil Winding") starting sequence_id back at 1; when a multi-level Work
  Order concatenates operations across BOM levels, that reset collides with
  ERPNext's sequence_id validation (`Work Order.validate_operations_sequence`)
  and the Work Order fails to submit with e.g. "Row #8: Sequence ID must be 7
  or 8 for Operation Coil Winding." Giving each sub-assembly only the single
  operation it actually performs avoids the collision and is more accurate.

Both full routings share the High Voltage Testing and Final Inspection &
Packing operations — demonstrating the common testing infrastructure across
product families. All five are cached for reference by the BOM seeder.
Idempotent — skips routings that already exist.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

TRANSFORMER_ROUTING = "Transformer Manufacturing Route"
SWITCHGEAR_ROUTING = "Switchgear Manufacturing Route"
COIL_WINDING_ROUTING = "Coil Winding Route"
CORE_LAMINATION_ROUTING = "Core Lamination Route"
BUSBAR_ASSEMBLY_ROUTING = "Busbar Assembly Route"

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

#: Single-step routings for sub-assembly BOMs (see module docstring for why
#: these can't just reuse the finished-good routings above).
COIL_WINDING_OPERATIONS = [
    {
        "operation": "Coil Winding",
        "workstation": "Coil Winding Station",
        "time_in_mins": 480,
    },
]

CORE_LAMINATION_OPERATIONS = [
    {
        "operation": "Core Lamination & Stacking",
        "workstation": "Core Lamination Station",
        "time_in_mins": 360,
    },
]

BUSBAR_ASSEMBLY_OPERATIONS = [
    {
        "operation": "Switchgear Panel Assembly",
        "workstation": "Switchgear Assembly Bay",
        "time_in_mins": 120,
    },
]


class RoutingSeeder(BaseMasterSeeder):
    label = "Routings (Transformer & Switchgear)"
    priority = 66

    def run(self) -> None:
        routings = [
            (TRANSFORMER_ROUTING, TRANSFORMER_OPERATIONS),
            (SWITCHGEAR_ROUTING, SWITCHGEAR_OPERATIONS),
            (COIL_WINDING_ROUTING, COIL_WINDING_OPERATIONS),
            (CORE_LAMINATION_ROUTING, CORE_LAMINATION_OPERATIONS),
            (BUSBAR_ASSEMBLY_ROUTING, BUSBAR_ASSEMBLY_OPERATIONS),
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
        self.ctx.cache_set("transformer_routing", TRANSFORMER_ROUTING)
        self.ctx.cache_set("switchgear_routing", SWITCHGEAR_ROUTING)
        self.ctx.cache_set("coil_winding_routing", COIL_WINDING_ROUTING)
        self.ctx.cache_set("core_lamination_routing", CORE_LAMINATION_ROUTING)
        self.ctx.cache_set("busbar_assembly_routing", BUSBAR_ASSEMBLY_ROUTING)
