"""
Shared seeder: Subcontracting master data (ref #32).

ERPNext v15's Subcontracting module (Item → Purchase Order → Subcontracting
Order → Subcontracting Receipt) has nothing to demo out of the box: no
subcontractor Supplier Group, no Supplier flagged for it, nowhere to reserve
the vendor's stock, and no non-stock Service Item to put on a subcontracted
Purchase Order line (the new-flow PO item row's `item_code` is the *service*
being bought, not the finished good — `fg_item` carries the finished good).
This seeder builds that scaffold so `205_subcontracting_orders.py` has
something to work with:

    1. Flags a handful of BOM-backed finished goods as
       `is_sub_contracted_item` (Item's "Supply Raw Materials for Purchase"
       checkbox) — candidates are whatever already has a submitted, active,
       default BOM, so this never invents manufacturing data of its own.
    2. Creates the "Sub Contractors" Supplier Group and a couple of Suppliers
       in it.
    3. Creates a "<Supplier> - Subcontract Store" Warehouse per subcontractor
       — the `supplier_warehouse` ERPNext uses to track stock physically
       sitting at that vendor's premises.
    4. Creates one non-stock Service Item per flagged finished good (the
       `item_code` a subcontracted Purchase Order line actually orders).
    5. Creates an Outsourced Workstation per subcontractor and a shared
       "Subcontracted Processing" Operation. ERPNext's Workstation/Operation
       schema has no subcontract-specific field — this is purely a routing
       label so a demo's Operation list isn't 100% in-house — but the issue
       asked for Workstation/Operation setup, so it's included for
       completeness.

Only runs for industries with the Manufacturing module; only acts on
industries that already have at least one submitted default BOM (i.e. the
industry's own BOM seeder ran). Idempotent throughout.

Priority 71 runs right after the BOM seeder (70, see industries/*/seeders/
01_master/10_bom.py) so the finished goods it flags already have a BOM, and
well ahead of Opening Stock (90). Caches "subcontract_setup" for
`02_transactions/205_subcontracting_orders.py`.
"""

from __future__ import annotations

import json
from typing import Any

from demostackkit.seeder.base import BaseMasterSeeder

#: Marker used to lift the resolved setup payload out of the container's stdout.
_PAYLOAD_MARKER = "DSK_SUBCONTRACT_SETUP::"

#: Cap on how many BOM-backed finished goods get flagged for subcontracting.
_MAX_SUBCONTRACT_ITEMS = 3

_SUPPLIER_GROUP = "Sub Contractors"

#: Generic subcontractor names — deliberately industry-agnostic, since this
#: seeder runs identically across every manufacturing industry.
_SUBCONTRACTORS: tuple[str, ...] = (
    "Precision Sub-Assemblies Pvt Ltd",
    "Alliance Contract Manufacturing Co",
)


class SubcontractingSetupSeeder(BaseMasterSeeder):
    label = "Subcontracting Setup"
    priority = 71

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Manufacturing" not in cfg.modules:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        abbr = self.ctx.cache_get("company_abbr", cfg.company.abbr)

        payload = {
            "company": company,
            "abbr": abbr,
            "country": cfg.company.country,
            "supplier_group": _SUPPLIER_GROUP,
            "subcontractors": list(_SUBCONTRACTORS),
            "max_items": _MAX_SUBCONTRACT_ITEMS,
        }
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']
abbr = payload['abbr']
supplier_group = payload['supplier_group']
subcontractors = payload['subcontractors']

# Candidates: finished goods that already have a submitted, active, default
# BOM. This is the only reliable signal available identically across every
# manufacturing industry (item-seeder cache keys are not consistently named).
candidates = frappe.get_all(
    'BOM',
    filters={{'docstatus': 1, 'is_active': 1, 'is_default': 1, 'company': company}},
    fields=['item'],
    order_by='creation asc',
    group_by='item',
    limit_page_length=payload['max_items'],
)
item_codes = [d.item for d in candidates]

if not item_codes:
    print('Subcontracting Setup: skipped, no BOM-backed finished goods for this company')
