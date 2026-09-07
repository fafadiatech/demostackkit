"""
Shared seeder: Quality Inspection Templates for each industry's QC Operation
(ref #1, phase 1).

Every Manufacturing industry already names one Operation as its quality gate
("Solar QC Sign-off", "QC Inspection", "Quality Testing", ...), but nothing
ever attaches a `Quality Inspection Template` to it — the field sits empty,
so a Job Card against that Operation never carries a checklist and the
Job Card completion seeder (`215_production.py`) has nothing to react to.

Reads the `qc_operation_name` / `qc_inspection_parameters` cache keys each
industry's `08_operations.py` sets, ensures each specification exists as a
`Quality Inspection Parameter` master (the Link target for template /
reading rows), builds one `Quality Inspection Template` from those
industry-specific parameters (reusing the same specifications the
per-industry `03_quality_inspections.py` seeder already uses for its own
readings), and links it onto the Operation via `quality_inspection_template`.

No-ops when Manufacturing isn't in `modules` or the industry's operations
seeder never cached a QC operation. Idempotent — skips Parameter / template
docs that already exist and only writes the Operation link when it's missing.

Priority 95 — after every industry's Operations (50) and BOM (70) seeders,
well before Opening Stock / Production (215) so the link is in place before
any Job Card is ever created.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

_MARKER = "DSK_QI_TEMPLATE::"


class QualityInspectionTemplateSeeder(BaseMasterSeeder):
    label = "Quality Inspection Templates"
    priority = 95

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Manufacturing" not in cfg.modules:
            return

        operation_name = self.ctx.cache_get("qc_operation_name")
        parameters = self.ctx.cache_get("qc_inspection_parameters")
        if not operation_name or not parameters:
            return

        template_name = f"{operation_name} QC Template"
        params = [
            {"specification": spec, "min_value": lo, "max_value": hi} for spec, lo, hi in parameters
        ]
        payload_json = json.dumps(
            {"operation": operation_name, "template_name": template_name, "params": params}
        )
        script = f"""
import json

payload = json.loads('''{payload_json}''')
operation = payload['operation']
template_name = payload['template_name']
params = payload['params']

created = linked = 0
if frappe.db.exists('Operation', operation):
    # specification is a Link to Quality Inspection Parameter — create
    # masters first or template insert raises LinkValidationError.
    for p in params:
        if not frappe.db.exists('Quality Inspection Parameter', p['specification']):
            frappe.get_doc({{
                'doctype': 'Quality Inspection Parameter',
                'parameter': p['specification'],
                'description': p['specification'],
            }}).insert(ignore_permissions=True)

    if not frappe.db.exists('Quality Inspection Template', template_name):
        frappe.get_doc({{
            'doctype': 'Quality Inspection Template',
            'quality_inspection_template_name': template_name,
            'item_quality_inspection_parameter': [
                {{
                    'specification': p['specification'],
                    'numeric': 1,
                    'min_value': p['min_value'],
                    'max_value': p['max_value'],
                }}
                for p in params
            ],
        }}).insert(ignore_permissions=True)
        created = 1

    if frappe.db.get_value('Operation', operation, 'quality_inspection_template') != template_name:
        frappe.db.set_value('Operation', operation, 'quality_inspection_template', template_name)
        linked = 1

frappe.db.commit()
print('{_MARKER}' + json.dumps({{'created': created, 'linked': linked}}))
print(f'Quality Inspection Template: created={{created}}, linked={{linked}}')
"""
        self._exec(script, timeout=120)
