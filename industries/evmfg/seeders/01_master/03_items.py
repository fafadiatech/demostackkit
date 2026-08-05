"""
Seeder: Items for Voltara EV Manufacturing.

Loads items from data/items.csv covering battery cells, BMS modules,
motor controllers, wiring harnesses, structural components, tyres,
manufacturing consumables, packaging, and finished electric vehicles
(cars: sedan, SUV, hatchback; bikes: sport, city, cargo).

Caches fg_item_codes, rm_item_codes, item_codes, and rm_items (with
valuation data) for use by downstream transaction seeders.
Also caches car_item_codes and bike_item_codes for the Sales Order seeder
to correctly split volume between vehicle families.
Idempotent — skips existing items.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from demostackkit.seeder.base import BaseMasterSeeder

_FG_GROUPS = {"Electric Cars", "Electric Bikes"}
_RM_GROUPS = {
    "Battery Components",
    "Electrical & Electronics",
    "Structural & Body",
    "Manufacturing Supplies",
    "Packaging",
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

        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        items_json = json.dumps(items)

        # Collect all UOMs used in the CSV so we can ensure they exist.
        required_uoms = sorted({row.get("stock_uom", "Nos") for row in items if row.get("stock_uom")})
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
                if row.get("item_group") in _RM_GROUPS
            ],
        )
        # Cache separate lists for SO seeder to split car vs bike volume
        self.ctx.cache_set(
            "car_item_codes",
            [row["item_code"] for row in items if row.get("item_group") == "Electric Cars"],
        )
        self.ctx.cache_set(
            "bike_item_codes",
            [row["item_code"] for row in items if row.get("item_group") == "Electric Bikes"],
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]
