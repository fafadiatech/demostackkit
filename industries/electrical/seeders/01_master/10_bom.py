"""
Seeder: Bill of Materials for PowerTech Electrical Manufacturing.

Creates 7 finished-good BOMs — 4 transformers (100kVA, 250kVA, 500kVA, 1MVA)
and 3 switchgear panels (HT 11kV, LT 415V, MCC 415V) — plus 4 sub-assembly
BOMs (wound HV/LV coils, core, switchgear busbar assembly). Each BOM
references the appropriate routing.

Key design point — multi-level BOM:
EFG-TRANS-100 is built from ESA-COIL-HV, ESA-COIL-LV and ESA-CORE rather
than raw copper wire/CRGO steel/insulation paper directly, and EFG-SWGR-HT
is built from ESA-SWGR-BUS. Those four sub-assembly items each carry their
own submitted BOM (created first, below), so a BOM report for EFG-TRANS-100
or EFG-SWGR-HT explodes two levels deep — matching how a transformer winding
shop actually winds coils and stacks cores as intermediate assemblies before
final tanking, rather than treating raw wire as a single-step input.

Key design point — shared raw materials across product families:
The following items appear in BOTH transformer and switchgear BOMs,
demonstrating the shared procurement story central to this demo:
  - ERM-MS-SHEET    (MS Steel Sheet — used for both tanks and panel enclosures)
  - EPKG-WRAP       (Stretch Wrap Film — common packaging across all products)

Transformer BOMs use wound coil/core sub-assemblies, transformer oil,
MS steel, HV/LV bushings, Buchholz relay, and temperature indicator;
switchgear BOMs use VCBs/MCCBs, busbar assemblies, CTs, and protection relays.
BOMs are submitted (active) after creation.
Idempotent — skips items that already have an active BOM.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

BOMS = [
    # ── Sub-assemblies (consumed by the finished goods below) ──────────────────
    {
        "item": "ESA-COIL-LV",
        "qty": 1,
        "routing": "Transformer Manufacturing Route",
        "items": [
            {"item_code": "ERM-CU-WIRE-15", "qty": 180.0, "uom": "Kg", "rate": 750.0},
            {"item_code": "ERM-INS-PAPER", "qty": 15.0, "uom": "Kg", "rate": 180.0},
        ],
    },
    {
        "item": "ESA-COIL-HV",
        "qty": 1,
        "routing": "Transformer Manufacturing Route",
        "items": [
            {"item_code": "ERM-CU-WIRE-30", "qty": 45.0, "uom": "Kg", "rate": 740.0},
            {"item_code": "ERM-INS-PAPER", "qty": 10.0, "uom": "Kg", "rate": 180.0},
        ],
    },
    {
        "item": "ESA-CORE",
        "qty": 1,
        "routing": "Transformer Manufacturing Route",
        "items": [
            {"item_code": "ERM-CRGO-STEEL", "qty": 280.0, "uom": "Kg", "rate": 120.0},
        ],
    },
    {
        "item": "ESA-SWGR-BUS",
        "qty": 1,
        "routing": "Switchgear Manufacturing Route",
        "items": [
            {"item_code": "ECOMP-BUSBAR-CU", "qty": 6.0, "uom": "Meter", "rate": 620.0},
            {"item_code": "ERM-MS-SHEET", "qty": 5.0, "uom": "Kg", "rate": 65.0},
        ],
    },
    # ── Distribution Transformers ─────────────────────────────────────────────
    {
        "item": "EFG-TRANS-100",
        "qty": 1,
        "routing": "Transformer Manufacturing Route",
        "items": [
            # Wound coil and core sub-assemblies (each carries its own BOM —
            # see above — making this a two-level BOM)
            {"item_code": "ESA-COIL-LV", "qty": 1, "uom": "Nos", "rate": 18000.0},
            {"item_code": "ESA-COIL-HV", "qty": 1, "uom": "Nos", "rate": 25000.0},
            {"item_code": "ESA-CORE", "qty": 1, "uom": "Nos", "rate": 35000.0},
            # Insulation
            {"item_code": "ERM-TRANS-OIL", "qty": 150.0, "uom": "Litre", "rate": 95.0},
            # Tank
            {"item_code": "ERM-MS-SHEET", "qty": 80.0, "uom": "Kg", "rate": 65.0},
            # Accessories
            {"item_code": "ECOMP-BUSH-HV", "qty": 3, "uom": "Nos", "rate": 3500.0},
            {"item_code": "ECOMP-BUSH-LV", "qty": 6, "uom": "Nos", "rate": 850.0},
            {"item_code": "ECOMP-BUCHHOLZ", "qty": 1, "uom": "Nos", "rate": 4500.0},
            {"item_code": "ECOMP-TEMP-IND", "qty": 1, "uom": "Nos", "rate": 2800.0},
            {"item_code": "ECOMP-PRD", "qty": 1, "uom": "Nos", "rate": 2200.0},
            {"item_code": "ECOMP-GASKET", "qty": 1, "uom": "Set", "rate": 1200.0},
            {"item_code": "ECOMP-CABLE-LUG", "qty": 6, "uom": "Nos", "rate": 95.0},
            # Packaging
            {"item_code": "EPKG-CRATE-LG", "qty": 1, "uom": "Nos", "rate": 8500.0},
            {"item_code": "EPKG-WRAP", "qty": 2, "uom": "Nos", "rate": 950.0},
        ],
    },
    {
        # Alternate BOM for EFG-TRANS-100 — built directly from raw copper
        # wire/CRGO steel on-site instead of pre-wound coil/core
        # sub-assemblies (a shop that winds in-house vs. one that
        # outsources winding).
        "item": "EFG-TRANS-100",
        "qty": 1,
        "routing": "Transformer Manufacturing Route",
        "is_default": False,
        "items": [
            {"item_code": "ERM-CU-WIRE-15", "qty": 220.0, "uom": "Kg", "rate": 750.0},
            {"item_code": "ERM-CU-WIRE-30", "qty": 55.0, "uom": "Kg", "rate": 740.0},
            {"item_code": "ERM-CRGO-STEEL", "qty": 320.0, "uom": "Kg", "rate": 120.0},
            {"item_code": "ERM-TRANS-OIL", "qty": 150.0, "uom": "Litre", "rate": 95.0},
            {"item_code": "ERM-INS-PAPER", "qty": 18.0, "uom": "Kg", "rate": 180.0},
            {"item_code": "ERM-MS-SHEET", "qty": 80.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "ECOMP-BUSH-HV", "qty": 3, "uom": "Nos", "rate": 3500.0},
            {"item_code": "ECOMP-BUSH-LV", "qty": 6, "uom": "Nos", "rate": 850.0},
            {"item_code": "ECOMP-BUCHHOLZ", "qty": 1, "uom": "Nos", "rate": 4500.0},
            {"item_code": "ECOMP-TEMP-IND", "qty": 1, "uom": "Nos", "rate": 2800.0},
            {"item_code": "ECOMP-PRD", "qty": 1, "uom": "Nos", "rate": 2200.0},
            {"item_code": "ECOMP-GASKET", "qty": 1, "uom": "Set", "rate": 1200.0},
            {"item_code": "ECOMP-CABLE-LUG", "qty": 6, "uom": "Nos", "rate": 95.0},
            {"item_code": "EPKG-CRATE-LG", "qty": 1, "uom": "Nos", "rate": 8500.0},
            {"item_code": "EPKG-WRAP", "qty": 2, "uom": "Nos", "rate": 950.0},
        ],
    },
    {
        "item": "EFG-TRANS-250",
        "qty": 1,
        "routing": "Transformer Manufacturing Route",
        "items": [
            {"item_code": "ERM-CU-WIRE-15", "qty": 320.0, "uom": "Kg", "rate": 750.0},
            {"item_code": "ERM-CU-WIRE-30", "qty": 90.0, "uom": "Kg", "rate": 740.0},
            {"item_code": "ERM-CRGO-STEEL", "qty": 520.0, "uom": "Kg", "rate": 120.0},
            {"item_code": "ERM-TRANS-OIL", "qty": 280.0, "uom": "Litre", "rate": 95.0},
            {"item_code": "ERM-INS-PAPER", "qty": 45.0, "uom": "Kg", "rate": 180.0},
            {"item_code": "ERM-MS-SHEET", "qty": 150.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "ECOMP-BUSH-HV", "qty": 3, "uom": "Nos", "rate": 3500.0},
            {"item_code": "ECOMP-BUSH-LV", "qty": 6, "uom": "Nos", "rate": 850.0},
            {"item_code": "ECOMP-BUCHHOLZ", "qty": 1, "uom": "Nos", "rate": 4500.0},
            {"item_code": "ECOMP-TEMP-IND", "qty": 1, "uom": "Nos", "rate": 2800.0},
            {"item_code": "ECOMP-PRD", "qty": 1, "uom": "Nos", "rate": 2200.0},
            {"item_code": "ECOMP-GASKET", "qty": 1, "uom": "Set", "rate": 1200.0},
            {"item_code": "ECOMP-CABLE-LUG", "qty": 6, "uom": "Nos", "rate": 95.0},
            {"item_code": "EPKG-CRATE-LG", "qty": 1, "uom": "Nos", "rate": 8500.0},
            {"item_code": "EPKG-WRAP", "qty": 2, "uom": "Nos", "rate": 950.0},
        ],
    },
    {
        "item": "EFG-TRANS-500",
        "qty": 1,
        "routing": "Transformer Manufacturing Route",
        "items": [
            {"item_code": "ERM-CU-WIRE-15", "qty": 580.0, "uom": "Kg", "rate": 750.0},
            {"item_code": "ERM-CU-WIRE-30", "qty": 160.0, "uom": "Kg", "rate": 740.0},
            {"item_code": "ERM-CRGO-STEEL", "qty": 950.0, "uom": "Kg", "rate": 120.0},
            {"item_code": "ERM-TRANS-OIL", "qty": 520.0, "uom": "Litre", "rate": 95.0},
            {"item_code": "ERM-INS-PAPER", "qty": 80.0, "uom": "Kg", "rate": 180.0},
            {"item_code": "ERM-MS-SHEET", "qty": 280.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "ECOMP-BUSH-HV", "qty": 3, "uom": "Nos", "rate": 3500.0},
            {"item_code": "ECOMP-BUSH-LV", "qty": 6, "uom": "Nos", "rate": 850.0},
            {"item_code": "ECOMP-BUCHHOLZ", "qty": 1, "uom": "Nos", "rate": 4500.0},
            {"item_code": "ECOMP-TEMP-IND", "qty": 1, "uom": "Nos", "rate": 2800.0},
            {"item_code": "ECOMP-PRD", "qty": 1, "uom": "Nos", "rate": 2200.0},
            {"item_code": "ECOMP-GASKET", "qty": 2, "uom": "Set", "rate": 1200.0},
            {"item_code": "ECOMP-CABLE-LUG", "qty": 6, "uom": "Nos", "rate": 95.0},
            {"item_code": "EPKG-CRATE-LG", "qty": 1, "uom": "Nos", "rate": 8500.0},
            {"item_code": "EPKG-WRAP", "qty": 3, "uom": "Nos", "rate": 950.0},
        ],
    },
    # ── Power Transformer 1 MVA ───────────────────────────────────────────────
    {
        "item": "EFG-TRANS-1MVA",
        "qty": 1,
        "routing": "Transformer Manufacturing Route",
        "items": [
            {"item_code": "ERM-CU-WIRE-15", "qty": 800.0, "uom": "Kg", "rate": 750.0},
            {"item_code": "ERM-CU-WIRE-30", "qty": 450.0, "uom": "Kg", "rate": 740.0},
            {"item_code": "ERM-CRGO-STEEL", "qty": 2200.0, "uom": "Kg", "rate": 120.0},
            {"item_code": "ERM-TRANS-OIL", "qty": 2500.0, "uom": "Litre", "rate": 95.0},
            {"item_code": "ERM-INS-PAPER", "qty": 200.0, "uom": "Kg", "rate": 180.0},
            {"item_code": "ERM-MS-SHEET", "qty": 750.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "ECOMP-BUSH-HV", "qty": 3, "uom": "Nos", "rate": 3500.0},
            {"item_code": "ECOMP-BUSH-LV", "qty": 3, "uom": "Nos", "rate": 850.0},
            {"item_code": "ECOMP-BUCHHOLZ", "qty": 1, "uom": "Nos", "rate": 4500.0},
            {"item_code": "ECOMP-TEMP-IND", "qty": 2, "uom": "Nos", "rate": 2800.0},
            {"item_code": "ECOMP-PRD", "qty": 1, "uom": "Nos", "rate": 2200.0},
            {"item_code": "ECOMP-GASKET", "qty": 2, "uom": "Set", "rate": 1200.0},
            {"item_code": "ECOMP-CABLE-LUG", "qty": 12, "uom": "Nos", "rate": 95.0},
            {"item_code": "EPKG-CRATE-LG", "qty": 1, "uom": "Nos", "rate": 8500.0},
            {"item_code": "EPKG-WRAP", "qty": 4, "uom": "Nos", "rate": 950.0},
        ],
    },
    # ── Switchgear Panels ─────────────────────────────────────────────────────
    {
        "item": "EFG-SWGR-HT",
        "qty": 1,
        "routing": "Switchgear Manufacturing Route",
        "items": [
            # Shared with transformers
            {"item_code": "ERM-MS-SHEET", "qty": 120.0, "uom": "Kg", "rate": 65.0},
            # HT-specific components
            {"item_code": "ECOMP-VCB", "qty": 1, "uom": "Nos", "rate": 85000.0},
            {"item_code": "ECOMP-BUSBAR-CU", "qty": 6.0, "uom": "Meter", "rate": 620.0},
            {"item_code": "ECOMP-CT-11KV", "qty": 3, "uom": "Nos", "rate": 8500.0},
            {"item_code": "ECOMP-RELAY-PROT", "qty": 1, "uom": "Nos", "rate": 18500.0},
            # Busbar sub-assembly (carries its own BOM — see above)
            {"item_code": "ESA-SWGR-BUS", "qty": 1, "uom": "Nos", "rate": 22000.0},
            # Packaging
            {"item_code": "EPKG-CRATE-MD", "qty": 1, "uom": "Nos", "rate": 3500.0},
            {"item_code": "EPKG-WRAP", "qty": 2, "uom": "Nos", "rate": 950.0},
        ],
    },
    {
        "item": "EFG-SWGR-LT",
        "qty": 1,
        "routing": "Switchgear Manufacturing Route",
        "items": [
            {"item_code": "ERM-MS-SHEET", "qty": 60.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "ECOMP-MCCB-400A", "qty": 2, "uom": "Nos", "rate": 12500.0},
            {"item_code": "ECOMP-MCB-63A", "qty": 8, "uom": "Nos", "rate": 1850.0},
            {"item_code": "ECOMP-BUSBAR-AL", "qty": 12.0, "uom": "Meter", "rate": 210.0},
            {"item_code": "EPKG-CRATE-MD", "qty": 1, "uom": "Nos", "rate": 3500.0},
            {"item_code": "EPKG-WRAP", "qty": 1, "uom": "Nos", "rate": 950.0},
        ],
    },
    {
        "item": "EFG-MCC",
        "qty": 1,
        "routing": "Switchgear Manufacturing Route",
        "items": [
            {"item_code": "ERM-MS-SHEET", "qty": 120.0, "uom": "Kg", "rate": 65.0},
            {"item_code": "ECOMP-MCCB-400A", "qty": 1, "uom": "Nos", "rate": 12500.0},
            {"item_code": "ECOMP-MCB-63A", "qty": 12, "uom": "Nos", "rate": 1850.0},
            {"item_code": "ECOMP-BUSBAR-AL", "qty": 20.0, "uom": "Meter", "rate": 210.0},
            {"item_code": "ECOMP-RELAY-PROT", "qty": 2, "uom": "Nos", "rate": 18500.0},
            {"item_code": "EPKG-CRATE-MD", "qty": 1, "uom": "Nos", "rate": 3500.0},
            {"item_code": "EPKG-WRAP", "qty": 2, "uom": "Nos", "rate": 950.0},
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
