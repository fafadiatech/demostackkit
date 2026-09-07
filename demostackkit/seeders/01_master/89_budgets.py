"""
Shared seeder: Cost Centers and Budgets for a "Budgeting Scenarios" demo.

ERPNext's Budget doctype only ever budgets against a Cost Center or a Project
(see erpnext/accounts/doctype/budget/budget.json) — there is no Department or
Customer dimension to attach a budget to. Every company starts with exactly one
usable Cost Center ("Main - <ABBR>"), so the Budget report has nothing to slice
by and the feature looks unused in every demo.

This seeder:
  1. Creates a handful of leaf Cost Centers under the company's root — one per
     department the ERPNext HR module already auto-creates for every company
     (Sales, Marketing, Purchase, Management, and Production when the industry
     runs Manufacturing) — so the Cost Center tree mirrors a Department tree
     the user already sees, instead of inventing a parallel naming scheme.
  2. Books an annual Budget against each of those Cost Centers, covering the
     fiscal year containing today, against the expense accounts most relevant
     to that Cost Center in the "Standard" chart of accounts every industry
     installs via the ERPNext setup wizard.
  3. Books an annual Budget against up to two of the industry's seeded
     Projects, so the Budget vs Actual report has a project dimension too.

Customers are not touched here: ERPNext has no Customer-budget relationship,
so the issue's "Customers" checklist item is satisfied by the Customer master
data industries already seed, not by anything in this file.

Every budget uses action_if_*_exceeded = "Warn", never "Stop": this seeder
runs in the master phase, before the Purchase Order / Sales Order transaction
seeders, and a "Stop" action would block them the moment a seeded document
crosses the budget line.

Budgets are submitted after insert. ERPNext's Budget doctype is submittable,
and the Budget Variance Report (and budget-exceeded checks) only consider
docstatus=1 — leaving them Draft would leave the report empty even after
`230_budget_actuals.py` posts spend against them (ref #39).

Idempotent: Cost Centers are skipped if already present; Budgets are matched
on (company, fiscal_year, cost_center, account) or (company, fiscal_year,
project, account).
Priority 89 runs after Standard Warehouses (61), Employee Users (84) and every
industry's Project seeder (88, see project_seeders.py), and just ahead of
Opening Stock / Asset Maintenance (90) — so the Departments, Projects and
Fiscal Years this seeder reads already exist.

ERPNext 16 reworked the Budget doctype: the single `fiscal_year` Link became
`from_fiscal_year`/`to_fiscal_year`, and the `accounts` child table (multiple
account/budget_amount rows per Budget) was replaced by flat `account` and
`budget_amount` fields — one Budget document per account. The generated
script below detects the running version via `frappe.__version__` and builds
either shape at runtime, so the same seeder works against v14/v15 (child
table) and v16+ (one document per account).
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder

#: Cost Center name → (required modules, expense accounts to budget against,
#: from the "Standard" chart of accounts). An empty module tuple means the
#: Cost Center is created for every industry. Only created when a Department
#: of the same name already exists for the company (see `run`).
_COST_CENTER_BUDGETS: tuple[tuple[str, tuple[str, ...], tuple[str, ...]], ...] = (
    ("Sales", (), ("Sales Expenses", "Commission on Sales")),
    ("Marketing", (), ("Marketing Expenses", "Entertainment Expenses")),
    ("Purchase", (), ("Freight and Forwarding Charges", "Miscellaneous Expenses")),
    ("Management", (), ("Administrative Expenses", "Legal Expenses")),
    ("Production", ("Manufacturing",), ("Depreciation", "Utility Expenses")),
)

#: Expense accounts budgeted against each seeded Project.
_PROJECT_BUDGET_ACCOUNTS: tuple[str, ...] = ("Salary", "Travel Expenses")

#: Annual budget amount range per account line, in company currency, scaled
#: down by `seed.opening_stock.qty_scale` for small-format industries.
_AMOUNT_MIN = 300_000
_AMOUNT_MAX = 900_000

#: Cap on how many existing Projects get a Budget.
_MAX_PROJECT_BUDGETS = 2


class BudgetSeeder(BaseMasterSeeder):
    label = "Budgets"
    priority = 89

    def run(self) -> None:
        cfg = self.ctx.industry_config
        company = self.ctx.cache_get("company_name", cfg.company.name)
        abbr = self.ctx.cache_get("company_abbr", cfg.company.abbr)
        modules = set(cfg.modules)
        scale = cfg.seed.opening_stock.qty_scale

        def amount() -> float:
            return round(self.ctx.random.uniform(_AMOUNT_MIN, _AMOUNT_MAX) * scale, 2)

        cost_centers = [
            {"name": name, "accounts": list(accounts), "amounts": [amount() for _ in accounts]}
            for name, required_modules, accounts in _COST_CENTER_BUDGETS
            if not required_modules or modules.issuperset(required_modules)
        ]
        project_plan = [
            {
                "accounts": list(_PROJECT_BUDGET_ACCOUNTS),
                "amounts": [amount() for _ in _PROJECT_BUDGET_ACCOUNTS],
            }
            for _ in range(_MAX_PROJECT_BUDGETS)
        ]

        payload = json.dumps({"cost_centers": cost_centers, "projects": project_plan})

        script = f"""
