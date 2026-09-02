"""
Unit tests for the shared Purchase Receipts seeder (ref #35).

Same approach as test_standard_warehouses.py / test_subcontracting_setup.py:
stub out `_exec` and assert on the Frappe script that would have been sent.
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
SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "211_purchase_receipts.py"


def _load_seeder_class() -> type[BaseSeeder]:
    spec = importlib.util.spec_from_file_location("_test_purchase_receipts", SEEDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.PurchaseReceiptSeeder


def _all_industry_dirs() -> list[Path]:
    return sorted(
        d
        for d in (REPO_ROOT / "industries").iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "industry.yaml").is_file()
    )


def _quality_managed_industry_dirs() -> list[Path]:
    return [
        d
        for d in _all_industry_dirs()
        if "Quality Management" in load_industry_config(d / "industry.yaml").modules
    ]


def _non_quality_managed_industry_dirs() -> list[Path]:
    qm = set(_quality_managed_industry_dirs())
    return [d for d in _all_industry_dirs() if d not in qm]


def _run(industry_dir: Path) -> str:
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


def _payload(script: str) -> dict:
    return json.loads(script.split("payload = json.loads('''", 1)[1].split("''')", 1)[0])


@pytest.mark.unit
class TestPurchaseReceiptSeeder:
    @pytest.mark.parametrize("industry_dir", _all_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_industry(self, industry_dir: Path) -> None:
        """Every industry has Buying + Selling + Stock, so this always fires."""
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Purchase Receipts" in labels

    @pytest.mark.parametrize("industry_dir", _all_industry_dirs(), ids=lambda d: d.name)
    def test_generated_script_is_valid_python(self, industry_dir: Path) -> None:
        script = _run(industry_dir)
        assert script
        ast.parse(script)

    @pytest.mark.parametrize("industry_dir", _quality_managed_industry_dirs(), ids=lambda d: d.name)
    def test_quality_gated_true_for_quality_management_industries(self, industry_dir: Path) -> None:
        payload = _payload(_run(industry_dir))
        assert payload["quality_gated"] is True

    @pytest.mark.parametrize(
        "industry_dir", _non_quality_managed_industry_dirs(), ids=lambda d: d.name
    )
    def test_quality_gated_false_without_quality_management(self, industry_dir: Path) -> None:
        payload = _payload(_run(industry_dir))
        assert payload["quality_gated"] is False

    def test_payload_carries_volume_and_rejection_rate(self) -> None:
        payload = _payload(_run(REPO_ROOT / "industries" / "electrical"))
        assert payload["volume"] > 0
        assert 0 < payload["rejection_rate"] < 1

    def test_script_writes_to_vendor_rejected_warehouse(self) -> None:
        script = _run(REPO_ROOT / "industries" / "electrical")
        assert "Vendor Rejected -" in script

    def test_script_links_quality_inspection_back_to_receipt(self) -> None:
        script = _run(REPO_ROOT / "industries" / "electrical")
        assert "reference_type': 'Purchase Receipt'" in script
        assert "quality_inspection'" in script
