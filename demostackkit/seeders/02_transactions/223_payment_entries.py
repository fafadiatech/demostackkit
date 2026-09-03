"""
Shared seeder: Payment Entries against submitted Sales Invoices (ref #37).

Every Sales Invoice `221_sales_invoices.py` creates sits fully unpaid — there
is no Payment Entry seeding anywhere in the codebase — which leaves the
Accounts Receivable report showing gross outstanding with no aging variety
(everything is "fully unpaid since posting") and the Customer Ledger Summary
showing debit-only entries with no offsetting credits.

Each non-return Sales Invoice with `outstanding_amount > 0` is assigned one
of four payment outcomes (`_STATUS_WEIGHTS`), so both reports get realistic
variety:

    - full_on_time — paid in full between posting_date and due_date.
    - full_late    — paid in full after due_date (settled-but-overdue,
                      the case Accounts Receivable's aging buckets need
                      alongside genuinely-outstanding invoices).
    - partial      — paid a random fraction of grand_total, so the invoice
                      still carries a smaller outstanding balance in
                      whichever aging bucket its due date lands in.
    - unpaid       — no Payment Entry at all.

`full_late` only applies when the invoice is actually overdue (due_date in
the past); otherwise it falls back to `full_on_time` behaviour, since a
"late" payment before the due date has even arrived doesn't mean anything.
Payment dates are never generated in the future.

Uses ERPNext's own `get_payment_entry()` mapper (the same one the "Payment"
button on a Sales Invoice uses) so `paid_from`/`paid_to` accounts, party
details and exchange rates all come from ERPNext's own resolution rather
than being guessed here.

Priority 223 — after Sales Invoices (221) and Customer Returns (222), since
this needs the "sales_invoices" cache and should run once invoice-level
returns have already been applied.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from demostackkit.seeder.base import BaseTransactionSeeder

_PLAN_MARKER = "DSK_PAYMENT_ENTRIES_PLAN::"
_PAYLOAD_MARKER = "DSK_PAYMENT_ENTRIES::"

#: Outcome distribution across every outstanding Sales Invoice. Must sum to 1.
_STATUS_WEIGHTS: dict[str, float] = {
    "full_on_time": 0.35,
    "full_late": 0.15,
    "partial": 0.25,
    "unpaid": 0.25,
}

#: Fraction of grand_total paid for a "partial" invoice.
_PARTIAL_MIN, _PARTIAL_MAX = 0.2, 0.75

#: How many days past due_date a "full_late" payment can land, capped at today.
_LATE_MAX_DAYS = 120


class PaymentEntrySeeder(BaseTransactionSeeder):
    label = "Payment Entries"
    priority = 223

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("sales_invoices"):
            errors.append("sales_invoices not in cache")
        return errors

    def run(self) -> None:
        sales_invoices = self.ctx.cache_get("sales_invoices", {})
        si_names = list(sales_invoices.values())
        if not si_names:
            return

        plan = self._fetch_plan(si_names)
        rows = plan.get("invoices", [])
        modes_of_payment = plan.get("modes_of_payment", [])
        if not rows:
            return

        rng = self.ctx.random
        today = date.today()
        payments = []
        for row in rows:
            posting_date = date.fromisoformat(row["posting_date"])
            due_date = date.fromisoformat(row["due_date"]) if row["due_date"] else posting_date
            if due_date < posting_date:
                due_date = posting_date
            outstanding = float(row["outstanding_amount"])
            if outstanding <= 0:
                continue

            status = self._pick_status(rng, due_date, today)
            if status == "unpaid":
                continue

            pay_date = self._pick_pay_date(rng, status, posting_date, due_date, today)
            paid_amount = (
                round(outstanding * rng.uniform(_PARTIAL_MIN, _PARTIAL_MAX), 2)
                if status == "partial"
                else outstanding
            )
            payments.append(
                {
                    "sales_invoice": row["name"],
                    "posting_date": pay_date.isoformat(),
                    "paid_amount": paid_amount,
                    "mode_of_payment": (rng.choice(modes_of_payment) if modes_of_payment else None),
                }
            )

        self._submit(payments)

    # ── Planning ──────────────────────────────────────────────────────────────

    def _pick_status(self, rng, due_date: date, today: date) -> str:
        statuses = list(_STATUS_WEIGHTS.keys())
        weights = list(_STATUS_WEIGHTS.values())
        status = rng.choices(statuses, weights=weights, k=1)[0]
        if status == "full_late" and due_date >= today:
            status = "full_on_time"
        return status

    def _pick_pay_date(
        self, rng, status: str, posting_date: date, due_date: date, today: date
    ) -> date:
        if status == "full_late":
            earliest = due_date + timedelta(days=1)
            latest = min(due_date + timedelta(days=_LATE_MAX_DAYS), today)
            if latest < earliest:
                latest = earliest = min(due_date, today)
            span = max((latest - earliest).days, 0)
            return earliest + timedelta(days=rng.randint(0, span))

        # full_on_time / partial: anywhere from posting to whichever comes
        # first of due_date or today (partial payments may still land late).
        latest = min(due_date, today) if status == "full_on_time" else today
        latest = max(latest, posting_date)
        span = max((latest - posting_date).days, 0)
        return posting_date + timedelta(days=rng.randint(0, span))

    def _fetch_plan(self, si_names: list[str]) -> dict[str, Any]:
        payload_json = json.dumps(si_names)
        script = f"""
