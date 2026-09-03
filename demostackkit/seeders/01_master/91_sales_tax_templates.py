"""
Shared seeder: Sales Taxes and Charges Templates (ref #36).

Sales Register cross-cuts invoices by tax template, but nothing in the repo
ever created one — every industry's `01_company.py` sets up the company with
`chart_of_accounts: 'Standard'` and nothing invokes ERPNext's country-specific
tax wizard, so Sales Orders/Invoices have always gone out tax-free.

This seeder creates one or two Sales Taxes and Charges Templates per company —
a GST-style split for India-flagged companies (CompanyConfig.country), a flat
sales-tax template everywhere else — so `210_sales_orders.py` has more than
one template to vary orders across.

Tax accounts are resolved dynamically against whatever the "Standard" chart of
accounts actually created for this company, the same defensive pattern
`89_budgets.py::resolve_accounts` uses for expense accounts: there is no
guarantee a generic template ships country-specific ledgers like "CGST"/
"SGST", so a template with no resolvable account is skipped rather than
failing the whole seed run.

Idempotent: an existing template is matched on (title, company) and reused.

Caches "sales_tax_templates" (template names) for `210_sales_orders.py`.

Priority 91 — right after Opening Stock (90), so the company/CoA it depends on
already exists, and still well before any transaction seeder.
"""

from __future__ import annotations

import json
from typing import Any

from demostackkit.seeder.base import BaseMasterSeeder

_PAYLOAD_MARKER = "DSK_SALES_TAX_TEMPLATES::"

#: title -> [(account name hint, rate), ...]. Hints are matched against each
#: leaf Tax-type account's account_name (case-insensitive substring).
_INDIA_TEMPLATES: tuple[tuple[str, tuple[tuple[str, float], ...]], ...] = (
    ("GST 18%", (("CGST", 9.0), ("SGST", 9.0))),
    ("GST 5%", (("CGST", 2.5), ("SGST", 2.5))),
)
_DEFAULT_TEMPLATES: tuple[tuple[str, tuple[tuple[str, float], ...]], ...] = (
    ("Sales Tax 8%", (("Tax", 8.0),)),
)


class SalesTaxTemplateSeeder(BaseMasterSeeder):
    label = "Sales Tax Templates"
    priority = 91

    def run(self) -> None:
        cfg = self.ctx.industry_config
        company = self.ctx.cache_get("company_name", cfg.company.name)
        plan = _INDIA_TEMPLATES if cfg.company.country == "India" else _DEFAULT_TEMPLATES
        plan_payload = [{"title": title, "rows": list(rows)} for title, rows in plan]

        payload_json = json.dumps({"company": company, "plan": plan_payload})
        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']
plan = payload['plan']

tax_accounts = frappe.get_all(
    'Account',
    filters={{'company': company, 'account_type': 'Tax', 'is_group': 0}},
    fields=['name', 'account_name'],
)
if not tax_accounts:
    tax_accounts = frappe.get_all(
        'Account',
        filters={{'company': company, 'is_group': 0, 'parent_account': ['like', '%Duties and Taxes%']}},
        fields=['name', 'account_name'],
    )


def resolve_account(hint):
    hint_lower = hint.lower()
    for acc in tax_accounts:
        if hint_lower in (acc.account_name or '').lower():
            return acc.name
    return tax_accounts[0].name if tax_accounts else None


created = skipped = 0
template_names = []
for tpl in plan:
    title = tpl['title']
    existing = frappe.db.get_value(
        'Sales Taxes and Charges Template', {{'title': title, 'company': company}}, 'name'
    )
    if existing:
        skipped += 1
        template_names.append(existing)
        continue

    rows = []
    for hint, rate in tpl['rows']:
        account = resolve_account(hint)
        if not account:
            continue
        rows.append({{
            'charge_type': 'On Net Total',
            'account_head': account,
            'description': f'{{hint}} @ {{rate}}%',
            'rate': rate,
        }})
    if not rows:
        print(f'WARN Sales Tax Template {{title}}: no tax account found, skipped')
        continue

    doc = frappe.get_doc({{
        'doctype': 'Sales Taxes and Charges Template',
        'title': title,
        'company': company,
        'taxes': rows,
    }})
    doc.insert(ignore_permissions=True)
    created += 1
    template_names.append(doc.name)

frappe.db.commit()
print(f'Sales Tax Templates: created={{created}}, skipped={{skipped}}')
print('{_PAYLOAD_MARKER}' + json.dumps({{'sales_tax_templates': template_names}}))
"""
        output = self._exec(script, timeout=120)
        payload_out = self._extract_payload(output)
        if payload_out is not None:
            self.ctx.cache_set("sales_tax_templates", payload_out.get("sales_tax_templates", []))

    @staticmethod
    def _extract_payload(output: str) -> dict[str, Any] | None:
        for line in output.splitlines():
            if line.startswith(_PAYLOAD_MARKER):
                return json.loads(line[len(_PAYLOAD_MARKER) :])
        return None
