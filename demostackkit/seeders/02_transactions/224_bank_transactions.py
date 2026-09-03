"""
Shared seeder: Bank Transactions against seeded Payment Entries (ref #38).

`223_payment_entries.py` submits Payment Entries against Sales Invoices, and
`92_bank_accounts.py` points each company's Payment Entries at a real Bank
Account instead of Cash — but without any Bank Transaction records, the Bank
Reconciliation Tool has nothing to reconcile and the Bank Reconciliation
Statement's "Cheques and Deposits incorrectly cleared" / outstanding split
never shows any actual clearance activity.

Every submitted, not-yet-cleared Receive-type Payment Entry against a
company's seeded Bank Account is assigned one of three outcomes
(`_OUTCOME_WEIGHTS`):

    - matched   — a Bank Transaction for the exact date/amount is created and
                  reconciled against the Payment Entry via ERPNext's own
                  `reconcile_vouchers()` (the same call the Bank
                  Reconciliation Tool's "Reconcile" button makes), setting
                  the Payment Entry's `clearance_date`.
    - pending   — a Bank Transaction for the exact date/amount is created but
                  left unreconciled, standing in for a bank line the user
                  hasn't gotten to yet.
    - mismatch  — a Bank Transaction is created with a small amount/date
                  variance (bank fee, processing lag) and left unreconciled,
                  so the demo has a case that needs a human judgment call to
                  match rather than an exact auto-match.

Deposits only: 223 only seeds Receive-type Payment Entries (against Sales
Invoices), so there is no seeded Pay-type/withdrawal activity to mirror.
Standalone unreconciled transactions with nothing to match were considered
and rejected (see issue #38) — every transaction here traces back to a real
Payment Entry.

Priority 224 — right after Payment Entries (223), since this needs their
Payment Entries to exist and be queryable via `frappe.get_all`.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from demostackkit.seeder.base import BaseTransactionSeeder

_PLAN_MARKER = "DSK_BANK_TXN_PLAN::"
_PAYLOAD_MARKER = "DSK_BANK_TXN::"

#: Outcome distribution across every reconcilable Payment Entry. Must sum to 1.
_OUTCOME_WEIGHTS: dict[str, float] = {
    "matched": 0.55,
    "pending": 0.20,
    "mismatch": 0.25,
}

#: Amount variance applied to a "mismatch" transaction, as a fraction of the
#: Payment Entry's paid_amount (e.g. a bank fee shaving a bit off a deposit).
_MISMATCH_AMOUNT_MIN, _MISMATCH_AMOUNT_MAX = -0.03, 0.03

#: How many days after the Payment Entry's posting date a "mismatch"
#: transaction's bank date can land (processing lag), capped at today.
_MISMATCH_DAY_MIN, _MISMATCH_DAY_MAX = 1, 5


class BankTransactionSeeder(BaseTransactionSeeder):
    label = "Bank Transactions"
    priority = 224

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("bank_accounts"):
            errors.append("bank_accounts not in cache (Bank Account seeder must run first)")
        return errors

    def run(self) -> None:
        bank_accounts = self.ctx.cache_get("bank_accounts", {})
        if not bank_accounts:
            return

        plan = self._fetch_plan(bank_accounts)
        rows = plan.get("payment_entries", [])
        if not rows:
            return

        rng = self.ctx.random
        today = date.today()
        outcomes = list(_OUTCOME_WEIGHTS.keys())
        weights = list(_OUTCOME_WEIGHTS.values())

        transactions = []
        for row in rows:
            outcome = rng.choices(outcomes, weights=weights, k=1)[0]
            posting_date = date.fromisoformat(row["posting_date"])
            amount = float(row["paid_amount"])

            txn_date = posting_date
            deposit = amount
            reconcile = outcome == "matched"

            if outcome == "mismatch":
                deposit = round(
                    amount * (1 + rng.uniform(_MISMATCH_AMOUNT_MIN, _MISMATCH_AMOUNT_MAX)), 2
                )
                offset = rng.randint(_MISMATCH_DAY_MIN, _MISMATCH_DAY_MAX)
                txn_date = min(posting_date + timedelta(days=offset), today)

            transactions.append(
                {
                    "bank_account": row["bank_account"],
                    "date": txn_date.isoformat(),
                    "deposit": deposit,
                    "reference_number": row["reference_no"] or row["name"],
                    "description": f"Deposit from {row['party'] or row['name']}",
                    "payment_entry": row["name"] if reconcile else None,
                    "allocate_amount": amount if reconcile else None,
                }
            )

        self._submit(transactions)

    # ── Planning ──────────────────────────────────────────────────────────────

    def _fetch_plan(self, bank_accounts: dict[str, str]) -> dict[str, Any]:
        payload_json = json.dumps(bank_accounts)
        script = f"""
import json

bank_accounts = json.loads('''{payload_json}''')
rows = []
for company, bank_account in bank_accounts.items():
    account = frappe.db.get_value('Bank Account', bank_account, 'account')
    if not account:
        continue
    pes = frappe.get_all(
        'Payment Entry',
        filters={{
            'docstatus': 1,
            'company': company,
            'payment_type': 'Receive',
            'paid_to': account,
            'clearance_date': ['is', 'not set'],
        }},
        fields=['name', 'posting_date', 'reference_no', 'paid_amount', 'party'],
    )
    for p in pes:
        rows.append({{
            'name': p.name,
            'bank_account': bank_account,
            'posting_date': str(p.posting_date),
            'reference_no': p.reference_no,
            'paid_amount': float(p.paid_amount),
            'party': p.party,
        }})

print('{_PLAN_MARKER}' + json.dumps({{'payment_entries': rows}}))
"""
        output = self._exec(script, timeout=120)
        return self._extract_payload(output, _PLAN_MARKER) or {}

    # ── Submission ────────────────────────────────────────────────────────────

    def _submit(self, transactions: list[dict]) -> None:
        if not transactions:
            return
        transactions_json = json.dumps(transactions)
        script = f"""
import json

from erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool import (
    reconcile_vouchers,
)

transactions = json.loads('''{transactions_json}''')

created = reconciled = errors = 0
for t in transactions:
    try:
        bt = frappe.get_doc({{
            'doctype': 'Bank Transaction',
            'date': t['date'],
            'bank_account': t['bank_account'],
            'deposit': t['deposit'],
            'withdrawal': 0,
            'reference_number': t['reference_number'],
            'description': t['description'],
        }})
        bt.insert(ignore_permissions=True)
        bt.submit()
        created += 1

        if t.get('payment_entry'):
            reconcile_vouchers(bt.name, json.dumps([{{
                'payment_doctype': 'Payment Entry',
                'payment_name': t['payment_entry'],
                'amount': t['allocate_amount'],
            }}]))
            reconciled += 1
    except Exception as e:
        print(f"WARN Bank Transaction for {{t.get('reference_number')}}: {{e}}")
        errors += 1

frappe.db.commit()
print(f'Bank Transactions: created={{created}}, reconciled={{reconciled}}, errors={{errors}}')
print('{_PAYLOAD_MARKER}' + json.dumps({{'created': created, 'reconciled': reconciled, 'errors': errors}}))
"""
        self._exec(script, timeout=300)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_payload(output: str, marker: str) -> Any | None:
        for line in output.splitlines():
            if line.startswith(marker):
                return json.loads(line[len(marker) :])
        return None
