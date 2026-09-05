"""
Shared seeder: Purchase Receipts against submitted Purchase Orders, with
Incoming Quality Inspections linked to every receipt line (ref #35).

Purchase Orders currently just sit submitted with nothing received against
them anywhere in the repo — this seeder is the first thing that closes that
gap, using ERPNext's own `make_purchase_receipt()` mapper (the same mapping
the "Purchase Receipt" button on a PO uses) rather than hand-building the
derived document.

For industries carrying the Quality Management module, a share of receipts
(`_REJECTION_RATE`) get one line deliberately split into accepted/rejected
quantities before submit, with the rejected portion routed to the shared
`Vendor Rejected` warehouse (`61_standard_warehouses.py`). Every receipt line
— accepted or rejected — then gets a submitted Quality Inspection with
`reference_type`/`reference_name` pointing back at the Purchase Receipt (the
existing per-industry `03_quality_inspections.py` seeders never link back to
a source document; this is what actually gives the demo a QI → receipt
trail), linked onto the receipt item via `quality_inspection` after both are
submitted. Industries without Quality Management still get plain, fully
accepted receipts — the baseline receiving chain every Buying+Stock industry
needs regardless of quality tracking.

Caches "purchase_receipts" (all receipt names, for `212_purchase_invoices.py`)
and "vendor_rtv_candidates" (the rejected lines, for `213_return_to_vendor.py`)
via the same stdout-marker technique `71_subcontracting.py` uses.

Random selection of which POs to receive happens inside the container script
(the PO population isn't known client-side — no seeder caches created PO
names). To stay deterministic under `demostackkit reset`, `self.ctx.random`
draws a single seed which drives a `random.Random` inside the script, rather
than using unseeded randomness there.

Priority 211 — right after the industry Purchase Order seeder (210), well
ahead of Quality Inspections (230) since this seeder creates its own linked
inspections independently.

When `seed.batch_tracking.enabled` is true (ref #4), receiving RM items
that `86_batch_tracking.py` flagged with `has_batch_no`/`create_new_batch`
auto-creates a new Batch on submit with zero extra code (ERPNext's own
incoming-movement behavior) — this seeder's only addition is a cosmetic
"Vendor Batch" stamp on each such auto-created Batch, recording the
supplier's own lot identity; forward/backward traceability itself is
carried entirely by the Batch/Serial ledger linkage, not by this field.
"""

from __future__ import annotations

import json
from typing import Any

from demostackkit.seeder.base import BaseTransactionSeeder

_PAYLOAD_MARKER = "DSK_PURCHASE_RECEIPTS::"

#: Fraction of receipts (for Quality-Management industries) that get one line
#: split into accepted/rejected quantities.
_REJECTION_RATE = 0.18


