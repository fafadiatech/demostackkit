"""
Shared seeder: Production Plans, Work Orders and Job Cards (ref #40).

BOM / Routing / Workstation / Operation masters are already seeded for every
Manufacturing industry, but nothing ever *runs* that shop floor — Production
Analytics and Production Plan Summary stay empty because there are no
Production Plans, Work Orders or Job Cards.

This seeder builds that execution layer for every industry carrying the
Manufacturing module and a non-zero `seed.volumes.production_orders`:

    1. Discovers finished goods that already have a submitted default BOM with
       at least one BOM Operation (so Job Cards will actually be created on
       Work Order submit), preferring top-level FGs over sub-assemblies.
    2. Groups them into submitted Production Plans (optionally linking a live
       Sales Order line when one exists for the item), then calls ERPNext's
       own `Production Plan.make_work_order()` — the same path the UI's
       "Work Order" button uses.
    3. Walks the resulting Work Orders with a deliberate status mix so the
       reports show a live shop floor, not a completed archive:

           completed     — material transfer + every Job Card timed & submitted
                           + Manufacture stock entry
           in_progress   — material transfer + the first half of Job Cards done
           not_started   — Work Order submitted only (Job Cards stay Open)

Job Card time logs carry an Employee (when the industry seeded one) and a
realistic time band around the operation's planned minutes, so Production
Analytics has operation-level throughput / efficiency to chart.

Skipped entirely when Manufacturing is not in `modules`, when
`production_orders` is 0 (trading-only demos), or when the company has no
operation-backed BOM yet. Not idempotent — `demostackkit reset` recreates
the site.

Priority 215 — after Sales Orders (210) so Production Plan rows can link a
real SO line, ahead of Delivery Notes (220).
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import ITEM_ROW_HELPERS, parse_relative_date

_PLAN_MARKER = "DSK_PRODUCTION_PLAN::"
_PAYLOAD_MARKER = "DSK_PRODUCTION::"

#: Status mix across Work Orders. Must sum to 1.
_STATUS_WEIGHTS: dict[str, float] = {
    "completed": 0.40,
    "in_progress": 0.35,
    "not_started": 0.25,
}

#: How many FG lines to put on each Production Plan.
_ITEMS_PER_PLAN_MIN, _ITEMS_PER_PLAN_MAX = 2, 3

#: Planned manufacturing qty band (aligned to BOM whole-number multiples later).
_QTY_MIN, _QTY_MAX = 1, 5

#: Job Card actual time as a fraction of the operation's planned minutes —
#: under / on / over so Efficiency charts aren't a flat 100%.
_TIME_FACTOR_MIN, _TIME_FACTOR_MAX = 0.75, 1.35


class ProductionSeeder(BaseTransactionSeeder):
    label = "Production Plans & Work Orders"
    priority = 215
    _volume_attr = "production_orders"
    default_volume = 25

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Manufacturing" not in cfg.modules:
            return
        if self.volume <= 0:
            return

        default_company = self.ctx.cache_get("company_name", cfg.company.name)
        default_abbr = self.ctx.cache_get("company_abbr", cfg.company.abbr)
        companies = self.ctx.cache_get(
            "all_companies", [{"name": default_company, "abbr": default_abbr}]
        )

        opening = cfg.seed.opening_stock
        plan = self._fetch_plan(
            companies,
            fg_preferred=[opening.fg_warehouse, "Finished Goods", "Finished Goods Store"],
            wip_preferred=["Work In Progress", "WIP - Coil Winding", "WIP - Core Assembly"],
            source_preferred=[opening.warehouse, "Stores", "Raw Material Store"],
        )
        if not plan.get("companies"):
            return

        jobs = self._build_jobs(plan)
        if not jobs:
            return
        self._submit(jobs)

    # ── Planning ──────────────────────────────────────────────────────────────

    def _build_jobs(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        rng = self.ctx.random
        date_cfg = self.ctx.industry_config.seed.date_range
        start_date = parse_relative_date(date_cfg.start)
        end_date = parse_relative_date(date_cfg.end)
        span = max((end_date - start_date).days, 0)

        company_plans = plan["companies"]
        # Round-robin companies that actually have manufacturable items.
        active = [c for c in company_plans if c.get("items")]
        if not active:
            return []

        remaining = self.volume
        jobs: list[dict[str, Any]] = []
        company_idx = 0

        while remaining > 0:
            company = active[company_idx % len(active)]
            company_idx += 1

            items_info = company["items"]
            n_items = min(
                remaining,
                rng.randint(_ITEMS_PER_PLAN_MIN, _ITEMS_PER_PLAN_MAX),
                len(items_info),
            )
            chosen = rng.sample(items_info, n_items)
            posting_date = start_date + timedelta(days=rng.randint(0, span))

            rows = []
            for item in chosen:
                status = rng.choices(
                    list(_STATUS_WEIGHTS.keys()),
                    weights=list(_STATUS_WEIGHTS.values()),
                    k=1,
                )[0]
                qty = rng.randint(_QTY_MIN, _QTY_MAX)
                planned_start = posting_date + timedelta(days=rng.randint(0, 7))
                so = self._pick_sales_order(company.get("sales_orders", {}), item["item_code"], rng)

                rows.append(
                    {
                        "item_code": item["item_code"],
                        "bom_no": item["bom_no"],
                        "stock_uom": item["stock_uom"],
                        "qty": qty,
                        "warehouse": company["fg_warehouse"],
                        "planned_start_date": planned_start.isoformat(),
                        "sales_order": so["sales_order"] if so else None,
                        "sales_order_item": so["sales_order_item"] if so else None,
                        "status": status,
                    }
                )

            jobs.append(
                {
                    "company": company["name"],
                    "abbr": company["abbr"],
                    "posting_date": posting_date.isoformat(),
                    "wip_warehouse": company["wip_warehouse"],
                    "fg_warehouse": company["fg_warehouse"],
                    "scrap_warehouse": company["scrap_warehouse"],
                    "source_warehouse": company["source_warehouse"],
                    "employees": company.get("employees", []),
                    "items": rows,
                }
            )
            remaining -= n_items

        return jobs

    @staticmethod
    def _pick_sales_order(
        so_by_item: dict[str, list[dict[str, str]]],
        item_code: str,
        rng: Any,
    ) -> dict[str, str] | None:
        options = so_by_item.get(item_code) or []
        if not options:
            return None
        return rng.choice(options)

    def _fetch_plan(
        self,
        companies: list[dict[str, str]],
        *,
        fg_preferred: list[str],
        wip_preferred: list[str],
        source_preferred: list[str],
    ) -> dict[str, Any]:
        payload = {
            "companies": companies,
            "fg_preferred": fg_preferred,
            "wip_preferred": wip_preferred,
            "source_preferred": source_preferred,
        }
        payload_json = json.dumps(payload)
        script = f"""
