"""
Seeder: Quality Inspections for Crockery Manufacturing.

Creates Incoming, In Process, and Outgoing Quality Inspections
across crockery items. 85% pass rate for realistic demo data.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import parse_relative_date

# (specification, min_value, max_value)
_QI_PARAMETERS = [
    ("Water Absorption % (ceramics)", 0, 3),
    ("Glaze Thickness (microns)", 80, 200),
    ("Thermal Shock Resistance (cycles)", 10, 30),
    ("Dimensional Accuracy (mm)", 0, 1),
]

_INSPECTION_TYPES = ["Incoming", "In Process", "Outgoing"]


class QualityInspectionSeeder(BaseTransactionSeeder):
    label = "Quality Inspections"
    priority = 230
    _volume_attr = "quality_inspections"
    default_volume = 20

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("item_codes"):
            errors.append("item_codes not in cache — run ItemSeeder first")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        item_codes = self.ctx.cache_get("item_codes", [])

        if not item_codes:
            return

        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days

        inspections = []
        for _ in range(self.volume):
            report_date = start_date + timedelta(days=rng.randint(0, span))
            item_code = rng.choice(item_codes)
            inspection_type = rng.choice(_INSPECTION_TYPES)
            accepted = rng.random() < 0.85
            overall_status = "Accepted" if accepted else "Rejected"

            n_params = rng.randint(1, min(3, len(_QI_PARAMETERS)))
            chosen_params = rng.sample(_QI_PARAMETERS, n_params)
            readings = []
            for i, (spec, min_val, max_val) in enumerate(chosen_params):
                if accepted or i < n_params - 1:
                    reading_val = round(rng.uniform(min_val, max_val), 2)
                    r_status = "Accepted"
                else:
                    reading_val = round(rng.uniform(max_val * 1.05, max_val * 1.2), 2)
                    r_status = "Rejected"
                readings.append({
                    "specification": spec,
                    "value_type": "Numeric",
                    "min_value": min_val,
                    "max_value": max_val,
                    "reading_1": str(reading_val),
                    "status": r_status,
                })

            inspections.append({
                "item_code": item_code,
                "inspection_type": inspection_type,
                "report_date": report_date.isoformat(),
                "sample_size": rng.randint(5, 50),
                "status": overall_status,
                "readings": readings,
            })

        insp_json = json.dumps(inspections)
        script = f"""
import json

company = '{company}'
inspections = json.loads('''{insp_json}''')
created = 0
for insp in inspections:
    try:
        qi = frappe.get_doc({{
            'doctype': 'Quality Inspection',
            'company': company,
            'inspection_type': insp['inspection_type'],
            'item_code': insp['item_code'],
            'sample_size': insp['sample_size'],
            'report_date': insp['report_date'],
            'status': insp['status'],
            'inspected_by': 'Administrator',
            'readings': [{{
                'specification': r['specification'],
                'value_type': r['value_type'],
                'min_value': r['min_value'],
                'max_value': r['max_value'],
                'reading_1': r['reading_1'],
                'status': r['status'],
            }} for r in insp['readings']],
        }})
        qi.flags.ignore_mandatory = True
        qi.insert(ignore_permissions=True)
        qi.submit()
        created += 1
    except Exception as e:
        print(f'WARN QI: {{e}}')

frappe.db.commit()
print(f'Quality Inspections created: {{created}}')
"""
        self._exec(script, timeout=300)


