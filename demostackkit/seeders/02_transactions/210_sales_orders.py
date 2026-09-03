"""
Shared seeder: Sales Orders (ref #36).

Replaces the 17 near-duplicate `industries/*/seeders/02_transactions/02_sales_orders.py`
files that each hand-rolled the same customer/item/date/rate logic, with one
inconsistency that broke the Gross Profit report: item selling rate was drawn
from a flat `uniform(100, 5000)` band completely disconnected from the item's
own `valuation_rate` — a ₹750,000 vehicle would sell for ₹100-5000, showing a
deeply negative margin everywhere a high-value item was involved.

This seeder instead prices every line as a markup on the item's real
valuation/standard rate (`_MARKUP_MIN`-`_MARKUP_MAX`), and bands qty/lead-time
by that same value via `sales_order_qty_and_lead()` (demostackkit/seeder/utils.py)
— an expensive item sells in small quantities on a long lead time, a cheap one
sells by the dozen quickly. That single mechanism reproduces the kind of
price/qty differentiation industries used to hand-code per item family (e.g.
evmfg's cars-vs-bikes split) without any per-industry code at all.

Orders are also spread across the Cost Centers `89_budgets.py` already
creates and the Sales Taxes and Charges Templates `91_sales_tax_templates.py`
creates, so the Sales Register report has something to cross-cut by.

Runs once per company in `ctx.cache_get("all_companies", ...)` — same pattern
`90_opening_stock.py` uses — because electrical's multi-company group
(PowerTech Electrical/Transformers/Switchgear) needs orders spread across all
three, not just the default company.

Each item row's `warehouse` is pinned to wherever that item actually carries
opening-stock quantity for the order's company (read from `Bin`), rather than
left for ERPNext to fall back to the Item's default warehouse. Those two can
diverge — e.g. electrical's opening stock lands in "Finished Goods Store"
while the Item master's own default warehouse is the generic "Stores" — and a
row without stock in its warehouse gets silently trimmed to nothing by
`220_delivery_notes.py`'s finished-goods reserve cap, which is what a missing
`warehouse` field caused here before this was added.

Priority 210 — before Delivery Notes (220), so every submitted Sales Order is
in place before that seeder decides what to ship.
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import (
    parse_relative_date,
    resolve_saleable_items,
    sales_order_qty_and_lead,
)

_PLAN_MARKER = "DSK_SALES_ORDERS_PLAN::"
_PAYLOAD_MARKER = "DSK_SALES_ORDERS::"

#: Selling rate = item's real valuation/standard rate * a markup in this range.
_MARKUP_MIN, _MARKUP_MAX = 1.15, 1.40

#: Last-resort item value when an item carries neither a valuation nor standard rate.
_FALLBACK_VALUE = 1.0

#: Distinct items per order, for Item-wise Sales Register variety.
_ITEMS_PER_ORDER_MIN, _ITEMS_PER_ORDER_MAX = 1, 6

#: Header delivery_date fallback when an order somehow has no item lead time.
_DEFAULT_LEAD_DAYS = 14


class SalesOrderSeeder(BaseTransactionSeeder):
    label = "Sales Orders"
    priority = 210
    _volume_attr = "sales_orders"
    default_volume = 50

    def validate(self) -> list[str]:
        errors = []
        if not self.ctx.cache_get("customer_names"):
            errors.append("customer_names not in cache")
        if not resolve_saleable_items(self.ctx):
            errors.append("no saleable items in cache (fg_item_codes/item_codes)")
        return errors

    def run(self) -> None:
        cfg = self.ctx.industry_config
        modules = set(cfg.modules)
        if not {"Selling", "Stock"}.issubset(modules):
            return

        rng = self.ctx.random
        default_company = self.ctx.cache_get("company_name", cfg.company.name)
        companies = self.ctx.cache_get("all_companies", [{"name": default_company}])
        company_names = [c["name"] for c in companies]
        customers = self.ctx.cache_get("customer_names", [])
        item_codes = resolve_saleable_items(self.ctx)
        if not customers or not item_codes:
            return

        plan = self._fetch_plan(company_names, item_codes)
        tax_templates = self.ctx.cache_get("sales_tax_templates", [])

        date_cfg = cfg.seed.date_range
        start_date = parse_relative_date(date_cfg.start)
        end_date = parse_relative_date(date_cfg.end)
        span = max((end_date - start_date).days, 0)

        orders = []
        for _ in range(self.volume):
            company = rng.choice(company_names)
            items_info = plan["items"].get(company, [])
            if not items_info:
                continue
            cost_centers = plan["cost_centers"].get(company, [])

            order_date = start_date + timedelta(days=rng.randint(0, span))
            customer = rng.choice(customers)
            chosen = rng.sample(
                items_info,
                min(rng.randint(_ITEMS_PER_ORDER_MIN, _ITEMS_PER_ORDER_MAX), len(items_info)),
            )

            rows = []
            max_lead = 0
            for item in chosen:
                qty, lead_days = sales_order_qty_and_lead(item["value"], rng)
                max_lead = max(max_lead, lead_days)
                delivery_date = order_date + timedelta(days=lead_days)
                rate = round(item["value"] * rng.uniform(_MARKUP_MIN, _MARKUP_MAX), 2)
                rows.append(
                    {
                        "item_code": item["item_code"],
                        "qty": qty,
                        "rate": rate,
                        "uom": item["stock_uom"],
                        "warehouse": item["warehouse"],
                        "delivery_date": delivery_date.isoformat(),
                    }
                )

            header_delivery = order_date + timedelta(days=max_lead or _DEFAULT_LEAD_DAYS)
            orders.append(
                {
                    "company": company,
                    "customer": customer,
                    "transaction_date": order_date.isoformat(),
                    "delivery_date": header_delivery.isoformat(),
                    "cost_center": rng.choice(cost_centers) if cost_centers else None,
                    "taxes_and_charges": rng.choice(tax_templates) if tax_templates else None,
                    "items": rows,
                }
            )

        self._submit(orders)

    # ── Planning ──────────────────────────────────────────────────────────────

    def _fetch_plan(self, companies: list[str], item_codes: list[str]) -> dict[str, Any]:
        """Item valuation/UOM/warehouse and the Cost Center roster, per company, read live.

        Warehouse is picked as whichever warehouse in that company currently
        holds the most stock of the item (via Bin), not the Item's own default
        warehouse — the two can diverge from the industry's opening-stock
        warehouse configuration.
        """
        payload_json = json.dumps({"companies": companies, "item_codes": item_codes})
        script = f"""
