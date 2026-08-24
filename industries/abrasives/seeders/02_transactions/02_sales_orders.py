"""
Seeder: Sales Orders for Alpha Abrasives.

Generates sales orders split roughly 40% manufactured-line / 60%
traded-line (mirroring evmfg's split-generation pattern in
02_transactions), across three realistic buying patterns:

  - Manufactured wheels/discs/belts (~40% of volume): bulk stock-item
    orders at qty 20-300, priced at a margin over valuation_rate, short
    7-25 day delivery since these are make-to-stock items.
  - Traded machines & power/pneumatic tools (~30% of volume): low-qty
    high-value orders (qty 1-6), 14-45 day delivery reflecting import
    lead times on the machine side.
  - Traded polishing consumables & accessories (~30% of volume): higher-qty
    low-value orders (qty 5-60), short 7-21 day delivery.

Orders are shuffled before submission to produce a realistic interleaved
transaction timeline. Uses deterministic random (self.ctx.random) for
reproducibility.
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
        if not self.ctx.cache_get("fg_item_codes"):
            errors.append("fg_item_codes not in cache — run ItemSeeder first")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        customers = self.ctx.cache_get("customer_names", [])
        fg_items = self.ctx.cache_get("fg_item_codes", [])
        machine_tool_items = self.ctx.cache_get("machine_item_codes", []) + self.ctx.cache_get(
            "power_tool_item_codes", []
        )
        consumable_items = self.ctx.cache_get("consumable_item_codes", [])
        item_valuation = self.ctx.cache_get("item_valuation_by_code", {})

        if not customers or not fg_items:
            return

        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days

        n_manufactured = max(1, int(self.volume * 0.4))
        n_machine_tool = max(1, int(self.volume * 0.3)) if machine_tool_items else 0
        n_consumable = max(self.volume - n_manufactured - n_machine_tool, 0)

        def build_orders(items, count, qty_range, lead_range, margin_range, fallback_rate):
            built = []
            for _ in range(count):
                if not items:
                    break
                item_code = rng.choice(items)
                base_rate = item_valuation.get(item_code, fallback_rate)
                order_date = start_date + timedelta(days=rng.randint(0, span))
                delivery_date = order_date + timedelta(days=rng.randint(*lead_range))
                built.append(
                    {
                        "customer": rng.choice(customers),
                        "transaction_date": order_date.isoformat(),
                        "delivery_date": delivery_date.isoformat(),
                        "items": [
                            {
                                "item_code": item_code,
                                "qty": rng.randint(*qty_range),
                                "rate": round(base_rate * rng.uniform(*margin_range), 2),
                                "delivery_date": delivery_date.isoformat(),
                            }
                        ],
                    }
                )
            return built

        orders = []
        orders += build_orders(fg_items, n_manufactured, (20, 300), (7, 25), (1.20, 1.40), 100.0)
        orders += build_orders(
            machine_tool_items, n_machine_tool, (1, 6), (14, 45), (1.10, 1.30), 5000.0
        )
        orders += build_orders(
            consumable_items, n_consumable, (5, 60), (7, 21), (1.15, 1.35), 200.0
        )

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
