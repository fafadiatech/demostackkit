"""
Seeder: Item Groups for Voltara EV Manufacturing.

Creates a hierarchy of item groups covering EV battery components,
electrical and electronic sub-assemblies, structural and body parts,
manufacturing consumables, packaging, and finished vehicle categories
for both electric cars and electric bikes.
Idempotent — uses ignore_if_duplicate=True pattern.
"""

from __future__ import annotations

from demostackkit.seeder.base import BaseMasterSeeder

_ITEM_GROUPS = [
    {"item_group_name": "Raw Material", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Finished Goods", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Consumable", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Packaging", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Battery Components", "parent_item_group": "Raw Material"},
    {"item_group_name": "Electrical & Electronics", "parent_item_group": "Raw Material"},
    {"item_group_name": "Structural & Body", "parent_item_group": "Raw Material"},
    {"item_group_name": "Manufacturing Supplies", "parent_item_group": "Consumable"},
    {"item_group_name": "Electric Cars", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Electric Bikes", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Sub Assemblies", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Battery Pack Modules", "parent_item_group": "Sub Assemblies"},
    {"item_group_name": "Motor Drive Sub-Assemblies", "parent_item_group": "Sub Assemblies"},
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