import json

company = '''{company}'''
abbr = '''{abbr}'''
plan = json.loads('''{payload}''')

# ERPNext 16 dropped Budget.fiscal_year + the Budget.accounts child table in
# favour of from_fiscal_year/to_fiscal_year + one Budget document per account.
budget_per_account = int(frappe.__version__.split('.')[0]) >= 16

fy_row = frappe.db.sql(
    "select name from `tabFiscal Year` "
    "where year_start_date <= CURDATE() and year_end_date >= CURDATE()"
)
fiscal_year = fy_row[0][0] if fy_row else None

cc_created = cc_skipped = 0
budget_created = budget_skipped = 0

def resolve_rows(names, amounts):
    # Pair each account with its amount BEFORE dropping accounts that don't
    # exist, so a missing account never shifts a later account onto the
    # wrong amount.
    rows = []
    for name, amt in zip(names, amounts):
        if not amt:
            continue
        full = f'{{name}} - {{abbr}}'
        if frappe.db.exists('Account', full):
            rows.append({{'account': full, 'budget_amount': amt}})
    return rows

_BUDGET_DEFAULTS = {{
    'applicable_on_material_request': 1,
    'applicable_on_purchase_order': 1,
    'applicable_on_booking_actual_expenses': 1,
    'action_if_annual_budget_exceeded': 'Warn',
    'action_if_accumulated_monthly_budget_exceeded': 'Warn',
    'action_if_annual_budget_exceeded_on_mr': 'Warn',
    'action_if_accumulated_monthly_budget_exceeded_on_mr': 'Warn',
    'action_if_annual_budget_exceeded_on_po': 'Warn',
    'action_if_accumulated_monthly_budget_exceeded_on_po': 'Warn',
}}

def budget_exists(budget_against, target, account=None):
    filters = {{'company': company, 'budget_against': budget_against}}
    filters['cost_center' if budget_against == 'Cost Center' else 'project'] = target
    if budget_per_account:
        filters['account'] = account
        filters['from_fiscal_year'] = fiscal_year
    else:
        filters['fiscal_year'] = fiscal_year
    return frappe.db.exists('Budget', filters)

def create_budgets(budget_against, target, rows):
    # Budget is submittable; Budget Variance Report only reads docstatus=1.
    global budget_created, budget_skipped
    if not rows:
        return
    base = dict(_BUDGET_DEFAULTS)
    base['doctype'] = 'Budget'
    base['budget_against'] = budget_against
    base['company'] = company
    base['cost_center' if budget_against == 'Cost Center' else 'project'] = target
    if budget_per_account:
        for row in rows:
            if budget_exists(budget_against, target, row['account']):
                budget_skipped += 1
                continue
            fields = dict(base)
            fields['account'] = row['account']
            fields['budget_amount'] = row['budget_amount']
            fields['from_fiscal_year'] = fiscal_year
            fields['to_fiscal_year'] = fiscal_year
            doc = frappe.get_doc(fields)
            doc.insert(ignore_permissions=True)
            doc.submit()
            budget_created += 1
    else:
        if budget_exists(budget_against, target):
            budget_skipped += 1
            return
        fields = dict(base)
        fields['fiscal_year'] = fiscal_year
        fields['accounts'] = rows
        doc = frappe.get_doc(fields)
        doc.insert(ignore_permissions=True)
        doc.submit()
        budget_created += 1

if not fiscal_year:
    print('Budgets: skipped, no Fiscal Year covers today')
else:
    parent = f'{{company}} - {{abbr}}'
    if not frappe.db.exists('Cost Center', {{'name': parent, 'company': company}}):
        parent = frappe.db.get_value(
            'Cost Center',
            {{'company': company, 'is_group': 1, 'parent_cost_center': ['is', 'not set']}},
            'name',
        ) or parent

    existing_depts = set(
        frappe.get_all('Department', filters={{'company': company}}, pluck='department_name')
    )

    for cc in plan['cost_centers']:
        name = cc['name']
        if name not in existing_depts:
            continue

        cc_full = f'{{name}} - {{abbr}}'
        if not frappe.db.exists('Cost Center', cc_full):
            frappe.get_doc({{
                'doctype': 'Cost Center',
                'cost_center_name': name,
                'parent_cost_center': parent,
                'company': company,
            }}).insert(ignore_permissions=True)
            cc_created += 1
        else:
            cc_skipped += 1

        rows = resolve_rows(cc['accounts'], cc['amounts'])
        create_budgets('Cost Center', cc_full, rows)

    projects = frappe.get_all(
        'Project',
        filters={{'company': company}},
        order_by='creation asc',
        pluck='name',
        limit_page_length={_MAX_PROJECT_BUDGETS},
    )
    for proj, proj_plan in zip(projects, plan['projects']):
        rows = resolve_rows(proj_plan['accounts'], proj_plan['amounts'])
        create_budgets('Project', proj, rows)

frappe.db.commit()
print(
    f'Budgets: cost_centers created={{cc_created}} skipped={{cc_skipped}}, '
    f'budgets created={{budget_created}} skipped={{budget_skipped}}'
)
"""
        self._exec(script)
