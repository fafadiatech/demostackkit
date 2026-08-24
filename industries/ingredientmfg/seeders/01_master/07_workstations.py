"""
Seeder: Workstations for Ingredient Manufacturing.

Creates manufacturing workstations used in batch extraction and
standardisation of food and nutraceutical ingredients.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

WORKSTATIONS = [
    {
        "workstation_name": "Weighing & Dosing Station",
        "description": "Calibrated weighing and dosing of raw botanicals and chemicals",
        "hour_rate": 150.0,
    },
    {
        "workstation_name": "Extraction Vessel",
        "description": "Jacketed solvent extraction vessel for botanical actives",
        "hour_rate": 380.0,
    },
    {
        "workstation_name": "Filtration Unit",
        "description": "Pressure filtration and clarification station",
        "hour_rate": 260.0,
    },
    {
        "workstation_name": "Drying & Standardization Unit",
        "description": "Vacuum drying and potency standardisation line",
        "hour_rate": 320.0,
    },
    {
        "workstation_name": "QC Lab",
        "description": "Quality control and analytical testing laboratory",
        "hour_rate": 300.0,
    },
    {
        "workstation_name": "Packing Line",
        "description": "Automated filling and sealing line",
        "hour_rate": 180.0,
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