import json
from collections import defaultdict

payload = json.loads('''{payload_json}''')

def pick_warehouse(company, abbr, preferred, fuzzy_tokens=None):
    for name in preferred:
        if not name:
            continue
        full = f'{{name}} - {{abbr}}'
        if frappe.db.exists('Warehouse', {{'name': full, 'company': company, 'is_group': 0}}):
            return full
    if fuzzy_tokens:
        rows = frappe.get_all(
            'Warehouse',
            filters={{'company': company, 'is_group': 0}},
            fields=['name', 'warehouse_name'],
        )
        for token in fuzzy_tokens:
            token_l = token.lower()
            for row in rows:
                if token_l in (row.warehouse_name or '').lower() or token_l in row.name.lower():
                    return row.name
    return frappe.db.get_value(
        'Warehouse', {{'company': company, 'is_group': 0}}, 'name', order_by='creation asc'
    )

result = {{'companies': []}}
for c in payload['companies']:
    company = c['name']
    abbr = c['abbr']

    bom_rows = frappe.get_all(
        'BOM',
        filters={{
            'docstatus': 1,
            'is_active': 1,
            'is_default': 1,
            'company': company,
        }},
        fields=['name', 'item', 'quantity'],
        order_by='creation asc',
    )
    if not bom_rows:
        continue

    # Prefer top-level finished goods (not consumed as a component elsewhere)
    # so Production Plans look like real FG demand, not sub-assembly churn.
    bom_names = [b.name for b in bom_rows]
    components = {{
        row.item_code
        for row in frappe.get_all(
            'BOM Item',
            filters={{'parent': ['in', bom_names]}},
            fields=['item_code'],
        )
    }}
    with_ops = set(
        frappe.db.sql_list(
            'select distinct parent from `tabBOM Operation` where parent in %(parents)s',
            {{'parents': bom_names}},
        )
        or []
    )

    candidates = [b for b in bom_rows if b.name in with_ops and b.item not in components]
    if not candidates:
        candidates = [b for b in bom_rows if b.name in with_ops]
    if not candidates:
        continue

    item_codes = [b.item for b in candidates]
    uom_map = {{
        row.name: row.stock_uom or 'Nos'
        for row in frappe.get_all(
            'Item', filters={{'name': ['in', item_codes]}}, fields=['name', 'stock_uom']
        )
    }}

    so_by_item = defaultdict(list)
    if item_codes:
        so_rows = frappe.db.sql(
            '''
            select soi.parent as sales_order, soi.name as sales_order_item,
                   soi.item_code
            from `tabSales Order Item` soi
            inner join `tabSales Order` so on so.name = soi.parent
            where so.docstatus = 1
              and so.company = %s
              and soi.item_code in ({{placeholders}})
            order by so.transaction_date desc
            '''.format(placeholders=', '.join(['%s'] * len(item_codes))),
            tuple([company, *item_codes]),
            as_dict=True,
        )
        for row in so_rows:
            # Cap per item so the payload stays small; pick happens host-side.
            bucket = so_by_item[row.item_code]
            if len(bucket) < 8:
                bucket.append({{
                    'sales_order': row.sales_order,
                    'sales_order_item': row.sales_order_item,
                }})

    employees = frappe.get_all(
        'Employee',
        filters={{'company': company, 'status': 'Active'}},
        pluck='name',
        limit_page_length=40,
    )

    result['companies'].append({{
        'name': company,
        'abbr': abbr,
        'fg_warehouse': pick_warehouse(
            company, abbr, payload['fg_preferred'], fuzzy_tokens=['finished']
        ),
        'wip_warehouse': pick_warehouse(
            company, abbr, payload['wip_preferred'], fuzzy_tokens=['wip', 'work in']
        ),
        'scrap_warehouse': pick_warehouse(
            company, abbr, ['Scrap'], fuzzy_tokens=['scrap']
        ),
        'source_warehouse': pick_warehouse(
            company, abbr, payload['source_preferred'],
            fuzzy_tokens=['stores', 'raw'],
        ),
        'employees': employees,
        'items': [
            {{
                'item_code': b.item,
                'bom_no': b.name,
                'stock_uom': uom_map.get(b.item, 'Nos'),
                'bom_qty': float(b.quantity or 1),
            }}
            for b in candidates
        ],
        'sales_orders': dict(so_by_item),
    }})

