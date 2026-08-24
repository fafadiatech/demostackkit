"""
Seeder: Items for Alpha Abrasives.

Loads items from data/items.csv covering:
  - Manufactured line: abrasive raw materials, packaging, and the finished
    goods built from them (bonded abrasive wheels, abrasive/flap discs,
    coated abrasive belts) — each of which carries a BOM and routing.
  - Traded line: polishing machines, power & pneumatic tools, and polishing
    consumables/accessories bought and resold with no BOM at all.

Caches fg_item_codes (manufactured, BOM-bearing), rm_item_codes (raw
materials + packaging consumed by BOMs), traded_item_codes (pure resale),
and per-family lists for the Sales/Purchase Order seeders.
Idempotent — skips existing items.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from demostackkit.seeder.base import BaseMasterSeeder

_FG_GROUPS = {
    "Bonded Abrasive Wheels",
    "Abrasive Discs & Flap Discs",
    "Coated Abrasive Belts",
}
_RM_GROUPS = {"Abrasive Raw Materials", "Packaging Materials"}
_TRADED_GROUPS = {
    "Polishing Machines",
    "Power & Pneumatic Tools",
    "Polishing Consumables & Accessories",
}


class ItemSeeder(BaseMasterSeeder):
    label = "Items (from CSV)"
    priority = 30

    def validate(self) -> list[str]:
        csv_path = self.ctx.industry_config.industry_dir / self.ctx.industry_config.data.items
        if not csv_path.exists():
            return [f"Items CSV not found: {csv_path}"]
        return []

    def run(self) -> None:
        csv_path = self.ctx.industry_config.industry_dir / self.ctx.industry_config.data.items
        items = _read_csv(csv_path)

        items_json = json.dumps(items)
        required_uoms = sorted(
            {row.get("stock_uom", "Nos") for row in items if row.get("stock_uom")}
        )
        uoms_json = json.dumps(required_uoms)

        script = f"""
import json

for uom_name in json.loads('''{uoms_json}'''):
    if not frappe.db.exists('UOM', uom_name):
        frappe.get_doc({{'doctype': 'UOM', 'uom_name': uom_name}}).insert(ignore_permissions=True)
frappe.db.commit()

items = json.loads('''{items_json}''')
created = 0
skipped = 0
for item in items:
    if frappe.db.exists('Item', item['item_code']):
        skipped += 1
        continue
    doc = frappe.get_doc({{
        'doctype': 'Item',
        'item_code': item['item_code'],
        'item_name': item['item_name'],
        'item_group': item.get('item_group', 'All Item Groups'),
        'stock_uom': item.get('stock_uom', 'Nos'),
        'description': item.get('description', ''),
        'is_stock_item': int(item.get('is_stock_item', 1)),
        'valuation_rate': float(item.get('valuation_rate', 0)),
        'standard_rate': float(item.get('valuation_rate', 0)),
    }})
    doc.insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Items: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=180)

        item_codes = [row["item_code"] for row in items]
        self.ctx.cache_set("item_codes", item_codes)
        self.ctx.cache_set(
            "fg_item_codes",
            [row["item_code"] for row in items if row.get("item_group") in _FG_GROUPS],
        )
        self.ctx.cache_set(
            "rm_item_codes",
            [row["item_code"] for row in items if row.get("item_group") in _RM_GROUPS],
        )
        self.ctx.cache_set(
            "rm_items",
            [
                {
                    "item_code": row["item_code"],
                    "stock_uom": row.get("stock_uom", "Nos"),
                    "valuation_rate": float(row.get("valuation_rate", 0)),
                }
                for row in items
                if row.get("item_group") in _RM_GROUPS
            ],
        )
        self.ctx.cache_set(
            "traded_item_codes",
            [row["item_code"] for row in items if row.get("item_group") in _TRADED_GROUPS],
        )
        self.ctx.cache_set(
            "traded_items",
            [
                {
                    "item_code": row["item_code"],
                    "stock_uom": row.get("stock_uom", "Nos"),
                    "valuation_rate": float(row.get("valuation_rate", 0)),
                }
                for row in items
                if row.get("item_group") in _TRADED_GROUPS
            ],
        )
        # Per-family lists so the Sales Order seeder can split volume between
        # wheels, discs, belts and each traded sub-category.
        for group_name, cache_key in (
            ("Bonded Abrasive Wheels", "wheel_item_codes"),
            ("Abrasive Discs & Flap Discs", "disc_item_codes"),
            ("Coated Abrasive Belts", "belt_item_codes"),
            ("Polishing Machines", "machine_item_codes"),
            ("Power & Pneumatic Tools", "power_tool_item_codes"),
            ("Polishing Consumables & Accessories", "consumable_item_codes"),
        ):
            self.ctx.cache_set(
                cache_key,
                [row["item_code"] for row in items if row.get("item_group") == group_name],
            )
        self.ctx.cache_set(
            "item_valuation_by_code",
            {row["item_code"]: float(row.get("valuation_rate", 0)) for row in items},
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]
