"""
Seeder: Bill of Materials for Chemical Manufacturing.

Creates BOMs for finished chemical products, linking them to raw materials
and the Chemical Standard Route. BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Chemical Standard Route"

# Each BOM: finished product → list of {item_code, qty, uom, rate}
BOMS = [
    {
        "item": "CHM-FIN-CLN-001",  # Industrial Cleaner Pro (per Litre)
        "qty": 100,
        "items": [
            {"item_code": "CHM-RAW-HCL-002", "qty": 15.0, "uom": "Kg", "rate": 22.0},
            {"item_code": "CHM-RAW-NaOH-003", "qty": 8.0, "uom": "Kg", "rate": 38.0},
            {"item_code": "CHM-RAW-IPA-006", "qty": 5.0, "uom": "Litre", "rate": 125.0},
            {"item_code": "PKG-BTL-001-004", "qty": 100, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        "item": "CHM-FIN-CLN-002",  # Alkaline Degreaser 5X (per Litre)
        "qty": 100,
        "items": [
            {"item_code": "CHM-RAW-NaOH-003", "qty": 20.0, "uom": "Kg", "rate": 38.0},
            {"item_code": "CHM-INT-DMS-008", "qty": 10.0, "uom": "Kg", "rate": 320.0},
            {"item_code": "PKG-BTL-001-004", "qty": 100, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        "item": "CHM-FIN-TRT-003",  # Rust Inhibitor Concentrate (per Litre)
        "qty": 50,
        "items": [
            {"item_code": "CHM-INT-ACT-007", "qty": 12.0, "uom": "Kg", "rate": 180.0},
            {"item_code": "CHM-RAW-IPA-006", "qty": 20.0, "uom": "Litre", "rate": 125.0},
            {"item_code": "PKG-CAN-020-002", "qty": 3, "uom": "Nos", "rate": 185.0},
        ],
    },
    {
        "item": "CHM-FIN-TRT-004",  # Water Treatment Chemical (per Kg)
        "qty": 500,
        "items": [
            {"item_code": "CHM-RAW-SUL-001", "qty": 100.0, "uom": "Kg", "rate": 45.0},
            {"item_code": "CHM-RAW-NaOH-003", "qty": 80.0, "uom": "Kg", "rate": 38.0},
            {"item_code": "PKG-BAG-025-003", "qty": 20, "uom": "Nos", "rate": 28.0},
        ],
    },
    {
        "item": "CHM-FIN-PNT-006",  # Paint Thinner Premium (per Litre)
        "qty": 100,
        "items": [
            {"item_code": "CHM-RAW-TOL-004", "qty": 60.0, "uom": "Litre", "rate": 95.0},
            {"item_code": "CHM-RAW-ACE-005", "qty": 30.0, "uom": "Litre", "rate": 75.0},
            {"item_code": "PKG-CAN-020-002", "qty": 5, "uom": "Nos", "rate": 185.0},
        ],
    },
    {
        "item": "CHM-FIN-PHR-008",  # Pharma Grade Ethanol 96% (per Litre)
        "qty": 100,
        "items": [
            {"item_code": "CHM-RAW-IPA-006", "qty": 110.0, "uom": "Litre", "rate": 125.0},
            {"item_code": "PKG-BTL-001-004", "qty": 100, "uom": "Nos", "rate": 18.0},
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
    if frappe.db.exists('BOM', {{'item': b['item'], 'docstatus': 1}}):
        skipped += 1
        continue
    try:
        doc = frappe.get_doc({{
            'doctype': 'BOM',
            'company': company_name,
            'item': b['item'],
            'quantity': b.get('qty', 1),
            'with_operations': 1,
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
