"""
Seeder: Bill of Materials for Ingredient Manufacturing.

Creates BOMs for finished ingredient products, linking them to raw
botanicals/chemicals and the Ingredient Manufacturing Standard Route.

Key design point — multi-level BOM:
ING-INT-CUR-014 and ING-INT-HYD-015 (both Intermediates, consumed by
ING-FIN-CUR-026 and ING-FIN-COL-029 respectively) each carry their own BOM
synthesised from raw botanicals/chemicals, so those finished products
explode two levels deep on the intermediate line.

BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Ingredient Manufacturing Standard Route"

# Each BOM: finished product → list of {item_code, qty, uom, rate}
BOMS = [
    # ── Intermediates (consumed by the finished products below) ─────────────────
    {
        "item": "ING-INT-CUR-014",  # Standardized Curcuminoid Concentrate (per 10 Kg batch)
        "qty": 10,
        "items": [
            {"item_code": "ING-RAW-TUR-001", "qty": 60.0, "uom": "Kg", "rate": 220.0},
            {"item_code": "ING-RAW-ETL-007", "qty": 25.0, "uom": "Litre", "rate": 145.0},
        ],
    },
    {
        "item": "ING-INT-HYD-015",  # Hydrolyzed Collagen Concentrate (per 10 Kg batch)
        "qty": 10,
        "items": [
            {"item_code": "ING-RAW-COL-011", "qty": 15.0, "uom": "Kg", "rate": 620.0},
            {"item_code": "ING-RAW-CIT-008", "qty": 2.0, "uom": "Kg", "rate": 88.0},
        ],
    },
    # ── Flavours, Colours & Functional Additives ─────────────────────────────────
    {
        "item": "ING-FIN-FLV-020",  # Natural Vanilla Flavour Compound (per 50 Kg)
        "qty": 50,
        "items": [
            {"item_code": "ING-RAW-VNC-012", "qty": 8.0, "uom": "Kg", "rate": 780.0},
            {"item_code": "ING-RAW-ETL-007", "qty": 20.0, "uom": "Litre", "rate": 145.0},
            {"item_code": "ING-RAW-MAL-009", "qty": 15.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "PKG-JAR-005-018", "qty": 100, "uom": "Nos", "rate": 22.0},
        ],
    },
    {
        "item": "ING-FIN-FLV-021",  # Citrus Flavour Concentrate (per 50 Kg)
        "qty": 50,
        "items": [
            {"item_code": "ING-RAW-CIT-008", "qty": 12.0, "uom": "Kg", "rate": 88.0},
            {"item_code": "ING-RAW-ETL-007", "qty": 18.0, "uom": "Litre", "rate": 145.0},
            {"item_code": "PKG-BTL-001-019", "qty": 80, "uom": "Nos", "rate": 45.0},
        ],
    },
    {
        "item": "ING-FIN-CLR-022",  # Natural Turmeric Colour Extract (per 50 Kg)
        "qty": 50,
        "items": [
            {"item_code": "ING-RAW-TUR-001", "qty": 80.0, "uom": "Kg", "rate": 220.0},
            {"item_code": "ING-RAW-ETL-007", "qty": 25.0, "uom": "Litre", "rate": 145.0},
            {"item_code": "PKG-DRM-025-016", "qty": 2, "uom": "Nos", "rate": 320.0},
        ],
    },
    {
        "item": "ING-FIN-CLR-023",  # Marigold Lutein Colour Extract (per 50 Kg)
        "qty": 50,
        "items": [
            {"item_code": "ING-RAW-MRG-006", "qty": 70.0, "uom": "Kg", "rate": 190.0},
            {"item_code": "ING-RAW-ETL-007", "qty": 20.0, "uom": "Litre", "rate": 145.0},
            {"item_code": "PKG-DRM-025-016", "qty": 2, "uom": "Nos", "rate": 320.0},
        ],
    },
    {
        "item": "ING-FIN-STB-024",  # Hydrocolloid Stabiliser Blend (per 50 Kg)
        "qty": 50,
        "items": [
            {"item_code": "ING-RAW-GUM-010", "qty": 35.0, "uom": "Kg", "rate": 480.0},
            {"item_code": "ING-RAW-MAL-009", "qty": 20.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "PKG-BAG-001-017", "qty": 50, "uom": "Nos", "rate": 12.0},
        ],
    },
    {
        "item": "ING-FIN-SWT-025",  # High Intensity Sweetener Blend (per 50 Kg)
        "qty": 50,
        "items": [
            {"item_code": "ING-RAW-MAL-009", "qty": 40.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "ING-RAW-CIT-008", "qty": 5.0, "uom": "Kg", "rate": 88.0},
            {"item_code": "PKG-BAG-001-017", "qty": 50, "uom": "Nos", "rate": 12.0},
        ],
    },
    # ── Nutraceutical & Botanical Actives ────────────────────────────────────────
    {
        "item": "ING-FIN-CUR-026",  # Curcumin Extract 95% (per 10 Kg)
        "qty": 10,
        "items": [
            {"item_code": "ING-INT-CUR-014", "qty": 12.0, "uom": "Kg", "rate": 1200.0},
            {"item_code": "ING-RAW-ETL-007", "qty": 5.0, "uom": "Litre", "rate": 145.0},
            {"item_code": "PKG-JAR-005-018", "qty": 20, "uom": "Nos", "rate": 22.0},
        ],
    },
    {
        "item": "ING-FIN-ASH-027",  # Ashwagandha Extract 5% Withanolides (per 10 Kg)
        "qty": 10,
        "items": [
            {"item_code": "ING-RAW-ASH-003", "qty": 60.0, "uom": "Kg", "rate": 340.0},
            {"item_code": "ING-RAW-ETL-007", "qty": 15.0, "uom": "Litre", "rate": 145.0},
            {"item_code": "PKG-JAR-005-018", "qty": 20, "uom": "Nos", "rate": 22.0},
        ],
    },
    {
        "item": "ING-FIN-GRT-028",  # Green Tea Extract 50% EGCG (per 10 Kg)
        "qty": 10,
        "items": [
            {"item_code": "ING-RAW-GRT-004", "qty": 55.0, "uom": "Kg", "rate": 410.0},
            {"item_code": "ING-RAW-ETL-007", "qty": 18.0, "uom": "Litre", "rate": 145.0},
            {"item_code": "PKG-JAR-005-018", "qty": 20, "uom": "Nos", "rate": 22.0},
        ],
    },
    {
        "item": "ING-FIN-COL-029",  # Hydrolyzed Collagen Peptide Powder (per 10 Kg)
        "qty": 10,
        "items": [
            {"item_code": "ING-INT-HYD-015", "qty": 11.0, "uom": "Kg", "rate": 1450.0},
            {"item_code": "ING-RAW-MAL-009", "qty": 3.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "PKG-DRM-025-016", "qty": 1, "uom": "Nos", "rate": 320.0},
        ],
    },
    {
        "item": "ING-FIN-HIB-030",  # Hibiscus Extract Standardized (per 10 Kg)
        "qty": 10,
        "items": [
            {"item_code": "ING-RAW-HIB-005", "qty": 50.0, "uom": "Kg", "rate": 260.0},
            {"item_code": "ING-RAW-ETL-007", "qty": 15.0, "uom": "Litre", "rate": 145.0},
            {"item_code": "PKG-JAR-005-018", "qty": 20, "uom": "Nos", "rate": 22.0},
        ],
    },
    {
        "item": "ING-FIN-PRO-031",  # Plant Protein Concentrate 80% (per 10 Kg)
        "qty": 10,
        "items": [
            {"item_code": "ING-RAW-PEA-013", "qty": 15.0, "uom": "Kg", "rate": 210.0},
            {"item_code": "ING-RAW-MAL-009", "qty": 3.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "PKG-DRM-025-016", "qty": 1, "uom": "Nos", "rate": 320.0},
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
