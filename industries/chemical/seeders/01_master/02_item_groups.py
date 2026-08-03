from __future__ import annotations
from demostackkit.seeder.base import BaseMasterSeeder

_ITEM_GROUPS = [
    {"item_group_name": "Raw Chemicals", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Solvents", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Intermediates", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Finished Products", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Packaging Materials", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Hazardous Materials", "parent_item_group": "Raw Chemicals"},
    {"item_group_name": "Organic Chemicals", "parent_item_group": "Raw Chemicals"},
    {"item_group_name": "Inorganic Chemicals", "parent_item_group": "Raw Chemicals"},
]

class ItemGroupSeeder(BaseMasterSeeder):
    label = "Item Groups"
    priority = 20

    def run(self) -> None:
        groups_json = __import__("json").dumps(_ITEM_GROUPS)
        script = f"""
import frappe, json
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()
groups = json.loads('''{groups_json}''')
for grp in groups:
    if not frappe.db.exists('Item Group', grp['item_group_name']):
        doc = frappe.get_doc({{'doctype': 'Item Group', **grp}})
        doc.insert(ignore_permissions=True)
        print(f"CREATED: Item Group {{grp['item_group_name']}}")
    else:
        print(f"EXISTS: Item Group {{grp['item_group_name']}}")
frappe.db.commit()
"""
        self._exec(script)
