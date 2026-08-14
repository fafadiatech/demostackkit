"""
Seeder: Items for Nexus TCG & Hobbies.

Loads items from data/items.csv covering batch-tracked sealed product (booster
boxes and cases for Pokémon, MTG, and Yu-Gi-Oh!), serial-tracked graded cards
(PSA/BGS certified), standard-stock singles and accessories (sleeves, deck
boxes, playmats, toploaders, binders), and non-stock service items (tournament
fees, table rental, grading submissions).

Caches item_codes, sealed_item_codes, singles_item_codes, graded_item_codes,
accessory_item_codes, and rm_items (sealed + singles with valuation data) for
downstream transaction seeders.
Idempotent — skips existing items.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from demostackkit.seeder.base import BaseMasterSeeder

_SEALED_GROUPS = {"Sealed Product"}
_SINGLES_GROUPS = {"Singles"}
_GRADED_GROUPS = {"Graded Cards"}
_ACCESSORY_GROUPS = {"Accessories"}
# Items used in purchase orders: sealed product and singles (purchasable for resale)
_PO_GROUPS = {"Sealed Product", "Singles"}


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

        # Collect all UOMs used in the CSV so we can ensure they exist.
        required_uoms = sorted(
            {row.get("stock_uom", "Nos") for row in items if row.get("stock_uom")}
        )
        uoms_json = json.dumps(required_uoms)

        script = f"""
import json

# Ensure all required UOMs exist before inserting items.
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
        'has_batch_no': int(item.get('has_batch_no', 0)),
        'has_serial_no': int(item.get('has_serial_no', 0)),
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
            "sealed_item_codes",
            [row["item_code"] for row in items if row.get("item_group") in _SEALED_GROUPS],
        )
        self.ctx.cache_set(
            "singles_item_codes",
            [row["item_code"] for row in items if row.get("item_group") in _SINGLES_GROUPS],
        )
        self.ctx.cache_set(
            "graded_item_codes",
            [row["item_code"] for row in items if row.get("item_group") in _GRADED_GROUPS],
        )
        self.ctx.cache_set(
            "accessory_item_codes",
            [row["item_code"] for row in items if row.get("item_group") in _ACCESSORY_GROUPS],
        )
        # Cache full rm_items dicts for PO seeder (needs stock_uom and valuation_rate)
        self.ctx.cache_set(
            "rm_items",
            [
                {
                    "item_code": row["item_code"],
                    "stock_uom": row.get("stock_uom", "Nos"),
                    "valuation_rate": float(row.get("valuation_rate", 0)),
                }
                for row in items
                if row.get("item_group") in _PO_GROUPS
            ],
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]
