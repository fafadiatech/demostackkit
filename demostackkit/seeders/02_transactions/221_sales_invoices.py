"""
Shared seeder: Sales Invoices against every Delivery Note created by
`220_delivery_notes.py` (ref #35).

One invoice per delivery note via ERPNext's own
`delivery_note.make_sales_invoice()` mapper — no separate volume knob, since
it just closes out whatever `220_delivery_notes.py` already decided to ship.

Caches "sales_invoices" (a dn_name -> invoice_name map) for
`222_customer_returns.py`'s stock-less write-off case, which needs an
original Sales Invoice to build a stock-less return against.

Priority 221 — right after Delivery Notes (220), ahead of Customer Returns
(222).
"""

from __future__ import annotations

import json
from typing import Any

from demostackkit.seeder.base import BaseTransactionSeeder

_PAYLOAD_MARKER = "DSK_SALES_INVOICES::"


class SalesInvoiceSeeder(BaseTransactionSeeder):
    label = "Sales Invoices"
    priority = 221

    def run(self) -> None:
        dn_names = self.ctx.cache_get("delivery_notes", [])
        if not dn_names:
            return

        payload_json = json.dumps(dn_names)
        script = f"""
import json

from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

dn_names = json.loads('''{payload_json}''')
created = errors = 0
sales_invoices = {{}}
for dn_name in dn_names:
    try:
        si = make_sales_invoice(dn_name)
        si.insert(ignore_permissions=True)
        si.submit()
        created += 1
        sales_invoices[dn_name] = si.name
    except Exception as e:
        print(f'WARN Sales Invoice for {{dn_name}}: {{e}}')
        errors += 1

frappe.db.commit()
print(f'Sales Invoices: created={{created}}, errors={{errors}}')
print('{_PAYLOAD_MARKER}' + json.dumps({{'sales_invoices': sales_invoices}}))
"""
        output = self._exec(script, timeout=300)
        payload_out = self._extract_payload(output)
        if payload_out is not None:
            self.ctx.cache_set("sales_invoices", payload_out.get("sales_invoices", {}))

    @staticmethod
    def _extract_payload(output: str) -> dict[str, Any] | None:
        for line in output.splitlines():
            if line.startswith(_PAYLOAD_MARKER):
                return json.loads(line[len(_PAYLOAD_MARKER) :])
        return None
