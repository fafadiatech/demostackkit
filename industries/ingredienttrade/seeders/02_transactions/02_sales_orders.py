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
            errors.append("customer_names not in cache")
        if not self.ctx.cache_get("rm_items"):
            errors.append("rm_items not in cache — run ItemSeeder first")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        customers = self.ctx.cache_get("customer_names", [])
        # Every stocked ingredient can be resold — reuse rm_items so sale
        # prices stay pegged to the item's underlying commodity cost instead
        # of a flat random range.
        rm_items = self.ctx.cache_get("rm_items", [])
        if not customers or not rm_items:
            return
        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days
        orders = []
        for _ in range(self.volume):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            delivery_date = order_date + timedelta(days=rng.randint(20, 50))
            customer = rng.choice(customers)
            chosen = rng.sample(rm_items, min(rng.randint(1, 4), len(rm_items)))
            items = [
                {
                    "item_code": rm["item_code"],
                    "qty": rng.randint(20, 300),
                    # Tight commodity-trading margin over cost — the spread
                    # between buy and sell price is narrow, unlike a branded
                    # FMCG distributor's markup.
                    "rate": round(rm["valuation_rate"] * rng.uniform(1.03, 1.10), 2),
                    "uom": rm["stock_uom"],
                    "delivery_date": delivery_date.isoformat(),
                }
                for rm in chosen
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
            'items': [{{'item_code': it['item_code'], 'qty': it['qty'], 'rate': it['rate'], 'delivery_date': it['delivery_date'], 'uom': it['uom'], 'stock_uom': it['uom'], 'conversion_factor': 1}} for it in o['items']],
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
