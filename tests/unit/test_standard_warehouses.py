"""
Unit tests for the shared Standard Warehouses seeder.

The seeder builds a Frappe script as a string and hands it to a container, so the
tests stub out `_exec` and assert on what would have been sent: which warehouses
an industry gets, and that the script is syntactically valid Python.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import pytest
from _seeder_harness import (
    REPO_ROOT,
    SHARED_SEEDERS,
    all_industry_dirs,
    load_seeder_class,
    run_seeder,
)

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "01_master" / "61_standard_warehouses.py"


def _run(industry_dir: Path) -> str:
    seeder_cls = load_seeder_class(SEEDER_PATH, "StandardWarehouseSeeder")
    return run_seeder(seeder_cls, industry_dir)


def _warehouse_names(script: str) -> list[str]:
    payload = re.search(r"warehouses = json\.loads\('''(.*?)'''\)", script, re.DOTALL)
    assert payload, "seeder script does not carry a warehouse payload"
    return [wh["warehouse_name"] for wh in json.loads(payload.group(1))]


@pytest.mark.unit
class TestStandardWarehouseSeeder:
    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_industry(self, industry_dir: Path) -> None:
        """Discovery must pick the shared seeder up for every industry package."""
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Standard Warehouses" in labels

    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_seeds_scrap_and_rejected_everywhere(self, industry_dir: Path) -> None:
        names = _warehouse_names(_run(industry_dir))
        assert "Scrap" in names
        assert "Rejected" in names

    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_seeds_vendor_rejected_and_customer_returns_everywhere(
        self, industry_dir: Path
    ) -> None:
        """ref #35: RTV/Customer Return flows need their own isolated warehouses."""
        names = _warehouse_names(_run(industry_dir))
        assert "Vendor Rejected" in names
        assert "Customer Returns" in names

    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_rework_follows_the_manufacturing_module(self, industry_dir: Path) -> None:
        cfg = load_industry_config(industry_dir / "industry.yaml")
        names = _warehouse_names(_run(industry_dir))
        assert ("Rework" in names) is ("Manufacturing" in cfg.modules)

    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_generated_script_is_valid_python(self, industry_dir: Path) -> None:
        ast.parse(_run(industry_dir))

    def test_only_the_rejected_warehouse_carries_the_flag(self) -> None:
        script = _run(REPO_ROOT / "industries" / "garment")
        payload = re.search(r"warehouses = json\.loads\('''(.*?)'''\)", script, re.DOTALL)
        assert payload
        flagged = [
            wh["warehouse_name"]
            for wh in json.loads(payload.group(1))
            if wh["is_rejected_warehouse"]
        ]
        assert flagged == ["Rejected"]

    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_industries_do_not_redeclare_the_standard_warehouses(self, industry_dir: Path) -> None:
        """A themed warehouse tree must not duplicate what the shared seeder owns."""
        seeder = industry_dir / "seeders" / "01_master" / "06_warehouses.py"
        if not seeder.is_file():
            pytest.skip(f"{industry_dir.name} seeds no warehouses of its own")
        declared = set(re.findall(r'"warehouse_name": "([^"]+)"', seeder.read_text()))
        assert not declared & {"Scrap", "Rejected", "Rework"}
