"""
Shared seeder: Subcontracted Purchase Orders + the Subcontracting Orders
raised against them (ref #32).

Builds one subcontracted Purchase Order per order (ERPNext's new
subcontracting flow: the PO line's `item_code` is the non-stock Service Item
from `71_subcontracting.py`, `fg_item` is the finished good actually being
made), submits it, then calls ERPNext's own
`purchase_order.make_subcontracting_order()` to raise and submit the
Subcontracting Order — the same mapping the "Subcontracting Order" button on
a subcontracted PO uses, so raw-material consumption (`supplied_items`) is
derived from the finished good's BOM exactly as the UI would derive it.

No-ops for any industry `71_subcontracting.py` skipped (no Manufacturing
module, or no BOM-backed finished good yet).

Priority 205 — inside the transaction phase, ahead of the regular Purchase
Order seeder (210) so a demo's subcontracting activity isn't buried under
routine procurement.
"""

from __future__ import annotations

import json
from datetime import timedelta

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import parse_relative_date

#: Subcontracting service fee, as a fraction of the finished good's own
#: valuation rate — a rough stand-in for "labour + margin" a vendor would
#: charge to assemble/process the item, with ±20% variance per order.
_SERVICE_FEE_RATIO = 0.25


class SubcontractingOrderSeeder(BaseTransactionSeeder):
    label = "Subcontracting Orders"
    priority = 205
    _volume_attr = "subcontracting_orders"

    def run(self) -> None:
        rng = self.ctx.random
        setup = self.ctx.cache_get("subcontract_setup")
        if not setup or not setup.get("item_codes"):
            return

        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = max((end_date - start_date).days, 1)

        item_codes = setup["item_codes"]
        item_details = setup["item_details"]
        supplier_names = setup["subcontractor_names"]

        orders = []
        for _ in range(self.volume):
            item_code = rng.choice(item_codes)
            details = item_details[item_code]
            supplier = rng.choice(supplier_names)
            order_date = start_date + timedelta(days=rng.randint(0, span))
            schedule_date = order_date + timedelta(days=rng.randint(10, 30))
            qty = rng.randint(5, 20)
            base_rate = details["valuation_rate"] or 1000
            rate = round(base_rate * _SERVICE_FEE_RATIO * rng.uniform(0.8, 1.2), 2)

            orders.append(
                {
                    "item_code": item_code,
                    "service_item": setup["service_items"][item_code],
                    "supplier": supplier,
                    "supplier_warehouse": setup["supplier_warehouses"][supplier],
                    "transaction_date": order_date.isoformat(),
                    "schedule_date": schedule_date.isoformat(),
                    "qty": qty,
                    "rate": rate,
                    "uom": details["stock_uom"],
                }
            )

        payload = {
            "company": company,
            "reserve_warehouse": setup["reserve_warehouse"],
            "target_warehouse": setup["target_warehouse"],
            "orders": orders,
        }
        payload_json = json.dumps(payload)

        script = f"""
import json

from erpnext.buying.doctype.purchase_order.purchase_order import make_subcontracting_order

payload = json.loads('''{payload_json}''')
company = payload['company']
reserve_warehouse = payload['reserve_warehouse']
target_warehouse = payload['target_warehouse']

po_created = sco_created = errors = 0
for o in payload['orders']:
    try:
        po = frappe.get_doc({{
            'doctype': 'Purchase Order',
            'company': company,
            'supplier': o['supplier'],
            'transaction_date': o['transaction_date'],
            'schedule_date': o['schedule_date'],
            'is_subcontracted': 1,
            'supplier_warehouse': o['supplier_warehouse'],
            'items': [{{
                'item_code': o['service_item'],
                'qty': o['qty'],
                'rate': o['rate'],
                'uom': o['uom'],
                'stock_uom': o['uom'],
                'conversion_factor': 1,
                'fg_item': o['item_code'],
                'fg_item_qty': o['qty'],
                'warehouse': target_warehouse,
                'schedule_date': o['schedule_date'],
            }}],
        }})
        po.insert(ignore_permissions=True)
        po.submit()
        po_created += 1

        sco = make_subcontracting_order(po.name)
        if reserve_warehouse:
            sco.set_reserve_warehouse = reserve_warehouse
            for row in sco.supplied_items:
                row.reserve_warehouse = reserve_warehouse
        sco.transaction_date = o['transaction_date']
        sco.insert(ignore_permissions=True)
        sco.submit()
        sco_created += 1
    except Exception as e:
        print(f'WARN Subcontracting Order for {{o["item_code"]}}: {{e}}')
        errors += 1

frappe.db.commit()
print(
    f'Subcontracting Orders: purchase_orders={{po_created}}, '
    f'subcontracting_orders={{sco_created}}, errors={{errors}}'
)
"""
        self._exec(script, timeout=300)
