"""
Seeder: Company setup for Healthcare & Pharma demo.

Creates the company. All operations are idempotent — safe to run multiple times.
"""

from __future__ import annotations

from demostackkit.seeder.base import BaseMasterSeeder


class CompanySeeder(BaseMasterSeeder):
    label = "Company"
    priority = 10

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.industry_config.company.name:
            errors.append("company.name is empty in industry.yaml")
        return errors

    def run(self) -> None:
        cfg = self.ctx.industry_config
        company = cfg.company

        script = f"""

# Ensure required Warehouse Types exist (not created by setup wizard bypass)
for wh_type in ['Transit', 'Finished Goods', 'Work In Progress', 'Stores']:
    if not frappe.db.exists('Warehouse Type', wh_type):
        frappe.get_doc({{'doctype': 'Warehouse Type', 'name': wh_type, 'warehouse_type': wh_type}}).insert(ignore_permissions=True)
frappe.db.commit()

# Create company if not exists
if not frappe.db.exists('Company', '{company.name}'):
    doc = frappe.get_doc({{
        'doctype': 'Company',
        'company_name': '{company.name}',
        'abbr': '{company.abbr}',
        'default_currency': '{company.currency}',
        'country': '{company.country}',
        'create_chart_of_accounts_based_on': 'Standard Template',
        'chart_of_accounts': 'Standard',
    }})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print('CREATED: Company {company.name}')
else:
    print('EXISTS: Company {company.name}')

frappe.db.commit()
"""
        self._exec(script)
        self.ctx.cache_set("company_name", company.name)
        self.ctx.cache_set("company_abbr", company.abbr)
        self.ctx.cache_set("currency", company.currency)
