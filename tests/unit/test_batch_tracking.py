"""
Unit tests for the shared Batch/Serial Tracking seeder (ref #4).

Same approach as test_subcontracting_setup.py: stub out `_exec` and assert on
the Frappe script that would have been sent, rather than hitting a live site.
"""

from __future__ import annotations

import ast
import random
import types
from pathlib import Path
from typing import Any

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

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import SeedContext
from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "01_master" / "86_batch_tracking.py"


def _run(industry_dir: Path) -> str:
    """Run against the industry's real industry.yaml (batch_tracking as authored)."""
    seeder_cls = load_seeder_class(SEEDER_PATH, "BatchTrackingSeeder")
    return run_seeder(seeder_cls, industry_dir)


def _run_with_override(industry_dir: Path, **batch_tracking_overrides: Any) -> str:
    """Run with one or more `seed.batch_tracking.*` fields overridden in memory."""
    seeder_cls = load_seeder_class(SEEDER_PATH, "BatchTrackingSeeder")
    captured: list[str] = []

    class Recording(seeder_cls):  # type: ignore[valid-type, misc]
        def _exec(self, script: str, timeout: int = 120) -> str:
            captured.append(script)
            return ""

    cfg = load_industry_config(industry_dir / "industry.yaml")
    for key, value in batch_tracking_overrides.items():
        setattr(cfg.seed.batch_tracking, key, value)
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
class TestBatchTrackingSeederGating:
    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_with_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_discovered_for_manufacturing_industries(self, industry_dir: Path) -> None:
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Batch/Serial Tracking (raw-material lots & FG serials)" in labels

    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_without_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_no_op_without_manufacturing_module(self, industry_dir: Path) -> None:
        assert _run(industry_dir) == ""

    def test_no_op_when_disabled_even_with_manufacturing_module(self) -> None:
        # All 11 Manufacturing industries ship with batch_tracking.enabled: true
        # (ref #4 rollout) -- explicitly override it off here to prove the gate
        # itself works, independent of what any single industry.yaml currently sets.
        script = _run_with_override(REPO_ROOT / "industries" / "evmfg", enabled=False)
        assert script == ""

    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_with_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_runs_for_every_manufacturing_industry_as_shipped(self, industry_dir: Path) -> None:
        """Every Manufacturing industry ships with batch_tracking.enabled: true."""
        assert _run(industry_dir) != ""


@pytest.mark.unit
class TestBatchTrackingSeederScripts:
    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_with_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_generated_script_is_valid_python(self, industry_dir: Path) -> None:
        script = _run(industry_dir)
        assert script
        ast.parse(script)

    def test_component_and_top_level_fg_split_uses_bom_item_query(self) -> None:
        script = _run(REPO_ROOT / "industries" / "evmfg")
        assert "'BOM Item'" in script
        assert "top_level_fg_codes = fg_item_codes - component_codes" in script

    def test_components_get_batch_flags(self) -> None:
        script = _run(REPO_ROOT / "industries" / "evmfg")
        assert "'has_batch_no': 1" in script
        assert "'create_new_batch': 1" in script
        assert "'batch_number_series':" in script

    def test_top_level_fg_gets_serial_flags_by_default(self) -> None:
        script = _run(REPO_ROOT / "industries" / "evmfg")  # serialize_top_level_fg: true
        assert "'has_serial_no': 1" in script
        assert "'serial_no_series':" in script

    def test_top_level_fg_batch_tracked_when_not_serializing(self) -> None:
        script = _run(REPO_ROOT / "industries" / "ingredientmfg")  # serialize_top_level_fg: false
        assert "serialize_top_level_fg = payload['serialize_top_level_fg']" in script
        payload = payload_from_script(script)
        assert payload["serialize_top_level_fg"] is False


@pytest.mark.unit
class TestBatchTrackingSeederBehaviour:
    """Behavioral regression: runs the generated script against fakes so a
    rewrite of the component/FG split still fails even if the source strings
    are reworded."""

    def test_split_flags_components_and_top_level_fg_correctly(self) -> None:
        script = _run(REPO_ROOT / "industries" / "evmfg")

        # A two-level BOM tree: FG-1 consumes SUB-1 and RM-1; SUB-1 itself has
        # its own default BOM consuming RM-2 (a genuine sub-assembly, like
        # evmfg's MAT-BRAKE-DISC) -- so SUB-1 must be batch-tracked (it's a
        # component of FG-1's BOM), never serial-tracked, even though it also
        # has its own BOM.
        bom_rows = [
            {"name": "BOM-FG-1", "item": "FG-1"},
            {"name": "BOM-SUB-1", "item": "SUB-1"},
        ]
        bom_items = {
            "BOM-FG-1": [{"item_code": "SUB-1"}, {"item_code": "RM-1"}],
            "BOM-SUB-1": [{"item_code": "RM-2"}],
        }
        item_meta = {
            "FG-1": {"is_stock_item": 1, "has_batch_no": 0, "has_serial_no": 0},
            "SUB-1": {"is_stock_item": 1, "has_batch_no": 0, "has_serial_no": 0},
            "RM-1": {"is_stock_item": 1, "has_batch_no": 0, "has_serial_no": 0},
            "RM-2": {"is_stock_item": 1, "has_batch_no": 0, "has_serial_no": 0},
            # Already flagged -- must be skipped (idempotency).
            "ALREADY-FLAGGED": {"is_stock_item": 1, "has_batch_no": 1, "has_serial_no": 0},
            # Non-stock -- must be skipped (invalid to batch/serial-track).
            "NON-STOCK-SVC": {"is_stock_item": 0, "has_batch_no": 0, "has_serial_no": 0},
        }
        bom_rows.append({"name": "BOM-EXTRA", "item": "ALREADY-FLAGGED"})
        bom_items["BOM-EXTRA"] = [{"item_code": "NON-STOCK-SVC"}]

        def fake_get_all(doctype, filters=None, fields=None, **kwargs):
            if doctype == "BOM":
                return [types.SimpleNamespace(**row) for row in bom_rows]
            if doctype == "BOM Item":
                parents = filters["parent"][1]
                rows = [row for p in parents for row in bom_items.get(p, [])]
                return [types.SimpleNamespace(**row) for row in rows]
            if doctype == "Item":
                names = filters["name"][1]
                return [
                    types.SimpleNamespace(name=n, **item_meta[n]) for n in names if n in item_meta
                ]
            return []

        set_value_calls: dict[str, dict] = {}

        def fake_set_value(doctype, name, values):
            set_value_calls[name] = values

        fake_frappe = types.SimpleNamespace(
            get_all=fake_get_all,
            db=types.SimpleNamespace(set_value=fake_set_value, commit=lambda: None),
        )

        exec(compile(script, "<batch tracking seeder>", "exec"), {"frappe": fake_frappe})

        # FG-1 is the only top-level FG (never a component); SUB-1/RM-1/RM-2
        # are all components (SUB-1 despite also having its own BOM).
        assert set_value_calls["FG-1"] == {
            "has_serial_no": 1,
            "serial_no_series": "FG-1-SN-.####",
        }
        for code in ("SUB-1", "RM-1", "RM-2"):
            assert set_value_calls[code] == {
                "has_batch_no": 1,
                "create_new_batch": 1,
                "batch_number_series": f"{code}-BATCH-.####",
            }
        assert "ALREADY-FLAGGED" not in set_value_calls
        assert "NON-STOCK-SVC" not in set_value_calls