print('{_PLAN_MARKER}' + json.dumps(result))
"""
        stdout = self._exec(script, timeout=180)
        for line in stdout.splitlines():
            if line.startswith(_PLAN_MARKER):
                return json.loads(line[len(_PLAN_MARKER) :])
        return {"companies": []}

    # ── Submit ────────────────────────────────────────────────────────────────

    def _submit(self, jobs: list[dict[str, Any]]) -> None:
        payload_json = json.dumps({"jobs": jobs})
        script = f"""
import json
from datetime import datetime, timedelta

from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

{ITEM_ROW_HELPERS}

payload = json.loads('''{payload_json}''')
jobs = payload['jobs']

# Widen over-production allowance so seeded WOs against SO-linked plans never
# trip OverProductionError when opening stock / prior WOs already cover demand.
ms = frappe.get_single('Manufacturing Settings')
if hasattr(ms, 'over_production_allowance_percentage'):
    ms.over_production_allowance_percentage = max(
        float(ms.over_production_allowance_percentage or 0), 100
    )
if hasattr(ms, 'enforce_time_logs'):
    ms.enforce_time_logs = 0
ms.flags.ignore_permissions = True
ms.save(ignore_permissions=True)

def best_source_warehouse(item_code, company, fallback):
    bins = frappe.get_all(
        'Bin',
        filters={{'item_code': item_code, 'actual_qty': ['>', 0]}},
        fields=['warehouse', 'actual_qty'],
        order_by='actual_qty desc',
        limit_page_length=20,
    )
    for b in bins:
        wh_company = frappe.db.get_value('Warehouse', b.warehouse, 'company')
        if wh_company == company and not frappe.db.get_value('Warehouse', b.warehouse, 'is_group'):
            return b.warehouse
    return fallback

