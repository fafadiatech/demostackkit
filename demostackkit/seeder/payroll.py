"""
Country-aware payroll shapes shared by every industry's payroll seeder.

An industry supplies one number per designation — the annual cost to company —
and this module turns it into the Salary Component masters, the Salary Structure
rows, and the per-period `base` an assignment carries. Keeping it here means a
new industry's payroll seeder is a table of salaries plus a call, and the two
payroll conventions live in one place instead of drifting per industry.

Two conventions are supported:

    Monthly (the default, used by every non-US demo)
        Twelve payslips a year. `base` is one month's cost to company and every
        component is a formula over it, so one Salary Structure serves the whole
        workforce and the assignment's `base` is what makes a supervisor's slip
        differ from an operator's.

    Hourly (United States)
        US demos are expected to run payroll off timesheets, so the structure is
        flagged `salary_slip_based_on_timesheet` with an `hour_rate`, and pays
        Weekly. HRMS carries the rate on the Salary Structure rather than the
        assignment, so a US industry creates one structure per pay grade — see
        `hour_rate()` — instead of the single structure a monthly demo needs.

Formulas deliberately reference only `base`, never another component's
abbreviation: HRMS rejects a formula that reads a payment-days-dependent
component while itself depending on payment days (the amount would be prorated
twice), and `base` sidesteps that whole class of failure.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

#: Countries whose demos run payroll hourly, off timesheets, rather than monthly.
HOURLY_PAYROLL_COUNTRIES = frozenset({"United States"})

#: A full-time week and year, the basis for converting an annual salary to an
#: hourly rate. 40 × 52 = the 2080 hours US employers quote rates against.
WORK_HOURS_PER_WEEK = 40
WORK_WEEKS_PER_YEAR = 52
WORK_HOURS_PER_YEAR = WORK_HOURS_PER_WEEK * WORK_WEEKS_PER_YEAR

#: The earning a timesheet's hours are paid against on an hourly structure.
TIMESHEET_EARNING = "Basic"


def is_hourly_payroll(country: str) -> bool:
    """Whether this country's demo pays by the hour instead of by the month."""
    return country in HOURLY_PAYROLL_COUNTRIES


def payroll_frequency(country: str) -> str:
    """ERPNext payroll frequency for the country's convention."""
    return "Weekly" if is_hourly_payroll(country) else "Monthly"


def weekly_offs(country: str) -> list[str]:
    """The days the Holiday List marks as a weekly off.

    A Salary Slip cannot be raised at all without a Holiday List, and the days it
    marks decide the payment days every prorated component is scaled by. US demos
    get the two-day weekend their hourly timesheets assume; elsewhere a
    single Sunday off matches how the seeded plants and workshops run.
    """
    return ["Saturday", "Sunday"] if is_hourly_payroll(country) else ["Sunday"]


def hour_rate(annual_ctc: float) -> float:
    """Hourly rate for an annual cost to company, over a 2080-hour year."""
    return round(annual_ctc / WORK_HOURS_PER_YEAR, 2)


def period_base(annual_ctc: float, country: str) -> float:
    """One payroll period's pay — the `base` a Salary Structure Assignment carries.

    Every structure formula is written against `base`, so this has to match the
    structure's payroll frequency: a week's pay for an hourly demo, a month's for
    a monthly one.
    """
    if is_hourly_payroll(country):
        return round(hour_rate(annual_ctc) * WORK_HOURS_PER_WEEK, 2)
    return round(annual_ctc / 12, 2)


def timesheet_settings(country: str, annual_ctc: float) -> dict[str, Any]:
    """Salary Structure fields that turn a structure into an hourly, timesheet one.

    Empty for monthly countries, so a seeder can splat it into the structure
    payload either way. `annual_ctc` is the pay grade the structure represents —
    HRMS holds one rate per structure, so an hourly demo needs a structure per
    grade rather than per workforce.
    """
    if not is_hourly_payroll(country):
        return {}
    return {
        "salary_slip_based_on_timesheet": 1,
        "salary_component": TIMESHEET_EARNING,
        "hour_rate": hour_rate(annual_ctc),
    }


def salary_components(country: str) -> list[dict[str, Any]]:
    """Salary Component masters the country's structure references.

    HRMS ships Basic, House Rent Allowance, Provident Fund, Professional Tax and
    Income Tax with every site; they are listed here anyway so a seeder can
    create whatever is missing without caring which came from the install.
    """
    return _US_COMPONENTS if is_hourly_payroll(country) else _INDIA_COMPONENTS


def structure_rows(country: str) -> dict[str, list[dict[str, Any]]]:
    """The Salary Structure's `earnings` and `deductions` rows.

    Earnings always sum to `base` (an hourly structure's Basic row is overwritten
    by the timesheet's hours × rate at slip time), so the assignment's `base`
    reads as gross pay for the period.
    """
    rows = _US_STRUCTURE if is_hourly_payroll(country) else _INDIA_STRUCTURE
    # Copied so a caller mutating a row — adding an account, say — cannot edit
    # the module-level table every later industry will read.
    return {
        "earnings": [dict(row) for row in rows["earnings"]],
        "deductions": [dict(row) for row in rows["deductions"]],
    }


