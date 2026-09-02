"""
Shared seeder: Opening Stock balances for every stockable Item.

Nothing else in the seed run puts quantity on the shelf — Purchase Orders are
submitted but never received — so without this seeder every site starts with an
empty Stock Ledger. Stock Balance, Stock Projected Qty and Stock Ageing all come
back blank, and a hand-keyed Work Order cannot be transferred or finished because
its components have no stock to draw from.

This posts an ERPNext "Opening Stock" Stock Reconciliation (one per warehouse)
dated the day before the first seeded transaction, so the balances are already in
place when the demo's own documents start moving.

Item routing:
    - an item with an active default BOM is treated as a finished good and lands
      in `seed.opening_stock.fg_warehouse`
    - everything else lands in `seed.opening_stock.warehouse`

Batch- and serial-tracked items get an opening Batch / Serial No created first and
referenced through `use_serial_batch_fields`, which is the only way to open a
balance for items whose Item master carries no batch/serial naming series.

Idempotent, as master seeders must be: items that already carry a Stock Ledger
Entry *for the company being opened* are skipped, so a re-run adds nothing and a
partially seeded site is topped up rather than double-counted. Priority 90 puts
it after Items (30), Warehouses (60) and BOMs (70), and still ahead of every
transaction seeder.

Runs once per company in `ctx.cache_get("all_companies", ...)` — industries with
a single company (the default) get exactly today's behavior; an industry seeding
a multi-company group (see electrical's `additional_companies`) gets its own
Opening Stock posted per company, each against that company's own warehouses and
each company's own `CompanyConfig.opening_stock_qty_scale` (on top of the shared
`seed.opening_stock.qty_scale`), so a smaller subsidiary visibly opens with less
stock than the parent rather than merely landing in a different warehouse.
"""

from __future__ import annotations

import json
from typing import Any

from demostackkit.seeder.base import BaseMasterSeeder
from demostackkit.seeder.utils import opening_stock_date, opening_stock_qty, parse_relative_date

#: Marker used to lift a JSON payload out of the container's stdout.
_PAYLOAD_MARKER = "DSK_OPENING_STOCK::"

#: Every serialised unit needs its own Serial No document, so opening balances for
#: serialised items are capped — a demo needs a handful of scannable serials, not
#: two thousand rows in the Serial No list.
_MAX_SERIAL_QTY = 20

#: Last-resort valuation rate. ERPNext rejects an opening row with a zero rate,
#: and an item priced at zero everywhere else has nothing better to offer.
_FALLBACK_RATE = 1.0


