"""
Seeder: Workstations for Alpha Abrasives.

Creates the five-stage abrasive production floor: raw material mixing and
bonding, pressing/moulding into wheel or disc form, curing in the oven,
grading and QC, and final packing — a short routing comparable in length to
a kiln-firing ceramics line.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

WORKSTATIONS = [
    {
        "workstation_name": "Mixing & Bonding Station",
        "description": "Blend abrasive grain, resin/rubber bond and fillers into a mix ready for moulding",
        "hour_rate": 450.0,
    },
    {
        "workstation_name": "Press & Mould Station",
        "description": "Hydraulic press moulds the bonded mix into wheel, disc or belt form",
        "hour_rate": 550.0,
    },
    {
        "workstation_name": "Curing Oven",
        "description": "Thermal curing of pressed abrasive products to set the bond",
        "hour_rate": 400.0,
    },
    {
        "workstation_name": "Grading & QC Bench",
        "description": "Grit consistency, wheel balance, burst/RPM safety and bond hardness checks",
        "hour_rate": 350.0,
    },
    {
        "workstation_name": "Packing Station",
        "description": "Final labelling, boxing and stretch wrapping for dispatch",
        "hour_rate": 250.0,
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
