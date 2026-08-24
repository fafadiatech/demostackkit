"""
Seeder: Item Groups for 3D Printing Services.

Creates a hierarchy of item groups specific to 3D print farm operations,
covering FDM filaments, SLA resins, post-processing supplies, and
finished goods categories.
Idempotent — uses ignore_if_duplicate=True pattern.
"""

from __future__ import annotations

from demostackkit.seeder.base import BaseMasterSeeder

_ITEM_GROUPS = [
    {"item_group_name": "Raw Material", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Finished Goods", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Consumable", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Packaging", "parent_item_group": "All Item Groups"},
    {"item_group_name": "FDM Filaments", "parent_item_group": "Raw Material"},
    {"item_group_name": "SLA Resins", "parent_item_group": "Raw Material"},
    {"item_group_name": "Semi-Finished", "parent_item_group": "Raw Material"},
    {"item_group_name": "Post-Processing Supplies", "parent_item_group": "Consumable"},
    {"item_group_name": "Prototypes", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Functional Parts", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Display Models", "parent_item_group": "Finished Goods"},
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
