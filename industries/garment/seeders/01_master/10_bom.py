"""
Seeder: Bill of Materials for Garment Manufacturing.

Creates BOMs for all finished goods items, linking them to raw materials
and the Garment Standard Route. BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Garment Standard Route"

# Each BOM: finished good item → list of {item_code, qty, uom, rate}
BOMS = [
    {
        "item": "GRM-TSH-WH-S",
        "qty": 1,
        "items": [
            {"item_code": "FAB-COT-WH-001", "qty": 0.8, "uom": "Meter", "rate": 180.0},
            {"item_code": "THR-COT-WH-001", "qty": 2, "uom": "Spool", "rate": 45.0},
            {"item_code": "BTN-PLY-BK-001", "qty": 5, "uom": "Piece", "rate": 2.5},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-TSH-WH-M",
        "qty": 1,
        "items": [
            {"item_code": "FAB-COT-WH-001", "qty": 0.9, "uom": "Meter", "rate": 180.0},
            {"item_code": "THR-COT-WH-001", "qty": 2, "uom": "Spool", "rate": 45.0},
            {"item_code": "BTN-PLY-BK-001", "qty": 5, "uom": "Piece", "rate": 2.5},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-TSH-WH-L",
        "qty": 1,
        "items": [
            {"item_code": "FAB-COT-WH-001", "qty": 1.0, "uom": "Meter", "rate": 180.0},
            {"item_code": "THR-COT-WH-001", "qty": 2, "uom": "Spool", "rate": 45.0},
            {"item_code": "BTN-PLY-BK-001", "qty": 5, "uom": "Piece", "rate": 2.5},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-TSH-BL-M",
        "qty": 1,
        "items": [
            {"item_code": "FAB-COT-BL-002", "qty": 0.9, "uom": "Meter", "rate": 250.0},
            {"item_code": "THR-COT-BL-002", "qty": 2, "uom": "Spool", "rate": 38.0},
            {"item_code": "BTN-PLY-BK-001", "qty": 5, "uom": "Piece", "rate": 2.5},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-DNM-32",
        "qty": 1,
        "items": [
            {"item_code": "FAB-COT-BL-002", "qty": 1.5, "uom": "Meter", "rate": 250.0},
            {"item_code": "THR-COT-BL-002", "qty": 3, "uom": "Spool", "rate": 38.0},
            {"item_code": "BTN-MTL-SL-002", "qty": 1, "uom": "Piece", "rate": 8.0},
            {"item_code": "ZIP-MTL-GD-002", "qty": 1, "uom": "Piece", "rate": 25.0},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-DNM-34",
        "qty": 1,
        "items": [
            {"item_code": "FAB-COT-BL-002", "qty": 1.6, "uom": "Meter", "rate": 250.0},
            {"item_code": "THR-COT-BL-002", "qty": 3, "uom": "Spool", "rate": 38.0},
            {"item_code": "BTN-MTL-SL-002", "qty": 1, "uom": "Piece", "rate": 8.0},
            {"item_code": "ZIP-MTL-GD-002", "qty": 1, "uom": "Piece", "rate": 25.0},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-SHT-WH-M",
        "qty": 1,
        "items": [
            {"item_code": "FAB-COT-WH-001", "qty": 1.2, "uom": "Meter", "rate": 180.0},
            {"item_code": "THR-COT-WH-001", "qty": 3, "uom": "Spool", "rate": 45.0},
            {"item_code": "BTN-PLY-BK-001", "qty": 8, "uom": "Piece", "rate": 2.5},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-SHT-BL-M",
        "qty": 1,
        "items": [
            {"item_code": "FAB-LIN-NA-005", "qty": 1.2, "uom": "Meter", "rate": 320.0},
            {"item_code": "THR-COT-BL-002", "qty": 3, "uom": "Spool", "rate": 38.0},
            {"item_code": "BTN-PLY-BK-001", "qty": 8, "uom": "Piece", "rate": 2.5},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-JKT-BK-M",
        "qty": 1,
        "items": [
            {"item_code": "FAB-POL-BK-003", "qty": 2.0, "uom": "Meter", "rate": 120.0},
            {"item_code": "THR-COT-BL-002", "qty": 4, "uom": "Spool", "rate": 38.0},
            {"item_code": "BTN-MTL-SL-002", "qty": 4, "uom": "Piece", "rate": 8.0},
            {"item_code": "ZIP-MTL-GD-002", "qty": 1, "uom": "Piece", "rate": 25.0},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-DRS-RD-S",
        "qty": 1,
        "items": [
            {"item_code": "FAB-SIL-RD-004", "qty": 2.5, "uom": "Meter", "rate": 850.0},
            {"item_code": "THR-COT-WH-001", "qty": 3, "uom": "Spool", "rate": 45.0},
            {"item_code": "ZIP-NLN-BK-001", "qty": 1, "uom": "Piece", "rate": 12.0},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
        ],
    },
    {
        "item": "GRM-TRS-NA-32",
        "qty": 1,
        "items": [
            {"item_code": "FAB-LIN-NA-005", "qty": 1.4, "uom": "Meter", "rate": 320.0},
            {"item_code": "THR-COT-BL-002", "qty": 3, "uom": "Spool", "rate": 38.0},
            {"item_code": "BTN-MTL-SL-002", "qty": 1, "uom": "Piece", "rate": 8.0},
            {"item_code": "ZIP-MTL-GD-002", "qty": 1, "uom": "Piece", "rate": 25.0},
            {"item_code": "LBL-WVN-001", "qty": 1, "uom": "Piece", "rate": 3.5},
            {"item_code": "PKG-PLY-001", "qty": 1, "uom": "Piece", "rate": 4.0},
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

routing_name = '{ROUTING_NAME}'
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
            'routing': routing_name,
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
