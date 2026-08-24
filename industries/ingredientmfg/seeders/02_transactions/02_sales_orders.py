"""
Seeder: Sales Orders for Ingredient Manufacturing.

Each order draws from either the "Flavours, Colours & Functional Additives"
line (~60% of orders) or the "Nutraceutical & Botanical Actives" line
(~40% of orders). The nutraceutical line carries a materially higher
per-unit price band, reflecting the higher value of standardized actives
versus functional additives.
"""

from __future__ import annotations

import json
from datetime import timedelta

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import ITEM_ROW_HELPERS, parse_relative_date

_ADDITIVE_PRICE_RANGE = (1200.0, 4000.0)
_NUTRACEUTICAL_PRICE_RANGE = (4500.0, 14000.0)


class SalesOrderSeeder(BaseTransactionSeeder):
    label = "Sales Orders"
    priority = 220
    _volume_attr = "sales_orders"

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("customer_names"):
            errors.append("customer_names not in cache")
        if not self.ctx.cache_get("fg_item_codes"):
            errors.append("fg_item_codes not in cache")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        customers = self.ctx.cache_get("customer_names", [])
        additive_items = self.ctx.cache_get("fg_additive_item_codes", [])
        nutraceutical_items = self.ctx.cache_get("fg_nutraceutical_item_codes", [])
        if not customers or not (additive_items or nutraceutical_items):
            return
        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days
        orders = []
        for _ in range(self.volume):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            delivery_date = order_date + timedelta(days=rng.randint(14, 45))
            customer = rng.choice(customers)
            is_nutraceutical = rng.random() < 0.4 and nutraceutical_items
            pool = nutraceutical_items if is_nutraceutical else additive_items
            if not pool:
                pool = additive_items or nutraceutical_items
            price_low, price_high = (
                _NUTRACEUTICAL_PRICE_RANGE if is_nutraceutical else _ADDITIVE_PRICE_RANGE
            )
            chosen_items = rng.sample(pool, min(rng.randint(1, 5), len(pool)))
            items = [
                {
                    "item_code": ic,
                    "qty": rng.randint(5, 100),
                    "rate": round(rng.uniform(price_low, price_high), 2),
                    "delivery_date": delivery_date.isoformat(),
                }
                for ic in chosen_items
            ]
            orders.append(
                {
                    "customer": customer,
                    "transaction_date": order_date.isoformat(),
                    "delivery_date": delivery_date.isoformat(),
                    "items": items,
                }
            )
        orders_json = json.dumps(orders)
        script = (
            ITEM_ROW_HELPERS
            + f"""
import json
company = '{company}'
orders = json.loads('''{orders_json}''')
created = 0
for o in orders:
    try:
        so = frappe.get_doc({{
            'doctype': 'Sales Order',
            'company': company,
            'customer': o['customer'],
            'transaction_date': o['transaction_date'],
            'delivery_date': o['delivery_date'],
            'order_type': 'Sales',
            'items': [dsk_item_row(it['item_code'], it['qty'], rate=it['rate'], delivery_date=it['delivery_date']) for it in o['items']],
        }})
        so.insert(ignore_permissions=True)
        so.submit()
        created += 1
    except Exception as e:
        print(f'WARN SO: {{e}}')
frappe.db.commit()
print(f'Sales Orders created: {{created}}')
"""
        )
        self._exec(script, timeout=300)
