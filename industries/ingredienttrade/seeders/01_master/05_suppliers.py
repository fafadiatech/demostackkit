from __future__ import annotations

import csv
import json
from pathlib import Path

from demostackkit.seeder.base import BaseMasterSeeder

# Suppliers in this group are seeded for narrative colour only (compliance and
# testing services referenced from workspaces/notes) and are never picked as
# the supplier on a Purchase Order.
NON_TRANSACTING_GROUPS = ("Compliance & Testing Services",)


class SupplierSeeder(BaseMasterSeeder):
    label = "Suppliers (from CSV)"
    priority = 50

    def validate(self) -> list[str]:
        csv_path = self.ctx.industry_config.industry_dir / self.ctx.industry_config.data.suppliers
        if not csv_path.exists():
            return [f"Suppliers CSV not found: {csv_path}"]
        return []

    def run(self) -> None:
        csv_path = self.ctx.industry_config.industry_dir / self.ctx.industry_config.data.suppliers
        rows = _read_csv(csv_path)
        rows_json = json.dumps(rows)
        groups = sorted({r["supplier_group"] for r in rows if r.get("supplier_group")})
        groups_json = json.dumps(groups)
        script = f"""
import json
groups = json.loads('''{groups_json}''')
for grp in groups:
    if not frappe.db.exists('Supplier Group', grp):
        frappe.get_doc({{
            'doctype': 'Supplier Group',
            'supplier_group_name': grp,
            'parent_supplier_group': 'All Supplier Groups',
        }}).insert(ignore_permissions=True)
frappe.db.commit()
rows = json.loads('''{rows_json}''')
created = skipped = 0
for r in rows:
    if frappe.db.exists('Supplier', r['supplier_name']):
        skipped += 1
        continue
    doc = frappe.get_doc({{
        'doctype': 'Supplier',
        'supplier_name': r['supplier_name'],
        'supplier_group': r.get('supplier_group', 'All Supplier Groups'),
        'country': r.get('country', 'India'),
        'supplier_type': r.get('supplier_type', 'Company'),
    }})
    doc.insert(ignore_permissions=True)
    created += 1
frappe.db.commit()
print(f'Suppliers: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=180)
        transacting_names = [
            r["supplier_name"]
            for r in rows
            if r.get("supplier_group") not in NON_TRANSACTING_GROUPS
        ]
        self.ctx.cache_set("supplier_names", transacting_names)
        self.ctx.cache_set("all_supplier_names", [r["supplier_name"] for r in rows])


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]
