"""
Shared seeder: Delivery Notes against submitted Sales Orders (ref #35).

Sales Orders currently just sit submitted with nothing shipped against them
anywhere in the repo — this is the outward-flow counterpart to
`211_purchase_receipts.py`, using ERPNext's own `make_delivery_note()` mapper
(the same mapping the "Delivery Note" button on a Sales Order uses).

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

created = errors = 0
dn_names = []
for so_name in so_names:
    try:
        dn = make_delivery_note(so_name)
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
