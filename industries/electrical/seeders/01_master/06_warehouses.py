"""
Seeder: Warehouses for PowerTech Electrical Manufacturing.

Creates the same warehouse hierarchy — raw material storage (copper wire, CRGO
steel, oil), work-in-progress areas (coil winding, assembly), finished goods
holding for transformers and switchgear, quality hold and dispatch — once per
company in the group (see 01_company.py's `all_companies` cache), so each
company has its own physically separate inventory locations even though Item/
Customer/Supplier masters are shared. The Scrap / Rejected / Rework warehouses
come from the shared Standard Warehouses seeder. Idempotent — skips existing
warehouses.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


class WarehouseSeeder(BaseMasterSeeder):
    label = "Warehouses"
    priority = 60

    def run(self) -> None:
        default_company = self.ctx.industry_config.company
        companies = self.ctx.cache_get(
            "all_companies",
            [{"name": default_company.name, "abbr": default_company.abbr}],
        )
        for entry in companies:
            self._seed_for_company(entry["name"], entry["abbr"])

    def _seed_for_company(self, company: str, abbr: str) -> None:
        warehouses = [
            {
                "warehouse_name": "Raw Material Store",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
            {
                "warehouse_name": "WIP - Coil Winding",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
            {
                "warehouse_name": "WIP - Core Assembly",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
            {
                "warehouse_name": "Finished Goods Store",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
            {
                "warehouse_name": "Quality Hold",
                "parent_warehouse": f"All Warehouses - {abbr}",
            },
            {
                "warehouse_name": "Dispatch Area",
                "parent_warehouse": f"Finished Goods Store - {abbr}",
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
