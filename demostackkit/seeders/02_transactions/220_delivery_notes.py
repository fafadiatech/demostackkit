"""
Shared seeder: Delivery Notes against submitted Sales Orders (ref #35).

Sales Orders currently just sit submitted with nothing shipped against them
anywhere in the repo — this is the outward-flow counterpart to
`211_purchase_receipts.py`, using ERPNext's own `make_delivery_note()` mapper
(the same mapping the "Delivery Note" button on a Sales Order uses).

Nothing in this repo manufactures more Finished Goods once the demo starts —
`90_opening_stock.py` is the only place a finished good's Stock Ledger ever
gets credited — so shipping every Sales Order at face value would keep
draining fg items until the "Stock Balance" report shows zero (or the
Delivery Note itself starts failing on ERPNext's negative-stock check). Each
finished-good row is therefore capped to leave `_FG_RESERVE_QTY` behind in
its source warehouse, so every industry's demo still has some Finished Goods
on the shelf after the full transaction run. Raw materials/purchased items
aren't capped: they're replenished by Purchase Receipts (211) later in the
same run, so draining them briefly is not the problem this guards against.

Caches "delivery_notes" (all DN names) for `221_sales_invoices.py` and
`222_customer_returns.py`.

`make_delivery_note()` doesn't map `posting_date`, and ERPNext's
`validate_posting_time()` forces an unset posting_date to "today" on every
save — so without an explicit override every DN (and therefore every Sales
Invoice made from it) would collapse onto the seed run date regardless of
its source Sales Order's `transaction_date`. Each DN is posted on its
Sales Order's `delivery_date` instead (capped at today, ref #37 — this is
what starves the Accounts Receivable aging buckets of any real spread).

Random selection of which Sales Orders to ship happens inside the container
script for the same reason as `211_purchase_receipts.py`: no seeder caches
created Sales Order names client-side. `self.ctx.random` draws a single seed
that drives a `random.Random` inside the script, keeping `demostackkit reset`
deterministic without a second round trip to fetch SO names first.

A share of shipped SOs (`_PARTIAL_SHARE`) get a Delivery Note against only
part of the ordered qty rather than the full remaining amount — ERPNext marks
such an SO "Partly Delivered" the moment a DN ships less than it ordered, with
no explicit status field to set. Combined with SOs that never get a DN at all
(today's behavior whenever `delivery_notes` volume < `sales_orders` volume),
this gives the Sales Order Analysis report a genuine fully/partly/not
delivered mix (ref #36) instead of an all-or-nothing split. The partial trim
runs before `cap_finished_goods`, so the FG-availability cap still gets the
final say on quantity.

Priority 220 — after the vendor-side chain (Purchase Receipts 211 through
Return to Vendor 213) wraps up, ahead of Sales Invoices (221) and Customer
Returns (222).
"""

from __future__ import annotations

import json
from typing import Any

from demostackkit.seeder.base import BaseTransactionSeeder

_PAYLOAD_MARKER = "DSK_DELIVERY_NOTES::"

#: Minimum units of a finished good left behind in its source warehouse after
#: a Delivery Note ships it, so "Stock Balance" never bottoms out at zero.
_FG_RESERVE_QTY = 1

#: Share of shipped Sales Orders that get a partial-qty Delivery Note instead
#: of the full remaining amount.
_PARTIAL_SHARE = 0.35

#: Fraction of the mapped qty actually shipped, on a partial Delivery Note.
_PARTIAL_QTY_MIN, _PARTIAL_QTY_MAX = 0.3, 0.9


class DeliveryNoteSeeder(BaseTransactionSeeder):
    label = "Delivery Notes"
    priority = 220
    _volume_attr = "delivery_notes"
    default_volume = 35

    def run(self) -> None:
        cfg = self.ctx.industry_config
        modules = set(cfg.modules)
        if not {"Selling", "Stock"}.issubset(modules):
            return

        payload = {
            "volume": self.volume,
            "seed": self.ctx.random.randint(0, 2**31 - 1),
            "partial_share": _PARTIAL_SHARE,
            "partial_qty_min": _PARTIAL_QTY_MIN,
            "partial_qty_max": _PARTIAL_QTY_MAX,
        }
        payload_json = json.dumps(payload)

        script = f"""
import json
import random as _random_mod

from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note

payload = json.loads('''{payload_json}''')
rng = _random_mod.Random(payload['seed'])

so_names = frappe.get_all('Sales Order', filters={{'docstatus': 1}}, pluck='name')
rng.shuffle(so_names)
so_names = so_names[:payload['volume']]
partial_so_names = {{so for so in so_names if rng.random() < payload['partial_share']}}

manufactured = set(
    frappe.get_all(
        'BOM', filters={{'is_active': 1, 'is_default': 1, 'docstatus': 1}}, pluck='item'
    )
)
reserve_qty = {_FG_RESERVE_QTY}


def trim_partial(dn):
    \"\"\"Ship only a random fraction of each row's mapped qty.\"\"\"
    for row in dn.items:
        frac = rng.uniform(payload['partial_qty_min'], payload['partial_qty_max'])
        row.qty = max(1, int(row.qty * frac))


def cap_finished_goods(dn):
    \"\"\"Trim/drop fg rows so at least `reserve_qty` stays on the shelf.\"\"\"
    kept = []
    for row in dn.items:
        if row.item_code not in manufactured:
            kept.append(row)
            continue
        available = frappe.db.get_value(
            'Bin', {{'item_code': row.item_code, 'warehouse': row.warehouse}}, 'actual_qty'
        ) or 0
        shippable = available - reserve_qty
        if shippable <= 0:
            continue
        if row.qty > shippable:
            row.qty = shippable
        kept.append(row)
    dn.set('items', kept)


today = frappe.utils.getdate()
created = errors = 0
dn_names = []
for so_name in so_names:
    try:
        dn = make_delivery_note(so_name)
        if so_name in partial_so_names:
            trim_partial(dn)
        cap_finished_goods(dn)
        if not dn.items:
            continue
        # ERPNext's own mapper leaves posting_date unset, which
        # validate_posting_time() then forces to "today" on every DN
        # regardless of the source Sales Order's transaction_date —
        # collapsing every shipment onto the seed run date. Ship on the
        # SO's own delivery_date instead (capped at today, since nothing
        # ships in the future).
        so_delivery_date = frappe.db.get_value('Sales Order', so_name, 'delivery_date')
        dn.set_posting_time = 1
        dn.posting_date = min(so_delivery_date, today) if so_delivery_date else today
        dn.insert(ignore_permissions=True)
        dn.submit()
        created += 1
        dn_names.append(dn.name)
    except Exception as e:
        print(f'WARN Delivery Note for {{so_name}}: {{e}}')
        errors += 1

frappe.db.commit()
print(f'Delivery Notes: created={{created}}, errors={{errors}}')
print('{_PAYLOAD_MARKER}' + json.dumps({{'delivery_notes': dn_names}}))
"""
        output = self._exec(script, timeout=300)
        payload_out = self._extract_payload(output)
        if payload_out is not None:
            self.ctx.cache_set("delivery_notes", payload_out.get("delivery_notes", []))

    @staticmethod
    def _extract_payload(output: str) -> dict[str, Any] | None:
        for line in output.splitlines():
            if line.startswith(_PAYLOAD_MARKER):
                return json.loads(line[len(_PAYLOAD_MARKER) :])
        return None
