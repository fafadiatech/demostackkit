"""
Seeder: Sales Orders for Nexus TCG & Hobbies.

Generates sales orders across the customer base split between three product
categories with realistic retail price markups and delivery lead times:
  - Sealed Product (~50% of volume): qty 1-4 boxes/cases, retail price at
    1.35x–1.45x valuation_rate (standard hobby shop margin). Delivery 3–7 days.
  - Singles (~30% of volume): qty 1-3 cards, retail price at 1.40x–2.00x
    valuation_rate (variable singles market with higher margin). Delivery 1–3 days.
  - Accessories (~20% of volume): qty 1-6 units, retail price at 1.50x–1.80x
    valuation_rate (standard accessories retail margin). Delivery 1–2 days.

Orders are shuffled before submission to produce a realistic interleaved
transaction timeline across the retail mix.

Uses deterministic random (self.ctx.random) for reproducibility.
Running `demostackkit reset hobbytcg` always produces identical SOs.
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
        if not self.ctx.cache_get("sealed_item_codes"):
            errors.append("sealed_item_codes not in cache — run ItemSeeder first")
        if not self.ctx.cache_get("singles_item_codes"):
            errors.append("singles_item_codes not in cache — run ItemSeeder first")
        if not self.ctx.cache_get("accessory_item_codes"):
            errors.append("accessory_item_codes not in cache — run ItemSeeder first")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        customers = self.ctx.cache_get("customer_names", [])
        sealed_items = self.ctx.cache_get("sealed_item_codes", [])
        singles_items = self.ctx.cache_get("singles_item_codes", [])
        accessory_items = self.ctx.cache_get("accessory_item_codes", [])

        if not customers or (not sealed_items and not singles_items and not accessory_items):
            return

        # Build a quick lookup of valuation_rate by item_code from rm_items
        # (covers sealed + singles; accessories need fallback)
        rm_items = self.ctx.cache_get("rm_items", [])
        valuation_map: dict[str, float] = {r["item_code"]: r["valuation_rate"] for r in rm_items}

        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days

        # Split volume: ~50% sealed, ~30% singles, ~20% accessories
        n_sealed = max(1, int(self.volume * 0.50))
        n_singles = max(1, int(self.volume * 0.30))
        n_accessories = self.volume - n_sealed - n_singles

        orders = []

        # --- Sealed Product SOs: qty 1-4, delivery 3-7 days, margin 1.35-1.45x ---
        for _ in range(n_sealed):
            if not sealed_items:
                break
            order_date = start_date + timedelta(days=rng.randint(0, span))
            delivery_date = order_date + timedelta(days=rng.randint(3, 7))
            customer = rng.choice(customers)
            item_code = rng.choice(sealed_items)
            valuation = valuation_map.get(item_code, 72.00)
            qty = rng.randint(1, 4)
            rate = round(valuation * rng.uniform(1.35, 1.45), 2)
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
                            "uom": "Box",
                            "delivery_date": delivery_date.isoformat(),
                        }
                    ],
                }
            )

        # --- Singles SOs: qty 1-3, delivery 1-3 days, margin 1.40-2.00x ---
        for _ in range(n_singles):
            if not singles_items:
                break
            order_date = start_date + timedelta(days=rng.randint(0, span))
            delivery_date = order_date + timedelta(days=rng.randint(1, 3))
            customer = rng.choice(customers)
            item_code = rng.choice(singles_items)
            valuation = valuation_map.get(item_code, 15.00)
            qty = rng.randint(1, 3)
            rate = round(valuation * rng.uniform(1.40, 2.00), 2)
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
                            "uom": "Nos",
                            "delivery_date": delivery_date.isoformat(),
                        }
                    ],
                }
            )

        # --- Accessories SOs: qty 1-6, delivery 1-2 days, margin 1.50-1.80x ---
        for _ in range(n_accessories):
            if not accessory_items:
                break
            order_date = start_date + timedelta(days=rng.randint(0, span))
            delivery_date = order_date + timedelta(days=rng.randint(1, 2))
            customer = rng.choice(customers)
            item_code = rng.choice(accessory_items)
            # Accessories valuation rates are not in rm_items — use a default fallback
            # (accessory items range from ~$4.50 to $28.00 in our CSV)
            valuation = 10.00
            qty = rng.randint(1, 6)
            rate = round(valuation * rng.uniform(1.50, 1.80), 2)
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
                            "uom": "Nos",
                            "delivery_date": delivery_date.isoformat(),
                        }
                    ],
                }
            )

        # Shuffle to interleave all three product categories in the timeline
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
                'uom': it['uom'],
                'stock_uom': it['uom'],
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
