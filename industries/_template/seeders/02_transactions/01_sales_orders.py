"""
Template: Sales Order seeder.

IMPORTANT: Always use self.ctx.random for random values.
Never call random.random() directly — that breaks deterministic resets.
"""

from __future__ import annotations

import json
import subprocess
from datetime import date, timedelta

from demostackkit.seeder.base import BaseTransactionSeeder


class SalesOrderSeeder(BaseTransactionSeeder):
    label = "Sales Orders"
    priority = 210

    # Maps to industry.yaml seed.volumes.sales_orders
    _volume_attr = "sales_orders"

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("customer_names"):
            errors.append("customer_names not found in cache")
        return errors

    def run(self) -> None:
        rng = self.ctx.random  # ← ALWAYS use this, not random.random()
        company = self.ctx.cache_get("company_name", "")
        customers = self.ctx.cache_get("customer_names", [])

        if not customers:
            return

        today = date.today()
        orders = []
        for _ in range(self.volume):
            order_date = today - timedelta(days=rng.randint(1, 180))
            delivery_date = order_date + timedelta(days=rng.randint(14, 45))
            orders.append({
                "customer": rng.choice(customers),
                "transaction_date": order_date.isoformat(),
                "delivery_date": delivery_date.isoformat(),
                "rate": round(rng.uniform(100, 5000), 2),
                "qty": rng.randint(10, 100),
            })

        orders_json = json.dumps(orders)
        # ... submit via docker exec bench execute
        # See industries/garment/seeders/02_transactions/02_sales_orders.py
        # for a complete implementation example.
