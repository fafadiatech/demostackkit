"""
Unit tests for the shared Subcontracting Setup seeder (ref #32).

Same approach as test_standard_warehouses.py: stub out `_exec` and assert on
the Frappe script that would have been sent, rather than hitting a live site.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from _seeder_harness import (
    REPO_ROOT,
    SHARED_SEEDERS,
    industry_dirs_with_module,
    industry_dirs_without_module,
    load_seeder_class,
    payload_from_script,
    run_seeder,
)

from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "01_master" / "71_subcontracting.py"


def _run(industry_dir: Path) -> str:
    seeder_cls = load_seeder_class(SEEDER_PATH, "SubcontractingSetupSeeder")
    return run_seeder(seeder_cls, industry_dir)


@pytest.mark.unit
class TestSubcontractingSetupSeeder:
    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_with_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_runs_for_every_manufacturing_industry(self, industry_dir: Path) -> None:
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Subcontracting Setup" in labels

    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_without_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_no_op_without_manufacturing_module(self, industry_dir: Path) -> None:
        assert _run(industry_dir) == ""

    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_with_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_generated_script_is_valid_python(self, industry_dir: Path) -> None:
        script = _run(industry_dir)
        assert script
        ast.parse(script)

    def test_payload_carries_supplier_group_and_subcontractors(self) -> None:
        payload = payload_from_script(_run(REPO_ROOT / "industries" / "electrical"))
        assert payload["supplier_group"] == "Sub Contractors"
        assert len(payload["subcontractors"]) >= 2
        assert payload["max_items"] > 0