import json

payload = json.loads('''{payload_json}''')
companies = payload['companies']
item_codes = payload['item_codes']

item_rows = frappe.get_all(
    'Item',
    filters={{'name': ['in', item_codes]}},
    fields=['name', 'stock_uom', 'valuation_rate', 'standard_rate'],
)
item_value = {{
    row.name: float(row.valuation_rate or row.standard_rate or {_FALLBACK_VALUE})
    for row in item_rows
}}
item_uom = {{row.name: row.stock_uom or 'Nos' for row in item_rows}}

bins = frappe.get_all(
    'Bin',
    filters={{'item_code': ['in', item_codes], 'actual_qty': ['>', 0]}},
    fields=['item_code', 'warehouse', 'actual_qty'],
)
warehouse_company = {{
    w.name: w.company
    for w in frappe.get_all(
        'Warehouse',
        filters={{'name': ['in', list({{b.warehouse for b in bins}})]}},
        fields=['name', 'company'],
    )
}}

best_warehouse = {{}}
for b in bins:
    company = warehouse_company.get(b.warehouse)
    if company not in companies:
        continue
    key = (company, b.item_code)
    if key not in best_warehouse or b.actual_qty > best_warehouse[key][1]:
        best_warehouse[key] = (b.warehouse, b.actual_qty)

items_by_company = {{}}
for company in companies:
    items_by_company[company] = [
        {{
            'item_code': item_code,
            'stock_uom': item_uom[item_code],
            'value': item_value[item_code],
            'warehouse': warehouse,
        }}
        for (c, item_code), (warehouse, _qty) in best_warehouse.items()
        if c == company
    ]

cost_centers_by_company = {{
    company: frappe.get_all(
        'Cost Center', filters={{'company': company, 'is_group': 0}}, pluck='name'
    )
    for company in companies
}}

print('{_PLAN_MARKER}' + json.dumps({{'items': items_by_company, 'cost_centers': cost_centers_by_company}}))
"""
        output = self._exec(script, timeout=120)
        plan = self._extract_payload(output, _PLAN_MARKER)
        if plan is None:
            return {"items": {}, "cost_centers": {}}
        return plan

    # ── Submission ────────────────────────────────────────────────────────────

    def _submit(self, orders: list[dict]) -> None:
        if not orders:
            return
        orders_json = json.dumps(orders)
        script = f"""
import json

orders = json.loads('''{orders_json}''')

template_names = {{o['taxes_and_charges'] for o in orders if o.get('taxes_and_charges')}}
template_rows = {{}}
for template in template_names:
    doc = frappe.get_doc('Sales Taxes and Charges Template', template)
    template_rows[template] = [
        {{
            'charge_type': row.charge_type,
            'account_head': row.account_head,
            'description': row.description,
            'rate': row.rate,
        }}
        for row in doc.taxes
    ]

created = errors = 0
so_names = []
for o in orders:
    try:
        so = frappe.get_doc({{
            'doctype': 'Sales Order',
            'company': o['company'],
            'customer': o['customer'],
            'transaction_date': o['transaction_date'],
            'delivery_date': o['delivery_date'],
            'order_type': 'Sales',
            'cost_center': o.get('cost_center'),
            'items': [
                {{
                    'item_code': it['item_code'],
                    'qty': it['qty'],
                    'rate': it['rate'],
                    'uom': it['uom'],
                    'stock_uom': it['uom'],
                    'conversion_factor': 1,
                    'warehouse': it['warehouse'],
                    'delivery_date': it['delivery_date'],
                }}
                for it in o['items']
            ],
        }})
        template = o.get('taxes_and_charges')
        if template:
            so.taxes_and_charges = template
            so.set('taxes', template_rows.get(template, []))
        so.insert(ignore_permissions=True)
        so.submit()
        created += 1
        so_names.append(so.name)
    except Exception as e:
        print(f'WARN Sales Order: {{e}}')
        errors += 1

frappe.db.commit()
print(f'Sales Orders: created={{created}}, errors={{errors}}')
print('{_PAYLOAD_MARKER}' + json.dumps({{'sales_orders': so_names}}))
"""
        output = self._exec(script, timeout=300)
        payload_out = self._extract_payload(output, _PAYLOAD_MARKER)
        if payload_out is not None:
            self.ctx.cache_set("sales_orders", payload_out.get("sales_orders", []))

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_payload(output: str, marker: str) -> dict[str, Any] | None:
        for line in output.splitlines():
            if line.startswith(marker):
                return json.loads(line[len(marker) :])
        return None
