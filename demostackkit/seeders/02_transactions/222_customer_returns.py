"""
Shared seeder: Customer Returns + Credit Notes (ref #35).

Two cases, matching the issue's ask directly:

    (a) Physical return with stock — a return Delivery Note via ERPNext's
        generic `make_return_doc("Delivery Note", ...)` (the same mapper the
        "Sales Return" button uses), redirected to land in the shared
        `Customer Returns` warehouse instead of the mapper's default of the
        original source warehouse (so returns don't silently rejoin saleable
        Finished Goods stock), followed by a Credit Note via
        `make_sales_invoice()` against the return DN.
    (b) Disposal / write-off, no stock movement — a Credit Note with no
        stock document behind it at all: a stock-less copy of the original
        Sales Invoice (`update_stock=0`, `is_return=1`,
        `return_against=<original>`), with its per-row links back to the
        originating Sales Order/Delivery Note cleared so ERPNext doesn't try
        to reconcile billed quantities against them.

Only runs for industries carrying the Quality Management module — customer
returns here are specifically the quality/damage/spec-driven kind the issue
describes, not general order cancellations. Splits the returning sample
`_PHYSICAL_SHARE`/`(1 - _PHYSICAL_SHARE)` between the two cases.

Selection of which Delivery Notes return uses `self.ctx.random` directly
(unlike 211/220, "delivery_notes" and "sales_invoices" are already cached
client-side by the seeders that created them, so no server-side sampling is
needed here).

Priority 222 — after Sales Invoices (221), the last seeder in this chain.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseTransactionSeeder

#: Fraction of Delivery Notes that get some kind of customer return.
_RETURN_RATE = 0.2

#: Of the returning sample, the share that gets a physical return-with-stock
#: (the rest become stock-less write-off Credit Notes).
_PHYSICAL_SHARE = 0.7


class CustomerReturnSeeder(BaseTransactionSeeder):
    label = "Customer Returns"
    priority = 222

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Quality Management" not in cfg.modules:
            return

        dn_names = self.ctx.cache_get("delivery_notes", [])
        sales_invoices = self.ctx.cache_get("sales_invoices", {})
        if not dn_names or not sales_invoices:
            return

        rng = self.ctx.random
        n_returns = max(1, round(len(dn_names) * _RETURN_RATE))
        sample = rng.sample(dn_names, min(n_returns, len(dn_names)))
        split = round(len(sample) * _PHYSICAL_SHARE)
        physical, writeoff = sample[:split], sample[split:]

        payload = {"physical": physical, "writeoff": writeoff, "sales_invoices": sales_invoices}
        payload_json = json.dumps(payload)

        script = f"""
import json

from erpnext.controllers.sales_and_purchase_return import make_return_doc
from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

payload = json.loads('''{payload_json}''')
physical = payload['physical']
writeoff = payload['writeoff']
sales_invoices = payload['sales_invoices']

abbr_cache = {{}}
def _abbr(company):
    if company not in abbr_cache:
        abbr_cache[company] = frappe.get_cached_value('Company', company, 'abbr')
    return abbr_cache[company]

returns_created = credit_notes_created = writeoffs_created = errors = 0

for dn_name in physical:
    try:
        return_dn = make_return_doc('Delivery Note', dn_name)
        if not return_dn.items:
            continue
        returns_wh = f'Customer Returns - {{_abbr(return_dn.company)}}'
        if not frappe.db.exists('Warehouse', returns_wh):
            continue
        for item in return_dn.items:
            item.warehouse = returns_wh
        return_dn.insert(ignore_permissions=True)
        return_dn.submit()
        returns_created += 1

        credit_note = make_sales_invoice(return_dn.name)
        credit_note.insert(ignore_permissions=True)
        credit_note.submit()
        credit_notes_created += 1
    except Exception as e:
        print(f'WARN Customer Return for {{dn_name}}: {{e}}')
        errors += 1

for dn_name in writeoff:
    si_name = sales_invoices.get(dn_name)
    if not si_name:
        continue
    try:
        original = frappe.get_doc('Sales Invoice', si_name)
        credit_note = frappe.copy_doc(original)
        credit_note.is_return = 1
        credit_note.return_against = original.name
        credit_note.update_stock = 0
        credit_note.set_posting_time = 1
        credit_note.posting_date = original.posting_date
        for item in credit_note.items:
            item.qty = -abs(item.qty)
            item.stock_qty = -abs(item.stock_qty)
            item.so_detail = None
            item.dn_detail = None
            item.sales_order = None
            item.delivery_note = None
        credit_note.insert(ignore_permissions=True)
        credit_note.submit()
        writeoffs_created += 1
    except Exception as e:
        print(f'WARN Write-off Credit Note for {{dn_name}}: {{e}}')
        errors += 1

frappe.db.commit()
print(
    f'Customer Returns: returns={{returns_created}}, credit_notes={{credit_notes_created}}, '
    f'writeoff_credit_notes={{writeoffs_created}}, errors={{errors}}'
)
"""
        self._exec(script, timeout=300)
