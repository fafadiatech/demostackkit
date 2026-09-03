"""
Seeder: Workstations for Jewellery Manufacturing.

Creates manufacturing workstations used in jewellery production.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

WORKSTATIONS = [
    {
        "workstation_name": "Melting Furnace",
        "description": "High-temperature induction furnace for melting precious metals",
        "hour_rate": 50.0,
    },
    {
        "workstation_name": "Rolling Mill",
        "description": "Metal rolling mill for sheets and wire drawing",
        "hour_rate": 30.0,
    },
    {
        "workstation_name": "Casting Machine",
        "description": "Centrifugal casting machine for wax investment casting",
        "hour_rate": 40.0,
    },
    {
        "workstation_name": "Filing Bench",
        "description": "Jeweller's bench for hand filing and shaping",
        "hour_rate": 35.0,
    },
    {
        "workstation_name": "Stone Setting Bench",
        "description": "Precision bench for gemstone setting",
        "hour_rate": 60.0,
    },
    {
        "workstation_name": "Polishing Machine",
        "description": "Rotary polishing and buffing machine",
        "hour_rate": 25.0,
    },
    {
        "workstation_name": "QC Station",
        "description": "Quality inspection, hallmarking, and weighing station",
        "hour_rate": 40.0,
    },
]


class WorkstationSeeder(BaseMasterSeeder):
    label = "Workstations"
    priority = 40

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
