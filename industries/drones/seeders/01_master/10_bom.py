"""
Seeder: Bill of Materials for Drones Manufacturing.

Creates BOMs for all finished drone models, linking them to components
and the Drone Standard Route.

Key design point — multi-level BOM:
FCS-PIX-001 (the Pixhawk flight controller, consumed by DRN-AGR-5L,
DRN-SRV-4K and DRN-DLV-P5) carries its own BOM of a bare PCB, an IMU sensor
and a GPS module, so each of those finished drones explodes two levels deep
on the flight-controller line.

BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

ROUTING_NAME = "Drone Standard Route"

# Each BOM: finished good item → list of {item_code, qty, uom, rate}
BOMS = [
    # ── Sub-assembly (consumed by the finished drones below) ────────────────────
    {
        "item": "FCS-PIX-001",  # Flight Controller Pixhawk 6C
        "qty": 1,
        "items": [
            {"item_code": "PCB-FC-BARE-001", "qty": 1, "uom": "Nos", "rate": 2500.0},
            {"item_code": "SNS-IMU-001", "qty": 1, "uom": "Nos", "rate": 3200.0},
            {"item_code": "GPS-M8N-001", "qty": 1, "uom": "Nos", "rate": 1800.0},
        ],
    },
    {
        "item": "DRN-AGR-5L",
        "qty": 1,
        "items": [
            {"item_code": "FRM-CF-650", "qty": 1, "uom": "Nos", "rate": 4500.0},
            {"item_code": "MTR-BLDC-2212", "qty": 6, "uom": "Nos", "rate": 850.0},
            {"item_code": "ESC-30A-001", "qty": 6, "uom": "Nos", "rate": 650.0},
            {"item_code": "BAT-LIPO-4S", "qty": 2, "uom": "Nos", "rate": 3500.0},
            {"item_code": "FCS-PIX-001", "qty": 1, "uom": "Nos", "rate": 8500.0},
            {"item_code": "PRO-CF-15IN", "qty": 3, "uom": "Nos", "rate": 850.0},
            {"item_code": "GPS-M8N-001", "qty": 1, "uom": "Nos", "rate": 1800.0},
            {"item_code": "RCV-868-001", "qty": 1, "uom": "Nos", "rate": 950.0},
            {"item_code": "SPR-TANK-5L", "qty": 1, "uom": "Nos", "rate": 1200.0},
            {"item_code": "SPR-PUMP-001", "qty": 1, "uom": "Nos", "rate": 800.0},
            {"item_code": "LDG-GEAR-001", "qty": 1, "uom": "Nos", "rate": 1500.0},
            {"item_code": "SCW-M3-SS", "qty": 2, "uom": "Set", "rate": 120.0},
            {"item_code": "ADH-EP2-001", "qty": 2, "uom": "Piece", "rate": 95.0},
            {"item_code": "LBL-QR-001", "qty": 1, "uom": "Piece", "rate": 5.0},
            {"item_code": "PKG-BOX-DRN", "qty": 1, "uom": "Piece", "rate": 350.0},
            {"item_code": "PKG-FOM-001", "qty": 1, "uom": "Piece", "rate": 120.0},
        ],
    },
    {
        "item": "DRN-SRV-4K",
        "qty": 1,
        "items": [
            {"item_code": "FRM-CF-450", "qty": 1, "uom": "Nos", "rate": 2200.0},
            {"item_code": "MTR-BLDC-2212", "qty": 4, "uom": "Nos", "rate": 850.0},
            {"item_code": "ESC-30A-001", "qty": 4, "uom": "Nos", "rate": 650.0},
            {"item_code": "BAT-LIPO-4S", "qty": 1, "uom": "Nos", "rate": 3500.0},
            {"item_code": "FCS-PIX-001", "qty": 1, "uom": "Nos", "rate": 8500.0},
            {"item_code": "PRO-CF-10IN", "qty": 2, "uom": "Nos", "rate": 350.0},
            {"item_code": "GPS-M8N-001", "qty": 1, "uom": "Nos", "rate": 1800.0},
            {"item_code": "RCV-868-001", "qty": 1, "uom": "Nos", "rate": 950.0},
            {"item_code": "CAM-4K-001", "qty": 1, "uom": "Nos", "rate": 12000.0},
            {"item_code": "LDG-GEAR-001", "qty": 1, "uom": "Nos", "rate": 1500.0},
            {"item_code": "SCW-M3-SS", "qty": 1, "uom": "Set", "rate": 120.0},
            {"item_code": "ADH-EP2-001", "qty": 1, "uom": "Piece", "rate": 95.0},
            {"item_code": "LBL-QR-001", "qty": 1, "uom": "Piece", "rate": 5.0},
            {"item_code": "PKG-BOX-DRN", "qty": 1, "uom": "Piece", "rate": 350.0},
            {"item_code": "PKG-FOM-001", "qty": 1, "uom": "Piece", "rate": 120.0},
        ],
    },
    {
        "item": "DRN-DLV-P5",
        "qty": 1,
        "items": [
            {"item_code": "FRM-CF-650", "qty": 1, "uom": "Nos", "rate": 4500.0},
            {"item_code": "MTR-BLDC-2212", "qty": 8, "uom": "Nos", "rate": 850.0},
            {"item_code": "ESC-30A-001", "qty": 8, "uom": "Nos", "rate": 650.0},
            {"item_code": "BAT-LIPO-4S", "qty": 3, "uom": "Nos", "rate": 3500.0},
            {"item_code": "FCS-PIX-001", "qty": 1, "uom": "Nos", "rate": 8500.0},
            {"item_code": "PRO-CF-15IN", "qty": 4, "uom": "Nos", "rate": 850.0},
            {"item_code": "GPS-M8N-001", "qty": 2, "uom": "Nos", "rate": 1800.0},
            {"item_code": "RCV-868-001", "qty": 1, "uom": "Nos", "rate": 950.0},
            {"item_code": "CAM-4K-001", "qty": 1, "uom": "Nos", "rate": 12000.0},
            {"item_code": "LDG-GEAR-001", "qty": 1, "uom": "Nos", "rate": 1500.0},
            {"item_code": "SCW-M3-SS", "qty": 3, "uom": "Set", "rate": 120.0},
            {"item_code": "ADH-EP2-001", "qty": 2, "uom": "Piece", "rate": 95.0},
            {"item_code": "LBL-QR-001", "qty": 1, "uom": "Piece", "rate": 5.0},
            {"item_code": "PKG-BOX-DRN", "qty": 1, "uom": "Piece", "rate": 350.0},
            {"item_code": "PKG-FOM-001", "qty": 2, "uom": "Piece", "rate": 120.0},
        ],
    },
    {
        "item": "DRN-RCG-FPV",
        "qty": 1,
        "items": [
            {"item_code": "FRM-CF-450", "qty": 1, "uom": "Nos", "rate": 2200.0},
            {"item_code": "MTR-BLDC-2212", "qty": 4, "uom": "Nos", "rate": 850.0},
            {"item_code": "ESC-30A-001", "qty": 4, "uom": "Nos", "rate": 650.0},
            {"item_code": "BAT-LIPO-4S", "qty": 1, "uom": "Nos", "rate": 3500.0},
            {"item_code": "FCS-F4-001", "qty": 1, "uom": "Nos", "rate": 1200.0},
            {"item_code": "PRO-CF-10IN", "qty": 2, "uom": "Nos", "rate": 350.0},
            {"item_code": "RCV-868-001", "qty": 1, "uom": "Nos", "rate": 950.0},
            {"item_code": "SCW-M3-SS", "qty": 1, "uom": "Set", "rate": 120.0},
            {"item_code": "THR-SLD-001", "qty": 1, "uom": "Roll", "rate": 180.0},
            {"item_code": "LBL-QR-001", "qty": 1, "uom": "Piece", "rate": 5.0},
            {"item_code": "PKG-BOX-DRN", "qty": 1, "uom": "Piece", "rate": 350.0},
            {"item_code": "PKG-FOM-001", "qty": 1, "uom": "Piece", "rate": 120.0},
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
