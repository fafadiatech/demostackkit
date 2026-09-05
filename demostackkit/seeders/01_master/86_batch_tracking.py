"""
Shared seeder: Batch/Serial No flags for forward & backward traceability (ref #4).

Nothing in this repo tracks batches or serial numbers today (confirmed by a
repo-wide grep for `has_batch_no`/`has_serial_no`/`Batch`/`Serial No` before
this seeder was written) — so a raw-material lot can never be traced forward
through a Work Order to the finished good it became, and a shipped finished
good can never be traced backward to the raw-material lots consumed to build
it. ERPNext's own Batch-Wise Balance History report and Stock Ledger (filtered
by batch) already do this natively; they just have nothing to show without
Batch No / Serial No tracking switched on.

This seeder flips that on for every item genuinely part of a manufactured
product's supply chain, discovered purely by querying submitted, active,
default BOMs (the same "top-level FG vs component" split
`02_transactions/215_production.py._fetch_plan` already computes for its own
purposes, copied verbatim here for the same reason it exists there — this is
the only signal available identically across every Manufacturing industry;
item-seeder cache keys are not consistently named):

    - a component / sub-assembly (a `BOM Item.item_code` referenced by any
      submitted default BOM) gets `has_batch_no` + `create_new_batch` +
      `batch_number_series` — ERPNext then auto-creates a new Batch on every
      *incoming* stock movement (Purchase Receipt, Stock Entry "Manufacture"
      output) with zero further code, per
      `erpnext/stock/serial_batch_bundle.py::SerialBatchBundle.validate_item`.
    - a top-level finished good (a BOM's own `item`, never itself a
      component elsewhere) gets `has_serial_no` + `serial_no_series` instead
      when `seed.batch_tracking.serialize_top_level_fg` is true (the
      default) — an individually-identifiable end product (e.g. VIN-style),
      giving a richer "trace this exact unit back to its component batches"
      story. When false, top-level FGs are batch-tracked like everything
      else.

Items are never both batch- and serial-tracked, are skipped if already
flagged (idempotent, as master seeders must be) or if `is_stock_item=0`
(batch/serial tracking a non-stock item is invalid in ERPNext).

Outward stock movements (Work Order material consumption, Delivery Note
shipment) still need an *explicit* batch/serial selection — ERPNext will not
fabricate a lot on an outward move — which is what
`02_transactions/215_production.py` and `02_transactions/220_delivery_notes.py`
add once this seeder has switched tracking on.

No cache_set: every consumer (`90_opening_stock.py`, and the two seeders
above) re-reads `has_batch_no`/`has_serial_no` live off the Item master
rather than from any seed-time cache — the same "queried rather than
cached" idiom `90_opening_stock.py`'s own docstring already calls out as a
deliberate choice, so this seeder stays decoupled from execution-order
cache-key coupling.

Skipped entirely when Manufacturing is not in `modules` or
`seed.batch_tracking.enabled` is false (default). Priority 86 — after BOM
(70) and Subcontracting Setup (71), well ahead of Opening Stock (90) so its
Batch/Serial-aware branch already sees these flags on the Item master.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


class BatchTrackingSeeder(BaseMasterSeeder):
    label = "Batch/Serial Tracking (raw-material lots & FG serials)"
    priority = 86

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Manufacturing" not in cfg.modules:
            return
        if not cfg.seed.batch_tracking.enabled:
            return

        payload = {
            "serialize_top_level_fg": cfg.seed.batch_tracking.serialize_top_level_fg,
        }
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
serialize_top_level_fg = payload['serialize_top_level_fg']

bom_rows = frappe.get_all(
    'BOM',
    filters={{'docstatus': 1, 'is_active': 1, 'is_default': 1}},
    fields=['name', 'item'],
    order_by='creation asc',
)
if not bom_rows:
    print('Batch/Serial Tracking: skipped, no submitted default BOMs found')
else:
    bom_names = [b.name for b in bom_rows]
    fg_item_codes = {{b.item for b in bom_rows}}

    # Same components-set logic 215_production.py._fetch_plan already runs:
    # anything consumed as a BOM Item line, across every default BOM.
    component_codes = {{
        row.item_code
        for row in frappe.get_all(
            'BOM Item', filters={{'parent': ['in', bom_names]}}, fields=['item_code']
        )
    }}

    # Top-level FG: a BOM's own item that is never itself a component of
    # another BOM (prefers real end products over sub-assemblies). A BOM'd
    # item that IS also consumed elsewhere as a component (a sub-assembly)
    # stays in component_codes and is batch-tracked like any other component.
    top_level_fg_codes = fg_item_codes - component_codes

    all_codes = component_codes | top_level_fg_codes
    item_rows = frappe.get_all(
        'Item',
        filters={{'name': ['in', list(all_codes)]}},
        fields=['name', 'is_stock_item', 'has_batch_no', 'has_serial_no'],
    )
    item_meta = {{row.name: row for row in item_rows}}

    batch_flagged = serial_flagged = skipped_non_stock = skipped_already = 0

    def _eligible(code):
        global skipped_non_stock, skipped_already
        row = item_meta.get(code)
        if not row or not row.is_stock_item:
            skipped_non_stock += 1
            return False
        if row.has_batch_no or row.has_serial_no:
            skipped_already += 1
            return False
        return True

    for code in sorted(component_codes):
        if not _eligible(code):
            continue
        frappe.db.set_value('Item', code, {{
            'has_batch_no': 1,
            'create_new_batch': 1,
            'batch_number_series': f'{{code}}-BATCH-.####',
        }})
        batch_flagged += 1

    for code in sorted(top_level_fg_codes):
        if not _eligible(code):
            continue
        if serialize_top_level_fg:
            frappe.db.set_value('Item', code, {{
                'has_serial_no': 1,
                'serial_no_series': f'{{code}}-SN-.####',
            }})
            serial_flagged += 1
        else:
            frappe.db.set_value('Item', code, {{
                'has_batch_no': 1,
                'create_new_batch': 1,
                'batch_number_series': f'{{code}}-BATCH-.####',
            }})
            batch_flagged += 1

    frappe.db.commit()
    print(
        f'Batch/Serial Tracking: batch_flagged={{batch_flagged}}, '
        f'serial_flagged={{serial_flagged}}, skipped_non_stock={{skipped_non_stock}}, '
        f'skipped_already={{skipped_already}}'
    )
"""
        self._exec(script, timeout=180)
