"""
Template: Company seeder.

Copy this to your industry and customise. All seeder classes
must inherit from BaseMasterSeeder (master data) or BaseTransactionSeeder
(transactional data).
"""

from __future__ import annotations

import subprocess
from demostackkit.seeder.base import BaseMasterSeeder


class CompanySeeder(BaseMasterSeeder):
    """Creates the demo company. Idempotent — safe to run multiple times."""

    label = "Company"
    priority = 10  # Lower = runs first within this phase

    def validate(self) -> list[str]:
        """Return error strings if pre-conditions are not met."""
        errors = []
        if not self.ctx.industry_config.company.name:
            errors.append("company.name is empty in industry.yaml")
        return errors

    def run(self) -> None:
        cfg = self.ctx.industry_config
        company = cfg.company

        script = f"""
import frappe
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()
if not frappe.db.exists('Company', '{company.name}'):
    doc = frappe.get_doc({{
        'doctype': 'Company',
        'company_name': '{company.name}',
        'abbr': '{company.abbr}',
        'default_currency': '{company.currency}',
        'country': '{company.country}',
    }})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print('CREATED')
else:
    print('EXISTS')
"""
        result = subprocess.run(
            ["docker", "exec", "-i", self.ctx.backend_container, "python", "-c", script],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        # Store values in context cache for downstream seeders
        self.ctx.cache_set("company_name", company.name)
        self.ctx.cache_set("company_abbr", company.abbr)
