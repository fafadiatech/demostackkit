"""
Seeder: Bill of Materials for Crockery Manufacturing.

Creates BOMs for all finished crockery pieces, linking them to clay and glazes
and the Crockery Standard Route. BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Crockery Standard Route"

# Each BOM: finished good item → list of {item_code, qty, uom, rate}
BOMS = [
    {
        "item": "CRK-DIN-PLT-27",
        "qty": 1,
        "items": [
            {"item_code": "CLY-STN-001", "qty": 0.5, "uom": "Kg", "rate": 450.0},
            {"item_code": "GLZ-WH-001", "qty": 0.1, "uom": "Kg", "rate": 850.0},
            {"item_code": "SND-PPR-001", "qty": 2, "uom": "Piece", "rate": 15.0},
            {"item_code": "SPG-WET-001", "qty": 0.1, "uom": "Piece", "rate": 80.0},
            {"item_code": "LBL-STK-001", "qty": 1, "uom": "Piece", "rate": 4.0},
            {"item_code": "PKG-BOX-SGL", "qty": 1, "uom": "Piece", "rate": 65.0},
            {"item_code": "PKG-BUB-001", "qty": 0.2, "uom": "Roll", "rate": 25.0},
        ],
    },
    {
        "item": "CRK-DIN-PLT-22",
        "qty": 1,
        "items": [
            {"item_code": "CLY-STN-001", "qty": 0.35, "uom": "Kg", "rate": 450.0},
            {"item_code": "GLZ-WH-001", "qty": 0.08, "uom": "Kg", "rate": 850.0},
            {"item_code": "SND-PPR-001", "qty": 1, "uom": "Piece", "rate": 15.0},
            {"item_code": "SPG-WET-001", "qty": 0.1, "uom": "Piece", "rate": 80.0},
            {"item_code": "LBL-STK-001", "qty": 1, "uom": "Piece", "rate": 4.0},
            {"item_code": "PKG-BOX-SGL", "qty": 1, "uom": "Piece", "rate": 65.0},
            {"item_code": "PKG-BUB-001", "qty": 0.15, "uom": "Roll", "rate": 25.0},
        ],
    },
    {
        "item": "CRK-DIN-BWL-16",
        "qty": 1,
        "items": [
            {"item_code": "CLY-STN-001", "qty": 0.4, "uom": "Kg", "rate": 450.0},
            {"item_code": "GLZ-WH-001", "qty": 0.1, "uom": "Kg", "rate": 850.0},
            {"item_code": "SND-PPR-001", "qty": 1, "uom": "Piece", "rate": 15.0},
            {"item_code": "SPG-WET-001", "qty": 0.1, "uom": "Piece", "rate": 80.0},
            {"item_code": "LBL-STK-001", "qty": 1, "uom": "Piece", "rate": 4.0},
            {"item_code": "PKG-BOX-SGL", "qty": 1, "uom": "Piece", "rate": 65.0},
            {"item_code": "PKG-BUB-001", "qty": 0.15, "uom": "Roll", "rate": 25.0},
        ],
    },
    {
        "item": "CRK-DRK-MUG-300",
        "qty": 1,
        "items": [
            {"item_code": "CLY-STN-001", "qty": 0.45, "uom": "Kg", "rate": 450.0},
            {"item_code": "GLZ-BL-002", "qty": 0.1, "uom": "Kg", "rate": 950.0},
            {"item_code": "SND-PPR-001", "qty": 1, "uom": "Piece", "rate": 15.0},
            {"item_code": "SPG-WET-001", "qty": 0.1, "uom": "Piece", "rate": 80.0},
            {"item_code": "LBL-STK-001", "qty": 1, "uom": "Piece", "rate": 4.0},
            {"item_code": "PKG-BOX-SGL", "qty": 1, "uom": "Piece", "rate": 65.0},
            {"item_code": "PKG-BUB-001", "qty": 0.2, "uom": "Roll", "rate": 25.0},
        ],
    },
    {
        "item": "CRK-DRK-CUP-150",
        "qty": 1,
        "items": [
            {"item_code": "CLY-POR-001", "qty": 0.25, "uom": "Kg", "rate": 1200.0},
            {"item_code": "GLZ-WH-001", "qty": 0.06, "uom": "Kg", "rate": 850.0},
            {"item_code": "SND-PPR-001", "qty": 1, "uom": "Piece", "rate": 15.0},
            {"item_code": "SPG-WET-001", "qty": 0.1, "uom": "Piece", "rate": 80.0},
            {"item_code": "LBL-STK-001", "qty": 2, "uom": "Piece", "rate": 4.0},
            {"item_code": "PKG-BOX-SGL", "qty": 1, "uom": "Piece", "rate": 65.0},
            {"item_code": "PKG-BUB-001", "qty": 0.2, "uom": "Roll", "rate": 25.0},
        ],
    },
    {
        "item": "CRK-SRV-PLT-35",
        "qty": 1,
        "items": [
            {"item_code": "CLY-STN-001", "qty": 0.9, "uom": "Kg", "rate": 450.0},
            {"item_code": "GLZ-GR-003", "qty": 0.15, "uom": "Kg", "rate": 900.0},
            {"item_code": "SND-PPR-001", "qty": 2, "uom": "Piece", "rate": 15.0},
            {"item_code": "SPG-WET-001", "qty": 0.1, "uom": "Piece", "rate": 80.0},
            {"item_code": "LBL-STK-001", "qty": 1, "uom": "Piece", "rate": 4.0},
            {"item_code": "PKG-BOX-SGL", "qty": 1, "uom": "Piece", "rate": 65.0},
            {"item_code": "PKG-BUB-001", "qty": 0.3, "uom": "Roll", "rate": 25.0},
        ],
    },
    {
        "item": "CRK-SRV-BWL-25",
        "qty": 1,
        "items": [
            {"item_code": "CLY-STN-001", "qty": 0.7, "uom": "Kg", "rate": 450.0},
            {"item_code": "GLZ-TM-004", "qty": 0.12, "uom": "Kg", "rate": 780.0},
            {"item_code": "SND-PPR-001", "qty": 2, "uom": "Piece", "rate": 15.0},
            {"item_code": "SPG-WET-001", "qty": 0.1, "uom": "Piece", "rate": 80.0},
            {"item_code": "LBL-STK-001", "qty": 1, "uom": "Piece", "rate": 4.0},
            {"item_code": "PKG-BOX-SGL", "qty": 1, "uom": "Piece", "rate": 65.0},
            {"item_code": "PKG-BUB-001", "qty": 0.25, "uom": "Roll", "rate": 25.0},
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
