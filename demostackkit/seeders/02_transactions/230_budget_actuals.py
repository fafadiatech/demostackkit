"""
Shared seeder: actual spend against every Budget `89_budgets.py` creates
(ref #39).

Budgets and Cost Centers are seeded, but nothing ever posts against the same
accounts/cost centers/projects those Budgets cover, so the **Budget Variance**
report has a budgeted side and an empty (or incidentally-populated) actual
side — the variance it exists to show never renders meaningfully.

For every *submitted* Budget the company has for the fiscal year containing
today (the same one `89_budgets.py` books against), each budgeted account line
is assigned one of three outcomes so the report shows a realistic spread:

    - under      (55-85% of budget_amount)  — cost center came in under.
    - on_target  (92-108% of budget_amount) — cost center landed on plan.
    - over       (115-145% of budget_amount) — cost center overspent.

The resulting actual total is split across 2-4 Journal Entries dated
between the fiscal year's start and today (never into the future, and never
before the fiscal year starts), so the spend accrues the way real postings
would rather than landing as one lump sum. Each Journal Entry debits the
budgeted account — tagged with the Budget's Cost Center (or the company's
default leaf Cost Center when the Budget is against a Project, since P&L GL
entries always require a Cost Center) plus the Project when present — and
credits Cash. Cash balances the entry without inventing a supplier and
without draining the seeded bank ledger that `224_bank_transactions.py`
reconciles.

Skipped entirely for a Budget with no fiscal year match, per-company if Cash
cannot be resolved, and per-line if the budgeted amount is zero or no Cost
Center is available. Not idempotent (like every transaction seeder):
`demostackkit reset` drops and recreates the site before reseeding.

Priority 230 — after Bank Transactions (224) and the rest of the Accounts
transaction chain, well before Maintenance Contracts (245). Cash itself is
available from CoA setup; the late priority just keeps budget actuals after
the operational ledger is already populated.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from demostackkit.seeder.base import BaseTransactionSeeder

_PLAN_MARKER = "DSK_BUDGET_ACTUALS_PLAN::"
_PAYLOAD_MARKER = "DSK_BUDGET_ACTUALS::"

#: Outcome distribution across every budgeted account line. Must sum to 1.
_SCENARIO_WEIGHTS: dict[str, float] = {
    "under": 0.35,
    "on_target": 0.30,
    "over": 0.35,
}

#: Fraction of budget_amount actually posted, per scenario.
_SCENARIO_RANGES: dict[str, tuple[float, float]] = {
    "under": (0.55, 0.85),
    "on_target": (0.92, 1.08),
    "over": (1.15, 1.45),
}

#: How many Journal Entries a line's actual total is split across.
_MIN_ENTRIES, _MAX_ENTRIES = 2, 4


class BudgetActualsSeeder(BaseTransactionSeeder):
    label = "Budget Actuals"
    priority = 230

    def run(self) -> None:
        cfg = self.ctx.industry_config
        default_company = self.ctx.cache_get("company_name", cfg.company.name)
        default_abbr = self.ctx.cache_get("company_abbr", cfg.company.abbr)
        default_companies = [{"name": default_company, "abbr": default_abbr}]
        companies = self.ctx.cache_get("all_companies", default_companies)

        plan = self._fetch_plan(companies)
        lines = plan.get("lines", [])
        if not lines:
            return

        entries = self._build_entries(lines)
        self._submit(entries)

    # ── Planning ──────────────────────────────────────────────────────────────

    def _build_entries(self, lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rng = self.ctx.random
        today = date.today()
        entries: list[dict[str, Any]] = []

        for line in lines:
            budget_amount = float(line["budget_amount"])
            if budget_amount <= 0:
                continue
            cost_center = line.get("cost_center")
            if not cost_center:
                continue

            fy_start = date.fromisoformat(line["fiscal_year_start"])
            span = max((today - fy_start).days, 0)

            scenario = rng.choices(
                list(_SCENARIO_WEIGHTS.keys()), weights=list(_SCENARIO_WEIGHTS.values()), k=1
            )[0]
            factor = rng.uniform(*_SCENARIO_RANGES[scenario])
            total = round(budget_amount * factor, 2)
            if total <= 0:
                continue

            num_entries = rng.randint(_MIN_ENTRIES, _MAX_ENTRIES)
            weights = [rng.uniform(0.5, 1.5) for _ in range(num_entries)]
            weight_sum = sum(weights)
            amounts = [round(total * w / weight_sum, 2) for w in weights[:-1]]
            amounts.append(round(total - sum(amounts), 2))

            project = line.get("project") or None
            for amount in amounts:
                if amount <= 0:
                    continue
                posting_date = fy_start + timedelta(days=rng.randint(0, span))
                entries.append(
                    {
                        "company": line["company"],
                        "posting_date": posting_date.isoformat(),
                        "account": line["account"],
                        "credit_account": line["credit_account"],
                        "cost_center": cost_center,
                        "project": project,
                        "amount": amount,
                    }
                )

        return entries

    def _fetch_plan(self, companies: list[dict[str, str]]) -> dict[str, Any]:
        payload_json = json.dumps(companies)
        script = f"""
