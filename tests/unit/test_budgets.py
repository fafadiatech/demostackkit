"""
Unit tests for the shared Budgets seeder (ref #20, submit fix for #39).

Budget is submittable in ERPNext v15, and Budget Variance Report only reads
docstatus=1 — so the generated script must submit every Budget it inserts.
"""

from __future__ import annotations

import ast

import pytest
from _seeder_harness import (
    REPO_ROOT,
    SHARED_SEEDERS,
    all_industry_dirs,
    load_seeder_class,
    run_seeder,
)

from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "01_master" / "89_budgets.py"


def _run(industry_dir) -> str:
    seeder_cls = load_seeder_class(SEEDER_PATH, "BudgetSeeder")
    return run_seeder(seeder_cls, industry_dir)


@pytest.mark.unit
class TestBudgetSeeder:
    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_industry(self, industry_dir) -> None:
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Budgets" in labels

    def test_generated_script_is_valid_python(self) -> None:
        script = _run(REPO_ROOT / "industries" / "electrical")
        assert script
        ast.parse(script)

    def test_submits_budgets_after_insert(self) -> None:
        """ref #39: without submit(), Budget Variance Report never sees the budgets."""
        script = _run(REPO_ROOT / "industries" / "electrical")
        assert "doc.insert(ignore_permissions=True)" in script
        assert "doc.submit()" in script
        # Both Cost Center and Project budgets go through the same insert+submit path.
        assert script.count("doc.submit()") >= 2
