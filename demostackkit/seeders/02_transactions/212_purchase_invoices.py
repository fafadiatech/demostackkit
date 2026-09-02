"""
Shared seeder: Purchase Invoices against every Purchase Receipt created by
`211_purchase_receipts.py` (ref #35).

One invoice per receipt via ERPNext's own
`purchase_receipt.make_purchase_invoice()` mapper — no separate volume knob,
since it just closes out whatever `211_purchase_receipts.py` already decided
to receive.

Priority 212 — right after Purchase Receipts (211), ahead of Return to Vendor
(213) so the normal, non-rejected receipts are fully invoiced before the
rejected ones get their return documents.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseTransactionSeeder


class PurchaseInvoiceSeeder(BaseTransactionSeeder):
    label = "Purchase Invoices"
    priority = 212

    def run(self) -> None:
        receipt_names = self.ctx.cache_get("purchase_receipts", [])
        if not receipt_names:
            return

        payload_json = json.dumps(receipt_names)
        script = f"""
import json

from erpnext.stock.doctype.purchase_receipt.purchase_receipt import make_purchase_invoice

receipt_names = json.loads('''{payload_json}''')
created = errors = 0
for pr_name in receipt_names:
    try:
        pi = make_purchase_invoice(pr_name)
        pi.insert(ignore_permissions=True)
        pi.submit()
        created += 1
    except Exception as e:
        print(f'WARN Purchase Invoice for {{pr_name}}: {{e}}')
        errors += 1

frappe.db.commit()
print(f'Purchase Invoices: created={{created}}, errors={{errors}}')
"""
        self._exec(script, timeout=300)
