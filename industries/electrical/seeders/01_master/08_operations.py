"""
Seeder: Operations for PowerTech Electrical Manufacturing.

Creates manufacturing operations covering both transformer and switchgear
production workflows: coil winding, core lamination and stacking, core-and-coil
assembly, tank fabrication and fitting, vacuum oil filling, high voltage
testing, switchgear panel assembly, and final inspection and packing.

Transformer route uses all operations except switchgear assembly.
Switchgear route uses the assembly bay, HV testing, and packing steps.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

OPERATIONS = [
    {
        "name": "Coil Winding",
        "workstation": "Coil Winding Station",
        "description": "Wind HV and LV copper coils to specification on mandrel",
        "operating_cost": 600.0,
    },
    {
        "name": "Core Lamination & Stacking",
        "workstation": "Core Lamination Station",
        "description": "Cut CRGO laminations and stack into mitred-joint core",
        "operating_cost": 550.0,
    },
    {
        "name": "Core & Coil Assembly",
        "workstation": "Core & Coil Assembly Bay",
        "description": "Insert wound coils onto core, apply insulation and fit clamping structure",
        "operating_cost": 750.0,
    },
    {
        "name": "Tank Fabrication & Fitting",
        "workstation": "Tank Fabrication Bay",
        "description": "Fabricate MS tank, weld radiators and fit conservator and accessories",
        "operating_cost": 650.0,
    },
    {
        "name": "Vacuum Oil Filling",
        "workstation": "Oil Filling Station",
        "description": "Fill transformer oil under vacuum with hot oil circulation and degassing",
        "operating_cost": 500.0,
    },
    {
        "name": "High Voltage Testing",
        "workstation": "HV Testing Lab",
        "description": "Perform HV withstand, turns ratio, insulation resistance and load loss tests",
        "operating_cost": 900.0,
    },
    {
        "name": "Switchgear Panel Assembly",
        "workstation": "Switchgear Assembly Bay",
        "description": "Assemble busbars, VCB or MCCB, protection relays and wiring in panel",
        "operating_cost": 800.0,
    },
    {
        "name": "Final Inspection & Packing",
        "workstation": "Packing & Dispatch Area",
        "description": "Final visual inspection, protective crating and dispatch documentation",
        "operating_cost": 300.0,
    },
]


class OperationSeeder(BaseMasterSeeder):
    label = "Operations"
    priority = 80

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
