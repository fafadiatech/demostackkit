"""
Shared seeder: Warranty Claims against sold goods.

Needs no per-industry data — auto-pairs ``customer_names`` and item codes
the same way ``245_maintenance_contracts.py`` does, and no-ops when either
cache is empty or the industry has no ``Support`` module.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.utils import resolve_saleable_items


class WarrantyClaimSeeder(BaseTransactionSeeder):
    """Warranty Claims against sold goods."""

    label = "Warranty Claims"
    priority = 246
    _volume_attr = "warranty_claims"
    default_volume = 4

    _STATUS_MIX = ["Open", "Work In Progress", "Closed", "Closed"]
    _AMC_MIX = ["Under Warranty", "Under AMC", "Out of Warranty"]

    _COMPLAINTS = [
        "Unit stopped responding after a power fluctuation.",
        "Unusual noise reported during operation.",
        "Output quality degraded compared to spec.",
        "Customer reports intermittent failure under load.",
        "Cosmetic damage found on delivery, claim raised for replacement part.",
    ]

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Support" not in cfg.modules:
            return
        customers = self.ctx.cache_get("customer_names", [])
        items = resolve_saleable_items(self.ctx)
        if not customers or not items:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        today = date.today()
        rng = self.ctx.random

        claims = []
        for i in range(self.volume):
            status = self._STATUS_MIX[i % len(self._STATUS_MIX)]
            complaint_date = today - timedelta(days=rng.randint(10, 300))
            claim = {
                "customer": customers[i % len(customers)],
                "item_code": items[rng.randrange(len(items))],
                "complaint_date": complaint_date.isoformat(),
                "complaint": self._COMPLAINTS[i % len(self._COMPLAINTS)],
                "status": status,
                "warranty_amc_status": self._AMC_MIX[i % len(self._AMC_MIX)],
            }
            if status == "Closed":
                claim["resolution_date"] = (
                    complaint_date + timedelta(days=rng.randint(2, 14))
                ).isoformat()
                claim["resolution_details"] = (
                    "Issue diagnosed and resolved; part replaced under warranty."
                )
            claims.append(claim)

        payload = {"company": company, "claims": claims}
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']

if not frappe.db.exists('DocType', 'Warranty Claim'):
    print('Support: the Support module is not available on this site, nothing to seed')
    raise SystemExit(0)

created = errors = 0
for c in payload['claims']:
    try:
        doc = frappe.get_doc({{
            'doctype': 'Warranty Claim',
            'customer': c['customer'],
            'company': company,
            'item_code': c['item_code'],
            'complaint_date': c['complaint_date'],
            'complaint': c['complaint'],
            'status': c['status'],
            'warranty_amc_status': c['warranty_amc_status'],
            'resolution_date': c.get('resolution_date'),
            'resolution_details': c.get('resolution_details'),
        }})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        created += 1
    except Exception as ex:
        frappe.db.rollback()
        print(f"ERROR Warranty Claim for {{c['customer']}}: {{ex}}")
        errors += 1

frappe.db.commit()
print(f'Warranty Claims: created={{created}}, errors={{errors}}')
if errors:
    raise SystemExit(f'{{errors}} warranty claim(s) failed')
"""
        self._exec(script, timeout=180)
