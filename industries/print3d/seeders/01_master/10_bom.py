"""
Seeder: Bill of Materials for 3D Printing Services.

Creates BOMs for all 9 finished goods items (FDM prototypes, FDM functional
parts, SLA prototypes, SLA functional parts, and SLA display models).
Each BOM references either the FDM Standard Route or SLA Standard Route
and lists the appropriate filament/resin and consumable inputs.
BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


BOMS = [
    {
        "item": "PRT-FDM-PROTO-S", "qty": 1, "routing": "FDM Standard Route",
        "items": [
            {"item_code": "MAT-PLA-WHT",   "qty": 0.05, "uom": "Kg",   "rate": 18.0},
            {"item_code": "MAT-SAND-220",  "qty": 0.05, "uom": "Pack", "rate": 4.0},
            {"item_code": "MAT-PKG-BOX-S", "qty": 1,    "uom": "Nos",  "rate": 1.20},
        ],
    },
    {
        "item": "PRT-FDM-PROTO-M", "qty": 1, "routing": "FDM Standard Route",
        "items": [
            {"item_code": "MAT-PLA-BLK",    "qty": 0.15, "uom": "Kg",   "rate": 18.0},
            {"item_code": "MAT-SAND-220",   "qty": 0.10, "uom": "Pack", "rate": 4.0},
            {"item_code": "MAT-PKG-BOX-S",  "qty": 1,    "uom": "Nos",  "rate": 1.20},
            {"item_code": "MAT-PKG-BUBBLE", "qty": 1,    "uom": "Nos",  "rate": 0.50},
        ],
    },
    {
        "item": "PRT-FDM-PROTO-L", "qty": 1, "routing": "FDM Standard Route",
        "items": [
            {"item_code": "MAT-ABS-GRY",    "qty": 0.35, "uom": "Kg",   "rate": 22.0},
            {"item_code": "MAT-SAND-220",   "qty": 0.20, "uom": "Pack", "rate": 4.0},
            {"item_code": "MAT-PKG-BOX-S",  "qty": 1,    "uom": "Nos",  "rate": 1.20},
            {"item_code": "MAT-PKG-BUBBLE", "qty": 2,    "uom": "Nos",  "rate": 0.50},
        ],
    },
    {
        "item": "PRT-FDM-FUNC-S", "qty": 1, "routing": "FDM Standard Route",
        "items": [
            {"item_code": "MAT-PETG-CLR",  "qty": 0.05, "uom": "Kg",  "rate": 25.0},
            {"item_code": "MAT-PKG-BOX-S", "qty": 1,    "uom": "Nos", "rate": 1.20},
        ],
    },
    {
        "item": "PRT-FDM-FUNC-M", "qty": 1, "routing": "FDM Standard Route",
        "items": [
            {"item_code": "MAT-ABS-GRY",    "qty": 0.20, "uom": "Kg",   "rate": 22.0},
            {"item_code": "MAT-SAND-220",   "qty": 0.10, "uom": "Pack", "rate": 4.0},
            {"item_code": "MAT-PKG-BOX-S",  "qty": 1,    "uom": "Nos",  "rate": 1.20},
            {"item_code": "MAT-PKG-BUBBLE", "qty": 1,    "uom": "Nos",  "rate": 0.50},
        ],
    },
    {
        "item": "PRT-SLA-PROTO-S", "qty": 1, "routing": "SLA Standard Route",
        "items": [
            {"item_code": "MAT-RES-STD",   "qty": 0.03, "uom": "Litre", "rate": 45.0},
            {"item_code": "MAT-IPA-99",    "qty": 0.05, "uom": "Litre", "rate": 8.0},
            {"item_code": "MAT-PKG-BOX-S", "qty": 1,    "uom": "Nos",   "rate": 1.20},
        ],
    },
    {
        "item": "PRT-SLA-PROTO-M", "qty": 1, "routing": "SLA Standard Route",
        "items": [
            {"item_code": "MAT-RES-STD",    "qty": 0.10, "uom": "Litre", "rate": 45.0},
            {"item_code": "MAT-IPA-99",     "qty": 0.10, "uom": "Litre", "rate": 8.0},
            {"item_code": "MAT-SAND-220",   "qty": 0.05, "uom": "Pack",  "rate": 4.0},
            {"item_code": "MAT-PKG-BOX-S",  "qty": 1,    "uom": "Nos",   "rate": 1.20},
        ],
    },
    {
        "item": "PRT-SLA-FUNC-S", "qty": 1, "routing": "SLA Standard Route",
        "items": [
            {"item_code": "MAT-RES-ENG",   "qty": 0.04, "uom": "Litre", "rate": 75.0},
            {"item_code": "MAT-IPA-99",    "qty": 0.05, "uom": "Litre", "rate": 8.0},
            {"item_code": "MAT-PKG-BOX-S", "qty": 1,    "uom": "Nos",   "rate": 1.20},
        ],
    },
    {
        "item": "PRT-SLA-DISP-M", "qty": 1, "routing": "SLA Standard Route",
        "items": [
            {"item_code": "MAT-RES-STD",    "qty": 0.12, "uom": "Litre", "rate": 45.0},
            {"item_code": "MAT-IPA-99",     "qty": 0.12, "uom": "Litre", "rate": 8.0},
            {"item_code": "MAT-SAND-220",   "qty": 0.10, "uom": "Pack",  "rate": 4.0},
            {"item_code": "MAT-PRIMER",     "qty": 0.10, "uom": "Nos",   "rate": 6.0},
            {"item_code": "MAT-PKG-BOX-S",  "qty": 1,    "uom": "Nos",   "rate": 1.20},
            {"item_code": "MAT-PKG-BUBBLE", "qty": 1,    "uom": "Nos",   "rate": 0.50},
        ],
    },
]


class BOMSeeder(BaseMasterSeeder):
    label = "Bill of Materials"
    priority = 70

    def run(self) -> None:
        company_name = self.ctx.industry_config.company.name
        boms_json = json.dumps(BOMS)
        script = f"""
import json

company_name = '{company_name}'
boms = json.loads('''{boms_json}''')
created = skipped = errors = 0

for b in boms:
    # Skip if an active (submitted) BOM already exists for this item
    if frappe.db.exists('BOM', {{'item': b['item'], 'docstatus': 1}}):
        skipped += 1
        continue
    try:
        doc = frappe.get_doc({{
            'doctype': 'BOM',
            'company': company_name,
            'item': b['item'],
            'quantity': b.get('qty', 1),
            'routing': b['routing'],
            'is_active': 1,
            'is_default': 1,
            'items': [
                {{
                    'item_code': it['item_code'],
                    'qty': it['qty'],
                    'uom': it['uom'],
                    'rate': it['rate'],
                    'stock_uom': it['uom'],
                    'conversion_factor': 1,
                }}
                for it in b['items']
            ],
        }})
        doc.insert(ignore_permissions=True)
        doc.submit()
        created += 1
    except Exception as e:
        print(f'ERROR BOM {{b["item"]}}: {{e}}')
        errors += 1

frappe.db.commit()
print(f'BOMs: created={{created}}, skipped={{skipped}}, errors={{errors}}')
if errors:
    raise SystemExit(f'{{errors}} BOM(s) failed to create')
"""
        self._exec(script, timeout=300)
