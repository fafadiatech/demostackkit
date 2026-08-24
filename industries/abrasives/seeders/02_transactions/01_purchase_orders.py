"""
Seeder: Purchase Orders for Alpha Abrasives.

Generates purchase orders across two independent sourcing streams that
mirror the hybrid business model (evmfg's shared-component vs
vehicle-specific split-generation pattern applied to a manufacture + trade
company instead of a single production line):

  - Raw material POs (~40% of volume): sourced from Abrasive Raw Material
    Suppliers, buying the grain/bond/backing-cloth inputs the manufactured
    wheel/disc/belt line consumes.
  - Traded goods POs (~60% of volume): sourced from Machine & Tool Import
    Suppliers, buying the polishing machines, power/pneumatic tools and
    consumables that are resold with no BOM at all.

Uses deterministic random (self.ctx.random) for reproducibility.
"""

from __future__ import annotations

import json
from datetime import timedelta

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import parse_relative_date


class PurchaseOrderSeeder(BaseTransactionSeeder):
    label = "Purchase Orders"
    priority = 210
    _volume_attr = "purchase_orders"

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("rm_supplier_names"):
            errors.append("rm_supplier_names not in cache — run SupplierSeeder first")
        if not self.ctx.cache_get("traded_supplier_names"):
            errors.append("traded_supplier_names not in cache — run SupplierSeeder first")
        if not self.ctx.cache_get("rm_items"):
            errors.append("rm_items not in cache — run ItemSeeder first")
        if not self.ctx.cache_get("traded_items"):
            errors.append("traded_items not in cache — run ItemSeeder first")
        return errors

    def run(self) -> None:
        rng = self.ctx.random
        company = self.ctx.cache_get("company_name", self.ctx.industry_config.company.name)
        rm_suppliers = self.ctx.cache_get("rm_supplier_names", [])
        traded_suppliers = self.ctx.cache_get("traded_supplier_names", [])
        rm_items = self.ctx.cache_get("rm_items", [])
        traded_items = self.ctx.cache_get("traded_items", [])

        if not (rm_suppliers and rm_items) and not (traded_suppliers and traded_items):
            return

        cfg = self.ctx.industry_config.seed
        start_date = parse_relative_date(cfg.date_range.start)
        end_date = parse_relative_date(cfg.date_range.end)
        span = (end_date - start_date).days

        n_rm_orders = max(1, int(self.volume * 0.4)) if rm_suppliers and rm_items else 0
        n_traded_orders = self.volume - n_rm_orders if traded_suppliers and traded_items else 0

        orders = []

        # Raw material POs: 1-4 lines, qty 10-200, lead time 7-21 days.
        for _ in range(n_rm_orders):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            required_date = order_date + timedelta(days=rng.randint(7, 21))
            supplier = rng.choice(rm_suppliers)
            chosen = rng.sample(rm_items, min(rng.randint(1, 4), len(rm_items)))
            items = [
                {
                    "item_code": rm["item_code"],
                    "qty": rng.randint(10, 200),
                    "rate": round(rm["valuation_rate"] * rng.uniform(0.88, 1.12), 2),
                    "uom": rm["stock_uom"],
                    "schedule_date": required_date.isoformat(),
                }
                for rm in chosen
            ]
            orders.append(
                {
                    "supplier": supplier,
                    "transaction_date": order_date.isoformat(),
                    "schedule_date": required_date.isoformat(),
                    "items": items,
                }
            )

        # Traded goods POs: 1-3 lines, qty 1-15 (higher-value machines/tools),
        # longer import lead time 21-45 days.
        for _ in range(n_traded_orders):
            order_date = start_date + timedelta(days=rng.randint(0, span))
            required_date = order_date + timedelta(days=rng.randint(21, 45))
            supplier = rng.choice(traded_suppliers)
            chosen = rng.sample(traded_items, min(rng.randint(1, 3), len(traded_items)))
            items = [
                {
                    "item_code": ti["item_code"],
                    "qty": rng.randint(1, 15),
                    "rate": round(ti["valuation_rate"] * rng.uniform(0.85, 1.05), 2),
                    "uom": ti["stock_uom"],
                    "schedule_date": required_date.isoformat(),
                }
                for ti in chosen
            ]
            orders.append(
                {
                    "supplier": supplier,
                    "transaction_date": order_date.isoformat(),
                    "schedule_date": required_date.isoformat(),
                    "items": items,
                }
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
