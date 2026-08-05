from __future__ import annotations
from demostackkit.seeder.base import BaseMasterSeeder

_ITEM_GROUPS = [
    {"item_group_name": "Solar Panels", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Inverters", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Mounting Structures", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Balance of System", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Batteries", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Project Services", "parent_item_group": "All Item Groups"},
    {"item_group_name": "DC Components", "parent_item_group": "Balance of System"},
    {"item_group_name": "AC Components", "parent_item_group": "Balance of System"},
]


class ItemGroupSeeder(BaseMasterSeeder):
    label = "Item Groups"
    priority = 20

    def run(self) -> None:
        groups_json = __import__("json").dumps(_ITEM_GROUPS)
        script = f"""
import json
if not frappe.db.exists('Item Group', 'All Item Groups'):
    frappe.get_doc({{'doctype': 'Item Group', 'item_group_name': 'All Item Groups', 'is_group': 1}}).insert(ignore_permissions=True)
    frappe.db.commit()
    print('CREATED: Item Group All Item Groups (root)')
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
