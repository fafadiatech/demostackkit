"""
Shared seeder: Sales Invoices against every Delivery Note created by
`220_delivery_notes.py` (ref #35).

One invoice per delivery note via ERPNext's own
`delivery_note.make_sales_invoice()` mapper — no separate volume knob, since
it just closes out whatever `220_delivery_notes.py` already decided to ship.

The mapper is expected to carry `cost_center` and `taxes`/`taxes_and_charges`
through from the Delivery Note (itself inherited from the originating Sales
Order, see `210_sales_orders.py`), but that isn't guaranteed across ERPNext
mapper versions, and the Sales Register report (ref #36) reads those
dimensions off the Sales Invoice — so this seeder copies them explicitly from
the source Delivery Note whenever the mapper leaves them blank, rather than
trusting the mapper chain silently.

Caches "sales_invoices" (a dn_name -> invoice_name map) for
`222_customer_returns.py`'s stock-less write-off case, which needs an
original Sales Invoice to build a stock-less return against.

Also explicitly copies `posting_date` from the source Delivery Note (which
itself now pins its own posting_date, see `220_delivery_notes.py`), for the
same reason cost_center/taxes are copied: the mapper doesn't map it, and
ERPNext forces an unset posting_date to "today" on every save — collapsing
every invoice's due_date onto the seed run date and starving Accounts
Receivable's aging buckets of any real spread (ref #37).

`make_sales_invoice()`'s postprocess already runs `set_missing_values()`
against the *unset* (today-dated) posting_date, which computes and sets
`due_date` before we ever touch `posting_date` below. `set_missing_values()`
only fills `due_date` when it's falsy, so leaving the mapper's stale value in
place means every invoice's `due_date` stays pinned to the seed run date
regardless of `posting_date` — silently reintroducing the exact bug this
posting_date fix was meant to solve. Clearing `due_date` alongside
`posting_date` forces it to be recomputed off the corrected date.

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
        if not si.cost_center:
            si.cost_center = frappe.db.get_value('Delivery Note', dn_name, 'cost_center')
        if not si.taxes_and_charges:
            dn_taxes_template = frappe.db.get_value('Delivery Note', dn_name, 'taxes_and_charges')
            if dn_taxes_template:
                si.taxes_and_charges = dn_taxes_template
                dn_taxes = frappe.get_all(
                    'Sales Taxes and Charges',
                    filters={{'parent': dn_name, 'parenttype': 'Delivery Note'}},
                    fields=['charge_type', 'account_head', 'description', 'rate'],
                )
                if dn_taxes:
                    si.set('taxes', dn_taxes)
        # As with cost_center/taxes above: make_sales_invoice() doesn't map
        # posting_date, and validate_posting_time() forces an unset one to
        # "today" — so without this every invoice collapses onto the seed
        # run date, leaving due_date with no real spread (ref #37, this is
        # what starves Accounts Receivable's aging buckets).
        si.set_posting_time = 1
        si.posting_date = frappe.db.get_value('Delivery Note', dn_name, 'posting_date')
        # set_missing_values() (run by make_sales_invoice()'s postprocess)
        # already computed due_date off the pre-override (today-dated)
        # posting_date above, and only fills due_date when it's falsy — so
        # without clearing it here, due_date stays pinned to the seed run
        # date on every invoice regardless of posting_date (ref #37).
        si.due_date = None
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