class OpeningStockSeeder(BaseMasterSeeder):
    label = "Opening Stock"
    priority = 90

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if not cfg.seed.opening_stock.enabled:
            return

        default_companies = [{"name": cfg.company.name, "abbr": cfg.company.abbr}]
        companies = self.ctx.cache_get("all_companies", default_companies)
        company_scales = {
            c.name: c.opening_stock_qty_scale for c in [cfg.company, *cfg.additional_companies]
        }

        for entry in companies:
            company_scale = company_scales.get(entry["name"], 1.0)
            self._run_for_company(entry["name"], entry["abbr"], company_scale)

    def _run_for_company(self, company: str, abbr: str, company_scale: float) -> None:
        cfg = self.ctx.industry_config

        plan = self._fetch_plan(company, abbr)
        items = plan.get("items") or []
        if not items:
            print(
                f"Opening Stock ({company}): every item already has stock ledger "
                "entries, nothing to open"
            )
            return

        if plan.get("perpetual") and not plan.get("expense_account"):
            raise RuntimeError(
                "No balance-sheet difference account found for opening stock. "
                "Perpetual inventory is on, so ERPNext requires an Asset/Liability "
                "account (normally 'Temporary Opening') on the opening entry."
            )
        if not plan.get("rm_warehouse"):
            raise RuntimeError(
                f"No non-group warehouse found for company '{plan.get('company')}' — "
                "run the Warehouse seeder first."
            )

        posting_date = opening_stock_date(parse_relative_date(cfg.seed.date_range.start))
        documents = self._build_documents(plan, company_scale)

        payload = {
            "company": plan["company"],
            "posting_date": posting_date.isoformat(),
            "expense_account": plan.get("expense_account"),
            "cost_center": plan.get("cost_center"),
            "documents": documents,
        }
        self._post(payload)

    # ── Planning ──────────────────────────────────────────────────────────────

    def _fetch_plan(self, company: str, abbr: str) -> dict[str, Any]:
        """Read back from the site everything the opening entry depends on.

        Queried rather than taken from the seed cache so the roster covers every
        stockable item on the site, including any an industry created outside its
        items CSV, and so BOM/batch/serial flags come from the Item master itself.
        """
        cfg = self.ctx.industry_config
        opening = cfg.seed.opening_stock

        script = f"""
import json
import erpnext

company = '''{company}'''
abbr = '''{abbr}'''


def resolve_warehouse(candidates):
    for name in candidates:
        if not name:
            continue
        full = name if name.endswith(' - ' + abbr) else name + ' - ' + abbr
        found = frappe.db.get_value(
            'Warehouse', {{'name': full, 'company': company, 'is_group': 0}}, 'name'
        )
        if found:
            return found
    return None


any_warehouse = frappe.get_all(
    'Warehouse',
    filters={{'company': company, 'is_group': 0}},
    order_by='name',
    limit=1,
    pluck='name',
)
any_warehouse = any_warehouse[0] if any_warehouse else None
rm_warehouse = resolve_warehouse(['''{opening.warehouse}''', 'Stores']) or any_warehouse
fg_warehouse = resolve_warehouse(['''{opening.fg_warehouse}''', 'Finished Goods']) or rm_warehouse

# An opening entry debits stock against a Balance Sheet account; ERPNext raises
# OpeningEntryAccountError on a Profit and Loss one, which the default
# 'Stock Adjustment' account usually is.
expense_account = frappe.db.get_value(
    'Account', {{'account_name': 'Temporary Opening', 'company': company, 'is_group': 0}}, 'name'
)
if not expense_account:
    candidate = frappe.get_cached_value('Company', company, 'stock_adjustment_account')
    if candidate and frappe.db.get_value('Account', candidate, 'report_type') != 'Profit and Loss':
        expense_account = candidate

manufactured = set(
    frappe.get_all(
        'BOM', filters={{'is_active': 1, 'is_default': 1, 'docstatus': 1}}, pluck='item'
    )
)
already_stocked = set(
    frappe.get_all(
        'Stock Ledger Entry',
        filters={{'is_cancelled': 0, 'company': company}},
        distinct=True,
        pluck='item_code',
    )
)

items = []
for row in frappe.get_all(
    'Item',
    filters={{'is_stock_item': 1, 'disabled': 0, 'has_variants': 0, 'is_fixed_asset': 0}},
    fields=[
        'name', 'stock_uom', 'valuation_rate', 'last_purchase_rate',
        'standard_rate', 'has_batch_no', 'has_serial_no',
    ],
    order_by='name',
):
    if row.name in already_stocked:
        continue
    items.append({{
        'item_code': row.name,
        'stock_uom': row.stock_uom,
        'rate': float(row.valuation_rate or row.last_purchase_rate or row.standard_rate or 0),
        'has_batch_no': int(row.has_batch_no or 0),
        'has_serial_no': int(row.has_serial_no or 0),
        'is_finished_good': row.name in manufactured,
    }})

print('{_PAYLOAD_MARKER}' + json.dumps({{
    'company': company,
    'rm_warehouse': rm_warehouse,
    'fg_warehouse': fg_warehouse,
    'expense_account': expense_account,
    'cost_center': frappe.get_cached_value('Company', company, 'cost_center'),
    'perpetual': int(erpnext.is_perpetual_inventory_enabled(company)),
    'items': items,
}}))
"""
        return self._extract_payload(self._exec(script, timeout=180))

    def _build_documents(
        self, plan: dict[str, Any], company_scale: float = 1.0
    ) -> list[dict[str, Any]]:
        """Group priced opening rows into one document per warehouse.

        One Stock Reconciliation could hold every warehouse at once, but splitting
        keeps a failure in one warehouse from taking the rest of the opening
        balance down with it, and reads better in the demo's document list.

        `company_scale` layers the posting company's own
        `CompanyConfig.opening_stock_qty_scale` on top of the industry-wide
        `seed.opening_stock.qty_scale`, so a smaller subsidiary in a multi-company
        group opens with visibly less stock than the parent.
        """
        rng = self.ctx.random
        scale = self.ctx.industry_config.seed.opening_stock.qty_scale * company_scale
        by_warehouse: dict[str, list[dict[str, Any]]] = {}

        for item in plan["items"]:
            warehouse = plan["fg_warehouse"] if item["is_finished_good"] else plan["rm_warehouse"]
            rate = item["rate"] or _FALLBACK_RATE
            qty = opening_stock_qty(
                rate, rng, is_finished_good=item["is_finished_good"], scale=scale
            )

            row: dict[str, Any] = {
                "item_code": item["item_code"],
                "qty": qty,
                "valuation_rate": round(rate, 2),
            }
            if item["has_serial_no"]:
                row["qty"] = qty = min(qty, _MAX_SERIAL_QTY)
                row["serial_nos"] = [f"{item['item_code']}-OPEN-{n:04d}" for n in range(1, qty + 1)]
            elif item["has_batch_no"]:
                row["batch_no"] = f"{item['item_code']}-OPEN"

            by_warehouse.setdefault(warehouse, []).append(row)

        return [{"warehouse": warehouse, "items": rows} for warehouse, rows in by_warehouse.items()]

    # ── Posting ───────────────────────────────────────────────────────────────

    def _post(self, payload: dict[str, Any]) -> None:
        payload_json = json.dumps(payload)
        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']
