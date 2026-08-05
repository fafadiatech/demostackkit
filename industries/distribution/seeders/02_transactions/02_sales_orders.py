from __future__ import annotations
import json
from datetime import date, timedelta
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
        if not self.ctx.cache_get("fg_item_codes"):
            errors.append("fg_item_codes not in cache")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        customers = self.ctx.cache_get("customer_names", [])
        fg_items = self.ctx.cache_get("fg_item_codes", [])
        if not customers or not fg_items:
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
            chosen_items = rng.sample(fg_items, min(rng.randint(1, 5), len(fg_items)))
            items = [
                {
                    "item_code": ic,
                    "qty": rng.randint(5, 100),
                    "rate": round(rng.uniform(100, 5000), 2),
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
            'items': [{{'item_code': it['item_code'], 'qty': it['qty'], 'rate': it['rate'], 'delivery_date': it['delivery_date'], 'uom': 'Nos', 'stock_uom': 'Nos', 'conversion_factor': 1}} for it in o['items']],
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


