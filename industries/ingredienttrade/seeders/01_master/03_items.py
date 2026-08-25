from __future__ import annotations

import csv
import json
from pathlib import Path

from demostackkit.seeder.base import BaseMasterSeeder

# Ingredient trading is a pure buy-and-sell business; all stockable items are
# both sold (FG) and purchased (RM). We treat every item group as both.
FG_GROUPS = (
    "Starches & Carbohydrates",
    "Fats & Oils",
    "Fruits, Nuts & Spices",
    "Marine & Seaweed Raw Materials",
)
RM_GROUPS = (
    "Starches & Carbohydrates",
    "Fats & Oils",
    "Fruits, Nuts & Spices",
    "Marine & Seaweed Raw Materials",
)


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
created = skipped = 0
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
        # For a pure trading business both FG and RM cover all stock items
        all_stock_codes = [
            row["item_code"] for row in items if row.get("is_stock_item", "1") == "1"
        ]
        self.ctx.cache_set(
            "fg_item_codes",
            [row["item_code"] for row in items if row.get("item_group") in FG_GROUPS],
        )
        self.ctx.cache_set("rm_item_codes", all_stock_codes)
        self.ctx.cache_set(
            "rm_items",
            [
                {
                    "item_code": row["item_code"],
                    "stock_uom": row.get("stock_uom", "Nos"),
                    "valuation_rate": float(row.get("valuation_rate", 0)),
                }
                for row in items
                if row.get("is_stock_item", "1") == "1"
            ],
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]
