"""
Seeder: Bill of Materials for Voltara EV Manufacturing.

Creates 6 BOMs — 3 electric cars (sedan, SUV, hatchback) and 3 electric bikes
(sport, city, cargo). Each BOM references the appropriate routing.

Key design point — shared components across both vehicle families:
The following items appear in BOTH car and bike BOMs, demonstrating the
shared component procurement story central to this demo:
  - MAT-DCDC         (DC-DC Converter 12V 20A)
  - MAT-CHARGEPORT   (CCS2 Charging Port Assembly)
  - MAT-CLUSTER      (Instrument Cluster Display 7 inch)
  - MAT-CONTACTOR    (High-Voltage Contactor 200A)
  - MAT-FUSE-HV      (High-Voltage Fuse 250A)
  - MAT-BRAKE-DISC   (Disc Brake Assembly)
  - MAT-BUSBAR       (Copper Busbar Strip)
  - MAT-THERMAL      (Thermal Interface Pad 100mm)

Car BOMs use the 21700-format Li-Ion cells and high-voltage BMS/controllers;
bike BOMs use the smaller 18650-format cells and low-voltage variants.
BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


BOMS = [
    # ── Electric Cars ─────────────────────────────────────────────────────────
    {
        "item": "EV-CAR-SEDAN", "qty": 1, "routing": "EV Car Manufacturing Route",
        "items": [
            # Shared components (also appear in bike BOMs)
            {"item_code": "MAT-LICELL-21700", "qty": 960,  "uom": "Nos",   "rate": 265.0},
            {"item_code": "MAT-THERMAL",      "qty": 20,   "uom": "Nos",   "rate": 250.0},
            {"item_code": "MAT-BUSBAR",       "qty": 8,    "uom": "Meter", "rate": 660.0},
            {"item_code": "MAT-DCDC",         "qty": 1,    "uom": "Nos",   "rate": 2900.0},
            {"item_code": "MAT-CHARGEPORT",   "qty": 1,    "uom": "Nos",   "rate": 5400.0},
            {"item_code": "MAT-CLUSTER",      "qty": 1,    "uom": "Nos",   "rate": 7900.0},
            {"item_code": "MAT-CONTACTOR",    "qty": 4,    "uom": "Nos",   "rate": 1850.0},
            {"item_code": "MAT-FUSE-HV",      "qty": 2,    "uom": "Nos",   "rate": 1000.0},
            {"item_code": "MAT-BRAKE-DISC",   "qty": 4,    "uom": "Nos",   "rate": 7100.0},
            # Car-specific components
            {"item_code": "MAT-BMS-HV",       "qty": 1,    "uom": "Nos",   "rate": 15000.0},
            {"item_code": "MAT-CTRL-HV",      "qty": 2,    "uom": "Nos",   "rate": 26500.0},
            {"item_code": "MAT-HARNESS-CAR",  "qty": 1,    "uom": "Set",   "rate": 18500.0},
            {"item_code": "MAT-FRAME-CAR",    "qty": 1,    "uom": "Set",   "rate": 100000.0},
            {"item_code": "MAT-BODY-CAR",     "qty": 1,    "uom": "Set",   "rate": 70000.0},
            {"item_code": "MAT-MOTOR-CAR",    "qty": 2,    "uom": "Nos",   "rate": 150000.0},
            {"item_code": "MAT-SUSP-CAR",     "qty": 1,    "uom": "Set",   "rate": 35000.0},
            {"item_code": "MAT-AXLE-REAR",    "qty": 1,    "uom": "Nos",   "rate": 31500.0},
            {"item_code": "MAT-TYRE-CAR",     "qty": 1,    "uom": "Set",   "rate": 20000.0},
            {"item_code": "MAT-SEALANT",      "qty": 3,    "uom": "Nos",   "rate": 665.0},
            {"item_code": "MAT-PKG-WRAP",     "qty": 2,    "uom": "Nos",   "rate": 1250.0},
            {"item_code": "MAT-PKG-CRATE-L",  "qty": 1,    "uom": "Nos",   "rate": 7100.0},
        ],
    },
    {
        "item": "EV-CAR-SUV", "qty": 1, "routing": "EV Car Manufacturing Route",
        "items": [
            {"item_code": "MAT-LICELL-21700", "qty": 1200, "uom": "Nos",   "rate": 265.0},
            {"item_code": "MAT-THERMAL",      "qty": 24,   "uom": "Nos",   "rate": 250.0},
            {"item_code": "MAT-BUSBAR",       "qty": 10,   "uom": "Meter", "rate": 660.0},
            {"item_code": "MAT-DCDC",         "qty": 1,    "uom": "Nos",   "rate": 2900.0},
            {"item_code": "MAT-CHARGEPORT",   "qty": 1,    "uom": "Nos",   "rate": 5400.0},
            {"item_code": "MAT-CLUSTER",      "qty": 1,    "uom": "Nos",   "rate": 7900.0},
            {"item_code": "MAT-CONTACTOR",    "qty": 4,    "uom": "Nos",   "rate": 1850.0},
            {"item_code": "MAT-FUSE-HV",      "qty": 2,    "uom": "Nos",   "rate": 1000.0},
            {"item_code": "MAT-BRAKE-DISC",   "qty": 4,    "uom": "Nos",   "rate": 7100.0},
            {"item_code": "MAT-BMS-HV",       "qty": 1,    "uom": "Nos",   "rate": 15000.0},
            {"item_code": "MAT-CTRL-HV",      "qty": 2,    "uom": "Nos",   "rate": 26500.0},
            {"item_code": "MAT-HARNESS-CAR",  "qty": 1,    "uom": "Set",   "rate": 18500.0},
            {"item_code": "MAT-FRAME-CAR",    "qty": 1,    "uom": "Set",   "rate": 100000.0},
            {"item_code": "MAT-BODY-CAR",     "qty": 1,    "uom": "Set",   "rate": 70000.0},
            {"item_code": "MAT-MOTOR-CAR",    "qty": 2,    "uom": "Nos",   "rate": 150000.0},
            {"item_code": "MAT-SUSP-CAR",     "qty": 1,    "uom": "Set",   "rate": 35000.0},
            {"item_code": "MAT-AXLE-REAR",    "qty": 1,    "uom": "Nos",   "rate": 31500.0},
            {"item_code": "MAT-TYRE-CAR",     "qty": 1,    "uom": "Set",   "rate": 20000.0},
            {"item_code": "MAT-SEALANT",      "qty": 4,    "uom": "Nos",   "rate": 665.0},
            {"item_code": "MAT-PKG-WRAP",     "qty": 2,    "uom": "Nos",   "rate": 1250.0},
            {"item_code": "MAT-PKG-CRATE-L",  "qty": 1,    "uom": "Nos",   "rate": 7100.0},
        ],
    },
    {
        "item": "EV-CAR-HATCH", "qty": 1, "routing": "EV Car Manufacturing Route",
        "items": [
            {"item_code": "MAT-LICELL-21700", "qty": 720,  "uom": "Nos",   "rate": 265.0},
            {"item_code": "MAT-THERMAL",      "qty": 18,   "uom": "Nos",   "rate": 250.0},
            {"item_code": "MAT-BUSBAR",       "qty": 6,    "uom": "Meter", "rate": 660.0},
            {"item_code": "MAT-DCDC",         "qty": 1,    "uom": "Nos",   "rate": 2900.0},
            {"item_code": "MAT-CHARGEPORT",   "qty": 1,    "uom": "Nos",   "rate": 5400.0},
            {"item_code": "MAT-CLUSTER",      "qty": 1,    "uom": "Nos",   "rate": 7900.0},
            {"item_code": "MAT-CONTACTOR",    "qty": 4,    "uom": "Nos",   "rate": 1850.0},
            {"item_code": "MAT-FUSE-HV",      "qty": 2,    "uom": "Nos",   "rate": 1000.0},
            {"item_code": "MAT-BRAKE-DISC",   "qty": 4,    "uom": "Nos",   "rate": 7100.0},
            {"item_code": "MAT-BMS-HV",       "qty": 1,    "uom": "Nos",   "rate": 15000.0},
            {"item_code": "MAT-CTRL-HV",      "qty": 1,    "uom": "Nos",   "rate": 26500.0},
            {"item_code": "MAT-HARNESS-CAR",  "qty": 1,    "uom": "Set",   "rate": 18500.0},
            {"item_code": "MAT-FRAME-CAR",    "qty": 1,    "uom": "Set",   "rate": 100000.0},
            {"item_code": "MAT-BODY-CAR",     "qty": 1,    "uom": "Set",   "rate": 70000.0},
            {"item_code": "MAT-MOTOR-CAR",    "qty": 1,    "uom": "Nos",   "rate": 150000.0},
            {"item_code": "MAT-SUSP-CAR",     "qty": 1,    "uom": "Set",   "rate": 35000.0},
            {"item_code": "MAT-AXLE-REAR",    "qty": 1,    "uom": "Nos",   "rate": 31500.0},
            {"item_code": "MAT-TYRE-CAR",     "qty": 1,    "uom": "Set",   "rate": 20000.0},
            {"item_code": "MAT-SEALANT",      "qty": 2,    "uom": "Nos",   "rate": 665.0},
            {"item_code": "MAT-PKG-WRAP",     "qty": 2,    "uom": "Nos",   "rate": 1250.0},
            {"item_code": "MAT-PKG-CRATE-L",  "qty": 1,    "uom": "Nos",   "rate": 7100.0},
        ],
    },
    # ── Electric Bikes ────────────────────────────────────────────────────────
    {
        "item": "EV-BIKE-SPORT", "qty": 1, "routing": "EV Bike Manufacturing Route",
        "items": [
            # Shared components (same items as in car BOMs above)
            {"item_code": "MAT-LICELL-18650", "qty": 120,  "uom": "Nos",   "rate": 210.0},
            {"item_code": "MAT-THERMAL",      "qty": 6,    "uom": "Nos",   "rate": 250.0},
            {"item_code": "MAT-BUSBAR",       "qty": 1,    "uom": "Meter", "rate": 660.0},
            {"item_code": "MAT-DCDC",         "qty": 1,    "uom": "Nos",   "rate": 2900.0},
            {"item_code": "MAT-CHARGEPORT",   "qty": 1,    "uom": "Nos",   "rate": 5400.0},
            {"item_code": "MAT-CLUSTER",      "qty": 1,    "uom": "Nos",   "rate": 7900.0},
            {"item_code": "MAT-CONTACTOR",    "qty": 1,    "uom": "Nos",   "rate": 1850.0},
            {"item_code": "MAT-FUSE-HV",      "qty": 1,    "uom": "Nos",   "rate": 1000.0},
            {"item_code": "MAT-BRAKE-DISC",   "qty": 2,    "uom": "Nos",   "rate": 7100.0},
            # Bike-specific components
            {"item_code": "MAT-BMS-LV",       "qty": 1,    "uom": "Nos",   "rate": 3750.0},
            {"item_code": "MAT-CTRL-LV",      "qty": 1,    "uom": "Nos",   "rate": 7900.0},
            {"item_code": "MAT-HARNESS-BIKE", "qty": 1,    "uom": "Set",   "rate": 3750.0},
            {"item_code": "MAT-FRAME-BIKE",   "qty": 1,    "uom": "Nos",   "rate": 15000.0},
            {"item_code": "MAT-MOTOR-BIKE",   "qty": 1,    "uom": "Nos",   "rate": 18500.0},
            {"item_code": "MAT-TYRE-BIKE",    "qty": 1,    "uom": "Set",   "rate": 5000.0},
            {"item_code": "MAT-HANDLE-BIKE",  "qty": 1,    "uom": "Nos",   "rate": 2900.0},
            {"item_code": "MAT-SEALANT",      "qty": 1,    "uom": "Nos",   "rate": 665.0},
            {"item_code": "MAT-PKG-WRAP",     "qty": 1,    "uom": "Nos",   "rate": 1250.0},
            {"item_code": "MAT-PKG-CRATE-M",  "qty": 1,    "uom": "Nos",   "rate": 2900.0},
        ],
    },
    {
        "item": "EV-BIKE-CITY", "qty": 1, "routing": "EV Bike Manufacturing Route",
        "items": [
            {"item_code": "MAT-LICELL-18650", "qty": 80,   "uom": "Nos",   "rate": 210.0},
            {"item_code": "MAT-THERMAL",      "qty": 4,    "uom": "Nos",   "rate": 250.0},
            {"item_code": "MAT-BUSBAR",       "qty": 0.8,  "uom": "Meter", "rate": 660.0},
            {"item_code": "MAT-DCDC",         "qty": 1,    "uom": "Nos",   "rate": 2900.0},
            {"item_code": "MAT-CHARGEPORT",   "qty": 1,    "uom": "Nos",   "rate": 5400.0},
            {"item_code": "MAT-CLUSTER",      "qty": 1,    "uom": "Nos",   "rate": 7900.0},
            {"item_code": "MAT-CONTACTOR",    "qty": 1,    "uom": "Nos",   "rate": 1850.0},
            {"item_code": "MAT-FUSE-HV",      "qty": 1,    "uom": "Nos",   "rate": 1000.0},
            {"item_code": "MAT-BRAKE-DISC",   "qty": 2,    "uom": "Nos",   "rate": 7100.0},
            {"item_code": "MAT-BMS-LV",       "qty": 1,    "uom": "Nos",   "rate": 3750.0},
            {"item_code": "MAT-CTRL-LV",      "qty": 1,    "uom": "Nos",   "rate": 7900.0},
            {"item_code": "MAT-HARNESS-BIKE", "qty": 1,    "uom": "Set",   "rate": 3750.0},
            {"item_code": "MAT-FRAME-BIKE",   "qty": 1,    "uom": "Nos",   "rate": 15000.0},
            {"item_code": "MAT-MOTOR-BIKE",   "qty": 1,    "uom": "Nos",   "rate": 18500.0},
            {"item_code": "MAT-TYRE-BIKE",    "qty": 1,    "uom": "Set",   "rate": 5000.0},
            {"item_code": "MAT-HANDLE-BIKE",  "qty": 1,    "uom": "Nos",   "rate": 2900.0},
            {"item_code": "MAT-SEALANT",      "qty": 1,    "uom": "Nos",   "rate": 665.0},
            {"item_code": "MAT-PKG-WRAP",     "qty": 1,    "uom": "Nos",   "rate": 1250.0},
            {"item_code": "MAT-PKG-CRATE-M",  "qty": 1,    "uom": "Nos",   "rate": 2900.0},
        ],
    },
    {
        "item": "EV-BIKE-CARGO", "qty": 1, "routing": "EV Bike Manufacturing Route",
        "items": [
            {"item_code": "MAT-LICELL-18650", "qty": 160,  "uom": "Nos",   "rate": 210.0},
            {"item_code": "MAT-THERMAL",      "qty": 8,    "uom": "Nos",   "rate": 250.0},
            {"item_code": "MAT-BUSBAR",       "qty": 1.5,  "uom": "Meter", "rate": 660.0},
            {"item_code": "MAT-DCDC",         "qty": 1,    "uom": "Nos",   "rate": 2900.0},
            {"item_code": "MAT-CHARGEPORT",   "qty": 1,    "uom": "Nos",   "rate": 5400.0},
            {"item_code": "MAT-CLUSTER",      "qty": 1,    "uom": "Nos",   "rate": 7900.0},
            {"item_code": "MAT-CONTACTOR",    "qty": 1,    "uom": "Nos",   "rate": 1850.0},
            {"item_code": "MAT-FUSE-HV",      "qty": 1,    "uom": "Nos",   "rate": 1000.0},
            {"item_code": "MAT-BRAKE-DISC",   "qty": 2,    "uom": "Nos",   "rate": 7100.0},
            {"item_code": "MAT-BMS-LV",       "qty": 1,    "uom": "Nos",   "rate": 3750.0},
            {"item_code": "MAT-CTRL-LV",      "qty": 1,    "uom": "Nos",   "rate": 7900.0},
            {"item_code": "MAT-HARNESS-BIKE", "qty": 1,    "uom": "Set",   "rate": 3750.0},
            {"item_code": "MAT-FRAME-BIKE",   "qty": 1,    "uom": "Nos",   "rate": 15000.0},
            {"item_code": "MAT-MOTOR-BIKE",   "qty": 1,    "uom": "Nos",   "rate": 18500.0},
            {"item_code": "MAT-TYRE-BIKE",    "qty": 1,    "uom": "Set",   "rate": 5000.0},
            {"item_code": "MAT-HANDLE-BIKE",  "qty": 1,    "uom": "Nos",   "rate": 2900.0},
            {"item_code": "MAT-SEALANT",      "qty": 1,    "uom": "Nos",   "rate": 665.0},
            {"item_code": "MAT-PKG-WRAP",     "qty": 1,    "uom": "Nos",   "rate": 1250.0},
            {"item_code": "MAT-PKG-CRATE-M",  "qty": 1,    "uom": "Nos",   "rate": 2900.0},
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