class PurchaseReceiptSeeder(BaseTransactionSeeder):
    label = "Purchase Receipts"
    priority = 211
    _volume_attr = "purchase_receipts"
    default_volume = 20

    def run(self) -> None:
        cfg = self.ctx.industry_config
        modules = set(cfg.modules)
        if not {"Buying", "Stock"}.issubset(modules):
            return

        payload = {
            "volume": self.volume,
            "seed": self.ctx.random.randint(0, 2**31 - 1),
            "rejection_rate": _REJECTION_RATE,
            "quality_gated": "Quality Management" in modules,
            "batch_tracking_enabled": self.ctx.industry_config.seed.batch_tracking.enabled,
        }
        payload_json = json.dumps(payload)

        script = f"""
import json
import random as _random_mod

from erpnext.buying.doctype.purchase_order.purchase_order import make_purchase_receipt

payload = json.loads('''{payload_json}''')
rng = _random_mod.Random(payload['seed'])
quality_gated = payload['quality_gated']
rejection_rate = payload['rejection_rate']
batch_tracking_enabled = payload['batch_tracking_enabled']

def stamp_vendor_batch(pr):
    \"\"\"Record the supplier's own lot identity on every Batch ERPNext just
    auto-created for this receipt (has_batch_no + create_new_batch on the
    Item makes that automatic on submit -- see 86_batch_tracking.py). Purely
    cosmetic/informational: forward/backward traceability is carried entirely
    by the Batch/Serial ledger linkage, not by this field.
    \"\"\"
    batch_names = set()
    for sbb_name in frappe.get_all(
        'Serial and Batch Bundle',
        filters={{'voucher_type': 'Purchase Receipt', 'voucher_no': pr.name}},
        pluck='name',
    ):
        batch_names.update(
            frappe.get_all(
                'Serial and Batch Entry',
                filters={{'parent': sbb_name, 'batch_no': ['is', 'set']}},
                pluck='batch_no',
            )
        )
    for batch_no in batch_names:
        frappe.db.set_value('Batch', batch_no, {{
            'supplier': pr.supplier,
            'description': f'Vendor Batch: VB-{{rng.randint(100000, 999999)}}',
        }})

po_names = frappe.get_all('Purchase Order', filters={{'docstatus': 1}}, pluck='name')
rng.shuffle(po_names)
po_names = po_names[:payload['volume']]

abbr_cache = {{}}
def _abbr(company):
    if company not in abbr_cache:
        abbr_cache[company] = frappe.get_cached_value('Company', company, 'abbr')
    return abbr_cache[company]

created = rejected_lines = qi_created = errors = 0
receipt_names = []
rtv_candidates = []
for po_name in po_names:
    try:
        pr = make_purchase_receipt(po_name)
        if not pr.items:
            continue

        for item in pr.items:
            if not item.received_qty:
                item.received_qty = item.qty

        rejected_item = None
        if quality_gated and rng.random() < rejection_rate:
            candidate = rng.choice(pr.items)
            rejected_wh = f'Vendor Rejected - {{_abbr(pr.company)}}'
            if frappe.db.exists('Warehouse', rejected_wh):
                rq = max(1, int(round(candidate.received_qty * rng.uniform(0.15, 0.4))))
                rq = min(rq, int(candidate.received_qty))
                candidate.rejected_qty = rq
                candidate.qty = candidate.received_qty - rq
                candidate.rejected_warehouse = rejected_wh
                rejected_item = candidate

        pr.insert(ignore_permissions=True)
        pr.submit()
        created += 1
        receipt_names.append(pr.name)

        if batch_tracking_enabled:
            stamp_vendor_batch(pr)

        if quality_gated:
            for item in pr.items:
                is_rejected_line = rejected_item is not None and item.name == rejected_item.name
                qi = frappe.get_doc({{
                    'doctype': 'Quality Inspection',
                    'company': pr.company,
                    'inspection_type': 'Incoming',
                    'reference_type': 'Purchase Receipt',
                    'reference_name': pr.name,
                    'item_code': item.item_code,
                    'sample_size': min(int(item.received_qty) or 1, 10),
                    'report_date': pr.posting_date,
                    'status': 'Rejected' if is_rejected_line else 'Accepted',
                    'inspected_by': 'Administrator',
                }})
                qi.flags.ignore_mandatory = True
                qi.insert(ignore_permissions=True)
                qi.submit()
                qi_created += 1
                frappe.db.set_value('Purchase Receipt Item', item.name, 'quality_inspection', qi.name)

                if is_rejected_line:
                    rejected_lines += 1
                    rtv_candidates.append({{
                        'pr_name': pr.name,
                        'item_code': item.item_code,
                        'rejected_qty': item.rejected_qty,
                        'warehouse': item.rejected_warehouse,
                        'company': pr.company,
                    }})
    except Exception as e:
        print(f'WARN Purchase Receipt for {{po_name}}: {{e}}')
        errors += 1

frappe.db.commit()
print(
    f'Purchase Receipts: created={{created}}, rejected_lines={{rejected_lines}}, '
    f'qi_created={{qi_created}}, errors={{errors}}'
)
print('{_PAYLOAD_MARKER}' + json.dumps({{
    'purchase_receipts': receipt_names,
    'vendor_rtv_candidates': rtv_candidates,
}}))
"""
        output = self._exec(script, timeout=300)
        payload_out = self._extract_payload(output)
        if payload_out is not None:
            self.ctx.cache_set("purchase_receipts", payload_out.get("purchase_receipts", []))
            self.ctx.cache_set(
                "vendor_rtv_candidates", payload_out.get("vendor_rtv_candidates", [])
            )

    @staticmethod
    def _extract_payload(output: str) -> dict[str, Any] | None:
        for line in output.splitlines():
            if line.startswith(_PAYLOAD_MARKER):
                return json.loads(line[len(_PAYLOAD_MARKER) :])
        return None