import json

companies = json.loads('''{payload_json}''')

fy_row = frappe.db.sql(
    "select name, year_start_date, year_end_date from `tabFiscal Year` "
    "where year_start_date <= CURDATE() and year_end_date >= CURDATE()"
)

lines = []
if fy_row:
    fiscal_year, fy_start, fy_end = fy_row[0]
    for c in companies:
        company = c['name']
        abbr = c['abbr']

        # Credit Cash — not the bank ledger — so these balancing credits do not
        # invent unreconciled bank activity against the #38 Bank Reconciliation demo.
        credit_account = f'Cash - {{abbr}}'
        if not frappe.db.exists('Account', credit_account):
            credit_account = frappe.db.get_value('Company', company, 'default_cash_account')
        if not credit_account:
            continue

        # P&L GL entries always need a leaf Cost Center. Project Budgets have none
        # of their own, so fall back to Company.cost_center (or Main - ABBR).
        company_cc = frappe.db.get_value('Company', company, 'cost_center')
        if company_cc and frappe.db.get_value('Cost Center', company_cc, 'is_group'):
            company_cc = None
        if not company_cc:
            main = f'Main - {{abbr}}'
            company_cc = main if frappe.db.exists('Cost Center', main) else None

        budgets = frappe.get_all(
            'Budget',
            filters={{'company': company, 'fiscal_year': fiscal_year, 'docstatus': 1}},
            fields=['name', 'cost_center', 'project'],
        )
        for b in budgets:
            cost_center = b.cost_center or company_cc
            if not cost_center:
                continue
            rows = frappe.get_all(
                'Budget Account',
                filters={{'parent': b.name}},
                fields=['account', 'budget_amount'],
            )
            for r in rows:
                if not r.budget_amount:
                    continue
                lines.append({{
                    'company': company,
                    'account': r.account,
                    'budget_amount': float(r.budget_amount),
                    'cost_center': cost_center,
                    'project': b.project or None,
                    'credit_account': credit_account,
                    'fiscal_year_start': str(fy_start),
                }})

print('{_PLAN_MARKER}' + json.dumps({{'lines': lines}}))
"""
        output = self._exec(script, timeout=120)
        return self._extract_payload(output, _PLAN_MARKER) or {}

    # ── Submission ────────────────────────────────────────────────────────────

    def _submit(self, entries: list[dict[str, Any]]) -> None:
        if not entries:
            return
        entries_json = json.dumps(entries)
        script = f"""
import json

entries = json.loads('''{entries_json}''')

created = errors = 0
for e in entries:
    try:
        debit_row = {{
            'account': e['account'],
            'debit_in_account_currency': e['amount'],
            'cost_center': e['cost_center'],
        }}
        if e.get('project'):
            debit_row['project'] = e['project']

        je = frappe.get_doc({{
            'doctype': 'Journal Entry',
            'voucher_type': 'Journal Entry',
            'company': e['company'],
            'posting_date': e['posting_date'],
            'user_remark': 'Budget actual spend seeded (ref #39)',
            'accounts': [
                debit_row,
                {{
                    'account': e['credit_account'],
                    'credit_in_account_currency': e['amount'],
                }},
            ],
        }})
        je.insert(ignore_permissions=True)
        je.submit()
        created += 1
    except Exception as ex:
        print(f"WARN Journal Entry for {{e['account']}}: {{ex}}")
        errors += 1

frappe.db.commit()
print(f'Budget Actuals: created={{created}}, errors={{errors}}')
print('{_PAYLOAD_MARKER}' + json.dumps({{'created': created, 'errors': errors}}))
"""
        self._exec(script, timeout=300)

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_payload(output: str, marker: str) -> Any | None:
        for line in output.splitlines():
            if line.startswith(marker):
                return json.loads(line[len(marker) :])
        return None
