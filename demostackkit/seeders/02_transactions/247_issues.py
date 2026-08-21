"""
Shared seeder: Support Issues raised by customers.

Needs no per-industry data — draws ``issue_type_names`` from the cache left
by each industry's ``15_issue_types.py`` (built on
``demostackkit.seeder.support_seeder``) and no-ops when the industry has no
customers or no ``Support`` module.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from demostackkit.seeder.base import BaseTransactionSeeder


class IssueSeeder(BaseTransactionSeeder):
    """Support Issues raised by customers."""

    label = "Support Issues"
    priority = 247
    _volume_attr = "issues"
    default_volume = 5

    _STATUS_MIX = ["Open", "Replied", "On Hold", "Resolved", "Closed"]

    _SUBJECTS = [
        "Product not performing as expected",
        "Request for replacement part",
        "Delayed delivery follow-up",
        "Billing discrepancy on last invoice",
        "General product inquiry",
        "Installation support needed",
    ]

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Support" not in cfg.modules:
            return
        customers = self.ctx.cache_get("customer_names", [])
        issue_types = self.ctx.cache_get("issue_type_names", [])
        if not customers:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        today = date.today()
        rng = self.ctx.random

        issues = []
        for i in range(self.volume):
            issues.append(
                {
                    "customer": customers[i % len(customers)],
                    "subject": self._SUBJECTS[i % len(self._SUBJECTS)],
                    "status": self._STATUS_MIX[i % len(self._STATUS_MIX)],
                    "issue_type": issue_types[i % len(issue_types)] if issue_types else None,
                    "opening_date": (today - timedelta(days=rng.randint(1, 200))).isoformat(),
                }
            )

        payload = {"company": company, "issues": issues}
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']

if not frappe.db.exists('DocType', 'Issue'):
    print('Support: the Support module is not available on this site, nothing to seed')
    raise SystemExit(0)

created = errors = 0
for i in payload['issues']:
    try:
        doc = frappe.get_doc({{
            'doctype': 'Issue',
            'customer': i['customer'],
            'company': company,
            'subject': i['subject'],
            'status': i['status'],
            'issue_type': i.get('issue_type'),
            'opening_date': i['opening_date'],
            'raised_by': 'demo@example.com',
        }})
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        created += 1
    except Exception as ex:
        frappe.db.rollback()
        print(f"ERROR Issue for {{i['customer']}}: {{ex}}")
        errors += 1

frappe.db.commit()
print(f'Issues: created={{created}}, errors={{errors}}')
if errors:
    raise SystemExit(f'{{errors}} issue(s) failed')
"""
        self._exec(script, timeout=180)
