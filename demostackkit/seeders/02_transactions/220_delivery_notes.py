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

Random selection of which Sales Orders to ship happens inside the container
script for the same reason as `211_purchase_receipts.py`: no seeder caches
created Sales Order names client-side. `self.ctx.random` draws a single seed
that drives a `random.Random` inside the script, keeping `demostackkit reset`
deterministic without a second round trip to fetch SO names first.

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

manufactured = set(
    frappe.get_all(
        'BOM', filters={{'is_active': 1, 'is_default': 1, 'docstatus': 1}}, pluck='item'
    )
)
reserve_qty = {_FG_RESERVE_QTY}


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


created = errors = 0
dn_names = []
for so_name in so_names:
    try:
        dn = make_delivery_note(so_name)
        cap_finished_goods(dn)
        if not dn.items:
            continue
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
