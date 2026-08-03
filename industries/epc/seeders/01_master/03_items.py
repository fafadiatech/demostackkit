from __future__ import annotations
import csv, json
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
        items_json = json.dumps(items)
        required_uoms = sorted({row.get("stock_uom", "Nos") for row in items if row.get("stock_uom")})
        uoms_json = json.dumps(required_uoms)
        script = f"""
import frappe, json
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()
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
        self.ctx.cache_set("fg_item_codes", [row["item_code"] for row in items if row.get("item_group") in ("Electrical Equipment", "Mechanical Equipment") and row.get("is_stock_item") == "1"])
        self.ctx.cache_set("rm_item_codes", [row["item_code"] for row in items if row.get("item_group") in ("Civil Materials", "Structural Steel", "Pipes & Fittings", "Cables & Wiring", "Instruments & Controls") and row.get("is_stock_item") == "1"])

def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]
