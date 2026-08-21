"""
Shared Asset seeder bases for every industry.

Each industry supplies only ``ASSET_CATEGORIES`` / ``ASSETS`` in its
``01_master/14_assets.py``; this module carries the Frappe scripts and run
logic, the same split ``payroll_seeder.py`` and ``project_seeders.py`` use.

Two seeders, in order:

* ``AssetCategorySeeder`` — one ledger account per category (find-or-create,
  never assumes the Standard CoA's exact shape) plus a shared Accumulated
  Depreciation / Depreciation account pair reused across categories.
* ``AssetSeeder`` — one non-stock ``is_fixed_asset`` Item per category, then
  one submitted ``Asset`` per entry, existing-asset with a Straight Line
  finance book. ``depreciation_start_date`` is deliberately left unset —
  ``Asset.validate_asset_finance_books`` defaults it to the last day of
  ``available_for_use_date``'s month, which is exactly ERPNext's own
  convention and avoids duplicating that math here.

The Asset Maintenance follow-on (Asset Maintenance Team/Task/Log) needs no
per-industry data at all, so it is not a base class here — it lives directly
in ``demostackkit/seeders/01_master/90_asset_maintenance.py`` and auto-runs
for every industry that seeded maintenance-required Assets.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from demostackkit.seeder.base import BaseMasterSeeder
from demostackkit.seeder.utils import fiscal_year_windows


class AssetCategorySeeder(BaseMasterSeeder):
    """Asset Categories, each wired to a Fixed Asset ledger account."""

    label = "Asset Categories"
    priority = 14

    #: ``["Reactor", "Delivery Truck", ...]`` — set by the industry subclass.
    ASSET_CATEGORIES: list[str] = []

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Assets" not in cfg.modules or not self.ASSET_CATEGORIES:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        payload = {"company": company, "categories": self.ASSET_CATEGORIES}
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']

if not frappe.db.exists('DocType', 'Asset Category'):
    print('Assets: the Assets module is not available on this site, nothing to seed')
    raise SystemExit(0)


def find_or_create_group(account_name, root_type):
    existing = frappe.db.get_value(
        'Account', {{'company': company, 'account_name': account_name, 'is_group': 1}}, 'name'
    )
    if existing:
        return existing
    root = frappe.db.get_value(
        'Account',
        {{'company': company, 'root_type': root_type, 'is_group': 1, 'parent_account': ('is', 'not set')}},
        'name',
    )
    return frappe.get_doc({{
        'doctype': 'Account',
        'account_name': account_name,
        'company': company,
        'parent_account': root,
        'is_group': 1,
        'root_type': root_type,
    }}).insert(ignore_permissions=True).name


def find_or_create_ledger(account_name, account_type, parent, root_type):
    existing = frappe.db.get_value(
        'Account', {{'company': company, 'account_name': account_name, 'is_group': 0}}, 'name'
    )
    if existing:
        return existing
    return frappe.get_doc({{
        'doctype': 'Account',
        'account_name': account_name,
        'company': company,
        'parent_account': parent,
        'is_group': 0,
        'account_type': account_type,
        'root_type': root_type,
    }}).insert(ignore_permissions=True).name


# Reuse an existing ledger of the right type before creating a new one — the
# Standard CoA already carries an Accumulated Depreciation and a Depreciation
# ledger for most templates, and creating a second one would just orphan it.
accum_dep_account = frappe.db.get_value(
    'Account', {{'company': company, 'account_type': 'Accumulated Depreciation'}}, 'name'
)
dep_expense_account = frappe.db.get_value(
    'Account', {{'company': company, 'account_type': 'Depreciation'}}, 'name'
)
fixed_assets_group = find_or_create_group('Fixed Assets', 'Asset')

if not accum_dep_account:
    accum_dep_account = find_or_create_ledger(
        'Accumulated Depreciation', 'Accumulated Depreciation', fixed_assets_group, 'Asset'
    )
if not dep_expense_account:
    expense_group = frappe.db.get_value(
        'Account', {{'company': company, 'account_name': 'Indirect Expenses', 'is_group': 1}}, 'name'
    ) or find_or_create_group('Indirect Expenses', 'Expense')
    dep_expense_account = find_or_create_ledger(
        'Depreciation', 'Depreciation', expense_group, 'Expense'
    )

created = skipped = 0
for category in payload['categories']:
    if frappe.db.exists('Asset Category', category):
        skipped += 1
        continue
    fixed_asset_account = find_or_create_ledger(category, 'Fixed Asset', fixed_assets_group, 'Asset')
    frappe.get_doc({{
        'doctype': 'Asset Category',
        'asset_category_name': category,
        'accounts': [{{
            'company_name': company,
            'fixed_asset_account': fixed_asset_account,
            'accumulated_depreciation_account': accum_dep_account,
            'depreciation_expense_account': dep_expense_account,
        }}],
    }}).insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Asset Categories: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=180)
        self.ctx.cache_set("asset_category_names", list(self.ASSET_CATEGORIES))


class AssetSeeder(BaseMasterSeeder):
    """Fixed Asset Items and submitted Asset records."""

    label = "Assets"
    priority = 15

    #: ``[{"asset_name": ..., "category": ..., "location": ..., "gross_purchase_amount": ...,
    #:   "purchase_days_ago": 730, "useful_life_years": 5, "maintenance_required": True}, ...]``
    ASSETS: list[dict[str, Any]] = []

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Assets" not in cfg.modules or not self.ASSETS:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        today = date.today()

        assets = []
        for entry in self.ASSETS:
            purchase_date = today - timedelta(days=entry.get("purchase_days_ago", 730))
            useful_life_years = entry.get("useful_life_years", 5)
            assets.append(
                {
                    "asset_name": entry["asset_name"],
                    "category": entry["category"],
                    "location": entry.get("location", "Head Office"),
                    "purchase_date": purchase_date.isoformat(),
                    "available_for_use_date": purchase_date.isoformat(),
                    "gross_purchase_amount": entry["gross_purchase_amount"],
                    "total_number_of_depreciations": max(useful_life_years, 1) * 12,
                    "maintenance_required": bool(entry.get("maintenance_required", True)),
                }
            )

        categories = sorted({a["category"] for a in assets})

        # FiscalYearSeeder only covers back to roughly seed.date_range.start —
        # an asset purchased before that has no active Fiscal Year and
        # Asset.insert() throws. Ensure coverage back to the oldest purchase
        # date ourselves rather than guessing a "safe" purchase_days_ago per
        # industry (their date_range and fiscal_year_start both vary).
        earliest_purchase = min(date.fromisoformat(a["purchase_date"]) for a in assets)
        fy_windows = [
            {"year": label, "start": start.isoformat(), "end": end.isoformat()}
            for label, start, end in fiscal_year_windows(
                cfg.company.fiscal_year_start, earliest_purchase, today
            )
        ]

        payload = {
            "company": company,
            "categories": categories,
            "assets": assets,
            "fiscal_years": fy_windows,
        }
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']

if not frappe.db.exists('DocType', 'Asset'):
    print('Assets: the Assets module is not available on this site, nothing to seed')
    raise SystemExit(0)

fy_created = fy_skipped = 0
for w in payload['fiscal_years']:
    existing = frappe.db.sql(
        "select name from `tabFiscal Year` where year_start_date <= %s and year_end_date >= %s",
        (w['end'], w['start']),
    )
    if existing:
        fy_skipped += 1
        continue
    frappe.get_doc({{
        'doctype': 'Fiscal Year',
        'year': w['year'],
        'year_start_date': w['start'],
        'year_end_date': w['end'],
    }}).insert(ignore_permissions=True)
    fy_created += 1
frappe.db.commit()
print(f'Fiscal Years (for Assets): created={{fy_created}}, skipped={{fy_skipped}}')

if not frappe.db.exists('UOM', 'Nos'):
    frappe.get_doc({{'doctype': 'UOM', 'uom_name': 'Nos'}}).insert(ignore_permissions=True)

if not frappe.db.exists('Item Group', 'Fixed Assets'):
    frappe.get_doc({{
        'doctype': 'Item Group',
        'item_group_name': 'Fixed Assets',
        'parent_item_group': 'All Item Groups',
        'is_group': 0,
    }}).insert(ignore_permissions=True)

item_by_category = {{}}
for category in payload['categories']:
    item_code = f'AST-{{category}}'
    if not frappe.db.exists('Item', item_code):
        frappe.get_doc({{
            'doctype': 'Item',
            'item_code': item_code,
            'item_name': category,
            'item_group': 'Fixed Assets',
            'stock_uom': 'Nos',
            'is_stock_item': 0,
            'is_fixed_asset': 1,
            'asset_category': category,
        }}).insert(ignore_permissions=True)
    item_by_category[category] = item_code

locations = {{a['location'] for a in payload['assets']}}
for location_name in locations:
    if not frappe.db.exists('Location', location_name):
        frappe.get_doc({{'doctype': 'Location', 'location_name': location_name}}).insert(
            ignore_permissions=True
        )

# Committed before the Asset loop below: a failed Asset insert rolls back,
# and without this commit that rollback would also wipe out the Items and
# Locations just created above, cascading into every subsequent asset.
frappe.db.commit()

created = skipped = errors = 0
for a in payload['assets']:
    if frappe.db.exists('Asset', {{'asset_name': a['asset_name'], 'company': company}}):
        skipped += 1
        continue
    try:
        doc = frappe.get_doc({{
            'doctype': 'Asset',
            'asset_name': a['asset_name'],
            'item_code': item_by_category[a['category']],
            'asset_category': a['category'],
            'company': company,
            'location': a['location'],
            'purchase_date': a['purchase_date'],
            'available_for_use_date': a['available_for_use_date'],
            'gross_purchase_amount': a['gross_purchase_amount'],
            'asset_quantity': 1,
            'is_existing_asset': 1,
            'calculate_depreciation': 1,
            'maintenance_required': 1 if a['maintenance_required'] else 0,
            'finance_books': [{{
                'depreciation_method': 'Straight Line',
                'total_number_of_depreciations': a['total_number_of_depreciations'],
                'frequency_of_depreciation': 1,
                'expected_value_after_useful_life': 0,
            }}],
        }})
        doc.insert(ignore_permissions=True)
        doc.submit()
        frappe.db.commit()
        created += 1
        print(f"CREATED: Asset {{doc.name}} — {{a['asset_name']}}")
    except Exception as ex:
        frappe.db.rollback()
        print(f"ERROR Asset {{a['asset_name']}}: {{ex}}")
        errors += 1

frappe.db.commit()
print(f'Assets: created={{created}}, skipped={{skipped}}, errors={{errors}}')
if errors:
    raise SystemExit(f'{{errors}} asset(s) failed')
"""
        self._exec(script, timeout=300)
        self.ctx.cache_set(
            "asset_names",
            [a["asset_name"] for a in assets if a["maintenance_required"]],
        )
