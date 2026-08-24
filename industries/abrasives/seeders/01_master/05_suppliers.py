"""
Seeder: Suppliers for Alpha Abrasives.

Loads suppliers from data/suppliers.csv, split between two sourcing groups
that mirror the hybrid business model: Abrasive Raw Material Suppliers feed
the in-house manufactured line, and Machine & Tool Import Suppliers feed the
traded/distributed line of polishing machines, power and pneumatic tools.
Caches supplier_names (all), plus rm_supplier_names and traded_supplier_names
so the Purchase Order seeder can source each line independently.
Idempotent — skips existing suppliers.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from demostackkit.seeder.base import BaseMasterSeeder

_RM_SUPPLIER_GROUP = "Abrasive Raw Material Suppliers"
_TRADED_SUPPLIER_GROUP = "Machine & Tool Import Suppliers"


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

        required_groups = sorted(
            {
                r.get("supplier_group", "All Supplier Groups")
                for r in rows
                if r.get("supplier_group")
            }
        )
        groups_json = json.dumps(required_groups)

        script = f"""
import json

for grp in json.loads('''{groups_json}'''):
    if not frappe.db.exists('Supplier Group', grp):
        frappe.get_doc({{'doctype': 'Supplier Group', 'supplier_group_name': grp, 'parent_supplier_group': 'All Supplier Groups'}}).insert(ignore_permissions=True)
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

        supplier_names = [r["supplier_name"] for r in rows]
        self.ctx.cache_set("supplier_names", supplier_names)
        self.ctx.cache_set(
            "rm_supplier_names",
            [r["supplier_name"] for r in rows if r.get("supplier_group") == _RM_SUPPLIER_GROUP],
        )
        self.ctx.cache_set(
            "traded_supplier_names",
            [r["supplier_name"] for r in rows if r.get("supplier_group") == _TRADED_SUPPLIER_GROUP],
        )


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]
