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
            {"warehouse_name": "Central Warehouse", "parent_warehouse": f"All Warehouses - {abbr}"},
            {"warehouse_name": "Cold Storage", "parent_warehouse": f"All Warehouses - {abbr}"},
            {"warehouse_name": "Dispatch Bay", "parent_warehouse": f"All Warehouses - {abbr}"},
            {"warehouse_name": "Returns Area", "parent_warehouse": f"All Warehouses - {abbr}"},
            {"warehouse_name": "Damaged Goods Store", "parent_warehouse": f"All Warehouses - {abbr}"},
            {"warehouse_name": "Staging Area", "parent_warehouse": f"All Warehouses - {abbr}"},
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
