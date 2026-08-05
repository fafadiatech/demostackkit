"""
Seeder: Purchase Orders for Voltara EV Manufacturing.

Generates purchase orders for raw materials (battery cells, BMS modules,
motor controllers, wiring harnesses, structural components, tyres,
manufacturing consumables, and packaging) from the supplier list. Each PO
contains 1-4 randomly chosen raw material lines with quantities between
5-200 units and rates derived from the item's valuation_rate (with ±12%
market variance).

Uses deterministic random (self.ctx.random) for reproducibility.
Running `demostackkit reset evmfg` always produces identical POs.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import parse_relative_date


class PurchaseOrderSeeder(BaseTransactionSeeder):
    label = "Purchase Orders"
    priority = 210
    _volume_attr = "purchase_orders"

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("supplier_names"):
            errors.append("supplier_names not in cache — run SupplierSeeder first")
        if not self.ctx.cache_get("rm_items"):
            errors.append("rm_items not in cache — run ItemSeeder first")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        suppliers = self.ctx.cache_get("supplier_names", [])
        rm_items = self.ctx.cache_get("rm_items", [])

        if not suppliers or not rm_items:
            return

        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days

        orders = []
        for i in range(self.volume):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            required_date = order_date + timedelta(days=rng.randint(7, 21))
            supplier = rng.choice(suppliers)
            n_items = rng.randint(1, 4)
            chosen = rng.sample(rm_items, min(n_items, len(rm_items)))
            items = []
            for rm in chosen:
                rate = round(rm["valuation_rate"] * rng.uniform(0.88, 1.12), 2)
                items.append({
                    "item_code": rm["item_code"],
                    "qty": rng.randint(5, 200),
                    "rate": rate,
                    "uom": rm["stock_uom"],
                    "schedule_date": required_date.isoformat(),
                })
            orders.append({
                "supplier": supplier,
                "transaction_date": order_date.isoformat(),
                "schedule_date": required_date.isoformat(),
                "items": items,
            })

        orders_json = json.dumps(orders)
        script = f"""
import json

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
            'items': [{{
                'item_code': it['item_code'],
                'qty': it['qty'],
                'rate': it['rate'],
                'schedule_date': it['schedule_date'],
                'uom': it['uom'],
                'stock_uom': it['uom'],
                'conversion_factor': 1,
            }} for it in o['items']],
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


