from __future__ import annotations

from demostackkit.seeder.base import BaseMasterSeeder


class CompanySeeder(BaseMasterSeeder):
    label = "Company"
    priority = 10

    def run(self) -> None:
        cfg = self.ctx.industry_config
        company = cfg.company
        script = f"""
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
