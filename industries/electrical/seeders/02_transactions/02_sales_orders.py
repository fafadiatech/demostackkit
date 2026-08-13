"""
Seeder: Sales Orders for PowerTech Electrical Manufacturing.

Generates sales orders across the customer base split between two product
families with realistic price points and lead times:
  - Transformers (~60% of volume): qty 1-5 units, rate based on product type:
      100kVA: INR 1,65,000–2,00,000
      250kVA: INR 3,20,000–3,90,000
      500kVA: INR 5,80,000–6,80,000
      1MVA:   INR 16,00,000–20,00,000
    Delivery lead time 60-120 days (made-to-order, long manufacturing cycle).
  - Switchgear Panels (~40% of volume): qty 1-3 units, rate based on product:
      HT Panel:  INR 4,00,000–5,20,000
      LT Panel:  INR 1,10,000–1,45,000
      MCC:       INR 2,50,000–3,20,000
    Delivery lead time 30-60 days (faster panel assembly cycle).

Orders are shuffled before submission to produce a realistic interleaved
transaction timeline matching a project-driven B2B sales cycle.

Uses deterministic random (self.ctx.random) for reproducibility.
"""

from __future__ import annotations

import json
from datetime import timedelta

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import parse_relative_date

# Per-item rate ranges (min, max) in INR
_TRANSFORMER_RATES = {
    "EFG-TRANS-100": (165_000, 200_000),
    "EFG-TRANS-250": (320_000, 390_000),
    "EFG-TRANS-500": (580_000, 680_000),
    "EFG-TRANS-1MVA": (1_600_000, 2_000_000),
}

_SWITCHGEAR_RATES = {
    "EFG-SWGR-HT": (400_000, 520_000),
    "EFG-SWGR-LT": (110_000, 145_000),
    "EFG-MCC": (250_000, 320_000),
}


class SalesOrderSeeder(BaseTransactionSeeder):
    label = "Sales Orders"
    priority = 220
    _volume_attr = "sales_orders"

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("customer_names"):
            errors.append("customer_names not in cache — run CustomerSeeder first")
        if not self.ctx.cache_get("transformer_item_codes"):
            errors.append("transformer_item_codes not in cache — run ItemSeeder first")
        if not self.ctx.cache_get("switchgear_item_codes"):
            errors.append("switchgear_item_codes not in cache — run ItemSeeder first")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        customers = self.ctx.cache_get("customer_names", [])
        transformer_items = self.ctx.cache_get("transformer_item_codes", [])
        switchgear_items = self.ctx.cache_get("switchgear_item_codes", [])

        if not customers or (not transformer_items and not switchgear_items):
            return

        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days

        # Split volume: ~60% transformers (high-value, long lead time), ~40% switchgear
        n_trans_orders = max(1, int(self.volume * 0.6))
        n_swgr_orders = self.volume - n_trans_orders

        orders = []

        # Transformer SOs: qty 1-5, delivery 60-120 days
        for _ in range(n_trans_orders):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            delivery_date = order_date + timedelta(days=rng.randint(60, 120))
            customer = rng.choice(customers)
            item_code = rng.choice(transformer_items) if transformer_items else None
            if not item_code:
                continue
            rate_min, rate_max = _TRANSFORMER_RATES.get(item_code, (100_000, 200_000))
            qty = rng.randint(1, 5)
            rate = round(rng.uniform(rate_min, rate_max), 2)
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

        # Switchgear SOs: qty 1-3, delivery 30-60 days
        for _ in range(n_swgr_orders):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            delivery_date = order_date + timedelta(days=rng.randint(30, 60))
            customer = rng.choice(customers)
            item_code = rng.choice(switchgear_items) if switchgear_items else None
            if not item_code:
                continue
            rate_min, rate_max = _SWITCHGEAR_RATES.get(item_code, (100_000, 300_000))
            qty = rng.randint(1, 3)
            rate = round(rng.uniform(rate_min, rate_max), 2)
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

        # Shuffle to interleave transformer and switchgear orders in the timeline
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
