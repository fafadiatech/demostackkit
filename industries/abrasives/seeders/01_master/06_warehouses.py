"""
Seeder: Warehouses for Alpha Abrasives.

Creates a warehouse tree covering both lines of the hybrid business: a raw
material store feeding the manufactured line, a finished goods store for
manufactured wheels/discs/belts, and a separate traded goods store for
imported machines and tools that never touch a BOM. Quality Hold and
Dispatch Area are shared by both lines. The Scrap / Rejected / Rework
warehouses come from the shared Standard Warehouses seeder.
Idempotent — skips existing warehouses.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


class WarehouseSeeder(BaseMasterSeeder):
    label = "Warehouses"
    priority = 60

    def run(self) -> None:
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        abbr = self.ctx.cache_get("company_abbr", self.ctx.industry_config.company.abbr)

        warehouses = [
            {
                "warehouse_name": "Raw Material Store",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
            {
                "warehouse_name": "Finished Goods Store",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
            {
                "warehouse_name": "Traded Goods Store",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
            {
                "warehouse_name": "Quality Hold",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
            {
                "warehouse_name": "Dispatch Area",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
        ]
        wh_json = json.dumps(warehouses)

        script = f"""
import json

company = '{company}'
abbr = '{abbr}'
warehouses = json.loads('''{wh_json}''')
created = skipped = 0

for wh in warehouses:
    wh_full = f"{{wh['warehouse_name']}} - {{abbr}}"
    if frappe.db.exists('Warehouse', wh_full):
        skipped += 1
        continue
    doc = frappe.get_doc({{
        'doctype': 'Warehouse',
        'warehouse_name': wh['warehouse_name'],
        'parent_warehouse': wh['parent_warehouse'],
        'company': company,
    }})
    doc.insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Warehouses: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script)
