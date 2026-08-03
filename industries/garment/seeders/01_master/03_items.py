"""
Seeder: Items for Garment Manufacturing.

Loads items from data/items.csv. Idempotent.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

from demostackkit.seeder.base import BaseMasterSeeder


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

        script = f"""
import frappe, json
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()

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
        result = subprocess.run(
            ["docker", "exec", "-i", self.ctx.backend_container, "python", "-c", script],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)

        item_codes = [row["item_code"] for row in items]
        self.ctx.cache_set("item_codes", item_codes)
        self.ctx.cache_set(
            "fg_item_codes",
            [row["item_code"] for row in items if row.get("item_group") == "Finished Goods"],
        )
        self.ctx.cache_set(
            "rm_item_codes",
            [row["item_code"] for row in items if row.get("item_group") == "Raw Material"],
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]
