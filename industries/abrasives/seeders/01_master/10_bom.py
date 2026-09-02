"""
Seeder: Bill of Materials for Alpha Abrasives.

Creates 13 finished-good BOMs for the in-house manufactured line only —
6 bonded abrasive wheels (3 grinding wheel diameters/grits on an aluminium
oxide + vitrified/resin bond, 3 cutting wheel diameters/grits on a silicon
carbide + resin bond with fibreglass reinforcement), 4 abrasive/flap discs,
and 3 coated abrasive belts. Every BOM references the shared
"Abrasive Product Manufacturing Route".

The traded line (polishing machines, power/pneumatic tools, polishing
consumables) is deliberately excluded — it is bought and resold with no
BOM at all, matching a pure spare-parts-catalogue trading model.

BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

_ROUTE = "Abrasive Product Manufacturing Route"

BOMS = [
    # ── Grinding Wheels (aluminium oxide grain, vitrified/resin bond) ──────────
    {
        "item": "ABR-WH-01",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-01", "qty": 0.35, "uom": "Kg", "rate": 145.0},
            {"item_code": "ABR-RM-03", "qty": 0.05, "uom": "Kg", "rate": 210.0},
            {"item_code": "ABR-RM-09", "qty": 0.02, "uom": "Kg", "rate": 95.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
            {"item_code": "SA-WHEELHUB-01", "qty": 1, "uom": "Nos", "rate": 12.0},
        ],
    },
    {
        "item": "ABR-WH-02",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-01", "qty": 0.90, "uom": "Kg", "rate": 145.0},
            {"item_code": "ABR-RM-06", "qty": 0.15, "uom": "Kg", "rate": 60.0},
            {"item_code": "ABR-RM-09", "qty": 0.05, "uom": "Kg", "rate": 95.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        "item": "ABR-WH-03",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-01", "qty": 2.40, "uom": "Kg", "rate": 145.0},
            {"item_code": "ABR-RM-06", "qty": 0.40, "uom": "Kg", "rate": 60.0},
            {"item_code": "ABR-RM-09", "qty": 0.12, "uom": "Kg", "rate": 95.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        # Alternate BOM for ABR-WH-01 — resin bond formula instead of
        # vitrified bond (matches the bond system used on ABR-WH-02/03).
        "item": "ABR-WH-01",
        "qty": 1,
        "routing": _ROUTE,
        "is_default": False,
        "items": [
            {"item_code": "ABR-RM-01", "qty": 0.35, "uom": "Kg", "rate": 145.0},
            {"item_code": "ABR-RM-06", "qty": 0.06, "uom": "Kg", "rate": 60.0},
            {"item_code": "ABR-RM-09", "qty": 0.02, "uom": "Kg", "rate": 95.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    # ── Cutting Wheels (silicon carbide grain, resin bond, fibreglass mesh) ────
    {
        "item": "ABR-WH-04",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-02", "qty": 0.06, "uom": "Kg", "rate": 175.0},
            {"item_code": "ABR-RM-03", "qty": 0.015, "uom": "Kg", "rate": 210.0},
            {"item_code": "ABR-RM-05", "qty": 0.30, "uom": "Meter", "rate": 38.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        "item": "ABR-WH-05",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-02", "qty": 0.08, "uom": "Kg", "rate": 175.0},
            {"item_code": "ABR-RM-03", "qty": 0.02, "uom": "Kg", "rate": 210.0},
            {"item_code": "ABR-RM-05", "qty": 0.35, "uom": "Meter", "rate": 38.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        "item": "ABR-WH-06",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-02", "qty": 0.55, "uom": "Kg", "rate": 175.0},
            {"item_code": "ABR-RM-03", "qty": 0.12, "uom": "Kg", "rate": 210.0},
            {"item_code": "ABR-RM-05", "qty": 0.90, "uom": "Meter", "rate": 38.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    # ── Abrasive Discs & Flap Discs ─────────────────────────────────────────────
    {
        "item": "ABR-DC-01",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-01", "qty": 0.045, "uom": "Kg", "rate": 145.0},
            {"item_code": "ABR-RM-04", "qty": 0.02, "uom": "Kg", "rate": 260.0},
            {"item_code": "ABR-RM-05", "qty": 0.10, "uom": "Meter", "rate": 38.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        "item": "ABR-DC-02",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-01", "qty": 0.055, "uom": "Kg", "rate": 145.0},
            {"item_code": "ABR-RM-04", "qty": 0.025, "uom": "Kg", "rate": 260.0},
            {"item_code": "ABR-RM-05", "qty": 0.12, "uom": "Meter", "rate": 38.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        "item": "ABR-DC-03",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-01", "qty": 0.04, "uom": "Kg", "rate": 145.0},
            {"item_code": "ABR-RM-08", "qty": 0.01, "uom": "Litre", "rate": 320.0},
            {"item_code": "ABR-RM-07", "qty": 0.08, "uom": "Meter", "rate": 85.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        "item": "ABR-DC-04",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-01", "qty": 0.015, "uom": "Kg", "rate": 145.0},
            {"item_code": "ABR-RM-08", "qty": 0.005, "uom": "Litre", "rate": 320.0},
            {"item_code": "ABR-RM-07", "qty": 0.03, "uom": "Meter", "rate": 85.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    # ── Coated Abrasive Belts (backing cloth + grain + adhesive lamination) ────
    {
        "item": "ABR-BT-01",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-02", "qty": 0.12, "uom": "Kg", "rate": 175.0},
            {"item_code": "ABR-RM-07", "qty": 0.92, "uom": "Meter", "rate": 85.0},
            {"item_code": "ABR-RM-08", "qty": 0.05, "uom": "Litre", "rate": 320.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
            {"item_code": "SA-BELTMOD-01", "qty": 1, "uom": "Nos", "rate": 6.5},
        ],
    },
    {
        "item": "ABR-BT-02",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-02", "qty": 0.22, "uom": "Kg", "rate": 175.0},
            {"item_code": "ABR-RM-07", "qty": 1.22, "uom": "Meter", "rate": 85.0},
            {"item_code": "ABR-RM-08", "qty": 0.08, "uom": "Litre", "rate": 320.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
    {
        "item": "ABR-BT-03",
        "qty": 1,
        "routing": _ROUTE,
        "items": [
            {"item_code": "ABR-RM-02", "qty": 0.05, "uom": "Kg", "rate": 175.0},
            {"item_code": "ABR-RM-07", "qty": 0.35, "uom": "Meter", "rate": 85.0},
            {"item_code": "ABR-RM-08", "qty": 0.02, "uom": "Litre", "rate": 320.0},
            {"item_code": "ABR-PK-01", "qty": 1, "uom": "Nos", "rate": 18.0},
        ],
    },
]


class BOMSeeder(BaseMasterSeeder):
    label = "Bill of Materials"
    priority = 100

    def run(self) -> None:
        company_name = self.ctx.industry_config.company.name
        boms_json = json.dumps(BOMS)
        script = f"""
import json
from collections import defaultdict

company_name = '{company_name}'
boms = json.loads('''{boms_json}''')
created = skipped = errors = 0

existing_counts = {{}}
seen_counts = defaultdict(int)

for b in boms:
    item = b['item']
    if item not in existing_counts:
        existing_counts[item] = frappe.db.count('BOM', {{'item': item, 'docstatus': 1}})
    idx = seen_counts[item]
    seen_counts[item] += 1
    if idx < existing_counts[item]:
        skipped += 1
        continue
    try:
        doc = frappe.get_doc({{
            'doctype': 'BOM',
            'company': company_name,
            'item': item,
            'quantity': b.get('qty', 1),
            'with_operations': 1,
            'routing': b['routing'],
            'is_active': 1,
            'is_default': b.get('is_default', True),
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
