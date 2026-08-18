"""
Unit tests for the country-aware payroll shapes in demostackkit.seeder.payroll.

These feed straight into submitted Salary Structures and Salary Structure
Assignments, which a demo cannot correct after the fact without cancelling
payroll, so the arithmetic and the formula hygiene are pinned here.
"""

from __future__ import annotations

import re

import pytest

from demostackkit.seeder.payroll import (
    WORK_HOURS_PER_YEAR,
    hour_rate,
    is_hourly_payroll,
    payroll_frequency,
    period_base,
    salary_components,
    structure_plan,
    structure_rows,
    timesheet_settings,
    weekly_offs,
)

INDIA = "India"
US = "United States"

#: Designation → annual cost to company, shaped like an industry's own table.
GRADES = {"Plant Operator": 384_000, "Production Manager": 1_140_000}


def _identifiers(formula: str) -> set[str]:
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula))


@pytest.mark.unit
class TestPayrollConvention:
    def test_only_the_us_pays_hourly(self) -> None:
        assert is_hourly_payroll(US)
        for country in (INDIA, "United Kingdom", "Germany", "Australia"):
            assert not is_hourly_payroll(country)

    def test_frequency_follows_the_convention(self) -> None:
        assert payroll_frequency(US) == "Weekly"
        assert payroll_frequency(INDIA) == "Monthly"

    def test_us_gets_a_two_day_weekend(self) -> None:
        assert weekly_offs(US) == ["Saturday", "Sunday"]
        assert weekly_offs(INDIA) == ["Sunday"]


@pytest.mark.unit
class TestPayAmounts:
    def test_hour_rate_is_the_annual_salary_over_2080_hours(self) -> None:
        assert WORK_HOURS_PER_YEAR == 2080
        assert hour_rate(62_400) == 30.0
        assert hour_rate(145_600) == 70.0

    def test_monthly_base_is_a_twelfth_of_the_annual_ctc(self) -> None:
        assert period_base(1_140_000, INDIA) == 95_000.0
        assert period_base(264_000, INDIA) == 22_000.0

    def test_hourly_base_is_one_week_at_the_hourly_rate(self) -> None:
        # 62,400 a year is $30/hr, so a 40-hour week is 1,200.
        assert period_base(62_400, US) == 1_200.0

    def test_a_period_of_base_annualises_back_to_the_ctc(self) -> None:
        assert round(period_base(1_140_000, INDIA) * 12) == 1_140_000
        assert round(period_base(62_400, US) * 52) == 62_400


@pytest.mark.unit
class TestSalaryComponents:
    @pytest.mark.parametrize("country", [INDIA, US])
    def test_abbreviations_are_unique(self, country: str) -> None:
        abbrs = [c["salary_component_abbr"] for c in salary_components(country)]
        assert len(abbrs) == len(set(abbrs))

    @pytest.mark.parametrize("country", [INDIA, US])
    def test_abbreviations_are_usable_in_a_formula(self, country: str) -> None:
        """HRMS evaluates formulas as Python, so an abbr must be an identifier."""
        for component in salary_components(country):
            assert component["salary_component_abbr"].isidentifier()

    @pytest.mark.parametrize("country", [INDIA, US])
    def test_every_component_is_an_earning_or_a_deduction(self, country: str) -> None:
        for component in salary_components(country):
            assert component["type"] in {"Earning", "Deduction"}

    @pytest.mark.parametrize("country", [INDIA, US])
    def test_every_structure_row_has_a_component_master(self, country: str) -> None:
        defined = {c["salary_component"] for c in salary_components(country)}
        rows = structure_rows(country)
        for table in ("earnings", "deductions"):
            for row in rows[table]:
                assert row["salary_component"] in defined

    def test_the_two_countries_get_different_deductions(self) -> None:
        india = {c["salary_component"] for c in salary_components(INDIA)}
        us = {c["salary_component"] for c in salary_components(US)}
        assert "Provident Fund" in india and "Provident Fund" not in us
        assert "Social Security" in us and "Social Security" not in india