def structure_plan(
    country: str,
    currency: str,
    abbr: str,
    annual_ctc: Mapping[str, float],
) -> list[dict[str, Any]]:
    """Every Salary Structure an industry needs, ready to insert.

    `annual_ctc` maps a designation to its annual cost to company. A monthly
    demo gets one structure for the whole workforce — the formulas scale off each
    assignment's `base`, so one structure already pays a manager and an operator
    differently. An hourly demo gets one structure per designation, because HRMS
    carries `hour_rate` on the structure and a single shared rate would pay every
    role the same.

    Names carry the company abbreviation the way ERPNext's own company-scoped
    records do, so two industries on one bench never collide. Each entry also
    carries a `designations` list naming who it covers, so the seeder can match
    an employee to their structure without repeating this rule.
    """
    rows = structure_rows(country)
    common: dict[str, Any] = {
        "currency": currency,
        "payroll_frequency": payroll_frequency(country),
        "is_active": "Yes",
        **rows,
    }

    if not is_hourly_payroll(country):
        return [
            {
                "name": f"Monthly Payroll - {abbr}",
                "designations": sorted(annual_ctc),
                "is_default": "Yes",
                **common,
            }
        ]

    return [
        {
            "name": f"Hourly Payroll ({designation}) - {abbr}",
            "designations": [designation],
            "is_default": "No",
            **timesheet_settings(country, annual_ctc[designation]),
            **common,
        }
        for designation in sorted(annual_ctc)
    ]


def _formula_row(component: str, abbr: str, formula: str) -> dict[str, Any]:
    return {
        "salary_component": component,
        "abbr": abbr,
        "amount_based_on_formula": 1,
        "formula": formula,
    }


def _amount_row(component: str, abbr: str, amount: float) -> dict[str, Any]:
    return {
        "salary_component": component,
        "abbr": abbr,
        "amount_based_on_formula": 0,
        "amount": amount,
    }


def _component(name: str, abbr: str, component_type: str, **flags: int) -> dict[str, Any]:
    return {
        "salary_component": name,
        "salary_component_abbr": abbr,
        "type": component_type,
        "depends_on_payment_days": flags.get("depends_on_payment_days", 1),
        "is_tax_applicable": flags.get("is_tax_applicable", 1),
        "exempted_from_income_tax": flags.get("exempted_from_income_tax", 0),
        "round_to_the_nearest_integer": flags.get("round_to_the_nearest_integer", 1),
        "remove_if_zero_valued": flags.get("remove_if_zero_valued", 1),
    }


# ── Monthly (India and every other non-US demo) ───────────────────────────────
# A conventional Indian pay split: half the CTC as Basic, HRA at 40% of Basic,
# a flat conveyance slice and the remainder as Special Allowance.

_INDIA_COMPONENTS = [
    _component("Basic", "B", "Earning"),
    _component("House Rent Allowance", "HRA", "Earning"),
    _component(
        "Conveyance Allowance", "CA", "Earning", is_tax_applicable=0, exempted_from_income_tax=1
    ),
    _component("Special Allowance", "SA", "Earning"),
    _component("Provident Fund", "PF", "Deduction", is_tax_applicable=0),
    _component("Professional Tax", "PT", "Deduction", is_tax_applicable=0),
    _component("Income Tax", "IT", "Deduction", is_tax_applicable=0),
]

_INDIA_STRUCTURE: dict[str, list[dict[str, Any]]] = {
    "earnings": [
        _formula_row("Basic", "B", "base * 0.5"),
        _formula_row("House Rent Allowance", "HRA", "base * 0.2"),
        _formula_row("Conveyance Allowance", "CA", "base * 0.05"),
        _formula_row("Special Allowance", "SA", "base * 0.25"),
    ],
    "deductions": [
        # Statutory PF is 12% of Basic, and Basic is half of base.
        _formula_row("Provident Fund", "PF", "base * 0.06"),
        # Maharashtra's top professional tax slab — a flat monthly figure.
        _amount_row("Professional Tax", "PT", 200),
        _formula_row("Income Tax", "IT", "base * 0.05"),
    ],
}


# ── Hourly (United States) ────────────────────────────────────────────────────
# Basic is what the timesheet's hours are paid against; the deductions are the
# usual US federal withholdings plus an elective retirement contribution.

_US_COMPONENTS = [
    _component("Basic", "B", "Earning"),
    _component("Overtime", "OT", "Earning"),
    _component("Federal Income Tax", "FIT", "Deduction", is_tax_applicable=0),
    _component("Social Security", "SS", "Deduction", is_tax_applicable=0),
    _component("Medicare", "MC", "Deduction", is_tax_applicable=0),
    _component("Retirement Savings", "RS", "Deduction", is_tax_applicable=0),
]

_US_STRUCTURE: dict[str, list[dict[str, Any]]] = {
    "earnings": [
        # Overwritten by hours × hour_rate on a timesheet-based slip; the formula
        # is what a slip raised without a timesheet falls back to.
        _formula_row("Basic", "B", "base"),
        # Nothing to pay until a timesheet says otherwise, and the component is
        # flagged remove_if_zero_valued so an ordinary week's slip stays clean.
        _amount_row("Overtime", "OT", 0),
    ],
    "deductions": [
        _formula_row("Federal Income Tax", "FIT", "base * 0.12"),
        # FICA: 6.2% Social Security and 1.45% Medicare, employee share.
        _formula_row("Social Security", "SS", "base * 0.062"),
        _formula_row("Medicare", "MC", "base * 0.0145"),
        _formula_row("Retirement Savings", "RS", "base * 0.05"),
    ],
}
