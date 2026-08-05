"""
Seeder: Customers for 3D Printing Services.

Loads customers from data/customers.csv covering design studios,
engineering firms, healthcare organisations, and commercial clients.
Caches customer_names for use by the Sales Order seeder.
Idempotent — skips existing customers.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from demostackkit.seeder.base import BaseMasterSeeder


class CustomerSeeder(BaseMasterSeeder):
    label = "Customers (from CSV)"
    priority = 40

    def validate(self) -> list[str]:
        csv_path = self.ctx.industry_config.industry_dir / self.ctx.industry_config.data.customers
        if not csv_path.exists():
            return [f"Customers CSV not found: {csv_path}"]
        return []

    def run(self) -> None:
        csv_path = self.ctx.industry_config.industry_dir / self.ctx.industry_config.data.customers
        rows = _read_csv(csv_path)
        rows_json = json.dumps(rows)

        # Collect customer groups used in the CSV so we can ensure they exist.
        required_groups = sorted(
            {r.get("customer_group", "Commercial") for r in rows if r.get("customer_group")}
        )
        groups_json = json.dumps(required_groups)

        script = f"""
import json

# Ensure required Customer Groups exist.
for grp in json.loads('''{groups_json}'''):
    if not frappe.db.exists('Customer Group', grp):
        frappe.get_doc({{'doctype': 'Customer Group', 'customer_group_name': grp, 'parent_customer_group': 'All Customer Groups'}}).insert(ignore_permissions=True)
frappe.db.commit()

rows = json.loads('''{rows_json}''')
created = skipped = 0
for r in rows:
    if frappe.db.exists('Customer', r['customer_name']):
        skipped += 1
        continue
    doc = frappe.get_doc({{
        'doctype': 'Customer',
        'customer_name': r['customer_name'],
        'customer_group': r.get('customer_group', 'Commercial'),
        'territory': r.get('territory', 'All Territories'),
        'customer_type': r.get('customer_type', 'Company'),
    }})
    doc.insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Customers: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=180)

        customer_names = [r["customer_name"] for r in rows]
        self.ctx.cache_set("customer_names", customer_names)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]
