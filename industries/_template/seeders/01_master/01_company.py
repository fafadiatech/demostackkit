"""
Template: Company seeder.

Copy this to your industry and customise. All seeder classes
must inherit from BaseMasterSeeder (master data) or BaseTransactionSeeder
(transactional data).
"""

from __future__ import annotations

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

# Ensure required Warehouse Types exist (not created when setup wizard is bypassed)
for wh_type in ['Transit', 'Finished Goods', 'Work In Progress', 'Stores']:
    if not frappe.db.exists('Warehouse Type', wh_type):
        frappe.get_doc({{'doctype': 'Warehouse Type', 'name': wh_type, 'warehouse_type': wh_type}}).insert(ignore_permissions=True)
frappe.db.commit()

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
        self._exec(script)

        # Store values in context cache for downstream seeders
        self.ctx.cache_set("company_name", company.name)
        self.ctx.cache_set("company_abbr", company.abbr)
