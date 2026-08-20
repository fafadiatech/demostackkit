"""
Seeder: Bill of Materials for Jewellery Manufacturing.

Creates BOMs for finished jewellery items, linking them to raw materials
(precious metals and gemstones) and the Jewellery Standard Route.

Key design point — multi-level BOM:
JWL-GLD-NCK-001 is built partly from JWL-GLD-CHN-007 (the 22K Gold Chain,
itself a finished good with its own submitted BOM below) plus extra loose
gold for the pendant and clasp work, so JWL-GLD-NCK-001 explodes two levels
deep on the chain line — a chain assembled first, then finished into a
necklace, rather than melting raw gold straight into the final piece.

BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.

Note: Qty values represent grams of metal (or of the sub-assembly) per
finished piece.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Jewellery Standard Route"

# Each BOM: finished jewellery item → raw materials (metals + gems)
BOMS = [
    {
        "item": "JWL-GLD-NCK-001",  # 22K Gold Necklace Classic (~15g)
        "qty": 1,
        "items": [
            # Chain sub-assembly (carries its own BOM — see JWL-GLD-CHN-007
            # below), plus loose gold for the pendant and clasp work.
            {"item_code": "JWL-GLD-CHN-007", "qty": 10.0, "uom": "Gram", "rate": 6050.0},
            {"item_code": "RM-GLD-22K-001", "qty": 5.0, "uom": "Gram", "rate": 6000.0},
        ],
    },
    {
        "item": "JWL-GLD-NCK-002",  # 22K Gold Temple Necklace (~20g)
        "qty": 1,
        "items": [
            {"item_code": "RM-GLD-22K-001", "qty": 20.0, "uom": "Gram", "rate": 6000.0},
        ],
    },
    {
        "item": "JWL-GLD-RNG-003",  # 22K Gold Wedding Ring (~5g)
        "qty": 1,
        "items": [
            {"item_code": "RM-GLD-22K-001", "qty": 5.0, "uom": "Gram", "rate": 6000.0},
        ],
    },
    {
        "item": "JWL-GLD-RNG-004",  # 18K Gold Diamond Ring (~4g gold + 0.5ct diamond)
        "qty": 1,
        "items": [
            {"item_code": "RM-GLD-18K-002", "qty": 4.0, "uom": "Gram", "rate": 4800.0},
            {"item_code": "RM-DMD-RND-004", "qty": 0.5, "uom": "Carat", "rate": 25000.0},
        ],
    },
    {
        "item": "JWL-GLD-EAR-005",  # 22K Gold Jhumka Earrings (~8g pair)
        "qty": 1,
        "items": [
            {"item_code": "RM-GLD-22K-001", "qty": 8.0, "uom": "Gram", "rate": 6000.0},
        ],
    },
    {
        "item": "JWL-GLD-BNG-006",  # 22K Gold Bangle Set (~30g set of 4)
        "qty": 1,
        "items": [
            {"item_code": "RM-GLD-22K-001", "qty": 30.0, "uom": "Gram", "rate": 6000.0},
        ],
    },
    {
        "item": "JWL-GLD-CHN-007",  # 22K Gold Chain 18 inch (~10g)
        "qty": 1,
        "items": [
            {"item_code": "RM-GLD-22K-001", "qty": 10.0, "uom": "Gram", "rate": 6000.0},
        ],
    },
    {
        "item": "JWL-GLD-BRC-008",  # 22K Gold Bracelet (~12g)
        "qty": 1,
        "items": [
            {"item_code": "RM-GLD-22K-001", "qty": 12.0, "uom": "Gram", "rate": 6000.0},
        ],
    },
    {
        "item": "JWL-SLV-ANK-001",  # Pure Silver Anklet Pair (~20g)
        "qty": 1,
        "items": [
            {"item_code": "RM-SLV-999-003", "qty": 20.0, "uom": "Gram", "rate": 110.0},
        ],
    },
    {
        "item": "JWL-SLV-NCK-002",  # Silver Oxidised Necklace (~18g)
        "qty": 1,
        "items": [
            {"item_code": "RM-SLV-999-003", "qty": 18.0, "uom": "Gram", "rate": 110.0},
        ],
    },
    {
        "item": "JWL-DMD-EAR-002",  # Diamond Stud Earrings 0.3ct (~2g gold + 2× 0.15ct)
        "qty": 1,
        "items": [
            {"item_code": "RM-GLD-18K-002", "qty": 2.0, "uom": "Gram", "rate": 4800.0},
            {"item_code": "RM-DMD-RND-004", "qty": 0.3, "uom": "Carat", "rate": 25000.0},
        ],
    },
    {
        "item": "JWL-DMD-PDN-003",  # Diamond Pendant 0.2ct (~3g gold + 0.2ct)
        "qty": 1,
        "items": [
            {"item_code": "RM-GLD-18K-002", "qty": 3.0, "uom": "Gram", "rate": 4800.0},
            {"item_code": "RM-DMD-RND-004", "qty": 0.2, "uom": "Carat", "rate": 25000.0},
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
