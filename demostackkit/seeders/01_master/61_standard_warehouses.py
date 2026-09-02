"""
Shared seeder: the standard exception warehouses every stock demo needs.

Each industry seeds its own themed warehouse tree (Panel Store, Vault, Cold
Storage, ...), but the three warehouses ERPNext's own flows reach for are
missing almost everywhere:

    Scrap     — Work Order `scrap_warehouse`, and the destination for damaged or
                written-off stock in a Material Issue.
    Rejected  — Purchase Receipt / Subcontracting Receipt `rejected_warehouse`,
                where a failed incoming inspection parks the rejected qty.
    Rework    — where a Quality Inspection failure sends stock that can be
                repaired and re-offered, rather than scrapped.
    Vendor Rejected   — where the Rejection & Returns flow (ref #35) parks
                rejected-qty stock earmarked for Return to Vendor, kept
                separate from the generic `Rejected` warehouse above so
                vendor-side rejections never mix with customer-side ones.
    Customer Returns  — where finished goods returned by customers land,
                separate from saleable Finished Goods stock and from
                Vendor Rejected (ref #35).

Without them the demo cannot show a rejection or a scrap flow at all: the
warehouse picker on those fields comes up empty.

Relevance:
    Scrap and Rejected are created for every industry carrying the Stock module
    (i.e. all of them) — anyone who receives goods can reject them, and anyone
    holding stock can scrap it. Rework only appears for industries that run the
    Manufacturing module, since rework is a production-floor concept; a
    distributor or retail demo has no route to rework a purchased item. Vendor
    Rejected and Customer Returns follow the same "everyone with Stock gets
    one" rule as Scrap/Rejected.

Idempotent, as master seeders must be. Priority 61 puts it just after the
industry Warehouse seeders (60), so `All Warehouses - <ABBR>` is in place, and
well ahead of Opening Stock (90).
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

#: Warehouse name → the modules that make it relevant. An empty tuple means the
#: warehouse is created for every industry.
_STANDARD_WAREHOUSES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Scrap", ()),
    ("Rejected", ()),
    ("Rework", ("Manufacturing",)),
    ("Vendor Rejected", ()),
    ("Customer Returns", ()),
)


class StandardWarehouseSeeder(BaseMasterSeeder):
    label = "Standard Warehouses"
    priority = 61

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Stock" not in cfg.modules:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        abbr = self.ctx.cache_get("company_abbr", cfg.company.abbr)
        modules = set(cfg.modules)

        warehouses = [
            {
                "warehouse_name": name,
                # ERPNext keys the rejected-qty warehouse off this flag, so the
                # Purchase Receipt picker defaults to it instead of leaving the
                # user to guess which warehouse means "rejected".
                "is_rejected_warehouse": int(name == "Rejected"),
            }
            for name, required_modules in _STANDARD_WAREHOUSES
            if not required_modules or modules.issuperset(required_modules)
        ]
        wh_json = json.dumps(warehouses)

        script = f"""
import json

company = '''{company}'''
abbr = '''{abbr}'''
warehouses = json.loads('''{wh_json}''')

# The company's root warehouse is normally 'All Warehouses - <ABBR>'. Fall back to
# whatever root group the company actually has, so a company created outside the
# seeder (or one whose abbreviation was changed) still has somewhere to hang these.
parent = f'All Warehouses - {{abbr}}'
if not frappe.db.exists('Warehouse', {{'name': parent, 'company': company}}):
    parent = frappe.db.get_value(
        'Warehouse',
        {{'company': company, 'is_group': 1, 'parent_warehouse': ['is', 'not set']}},
        'name',
    ) or parent

# is_rejected_warehouse arrived in a later ERPNext version than some sites run.
has_rejected_flag = frappe.get_meta('Warehouse').has_field('is_rejected_warehouse')

created = skipped = 0
for wh in warehouses:
    wh_full = f"{{wh['warehouse_name']}} - {{abbr}}"
    if frappe.db.exists('Warehouse', wh_full):
        skipped += 1
        continue
    doc = frappe.get_doc({{
        'doctype': 'Warehouse',
        'warehouse_name': wh['warehouse_name'],
        'parent_warehouse': parent,
        'company': company,
    }})
    if has_rejected_flag and wh['is_rejected_warehouse']:
        doc.is_rejected_warehouse = 1
    doc.insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Standard Warehouses: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script)
