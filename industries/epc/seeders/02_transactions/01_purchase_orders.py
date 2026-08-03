from __future__ import annotations
import json
from datetime import date, timedelta
from demostackkit.seeder.base import BaseTransactionSeeder

class PurchaseOrderSeeder(BaseTransactionSeeder):
    label = "Purchase Orders"
    priority = 210
    _volume_attr = "purchase_orders"

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("supplier_names"):
            errors.append("supplier_names not in cache")
        if not self.ctx.cache_get("rm_item_codes"):
            errors.append("rm_item_codes not in cache")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        suppliers = self.ctx.cache_get("supplier_names", [])
        rm_items = self.ctx.cache_get("rm_item_codes", [])
        if not suppliers or not rm_items:
            return
        cfg = self.ctx.industry_config.seed
        start_date = _parse_relative_date(cfg.date_range.start)
        end_date = _parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days
        orders = []
        for _ in range(self.volume):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            required_date = order_date + timedelta(days=rng.randint(7, 21))
            supplier = rng.choice(suppliers)
            chosen_items = rng.sample(rm_items, min(rng.randint(1, 4), len(rm_items)))
            items = [{"item_code": ic, "qty": rng.randint(10, 200), "rate": round(rng.uniform(50, 2000), 2), "schedule_date": required_date.isoformat()} for ic in chosen_items]
            orders.append({"supplier": supplier, "transaction_date": order_date.isoformat(), "schedule_date": required_date.isoformat(), "items": items})
        orders_json = json.dumps(orders)
        script = f"""
import frappe, json
frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()
company = '{company}'
orders = json.loads('''{orders_json}''')
created = 0
for o in orders:
    try:
        po = frappe.get_doc({{
            'doctype': 'Purchase Order',
            'company': company,
            'supplier': o['supplier'],
            'transaction_date': o['transaction_date'],
            'schedule_date': o['schedule_date'],
            'items': [{{'item_code': it['item_code'], 'qty': it['qty'], 'rate': it['rate'], 'schedule_date': it['schedule_date'], 'uom': 'Nos', 'stock_uom': 'Nos', 'conversion_factor': 1}} for it in o['items']],
        }})
        po.insert(ignore_permissions=True)
        po.submit()
        created += 1
    except Exception as e:
        print(f'WARN PO: {{e}}')
frappe.db.commit()
print(f'Purchase Orders created: {{created}}')
"""
        self._exec(script, timeout=300)

def _parse_relative_date(value: str) -> date:
    today = date.today()
    if value.startswith("-") and value.endswith("d"):
        return today - timedelta(days=int(value[1:-1]))
    return date.fromisoformat(value)