else:
    has_sub_item_flag = frappe.get_meta('Item').has_field('is_sub_contracted_item')
    flagged = 0
    if has_sub_item_flag:
        for code in item_codes:
            frappe.db.set_value('Item', code, 'is_sub_contracted_item', 1)
            flagged += 1

    if not frappe.db.exists('Supplier Group', supplier_group):
        frappe.get_doc({{
            'doctype': 'Supplier Group',
            'supplier_group_name': supplier_group,
            'parent_supplier_group': 'All Supplier Groups',
        }}).insert(ignore_permissions=True)

    parent_wh = f'All Warehouses - {{abbr}}'
    if not frappe.db.exists('Warehouse', {{'name': parent_wh, 'company': company}}):
        parent_wh = frappe.db.get_value(
            'Warehouse',
            {{'company': company, 'is_group': 1, 'parent_warehouse': ['is', 'not set']}},
            'name',
        ) or parent_wh

    supplier_created = supplier_skipped = 0
    wh_created = wh_skipped = 0
    supplier_warehouses = {{}}
    for name in subcontractors:
        if not frappe.db.exists('Supplier', name):
            frappe.get_doc({{
                'doctype': 'Supplier',
                'supplier_name': name,
                'supplier_group': supplier_group,
                'supplier_type': 'Company',
                'country': payload['country'],
            }}).insert(ignore_permissions=True)
            supplier_created += 1
        else:
            supplier_skipped += 1

        wh_name = f'{{name}} - Subcontract Store'
        wh_full = f'{{wh_name}} - {{abbr}}'
        if not frappe.db.exists('Warehouse', wh_full):
            frappe.get_doc({{
                'doctype': 'Warehouse',
                'warehouse_name': wh_name,
                'parent_warehouse': parent_wh,
                'company': company,
            }}).insert(ignore_permissions=True)
            wh_created += 1
        else:
            wh_skipped += 1
        supplier_warehouses[name] = wh_full

    # Reserve warehouse: where raw materials are drawn from before being sent
    # out to a subcontractor. Reuse whatever raw-material store the industry
    # already seeded rather than inventing another warehouse.
    reserve_warehouse = None
    for label in ('Raw Material Store', 'Stores', 'Raw Materials'):
        hit = frappe.db.get_value('Warehouse', {{'company': company, 'warehouse_name': label}}, 'name')
        if hit:
            reserve_warehouse = hit
            break
    if not reserve_warehouse:
        reserve_warehouse = frappe.db.get_value(
            'Warehouse', {{'company': company, 'is_group': 0}}, 'name'
        )

    # Target warehouse: where the finished good lands once the subcontractor
    # delivers it back.
    target_warehouse = None
    for label in ('Finished Goods Store', 'Finished Goods'):
        hit = frappe.db.get_value('Warehouse', {{'company': company, 'warehouse_name': label}}, 'name')
        if hit:
            target_warehouse = hit
            break
    if not target_warehouse:
        target_warehouse = reserve_warehouse

    service_items = {{}}
    item_details = {{}}
    svc_created = svc_skipped = 0
    for code in item_codes:
        item_name, stock_uom, valuation_rate = frappe.db.get_value(
            'Item', code, ['item_name', 'stock_uom', 'valuation_rate']
        )
        svc_code = f'{{code}}-SVC'
        service_items[code] = svc_code
        item_details[code] = {{
            'stock_uom': stock_uom,
            'valuation_rate': valuation_rate or 0,
        }}
        if not frappe.db.exists('Item', svc_code):
            frappe.get_doc({{
                'doctype': 'Item',
                'item_code': svc_code,
                'item_name': f'Subcontracted Service - {{item_name}}',
                'item_group': 'Services',
                'stock_uom': stock_uom,
                'is_stock_item': 0,
                'is_purchase_item': 1,
                'is_sales_item': 0,
                'include_item_in_manufacturing': 0,
            }}).insert(ignore_permissions=True)
            svc_created += 1
        else:
            svc_skipped += 1

    # Workstation / Operation: no subcontract-specific field exists on either
    # doctype in ERPNext — this just gives the routing a named, filterable
    # "sent to vendor" step rather than the demo looking 100% in-house.
    ws_created = 0
    for name in subcontractors:
        ws_name = f'{{name}} - Outsourced'
        if not frappe.db.exists('Workstation', ws_name):
            frappe.get_doc({{
                'doctype': 'Workstation',
                'workstation_name': ws_name,
                'description': f'Outsourced processing performed at {{name}}',
            }}).insert(ignore_permissions=True)
            ws_created += 1

    op_name = 'Subcontracted Processing'
    op_created = 0
    if not frappe.db.exists('Operation', op_name):
        frappe.get_doc({{
            'doctype': 'Operation',
            'name': op_name,
            'description': 'Processing step carried out by a subcontractor rather than in-house.',
        }}).insert(ignore_permissions=True)
        op_created = 1

    frappe.db.commit()
    print(
        f'Subcontracting Setup: fg_flagged={{flagged}}, '
        f'suppliers created={{supplier_created}} skipped={{supplier_skipped}}, '
        f'warehouses created={{wh_created}} skipped={{wh_skipped}}, '
        f'service items created={{svc_created}} skipped={{svc_skipped}}, '
        f'workstations created={{ws_created}}, operation created={{op_created}}'
    )
    setup = {{
        'item_codes': item_codes,
        'item_details': item_details,
        'service_items': service_items,
        'subcontractor_names': subcontractors,
        'supplier_warehouses': supplier_warehouses,
        'reserve_warehouse': reserve_warehouse,
        'target_warehouse': target_warehouse,
    }}
    print('{_PAYLOAD_MARKER}' + json.dumps(setup))
"""
        output = self._exec(script)
        setup = self._extract_payload(output)
        if setup is not None:
            self.ctx.cache_set("subcontract_setup", setup)

    @staticmethod
    def _extract_payload(output: str) -> dict[str, Any] | None:
        for line in output.splitlines():
            if line.startswith(_PAYLOAD_MARKER):
                return json.loads(line[len(_PAYLOAD_MARKER) :])
        return None
