"""
Unit tests for the shared Subcontracting Setup seeder (ref #32).

Same approach as test_standard_warehouses.py: stub out `_exec` and assert on
the Frappe script that would have been sent, rather than hitting a live site.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import random
from pathlib import Path

import pytest

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import BaseSeeder, SeedContext
from demostackkit.seeder.loader import discover_seeders

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED_SEEDERS = REPO_ROOT / "demostackkit" / "seeders"
SEEDER_PATH = SHARED_SEEDERS / "01_master" / "71_subcontracting.py"


def _load_seeder_class() -> type[BaseSeeder]:
    spec = importlib.util.spec_from_file_location("_test_subcontracting_setup", SEEDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.SubcontractingSetupSeeder


def _all_industry_dirs() -> list[Path]:
    return sorted(
        d
        for d in (REPO_ROOT / "industries").iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "industry.yaml").is_file()
    )


def _manufacturing_industry_dirs() -> list[Path]:
    return [
        d
        for d in _all_industry_dirs()
        if "Manufacturing" in load_industry_config(d / "industry.yaml").modules
    ]


def _run(industry_dir: Path) -> str:
    """Run the seeder against an industry, returning the script it would execute."""
    captured: list[str] = []
    seeder_cls = _load_seeder_class()

    class Recording(seeder_cls):  # type: ignore[valid-type, misc]
        def _exec(self, script: str, timeout: int = 120) -> str:
            captured.append(script)
            return ""

    cfg = load_industry_config(industry_dir / "industry.yaml")
    ctx = SeedContext(
        site=cfg.site.name,
        industry_slug=industry_dir.name,
        industry_config=cfg,
        bench_path="/home/frappe/frappe-bench",
        random=random.Random(cfg.seed.random_seed),
    )
    Recording(ctx).run()
    return captured[0] if captured else ""


@pytest.mark.unit
class TestSubcontractingSetupSeeder:
    @pytest.mark.parametrize("industry_dir", _manufacturing_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_manufacturing_industry(self, industry_dir: Path) -> None:
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Subcontracting Setup" in labels

    @pytest.mark.parametrize(
        "industry_dir",
        [d for d in _all_industry_dirs() if d not in _manufacturing_industry_dirs()],
        ids=lambda d: d.name,
    )
    def test_no_op_without_manufacturing_module(self, industry_dir: Path) -> None:
        assert _run(industry_dir) == ""

    @pytest.mark.parametrize("industry_dir", _manufacturing_industry_dirs(), ids=lambda d: d.name)
    def test_generated_script_is_valid_python(self, industry_dir: Path) -> None:
        script = _run(industry_dir)
        assert script
        ast.parse(script)

    def test_payload_carries_supplier_group_and_subcontractors(self) -> None:
        script = _run(REPO_ROOT / "industries" / "electrical")
        payload = json.loads(script.split("payload = json.loads('''", 1)[1].split("''')", 1)[0])
        assert payload["supplier_group"] == "Sub Contractors"
        assert len(payload["subcontractors"]) >= 2
        assert payload["max_items"] > 0
