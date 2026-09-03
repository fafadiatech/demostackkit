"""
Unit tests for the shared Budget Actuals seeder (ref #39).

Two `_exec` round trips (fetch Budget/Budget Account plan, then submit
Journal Entries), so this stubs `_exec` with a small dispatcher — same
approach as test_payment_entries.py. The submit-script behavioural test
executes the generated Frappe script against fake ERPNext stand-ins, same
spirit as test_sales_invoices.py.
"""

from __future__ import annotations

import ast
import json
import random
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from _seeder_harness import REPO_ROOT, SHARED_SEEDERS, all_industry_dirs, load_seeder_class

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import SeedContext
from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "230_budget_actuals.py"

_TODAY = date.today()
_FY_START = (_TODAY - timedelta(days=200)).isoformat()


def _line(**overrides: object) -> dict:
    base = {
        "company": "Test Co",
        "account": "Sales Expenses - TC",
        "budget_amount": 100_000.0,
        "cost_center": "Sales - TC",
        "project": None,
        "credit_account": "Cash - TC",
        "fiscal_year_start": _FY_START,
    }
    base.update(overrides)
    return base


def _run(industry_dir: Path, cache: dict, lines: list[dict], seed: int = 1) -> tuple[str, str]:
    """Run the seeder, returning (plan_fetch_script, submit_script).

    submit_script is "" if the seeder no-oped before the second round trip
    (e.g. no budget lines came back from the plan).
    """
    seeder_cls = load_seeder_class(SEEDER_PATH, "BudgetActualsSeeder")
    calls: list[str] = []

    class Recording(seeder_cls):  # type: ignore[valid-type, misc]
        def _exec(self, script: str, timeout: int = 120) -> str:
            calls.append(script)
            if len(calls) == 1:
                return f"DSK_BUDGET_ACTUALS_PLAN::{json.dumps({'lines': lines})}\n"
            return "DSK_BUDGET_ACTUALS::" + json.dumps({"created": 1, "errors": 0}) + "\n"

    cfg = load_industry_config(industry_dir / "industry.yaml")
    ctx = SeedContext(
        site=cfg.site.name,
        industry_slug=industry_dir.name,
        industry_config=cfg,
        bench_path="/home/frappe/frappe-bench",
        random=random.Random(seed),
    )
    for key, value in cache.items():
        ctx.cache_set(key, value)
    Recording(ctx).run()
    return (calls[0] if calls else "", calls[1] if len(calls) > 1 else "")


def _make_seeder(seed: int = 1) -> Any:
    seeder_cls = load_seeder_class(SEEDER_PATH, "BudgetActualsSeeder")
    seeder = seeder_cls.__new__(seeder_cls)
    seeder.ctx = SeedContext(
        site="x",
        industry_slug="garment",
        industry_config=load_industry_config(
            REPO_ROOT / "industries" / "garment" / "industry.yaml"
        ),
        bench_path="/home/frappe/frappe-bench",
        random=random.Random(seed),
    )
    return seeder


class _FakeJournalEntry:
    """Stands in for the ERPNext Journal Entry the submit script builds."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.__dict__.update(data)
        self.name = "JE-AUTO-0001"
        self.docstatus = 0
        self.accounts = data.get("accounts", [])

    def insert(self, ignore_permissions: bool = False) -> None:
        return None

    def submit(self) -> None:
        self.docstatus = 1


def _exec_submit_script(script: str) -> list[_FakeJournalEntry]:
    """Execute the seeder's submit script against fake ERPNext stand-ins."""
    created: list[_FakeJournalEntry] = []

    def fake_get_doc(data: dict[str, Any]) -> _FakeJournalEntry:
        je = _FakeJournalEntry(data)
        created.append(je)
        return je

    fake_frappe = SimpleNamespace(
        get_doc=fake_get_doc,
        db=SimpleNamespace(commit=lambda: None),
    )
    exec(compile(script, "<budget actuals submit>", "exec"), {"frappe": fake_frappe, "json": json})
    return created


@pytest.mark.unit
class TestBudgetActualsSeeder:
    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_industry(self, industry_dir: Path) -> None:
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Budget Actuals" in labels

    def test_noop_without_budget_lines(self) -> None:
        plan_script, submit_script = _run(REPO_ROOT / "industries" / "garment", cache={}, lines=[])
        assert plan_script
        assert submit_script == ""

    def test_generated_scripts_are_valid_python(self) -> None:
        plan_script, submit_script = _run(
            REPO_ROOT / "industries" / "garment", cache={}, lines=[_line()]
        )
        assert plan_script
        ast.parse(plan_script)
        assert submit_script
        ast.parse(submit_script)

    def test_plan_filters_submitted_budgets_and_credits_cash(self) -> None:
        plan_script, _ = _run(REPO_ROOT / "industries" / "garment", cache={}, lines=[_line()])
        assert "'docstatus': 1" in plan_script
        assert "Cash - {abbr}" in plan_script
        assert "default_bank_account" not in plan_script

    def test_skips_zero_budget_lines(self) -> None:
        _, submit_script = _run(
            REPO_ROOT / "industries" / "garment",
            cache={},
            lines=[_line(budget_amount=0.0)],
        )
        assert submit_script == ""

    def test_skips_lines_without_cost_center(self) -> None:
        seeder = _make_seeder(seed=3)
        entries = seeder._build_entries([_line(cost_center=None, project="PROJ-0001")])
        assert entries == []

    def test_project_budget_line_carries_project_and_cost_center(self) -> None:
        """P&L GL entries require a Cost Center even when the Budget is against a Project."""
        seeder = _make_seeder(seed=3)
        lines = [_line(cost_center="Main - TC", project="PROJ-0001")]
        entries = seeder._build_entries(lines)
        assert entries
        for e in entries:
            assert e["project"] == "PROJ-0001"
            assert e["cost_center"] == "Main - TC"

    def test_entry_dates_stay_within_fiscal_year_and_never_future(self) -> None:
        seeder = _make_seeder(seed=7)
        fy_start = date.fromisoformat(_FY_START)
        for seed in range(20):
            seeder.ctx.random = random.Random(seed)
            entries = seeder._build_entries([_line()])
            for e in entries:
                posted = date.fromisoformat(e["posting_date"])
                assert fy_start <= posted <= _TODAY

    def test_entry_amounts_sum_close_to_scenario_target(self) -> None:
        # Not an exact scenario check (scenario is randomised), just a sanity
        # bound: total posted per line stays within the widest possible
        # scenario multiplier range (0.55x - 1.45x of budget_amount).
        seeder = _make_seeder(seed=11)
        budget_amount = 100_000.0
        entries = seeder._build_entries([_line(budget_amount=budget_amount)])
        total = sum(e["amount"] for e in entries)
        assert 0.5 * budget_amount <= total <= 1.5 * budget_amount

    def test_submit_script_posts_journal_entries_with_cost_center(self) -> None:
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", cache={}, lines=[_line()])
        assert submit_script
        created = _exec_submit_script(submit_script)
        assert created
        for je in created:
            assert je.docstatus == 1
            assert je.voucher_type == "Journal Entry"
            debit = je.accounts[0]
            credit = je.accounts[1]
            assert debit["account"] == "Sales Expenses - TC"
            assert debit["cost_center"] == "Sales - TC"
            assert credit["account"] == "Cash - TC"
            assert debit["debit_in_account_currency"] == credit["credit_in_account_currency"]
