"""
Unit tests for the shared Quality Inspection Templates seeder (ref #1, phase 1).
"""

from __future__ import annotations

import ast
import random
from pathlib import Path

import pytest
from _seeder_harness import (
    REPO_ROOT,
    SHARED_SEEDERS,
    industry_dirs_with_module,
    load_seeder_class,
    run_seeder,
)

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import SeedContext
from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "01_master" / "95_quality_inspection_templates.py"

_CACHE = {
    "qc_operation_name": "Solar QC Sign-off",
    "qc_inspection_parameters": [
        ("Efficiency %", 18, 22),
        ("Power Output (W)", 300, 400),
    ],
}


@pytest.mark.unit
class TestQualityInspectionTemplateSeeder:
    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_with_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_discovered_for_manufacturing_industries(self, industry_dir: Path) -> None:
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Quality Inspection Templates" in labels

    def test_no_op_when_no_qc_operation_cached(self) -> None:
        """An industry's `08_operations.py` didn't cache a QC operation (or
        hasn't run yet) — the seeder must not touch the container at all."""
        seeder_cls = load_seeder_class(SEEDER_PATH, "QualityInspectionTemplateSeeder")
        cfg = load_industry_config(REPO_ROOT / "industries" / "solar" / "industry.yaml")
        ctx = SeedContext(
            site=cfg.site.name,
            industry_slug="solar",
            industry_config=cfg,
            bench_path="/home/frappe/frappe-bench",
            random=random.Random(1),
        )

        captured: list[str] = []

        class Recording(seeder_cls):  # type: ignore[valid-type, misc]
            def _exec(self, script: str, timeout: int = 120) -> str:
                captured.append(script)
                return ""

        Recording(ctx).run()
        assert captured == []

    def test_generates_template_and_links_operation(self) -> None:
        seeder_cls = load_seeder_class(SEEDER_PATH, "QualityInspectionTemplateSeeder")
        script = run_seeder(seeder_cls, REPO_ROOT / "industries" / "solar", cache=_CACHE)
        assert script, "seeder should not no-op when qc_operation_name is cached"
        ast.parse(script)
        assert "Solar QC Sign-off" in script
        assert "Solar QC Sign-off QC Template" in script
        assert "Efficiency %" in script
        assert "quality_inspection_template" in script
