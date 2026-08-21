"""
Shared Issue Type seeder base for every industry.

Each industry supplies only ``ISSUE_TYPES`` in its ``01_master/15_issue_types.py``;
this module carries the Frappe script and run logic. ``Issue Type`` autonames by
prompt, so — like ``Task Type`` in ``project_seeders.py`` — the name has to be
assigned by hand or the insert fails with "Name is required".
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


class IssueTypeSeeder(BaseMasterSeeder):
    """Support Issue Types."""

    label = "Issue Types"
    priority = 17

    #: ``["Hardware Defect", "Installation Issue", ...]`` — set by the industry subclass.
    ISSUE_TYPES: list[str] = []

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Support" not in cfg.modules or not self.ISSUE_TYPES:
            return

        payload_json = json.dumps(self.ISSUE_TYPES)

        script = f"""
import json

issue_types = json.loads('''{payload_json}''')

if not frappe.db.exists('DocType', 'Issue Type'):
    print('Support: the Support module is not available on this site, nothing to seed')
    raise SystemExit(0)

created = skipped = 0
for name in issue_types:
    if frappe.db.exists('Issue Type', name):
        skipped += 1
        continue
    doc = frappe.new_doc('Issue Type')
    doc.name = name
    doc.insert(ignore_permissions=True)
    created += 1

frappe.db.commit()
print(f'Issue Types: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=120)
        self.ctx.cache_set("issue_type_names", list(self.ISSUE_TYPES))
