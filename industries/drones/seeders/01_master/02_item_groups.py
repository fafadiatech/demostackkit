"""
Seeder: Item Groups for Drones Manufacturing.

Creates a hierarchy of item groups specific to drone manufacturing.
Idempotent — uses ignore_if_duplicate=True.
"""

from __future__ import annotations

from demostackkit.seeder.base import BaseMasterSeeder

_ITEM_GROUPS = [
    {"item_group_name": "Raw Material", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Finished Goods", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Consumable", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Packaging", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Electronic Components", "parent_item_group": "Raw Material"},
    {"item_group_name": "Structural Components", "parent_item_group": "Raw Material"},
    {"item_group_name": "Flight Controllers", "parent_item_group": "Electronic Components"},
    {"item_group_name": "Motors & ESCs", "parent_item_group": "Electronic Components"},
    {"item_group_name": "Agricultural Drones", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Surveillance Drones", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Delivery Drones", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Sub Assemblies", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Flight Controller Sub-Assemblies", "parent_item_group": "Sub Assemblies"},
    {"item_group_name": "Motor-ESC Sub-Assemblies", "parent_item_group": "Sub Assemblies"},
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
