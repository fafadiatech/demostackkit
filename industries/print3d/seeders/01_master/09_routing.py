"""
Seeder: Routings for 3D Printing Services.

Creates two standard routings in a single script:
- FDM Standard Route: for all FDM (fused deposition modeling) printed parts
- SLA Standard Route: for all SLA (stereolithography) resin printed parts

Both are cached for reference by the BOM seeder.
Idempotent — skips routings that already exist.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


FDM_ROUTING = "FDM Standard Route"
SLA_ROUTING = "SLA Standard Route"

FDM_OPERATIONS = [
    {"operation": "FDM Printing",        "workstation": "FDM Printer Bank",      "time_in_mins": 120},
    {"operation": "Support Removal",     "workstation": "Post-Processing Bench", "time_in_mins": 10},
    {"operation": "Sanding & Finishing", "workstation": "Post-Processing Bench", "time_in_mins": 15},
    {"operation": "Print QC Inspection", "workstation": "QC Inspection Desk",   "time_in_mins": 5},
    {"operation": "Packing & Dispatch",  "workstation": "Packing Station",       "time_in_mins": 5},
]

SLA_OPERATIONS = [
    {"operation": "SLA Printing",        "workstation": "SLA Printer Bank",      "time_in_mins": 90},
    {"operation": "Support Removal",     "workstation": "Post-Processing Bench", "time_in_mins": 15},
    {"operation": "IPA Washing",         "workstation": "Washing Station",       "time_in_mins": 10},
    {"operation": "UV Curing",           "workstation": "UV Curing Chamber",     "time_in_mins": 15},
    {"operation": "Sanding & Finishing", "workstation": "Post-Processing Bench", "time_in_mins": 10},
    {"operation": "Print QC Inspection", "workstation": "QC Inspection Desk",   "time_in_mins": 5},
    {"operation": "Packing & Dispatch",  "workstation": "Packing Station",       "time_in_mins": 5},
]


class RoutingSeeder(BaseMasterSeeder):
    label = "Routings (FDM & SLA)"
    priority = 60

    def run(self) -> None:
        fdm_ops_json = json.dumps(FDM_OPERATIONS)
        sla_ops_json = json.dumps(SLA_OPERATIONS)

        script = f"""
import json

fdm_routing_name = '{FDM_ROUTING}'
sla_routing_name = '{SLA_ROUTING}'

# FDM Standard Route
if frappe.db.exists('Routing', fdm_routing_name):
    print(f'Routing already exists: {{fdm_routing_name}}')
else:
    fdm_ops = json.loads('''{fdm_ops_json}''')
    frappe.get_doc({{
        'doctype': 'Routing',
        'routing_name': fdm_routing_name,
        'operations': [
            {{
                'operation': op['operation'],
                'workstation': op['workstation'],
                'time_in_mins': op['time_in_mins'],
            }}
            for op in fdm_ops
        ],
    }}).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f'Routing created: {{fdm_routing_name}}')

# SLA Standard Route
if frappe.db.exists('Routing', sla_routing_name):
    print(f'Routing already exists: {{sla_routing_name}}')
else:
    sla_ops = json.loads('''{sla_ops_json}''')
    frappe.get_doc({{
        'doctype': 'Routing',
        'routing_name': sla_routing_name,
        'operations': [
            {{
                'operation': op['operation'],
                'workstation': op['workstation'],
                'time_in_mins': op['time_in_mins'],
            }}
            for op in sla_ops
        ],
    }}).insert(ignore_permissions=True)
    frappe.db.commit()
    print(f'Routing created: {{sla_routing_name}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("fdm_routing", FDM_ROUTING)
        self.ctx.cache_set("sla_routing", SLA_ROUTING)
