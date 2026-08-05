"""
Seeder: Workstations for 3D Printing Services.

Creates manufacturing workstations representing the FDM printer bank,
SLA printer bank, post-processing bench, washing station, UV curing
chamber, QC inspection desk, and packing station.
Idempotent — skips existing workstations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


WORKSTATIONS = [
    {"workstation_name": "FDM Printer Bank",      "description": "Farm of FDM (fused deposition modeling) printers",        "hour_rate": 15.0},
    {"workstation_name": "SLA Printer Bank",      "description": "Farm of SLA (stereolithography) resin printers",          "hour_rate": 30.0},
    {"workstation_name": "Post-Processing Bench", "description": "Workbench for support removal and surface finishing",      "hour_rate": 8.0},
    {"workstation_name": "Washing Station",       "description": "IPA ultrasonic washing unit for SLA parts",               "hour_rate": 5.0},
    {"workstation_name": "UV Curing Chamber",     "description": "UV curing chamber for SLA photopolymer parts",            "hour_rate": 5.0},
    {"workstation_name": "QC Inspection Desk",    "description": "Dimensional and visual quality inspection station",        "hour_rate": 8.0},
    {"workstation_name": "Packing Station",       "description": "Protective packaging and dispatch labelling station",     "hour_rate": 5.0},
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
        'hour_rate': ws.get('hour_rate', 0),
    }}).insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Workstations: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("workstation_names", [ws["workstation_name"] for ws in WORKSTATIONS])