import json

si_names = json.loads('''{payload_json}''')
rows = frappe.get_all(
    'Sales Invoice',
    filters={{'name': ['in', si_names], 'docstatus': 1, 'is_return': 0}},
    fields=['name', 'posting_date', 'due_date', 'grand_total', 'outstanding_amount'],
)
invoices = [
    {{
        'name': r.name,
        'posting_date': str(r.posting_date),
        'due_date': str(r.due_date) if r.due_date else None,
        'grand_total': float(r.grand_total),
        'outstanding_amount': float(r.outstanding_amount),
    }}
    for r in rows
]
modes_of_payment = frappe.get_all('Mode of Payment', filters={{'enabled': 1}}, pluck='name')
print('{_PLAN_MARKER}' + json.dumps({{'invoices': invoices, 'modes_of_payment': modes_of_payment}}))
"""
        output = self._exec(script, timeout=120)
        return self._extract_payload(output, _PLAN_MARKER) or {}

    # ── Submission ────────────────────────────────────────────────────────────

    def _submit(self, payments: list[dict]) -> None:
        if not payments:
            return
        payments_json = json.dumps(payments)
        script = f"""
import json

from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

payments = json.loads('''{payments_json}''')

created = errors = 0
for p in payments:
    try:
        pe = get_payment_entry('Sales Invoice', p['sales_invoice'])
        pe.posting_date = p['posting_date']
        pe.reference_date = p['posting_date']
        pe.reference_no = f"PMT-{{p['sales_invoice']}}"
        if p.get('mode_of_payment'):
            pe.mode_of_payment = p['mode_of_payment']
        pe.paid_amount = p['paid_amount']
        pe.received_amount = p['paid_amount']
        for ref in pe.references:
            if ref.reference_name == p['sales_invoice']:
                ref.allocated_amount = p['paid_amount']
        pe.insert(ignore_permissions=True)
        pe.submit()
        created += 1
    except Exception as e:
        print(f"WARN Payment Entry for {{p['sales_invoice']}}: {{e}}")
        errors += 1

frappe.db.commit()
print(f'Payment Entries: created={{created}}, errors={{errors}}')
print('{_PAYLOAD_MARKER}' + json.dumps({{'created': created, 'errors': errors}}))
"""
        self._exec(script, timeout=300)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_payload(output: str, marker: str) -> Any | None:
        for line in output.splitlines():
            if line.startswith(marker):
                return json.loads(line[len(marker) :])
        return None
