"""
Seeder: Sales Orders for Voltara EV Manufacturing.

Generates sales orders across the customer base split between two vehicle
families with realistic price points:
  - Electric Cars (~40% of volume): qty 1-3, rate INR 1,200,000-2,200,000,
    delivery lead time 30-90 days (manufacturing to order).
  - Electric Bikes (~60% of volume): qty 1-15, rate INR 80,000-180,000,
    delivery lead time 7-30 days (higher volume, faster turn).

Orders for both families are generated independently, then shuffled before
submission to produce a realistic interleaved transaction timeline.

Uses deterministic random (self.ctx.random) for reproducibility.
"""

from __future__ import annotations

import json
from datetime import timedelta

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import parse_relative_date


class SalesOrderSeeder(BaseTransactionSeeder):
    label = "Sales Orders"
    priority = 220
    _volume_attr = "sales_orders"

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("customer_names"):
            errors.append("customer_names not in cache — run CustomerSeeder first")
        if not self.ctx.cache_get("car_item_codes"):
            errors.append("car_item_codes not in cache — run ItemSeeder first")
        if not self.ctx.cache_get("bike_item_codes"):
            errors.append("bike_item_codes not in cache — run ItemSeeder first")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        customers = self.ctx.cache_get("customer_names", [])
        car_items = self.ctx.cache_get("car_item_codes", [])
        bike_items = self.ctx.cache_get("bike_item_codes", [])

        if not customers or (not car_items and not bike_items):
            return

        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days

        # Split volume: ~40% cars (low-volume, high-value), ~60% bikes
        n_car_orders = max(1, int(self.volume * 0.4))
        n_bike_orders = self.volume - n_car_orders

        orders = []

        # Car SOs: qty 1-3, rate INR 1,200,000 - 2,200,000, delivery 30-90 days
        for _ in range(n_car_orders):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            delivery_date = order_date + timedelta(days=rng.randint(30, 90))
            customer = rng.choice(customers)
            item_code = rng.choice(car_items) if car_items else None
            if not item_code:
                continue
            qty = rng.randint(1, 3)
            rate = round(rng.uniform(1_200_000, 2_200_000), 2)
            orders.append(
                {
                    "customer": customer,
                    "transaction_date": order_date.isoformat(),
                    "delivery_date": delivery_date.isoformat(),
                    "items": [
                        {
                            "item_code": item_code,
                            "qty": qty,
                            "rate": rate,
                            "delivery_date": delivery_date.isoformat(),
                        }
                    ],
                }
            )

        # Bike SOs: qty 1-15, rate INR 80,000 - 180,000, delivery 7-30 days
        for _ in range(n_bike_orders):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            delivery_date = order_date + timedelta(days=rng.randint(7, 30))
            customer = rng.choice(customers)
            item_code = rng.choice(bike_items) if bike_items else None
            if not item_code:
                continue
            qty = rng.randint(1, 15)
            rate = round(rng.uniform(80_000, 180_000), 2)
            orders.append(
                {
                    "customer": customer,
                    "transaction_date": order_date.isoformat(),
                    "delivery_date": delivery_date.isoformat(),
                    "items": [
                        {
                            "item_code": item_code,
                            "qty": qty,
                            "rate": rate,
                            "delivery_date": delivery_date.isoformat(),
                        }
                    ],
                }
            )

        # Shuffle to interleave car and bike orders in the timeline
        rng.shuffle(orders)

        orders_json = json.dumps(orders)
        script = f"""
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
            'items': [{{
                'item_code': it['item_code'],
                'qty': it['qty'],
                'rate': it['rate'],
                'delivery_date': it['delivery_date'],
                'uom': 'Nos',
                'stock_uom': 'Nos',
                'conversion_factor': 1,
            }} for it in o['items']],
        }})
        so.insert(ignore_permissions=True)
        so.submit()
        created += 1
    except Exception as e:
        print(f'WARN SO: {{e}}')

frappe.db.commit()
print(f'Sales Orders created: {{created}}')
"""
        self._exec(script, timeout=300)
