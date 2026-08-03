"""
Seeder: Customers for Garment Manufacturing. Idempotent.
"""

from __future__ import annotations

import csv
import json
import subprocess
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

        script = f"""
import frappe, json
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()

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
        result = subprocess.run(
            ["docker", "exec", "-i", self.ctx.backend_container, "python", "-c", script],
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)

        customer_names = [r["customer_name"] for r in rows]
        self.ctx.cache_set("customer_names", customer_names)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return [dict(row) for row in csv.DictReader(f)]
