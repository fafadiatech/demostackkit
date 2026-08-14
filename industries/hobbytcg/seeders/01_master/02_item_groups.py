"""
Seeder: Item Groups for Nexus TCG & Hobbies.

Creates a flat item group hierarchy covering the five product categories of a
hobby shop and trading card game retailer: Sealed Product (booster boxes and
cases), Graded Cards (PSA/BGS certified singles), Singles (raw individual
cards), Accessories (sleeves, deck boxes, playmats, toploaders, binders), and
Services (tournament fees, table rental, grading submissions).
Idempotent — skips existing groups.
"""

from __future__ import annotations

from demostackkit.seeder.base import BaseMasterSeeder

_ITEM_GROUPS = [
    {"item_group_name": "Sealed Product", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Graded Cards", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Singles", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Accessories", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Services", "parent_item_group": "All Item Groups"},
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
