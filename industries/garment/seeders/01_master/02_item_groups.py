"""
Seeder: Item Groups for Garment Manufacturing.

Creates a hierarchy of item groups specific to garment manufacturing.
Idempotent — uses ignore_if_duplicate=True.
"""

from __future__ import annotations

import subprocess
from demostackkit.seeder.base import BaseMasterSeeder


_ITEM_GROUPS = [
    {"item_group_name": "Raw Material", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Finished Goods", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Consumable", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Packaging", "parent_item_group": "All Item Groups"},
    {"item_group_name": "Fabric", "parent_item_group": "Raw Material"},
    {"item_group_name": "Yarn & Thread", "parent_item_group": "Raw Material"},
    {"item_group_name": "Trims & Accessories", "parent_item_group": "Consumable"},
    {"item_group_name": "T-Shirts", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Shirts", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Trousers & Jeans", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Dresses", "parent_item_group": "Finished Goods"},
    {"item_group_name": "Jackets & Outerwear", "parent_item_group": "Finished Goods"},
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
        result = subprocess.run(
            ["docker", "exec", "-i", self.ctx.backend_container, "python", "-c", script],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