@pytest.mark.unit
class TestStructureRows:
    @pytest.mark.parametrize("country", [INDIA, US])
    def test_formulas_read_base_and_nothing_else(self, country: str) -> None:
        """A formula naming another component's abbr trips HRMS' double-proration
        guard, which fails the Salary Structure at insert. `base` is the only safe
        variable, so no row may reference anything else."""
        rows = structure_rows(country)
        for table in ("earnings", "deductions"):
            for row in rows[table]:
                if row.get("formula"):
                    assert _identifiers(row["formula"]) == {"base"}

    @pytest.mark.parametrize("country", [INDIA, US])
    def test_earnings_add_up_to_base(self, country: str) -> None:
        earnings = structure_rows(country)["earnings"]
        total = sum(
            eval(row["formula"], {"base": 1.0})  # noqa: S307 - our own formulas
            if row.get("amount_based_on_formula")
            else row["amount"]
            for row in earnings
        )
        assert total == pytest.approx(1.0)

    @pytest.mark.parametrize("country", [INDIA, US])
    def test_deductions_leave_something_to_take_home(self, country: str) -> None:
        deductions = structure_rows(country)["deductions"]
        rate = sum(
            eval(row["formula"], {"base": 1.0})  # noqa: S307 - our own formulas
            for row in deductions
            if row.get("amount_based_on_formula")
        )
        assert 0 < rate < 0.5

    def test_rows_are_copies(self) -> None:
        """An industry that edits a row must not rewrite it for every other one."""
        structure_rows(INDIA)["earnings"][0]["formula"] = "base * 999"
        assert structure_rows(INDIA)["earnings"][0]["formula"] == "base * 0.5"


@pytest.mark.unit
class TestStructurePlan:
    def test_monthly_industries_get_one_structure_for_everyone(self) -> None:
        plans = structure_plan(INDIA, "INR", "ACH", GRADES)
        assert len(plans) == 1
        plan = plans[0]
        assert plan["name"] == "Monthly Payroll - ACH"
        assert plan["payroll_frequency"] == "Monthly"
        assert plan["is_default"] == "Yes"
        assert sorted(plan["designations"]) == sorted(GRADES)
        # Nothing timesheet-shaped leaks into a monthly structure.
        assert "hour_rate" not in plan
        assert "salary_slip_based_on_timesheet" not in plan

    def test_hourly_industries_get_a_structure_per_grade(self) -> None:
        plans = structure_plan(US, "USD", "NTH", GRADES)
        assert len(plans) == len(GRADES)
        for plan in plans:
            assert plan["payroll_frequency"] == "Weekly"
            assert plan["salary_slip_based_on_timesheet"] == 1
            assert plan["salary_component"] == "Basic"
            (designation,) = plan["designations"]
            assert plan["hour_rate"] == hour_rate(GRADES[designation])
            assert plan["name"] == f"Hourly Payroll ({designation}) - NTH"

    def test_every_designation_is_covered_exactly_once(self) -> None:
        for country in (INDIA, US):
            covered = [
                d
                for plan in structure_plan(country, "USD", "X", GRADES)
                for d in plan["designations"]
            ]
            assert sorted(covered) == sorted(GRADES)

    def test_currency_is_carried_through(self) -> None:
        assert structure_plan(INDIA, "INR", "ACH", GRADES)[0]["currency"] == "INR"
        assert structure_plan(US, "USD", "NTH", GRADES)[0]["currency"] == "USD"


@pytest.mark.unit
class TestTimesheetSettings:
    def test_monthly_countries_get_nothing(self) -> None:
        assert timesheet_settings(INDIA, 1_140_000) == {}

    def test_us_gets_the_timesheet_trio(self) -> None:
        settings = timesheet_settings(US, 62_400)
        assert settings == {
            "salary_slip_based_on_timesheet": 1,
            "salary_component": "Basic",
            "hour_rate": 30.0,
        }
