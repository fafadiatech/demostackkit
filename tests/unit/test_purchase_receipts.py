"""
Unit tests for the shared Purchase Receipts seeder (ref #35).

Same approach as test_standard_warehouses.py / test_subcontracting_setup.py:
stub out `_exec` and assert on the Frappe script that would have been sent.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from _seeder_harness import (
    REPO_ROOT,
    SHARED_SEEDERS,
    all_industry_dirs,
    industry_dirs_with_module,
    industry_dirs_without_module,
    load_seeder_class,
    payload_from_script,
    run_seeder,
)

from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "211_purchase_receipts.py"


def _run(industry_dir: Path) -> str:
    seeder_cls = load_seeder_class(SEEDER_PATH, "PurchaseReceiptSeeder")
    return run_seeder(seeder_cls, industry_dir)


@pytest.mark.unit
class TestPurchaseReceiptSeeder:
    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_industry(self, industry_dir: Path) -> None:
        """Every industry has Buying + Selling + Stock, so this always fires."""
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Purchase Receipts" in labels

    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_generated_script_is_valid_python(self, industry_dir: Path) -> None:
        script = _run(industry_dir)
        assert script
        ast.parse(script)

    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_with_module("Quality Management"), ids=lambda d: d.name
    )
    def test_quality_gated_true_for_quality_management_industries(self, industry_dir: Path) -> None:
        payload = payload_from_script(_run(industry_dir))
        assert payload["quality_gated"] is True

    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_without_module("Quality Management"), ids=lambda d: d.name
    )
    def test_quality_gated_false_without_quality_management(self, industry_dir: Path) -> None:
        payload = payload_from_script(_run(industry_dir))
        assert payload["quality_gated"] is False

    def test_payload_carries_volume_and_rejection_rate(self) -> None:
        payload = payload_from_script(_run(REPO_ROOT / "industries" / "electrical"))
        assert payload["volume"] > 0
        assert 0 < payload["rejection_rate"] < 1

    def test_script_writes_to_vendor_rejected_warehouse(self) -> None:
        script = _run(REPO_ROOT / "industries" / "electrical")
        assert "Vendor Rejected -" in script

    def test_script_links_quality_inspection_back_to_receipt(self) -> None:
        script = _run(REPO_ROOT / "industries" / "electrical")
        assert "reference_type': 'Purchase Receipt'" in script
        assert "quality_inspection'" in script
