"""
Shared seeder: Return to Vendor + Debit Note for every rejected receipt line
`211_purchase_receipts.py` produced (ref #35).

Consumes the "vendor_rtv_candidates" cache 211 populates (one entry per
Purchase Receipt line that got a rejected_qty split into the shared
`Vendor Rejected` warehouse). Uses ERPNext's own
`make_purchase_return_against_rejected_warehouse()` — the same mapper the
"Return / Debit Note" button on a Purchase Receipt uses when returning
specifically the *rejected* quantity (as opposed to a full-line return) — so
the stock movement correctly ships back out of Vendor Rejected rather than
the normal receiving warehouse. The resulting return Purchase Receipt is then
invoiced via `make_purchase_invoice()`, which carries `is_return`/
`return_against` through automatically, giving the Debit Note.

No separate volume knob: every rejected line gets an RTV, since the
rejection rate in 211 already controls how many of these exist. A leaf
seeder — nothing here is cached for anything downstream.

Priority 213 — right after Purchase Invoices (212), so a receipt's normal
invoice and its RTV/Debit Note (if any) both land before Sales Orders start
shipping (220).
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseTransactionSeeder


class ReturnToVendorSeeder(BaseTransactionSeeder):
    label = "Return to Vendor"
    priority = 213

    def run(self) -> None:
        candidates = self.ctx.cache_get("vendor_rtv_candidates", [])
        if not candidates:
            return

        pr_names = sorted({c["pr_name"] for c in candidates})
        payload_json = json.dumps(pr_names)
        script = f"""
import json

from erpnext.stock.doctype.purchase_receipt.purchase_receipt import (
    make_purchase_invoice,
    make_purchase_return_against_rejected_warehouse,
)

pr_names = json.loads('''{payload_json}''')
returns_created = debit_notes_created = errors = 0
for pr_name in pr_names:
    try:
        return_pr = make_purchase_return_against_rejected_warehouse(pr_name)
        if not return_pr.items:
            continue
        return_pr.insert(ignore_permissions=True)
        return_pr.submit()
        returns_created += 1

        debit_note = make_purchase_invoice(return_pr.name)
        debit_note.insert(ignore_permissions=True)
        debit_note.submit()
        debit_notes_created += 1
    except Exception as e:
        print(f'WARN Return to Vendor for {{pr_name}}: {{e}}')
        errors += 1

frappe.db.commit()
print(
    f'Return to Vendor: returns={{returns_created}}, '
    f'debit_notes={{debit_notes_created}}, errors={{errors}}'
)
"""
        self._exec(script, timeout=300)
