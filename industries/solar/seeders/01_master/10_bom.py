"""
Seeder: Bill of Materials for Solar System Assembly.

Creates BOMs for assembled solar system products, linking them to component
items (panels, inverters, mounting, cabling) and the Solar System Assembly Route.
BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Solar System Assembly Route"

# Each BOM: assembled solar system → component items
BOMS = [
    {
        "item": "SLR-SYS-RTF-5KW",  # 5KW Rooftop Solar System
        "qty": 1,
        "items": [
            {
                "item_code": "SLR-PNL-MON-001",
                "qty": 13,
                "uom": "Nos",
                "rate": 12500.0,
            },  # 13× 400W = 5.2kW
            {
                "item_code": "SLR-INV-HYB-003",
                "qty": 1,
                "uom": "Nos",
                "rate": 38000.0,
            },  # Hybrid 5KW inverter
            {
                "item_code": "SLR-MNT-RTF-001",
                "qty": 4,
                "uom": "Nos",
                "rate": 1200.0,
            },  # Mounting rails
            {"item_code": "SLR-BOS-CAB-001", "qty": 50, "uom": "Meter", "rate": 38.0},  # DC cable
            {"item_code": "SLR-BOS-CAB-002", "qty": 10, "uom": "Meter", "rate": 52.0},  # AC cable
            {"item_code": "SLR-BOS-MCB-003", "qty": 2, "uom": "Nos", "rate": 1850.0},  # DC MCB
            {
                "item_code": "SLR-BOS-SPD-004",
                "qty": 1,
                "uom": "Nos",
                "rate": 3200.0,
            },  # Surge protection
        ],
    },
    {
        "item": "SLR-SYS-RTF-10KW",  # 10KW Rooftop Solar System
        "qty": 1,
        "items": [
            {
                "item_code": "SLR-PNL-MON-001",
                "qty": 25,
                "uom": "Nos",
                "rate": 12500.0,
            },  # 25× 400W = 10kW
            {
                "item_code": "SLR-INV-STR-001",
                "qty": 1,
                "uom": "Nos",
                "rate": 48000.0,
            },  # String 10KW inverter
            {
                "item_code": "SLR-MNT-RTF-001",
                "qty": 8,
                "uom": "Nos",
                "rate": 1200.0,
            },  # Mounting rails
            {"item_code": "SLR-BOS-CAB-001", "qty": 100, "uom": "Meter", "rate": 38.0},  # DC cable
            {"item_code": "SLR-BOS-CAB-002", "qty": 20, "uom": "Meter", "rate": 52.0},  # AC cable
            {"item_code": "SLR-BOS-MCB-003", "qty": 4, "uom": "Nos", "rate": 1850.0},  # DC MCB
            {
                "item_code": "SLR-BOS-SPD-004",
                "qty": 2,
                "uom": "Nos",
                "rate": 3200.0,
            },  # Surge protection
        ],
    },
    {
        "item": "SLR-SYS-GRD-25KW",  # 25KW Ground Mount Solar System
        "qty": 1,
        "items": [
            {
                "item_code": "SLR-PNL-BFX-004",
                "qty": 46,
                "uom": "Nos",
                "rate": 19500.0,
            },  # 46× 550W bifacial = ~25kW
            {
                "item_code": "SLR-INV-STR-002",
                "qty": 1,
                "uom": "Nos",
                "rate": 95000.0,
            },  # String 25KW inverter
            {
                "item_code": "SLR-MNT-GRD-002",
                "qty": 1,
                "uom": "Nos",
                "rate": 28000.0,
            },  # Ground mount structure
            {"item_code": "SLR-BOS-CAB-001", "qty": 250, "uom": "Meter", "rate": 38.0},  # DC cable
            {"item_code": "SLR-BOS-CAB-002", "qty": 50, "uom": "Meter", "rate": 52.0},  # AC cable
            {"item_code": "SLR-BOS-MCB-003", "qty": 8, "uom": "Nos", "rate": 1850.0},  # DC MCB
            {
                "item_code": "SLR-BOS-SPD-004",
                "qty": 4,
                "uom": "Nos",
                "rate": 3200.0,
            },  # Surge protection
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
