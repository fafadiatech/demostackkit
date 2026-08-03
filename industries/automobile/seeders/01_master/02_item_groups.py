from __future__ import annotations
from demostackkit.seeder.base import BaseMasterSeeder

_ITEM_GROUPS = [
    {"item_group_name": "Vehicles", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Spare Parts", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Lubricants", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Tyres & Wheels", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Accessories", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Sedans", "parent_item_group": "Vehicles"},
    {"item_group_name": "SUVs", "parent_item_group": "Vehicles"},
    {"item_group_name": "Hatchbacks", "parent_item_group": "Vehicles"},
    {"item_group_name": "Engine Parts", "parent_item_group": "Spare Parts"},
    {"item_group_name": "Body Parts", "parent_item_group": "Spare Parts"},
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
