"""
Seeder: Workstations for PowerTech Electrical Manufacturing.

Creates manufacturing workstations representing the electrical equipment
production floor: coil winding for HV and LV coils, CRGO core lamination
and stacking, core-and-coil assembly, MS tank fabrication, vacuum oil filling,
high voltage testing laboratory, switchgear panel assembly bay, and packing
and dispatch area.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

WORKSTATIONS = [
    {
        "workstation_name": "Coil Winding Station",
        "description": "CNC coil winding machine for HV and LV copper coils",
        "hour_rate": 600.0,
    },
    {
        "workstation_name": "Core Lamination Station",
        "description": "CRGO lamination cutting, stacking and clamping bay",
        "hour_rate": 550.0,
    },
    {
        "workstation_name": "Core & Coil Assembly Bay",
        "description": "Assembly of wound coils onto laminated transformer core",
        "hour_rate": 750.0,
    },
    {
        "workstation_name": "Tank Fabrication Bay",
        "description": "MS tank fabrication by welding, dressing and accessory fitting",
        "hour_rate": 650.0,
    },
    {
        "workstation_name": "Oil Filling Station",
        "description": "Vacuum degassing and hot oil circulation filling station",
        "hour_rate": 500.0,
    },
    {
        "workstation_name": "HV Testing Lab",
        "description": "High voltage withstand, insulation resistance, turns ratio and load loss testing",
        "hour_rate": 900.0,
    },
    {
        "workstation_name": "Switchgear Assembly Bay",
        "description": "HT and LT panel assembly with busbar installation and breaker fitment",
        "hour_rate": 800.0,
    },
    {
        "workstation_name": "Packing & Dispatch Area",
        "description": "Protective crating, stretch wrapping and dispatch documentation",
        "hour_rate": 300.0,
    },
]


class WorkstationSeeder(BaseMasterSeeder):
    label = "Workstations"
    priority = 70

    def run(self) -> None:
        ws_json = json.dumps(WORKSTATIONS)
        script = f"""
import json

workstations = json.loads('''{ws_json}''')
created = skipped = 0
for ws in workstations:
    if frappe.db.exists('Workstation', ws['workstation_name']):
        skipped += 1
        continue
    frappe.get_doc({{
        'doctype': 'Workstation',
        'workstation_name': ws['workstation_name'],
        'description': ws.get('description', ''),
        # Workstation.before_save() recomputes hour_rate as the sum of the four
        # cost components, so hour_rate cannot be set directly -- seed the
        # components and let the declared rate fall out as their total.
        'hour_rate_labour': ws.get('hour_rate', 0) * 0.30,
        'hour_rate_electricity': ws.get('hour_rate', 0) * 0.40,
        'hour_rate_consumable': ws.get('hour_rate', 0) * 0.15,
        'hour_rate_rent': ws.get('hour_rate', 0) * 0.15,
    }}).insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Workstations: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("workstation_names", [ws["workstation_name"] for ws in WORKSTATIONS])
