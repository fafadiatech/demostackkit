"""
Seeder: Operations for Solar System Assembly.

Creates manufacturing operations linked to workstations.
Idempotent — skips existing operations.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


OPERATIONS = [
    {"name": "Panel Layout Planning",          "workstation": "Panel Assembly Bay",       "description": "Plan panel arrangement and mounting positions", "operating_cost": 50.0},
    {"name": "Panel Mounting",                 "workstation": "Panel Assembly Bay",       "description": "Fix panels to mounting structure using clamps", "operating_cost": 80.0},
    {"name": "Cable Routing & Crimping",       "workstation": "Cable Management Station", "description": "Route DC/AC cables and crimp MC4 connectors", "operating_cost": 70.0},
    {"name": "Inverter Installation",          "workstation": "Inverter Mounting Bay",    "description": "Mount inverter, connect strings and AC output", "operating_cost": 100.0},
    {"name": "System Commissioning & Testing", "workstation": "System Testing Bay",       "description": "String IV testing, grid sync and performance check", "operating_cost": 150.0},
    {"name": "Solar QC Sign-off",              "workstation": "QC Inspection Station",    "description": "Safety audit, earthing check and customer handover", "operating_cost": 80.0},
]


class OperationSeeder(BaseMasterSeeder):
    label = "Operations"
    priority = 50

    def run(self) -> None:
        ops_json = json.dumps(OPERATIONS)
        script = f"""
import frappe, json
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()

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