created = failed = 0

for doc in payload['documents']:
    try:
        # Tracked items need their Batch / Serial No masters to exist before the
        # reconciliation references them: the seeded Item masters carry no
        # batch or serial naming series, so ERPNext cannot mint them itself.
        for row in doc['items']:
            if row.get('batch_no') and not frappe.db.exists('Batch', row['batch_no']):
                frappe.get_doc({{
                    'doctype': 'Batch',
                    'batch_id': row['batch_no'],
                    'item': row['item_code'],
                }}).insert(ignore_permissions=True)
            for serial_no in row.get('serial_nos') or []:
                if not frappe.db.exists('Serial No', serial_no):
                    frappe.get_doc({{
                        'doctype': 'Serial No',
                        'serial_no': serial_no,
                        'item_code': row['item_code'],
                        'company': company,
                    }}).insert(ignore_permissions=True)

        sr = frappe.get_doc({{
            'doctype': 'Stock Reconciliation',
            'company': company,
            'purpose': 'Opening Stock',
            'set_posting_time': 1,
            'posting_date': payload['posting_date'],
            'posting_time': '00:00:00',
            'expense_account': payload['expense_account'],
            'cost_center': payload['cost_center'],
            'items': [
                {{
                    'item_code': row['item_code'],
                    'warehouse': doc['warehouse'],
                    'qty': row['qty'],
                    'valuation_rate': row['valuation_rate'],
                    'use_serial_batch_fields': 1 if (row.get('batch_no') or row.get('serial_nos')) else 0,
                    'batch_no': row.get('batch_no'),
                    'serial_no': '\\n'.join(row.get('serial_nos') or []) or None,
                }}
                for row in doc['items']
            ],
        }})
        sr.insert(ignore_permissions=True)
        sr.submit()
        created += 1
        print(f"CREATED: {{sr.name}} — {{len(sr.items)}} item(s) in {{doc['warehouse']}}")
    except Exception as e:
        failed += 1
        print(f"WARN Opening Stock ({{doc['warehouse']}}): {{e}}")

frappe.db.commit()
print(f'Opening Stock: documents={{created}}, failed={{failed}}')
"""
        self._exec(script, timeout=600)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_payload(output: str) -> dict[str, Any]:
        for line in output.splitlines():
            if line.startswith(_PAYLOAD_MARKER):
                return json.loads(line[len(_PAYLOAD_MARKER) :])
        raise RuntimeError(
            f"Opening stock plan not found in seeder output (missing {_PAYLOAD_MARKER!r})"
        )
