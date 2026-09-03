"""
Shared seeder: Bank + Bank Account master data (ref #38).

Every company's Standard Chart of Accounts ships a "Bank Accounts - <ABBR>"
group with no leaf ledger under it, and `Company.default_bank_account` is
never set — so `get_bank_cash_account()` (used by Payment Entry's
`get_payment_entry()` mapper) always falls back to the Cash account. Every
Payment Entry `223_payment_entries.py` creates therefore posts to Cash, and
there is no Bank Account master for the Bank Reconciliation Tool/Statement
to point at.

This seeder creates one shared "Bank" master (a single demo bank is enough —
the point is a reconcilable ledger, not a multi-bank scenario), then for each
company:
    - a leaf "<Bank> Current Account" ledger under its "Bank Accounts" group
    - a matching Bank Account master record (is_company_account=1)
    - `Company.default_bank_account` pointed at that ledger, so every
      Payment Entry seeded afterwards (223, priority 200+) naturally posts
      to the bank instead of Cash.

Runs once per company in `ctx.cache_get("all_companies", ...)`, the same
multi-company roster `90_opening_stock.py` iterates.

Idempotent, as master seeders must be. Priority 92 — right after Sales Tax
Templates (91), so it runs after Company/CoA setup and well before any
transaction seeder (200+), which is what actually matters since seeder
phases (master vs transactions) always run in full before the next phase
regardless of priority number.

Caches "bank_accounts" (company name -> Bank Account name) for
`224_bank_transactions.py`.
"""

from __future__ import annotations

import json
from typing import Any

from demostackkit.seeder.base import BaseMasterSeeder

_PAYLOAD_MARKER = "DSK_BANK_ACCOUNTS::"

_BANK_NAME = "Demo Bank"


class BankAccountSeeder(BaseMasterSeeder):
    label = "Bank Accounts"
    priority = 92

    def run(self) -> None:
        cfg = self.ctx.industry_config
        default_companies = [{"name": cfg.company.name, "abbr": cfg.company.abbr}]
        companies = self.ctx.cache_get("all_companies", default_companies)

        payload_json = json.dumps({"bank_name": _BANK_NAME, "companies": companies})
        script = f"""
import json

payload = json.loads('''{payload_json}''')
bank_name = payload['bank_name']
companies = payload['companies']

if not frappe.db.exists('Bank', bank_name):
    frappe.get_doc({{'doctype': 'Bank', 'bank_name': bank_name}}).insert(ignore_permissions=True)

bank_accounts = {{}}
created = skipped = 0
for c in companies:
    company = c['name']
    abbr = c['abbr']

    group = f'Bank Accounts - {{abbr}}'
    if not frappe.db.exists('Account', group):
        group = frappe.db.get_value(
            'Account', {{'company': company, 'account_type': 'Bank', 'is_group': 1}}, 'name'
        ) or group

    ledger_name = f'{{bank_name}} Current Account - {{abbr}}'
    if not frappe.db.exists('Account', ledger_name):
        acc = frappe.get_doc({{
            'doctype': 'Account',
            'account_name': f'{{bank_name}} Current Account',
            'parent_account': group,
            'company': company,
            'account_type': 'Bank',
            'is_group': 0,
        }})
        acc.insert(ignore_permissions=True)
        ledger_name = acc.name

    bank_account_name = f'{{company}} Current Account - {{bank_name}}'
    if not frappe.db.exists('Bank Account', bank_account_name):
        ba = frappe.get_doc({{
            'doctype': 'Bank Account',
            'account_name': f'{{company}} Current Account',
            'bank': bank_name,
            'account': ledger_name,
            'company': company,
            'is_company_account': 1,
            'is_default': 1,
        }})
        ba.insert(ignore_permissions=True)
        bank_account_name = ba.name
        created += 1
    else:
        skipped += 1

    if not frappe.db.get_value('Company', company, 'default_bank_account'):
        frappe.db.set_value('Company', company, 'default_bank_account', ledger_name)

    bank_accounts[company] = bank_account_name

frappe.db.commit()
print(f'Bank Accounts: created={{created}}, skipped={{skipped}}')
print('{_PAYLOAD_MARKER}' + json.dumps({{'bank_accounts': bank_accounts}}))
"""
        output = self._exec(script)
        payload_out = self._extract_payload(output)
        if payload_out is not None:
            self.ctx.cache_set("bank_accounts", payload_out.get("bank_accounts", {}))

    @staticmethod
    def _extract_payload(output: str) -> dict[str, Any] | None:
        for line in output.splitlines():
            if line.startswith(_PAYLOAD_MARKER):
                return json.loads(line[len(_PAYLOAD_MARKER) :])
        return None
