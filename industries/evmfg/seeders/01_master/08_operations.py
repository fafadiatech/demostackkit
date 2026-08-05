"""
Seeder: Operations for Voltara EV Manufacturing.

Creates manufacturing operations covering both the EV car and EV bike
production workflows: battery cell assembly, pack integration, motor
assembly, chassis welding, body panel fitting, electrical systems
integration, final assembly and trim, PDI and road test, and EV packing.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


OPERATIONS = [
    {"name": "Battery Cell Assembly",          "workstation": "Battery Assembly Station",   "description": "Sort, grade and spot-weld cells into modules",              "operating_cost": 800.0},
    {"name": "Battery Pack Integration",       "workstation": "Pack Integration Bay",       "description": "Stack modules, wire BMS and seal battery pack",            "operating_cost": 650.0},
    {"name": "Motor Assembly",                 "workstation": "Motor Assembly Bay",         "description": "Assemble stator, rotor and install bearings",              "operating_cost": 1000.0},
    {"name": "Chassis & Frame Welding",        "workstation": "Chassis Welding Station",    "description": "Weld steel monocoque or aluminium bike frame to spec",     "operating_cost": 700.0},
    {"name": "Body Panel Fitting",             "workstation": "Body Assembly Line",         "description": "Fit and hem exterior panels to body-in-white",             "operating_cost": 800.0},
    {"name": "Electrical Systems Integration", "workstation": "Electrical Integration Bay", "description": "Route wiring harness and connect all HV/LV systems",       "operating_cost": 750.0},
    {"name": "Final Assembly & Trim",          "workstation": "Final Assembly Bay",         "description": "Install trim, glass, seats and mechanical sub-assemblies", "operating_cost": 900.0},
    {"name": "PDI & Road Test",                "workstation": "PDI & Testing Bay",          "description": "Flash software, run diagnostics and complete road test",    "operating_cost": 600.0},
    {"name": "EV Packing & Dispatch",          "workstation": "EV Packing Station",         "description": "Wrap vehicle, crate and prepare dispatch documentation",    "operating_cost": 300.0},
]


class OperationSeeder(BaseMasterSeeder):
    label = "Operations"
    priority = 50

    def run(self) -> None:
        ops_json = json.dumps(OPERATIONS)
        script = f"""
import json

operations = json.loads('''{ops_json}''')
created = skipped = 0
for op in operations:
    if frappe.db.exists('Operation', op['name']):
        skipped += 1
        continue
    frappe.get_doc({{
        'doctype': 'Operation',
        'name': op['name'],
        'workstation': op['workstation'],
        'description': op.get('description', ''),
        'operating_cost': op.get('operating_cost', 0),
    }}).insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Operations: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("operation_names", [op["name"] for op in OPERATIONS])
