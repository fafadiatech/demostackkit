"""
Seeder: Item Groups for PowerTech Electrical Manufacturing.

Creates a hierarchy of item groups covering electrical raw materials
(copper wire, CRGO steel, insulating oil), electrical components
(bushings, breakers, relays), switchgear sub-assemblies, and finished
goods categories for transformers and switchgear panels.
Idempotent — skips existing groups.
"""

from __future__ import annotations

from demostackkit.seeder.base import BaseMasterSeeder

_ITEM_GROUPS = [
    {"item_group_name": "Raw Material", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Finished Goods", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Consumable", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Packaging Materials", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Electrical Raw Materials", "parent_item_group": "Raw Material"},
    {"item_group_name": "Electrical Components", "parent_item_group": "Raw Material"},
    {"item_group_name": "Switchgear Assemblies", "parent_item_group": "Raw Material"},
    {"item_group_name": "Transformers", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Switchgear", "parent_item_group": "Finished Goods"},
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