def ensure_settings_warehouses(wip, fg, scrap):
    ms_doc = frappe.get_single('Manufacturing Settings')
    dirty = False
    if wip and not ms_doc.default_wip_warehouse:
        ms_doc.default_wip_warehouse = wip
        dirty = True
    if fg and not ms_doc.default_fg_warehouse:
        ms_doc.default_fg_warehouse = fg
        dirty = True
    if scrap and not ms_doc.default_scrap_warehouse:
        ms_doc.default_scrap_warehouse = scrap
        dirty = True
    if dirty:
        ms_doc.flags.ignore_permissions = True
        ms_doc.save(ignore_permissions=True)

def complete_job_cards(wo_name, employees, planned_start, complete_count=None):
    cards = frappe.get_all(
        'Job Card',
        filters={{'work_order': wo_name, 'docstatus': 0}},
        fields=['name', 'for_quantity', 'operation'],
        order_by='creation asc',
    )
    if complete_count is not None:
        cards = cards[: max(0, complete_count)]

    start = datetime.fromisoformat(planned_start)
    employee = employees[0] if employees else None
    completed = 0
    for idx, card_row in enumerate(cards):
        try:
            jc = frappe.get_doc('Job Card', card_row.name)
            qty = float(jc.for_quantity or 0) or 1.0
            # Stagger successive operations so sequence_id validation passes
            # and Production Analytics has a realistic timeline.
            op_start = start + timedelta(hours=idx * 4)
            planned_mins = 30.0
            for op in frappe.get_all(
                'Work Order Operation',
                filters={{'parent': wo_name, 'operation': jc.operation}},
                fields=['time_in_mins'],
                limit_page_length=1,
            ):
                planned_mins = float(op.time_in_mins or 30) or 30.0
            # Deterministic-ish factor from operation index so efficiency varies
            # without needing host-side RNG inside the container.
            factor = {_TIME_FACTOR_MIN} + ((idx * 17) % 61) / 100.0 * ({_TIME_FACTOR_MAX} - {_TIME_FACTOR_MIN})
            actual_mins = max(5.0, planned_mins * factor)
            op_end = op_start + timedelta(minutes=actual_mins)

            jc.set('time_logs', [])
            log = {{
                'from_time': op_start.strftime('%Y-%m-%d %H:%M:%S'),
                'to_time': op_end.strftime('%Y-%m-%d %H:%M:%S'),
                'time_in_mins': actual_mins,
                'completed_qty': qty,
            }}
            if employee:
                log['employee'] = employee
            jc.append('time_logs', log)
            if employee and hasattr(jc, 'employee'):
                # Job Card also has an Employee multi-select child in some versions.
                try:
                    jc.set('employee', [])
                    jc.append('employee', {{'employee': employee, 'completed_qty': qty}})
                except Exception:
                    pass
            jc.flags.ignore_permissions = True
            jc.save(ignore_permissions=True)
            jc.submit()
            completed += 1
        except Exception as e:
            print(f'WARN Job Card {{card_row.name}} on {{wo_name}}: {{e}}')
    return completed

def apply_stock_entry(wo_name, purpose, qty, posting_date):
    se_dict = make_stock_entry(wo_name, purpose, qty=qty)
    se = frappe.get_doc(se_dict)
    se.set_posting_time = 1
    se.posting_date = posting_date
    se.flags.ignore_permissions = True
    se.insert(ignore_permissions=True)
    se.submit()
    return se.name

plans_created = wo_created = jc_completed = transfers = manufactures = errors = 0

