"""
Seeder: Company setup for PowerTech Electrical Manufacturing demo.

Creates the primary company plus any sibling legal entities configured under
`additional_companies` (the electrical demo's multi-company scenario: shared
Item/Customer/Supplier masters, separate Chart of Accounts / warehouses /
opening stock per company). Also ensures the required Warehouse Types.
All operations are idempotent — safe to run multiple times.
"""

from __future__ import annotations

from demostackkit.seeder.base import BaseMasterSeeder


class CompanySeeder(BaseMasterSeeder):
    label = "Company"
    priority = 10

    def run(self) -> None:
        cfg = self.ctx.industry_config
        company = cfg.company
        all_companies = [company, *cfg.additional_companies]

        script = """

# Ensure required Warehouse Types exist (not created by setup wizard bypass)
for wh_type in ['Transit', 'Finished Goods', 'Work In Progress', 'Stores']:
    if not frappe.db.exists('Warehouse Type', wh_type):
        frappe.get_doc({'doctype': 'Warehouse Type', 'name': wh_type, 'warehouse_type': wh_type}).insert(ignore_permissions=True)
frappe.db.commit()
"""
        for c in all_companies:
            script += f"""
# Create company if not exists
if not frappe.db.exists('Company', '{c.name}'):
    doc = frappe.get_doc({{
        'doctype': 'Company',
        'company_name': '{c.name}',
        'abbr': '{c.abbr}',
        'default_currency': '{c.currency}',
        'country': '{c.country}',
        'create_chart_of_accounts_based_on': 'Standard Template',
        'chart_of_accounts': 'Standard',
    }})
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    print('CREATED: Company {c.name}')
else:
    print('EXISTS: Company {c.name}')
"""
        script += "\nfrappe.db.commit()\n"
        self._exec(script)

        # company_name/company_abbr/currency stay pointed at the primary company
        # so shared, single-company-aware seeders (subcontracting, budgets, ...)
        # keep working unchanged. all_companies is the multi-company roster.
        self.ctx.cache_set("company_name", company.name)
        self.ctx.cache_set("company_abbr", company.abbr)
        self.ctx.cache_set("currency", company.currency)
        self.ctx.cache_set(
            "all_companies",
            [{"name": c.name, "abbr": c.abbr, "currency": c.currency} for c in all_companies],
        )
