"""
Shared seeder: Fiscal Years.

Creates every ERPNext Fiscal Year needed to cover the industry's seed date range,
derived from `company.fiscal_year_start` in industry.yaml.

Without this, ERPNext has no Fiscal Year covering the seeded transaction dates and
every Sales Order / Purchase Order / Stock Entry fails validation. Two paths need it:
the setup wizard only ever creates the single FY containing today (so a -180d range on
an Apr-Mar fiscal year is partly uncovered), and `demostackkit reset` skips the wizard
entirely.

Idempotent — a window is skipped when any existing Fiscal Year overlaps it, since
ERPNext rejects overlapping years and a site may already carry a hand-created one.
Priority 1 ensures this runs before every other master seeder.
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from demostackkit.seeder.base import BaseMasterSeeder
from demostackkit.seeder.utils import (
    fiscal_year_windows,
    opening_stock_date,
    parse_relative_date,
)


class FiscalYearSeeder(BaseMasterSeeder):
    label = "Fiscal Years"
    priority = 1

    def run(self) -> None:
        cfg = self.ctx.industry_config
        today = date.today()
        # Opening stock posts one day ahead of the range, which can fall in the
        # previous fiscal year when the range starts on the fiscal year boundary.
        first = min(opening_stock_date(parse_relative_date(cfg.seed.date_range.start)), today)
        # A year of headroom past the range so post-dated demo documents (delivery
        # dates, required-by dates) still land inside a Fiscal Year.
        last = max(parse_relative_date(cfg.seed.date_range.end), today) + timedelta(days=365)

        windows = [
            {"year": label, "start": start.isoformat(), "end": end.isoformat()}
            for label, start, end in fiscal_year_windows(cfg.company.fiscal_year_start, first, last)
        ]
        windows_json = json.dumps(windows)

        script = f"""
import json

windows = json.loads('''{windows_json}''')
created = skipped = 0

for w in windows:
    # Overlap is checked by date, not by name: ERPNext's validate_overlap() rejects
    # overlapping years regardless of naming, and existing years may be named anything.
    existing = frappe.db.sql(
        "select name from `tabFiscal Year` where year_start_date <= %s and year_end_date >= %s",
        (w['end'], w['start']),
    )
    if existing:
        skipped += 1
        print(f"EXISTS: Fiscal Year {{existing[0][0]}} overlaps {{w['start']}}..{{w['end']}}")
        continue

    frappe.get_doc({{
        'doctype': 'Fiscal Year',
        'year': w['year'],
        'year_start_date': w['start'],
        'year_end_date': w['end'],
    }}).insert(ignore_permissions=True)
    created += 1
    print(f"CREATED: Fiscal Year {{w['year']}} ({{w['start']}} to {{w['end']}})")

frappe.db.commit()
print(f'Fiscal Years: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script)