for job in jobs:
    company = job['company']
    ensure_settings_warehouses(job['wip_warehouse'], job['fg_warehouse'], job['scrap_warehouse'])

    try:
        po_items = []
        status_by_item = {{}}
        for row in job['items']:
            qty = dsk_align_qty(row['item_code'], row['qty'])
            status_by_item[row['item_code']] = row['status']
            entry = {{
                'item_code': row['item_code'],
                'bom_no': row['bom_no'],
                'planned_qty': qty,
                'stock_uom': row['stock_uom'],
                'warehouse': row['warehouse'] or job['fg_warehouse'],
                'planned_start_date': row['planned_start_date'],
            }}
            if row.get('sales_order'):
                entry['sales_order'] = row['sales_order']
            if row.get('sales_order_item'):
                entry['sales_order_item'] = row['sales_order_item']
            po_items.append(entry)

        pp = frappe.get_doc({{
            'doctype': 'Production Plan',
            'company': company,
            'posting_date': job['posting_date'],
            'for_warehouse': job['source_warehouse'],
            'ignore_existing_ordered_qty': 1,
            'po_items': po_items,
        }})
        pp.flags.ignore_permissions = True
        pp.insert(ignore_permissions=True)
        pp.submit()
        plans_created += 1

        # Create Work Orders the same way the Production Plan UI button does.
        pp.reload()
        pp.make_work_order()

        work_orders = frappe.get_all(
            'Work Order',
            filters={{'production_plan': pp.name, 'docstatus': 0}},
            fields=['name', 'production_item', 'qty', 'planned_start_date'],
        )
        # Also catch WOs that make_work_order already submitted in some versions.
        if not work_orders:
            work_orders = frappe.get_all(
                'Work Order',
                filters={{'production_plan': pp.name}},
                fields=['name', 'production_item', 'qty', 'planned_start_date', 'docstatus'],
            )

        for wo_row in work_orders:
            try:
                wo = frappe.get_doc('Work Order', wo_row.name)
                status = status_by_item.get(wo.production_item, 'not_started')

                if not wo.wip_warehouse:
                    wo.wip_warehouse = job['wip_warehouse']
                if not wo.fg_warehouse:
                    wo.fg_warehouse = job['fg_warehouse']
                if not wo.scrap_warehouse:
                    wo.scrap_warehouse = job['scrap_warehouse']
                wo.transfer_material_against = 'Work Order'
                wo.use_multi_level_bom = 1

                for req in wo.required_items:
                    req.source_warehouse = best_source_warehouse(
                        req.item_code, company, job['source_warehouse']
                    )

                if wo.docstatus == 0:
                    wo.flags.ignore_permissions = True
                    wo.flags.ignore_mandatory = True
                    wo.save(ignore_permissions=True)
                    wo.submit()
                wo_created += 1

                planned_start = str(wo.planned_start_date or job['posting_date'])[:19]
                if ' ' not in planned_start:
                    planned_start = planned_start + ' 09:00:00'

                if status == 'not_started':
                    continue

                # Transfer materials into WIP before completing any Job Cards.
                try:
                    apply_stock_entry(
                        wo.name,
                        'Material Transfer for Manufacture',
                        float(wo.qty),
                        job['posting_date'],
                    )
                    transfers += 1
                except Exception as e:
                    print(f'WARN Transfer {{wo.name}}: {{e}}')
                    # Still try Job Cards — transfer_material_against=Work Order
                    # means Job Cards themselves don't require transferred qty.

                ops_count = len(frappe.get_all('Job Card', filters={{'work_order': wo.name}}))
                if status == 'in_progress':
                    done = complete_job_cards(
                        wo.name,
                        job.get('employees') or [],
                        planned_start,
                        complete_count=max(1, ops_count // 2),
                    )
                    jc_completed += done
                    continue

                # completed
                done = complete_job_cards(
                    wo.name, job.get('employees') or [], planned_start, complete_count=None
                )
                jc_completed += done
                try:
                    apply_stock_entry(
                        wo.name, 'Manufacture', float(wo.qty), job['posting_date']
                    )
                    manufactures += 1
                except Exception as e:
                    print(f'WARN Manufacture {{wo.name}}: {{e}}')
            except Exception as e:
                print(f'WARN Work Order {{wo_row.name}}: {{e}}')
                errors += 1
    except Exception as e:
        print(f'WARN Production Plan for {{company}}: {{e}}')
        errors += 1

frappe.db.commit()
print(
    '{_PAYLOAD_MARKER}'
    + json.dumps({{
        'production_plans': plans_created,
        'work_orders': wo_created,
        'job_cards_completed': jc_completed,
        'transfers': transfers,
        'manufactures': manufactures,
        'errors': errors,
    }})
)
print(
    f'Production: plans={{plans_created}}, work_orders={{wo_created}}, '
    f'job_cards={{jc_completed}}, transfers={{transfers}}, '
    f'manufactures={{manufactures}}, errors={{errors}}'
)
"""
        self._exec(script, timeout=600)
