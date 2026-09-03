"""
Unit tests for the shared Delivery Notes seeder (ref #35).

Same approach as test_purchase_receipts.py.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from _seeder_harness import (
    REPO_ROOT,
    SHARED_SEEDERS,
    all_industry_dirs,
    load_seeder_class,
    payload_from_script,
    run_seeder,
)

from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "220_delivery_notes.py"


def _run(industry_dir: Path) -> str:
    seeder_cls = load_seeder_class(SEEDER_PATH, "DeliveryNoteSeeder")
    return run_seeder(seeder_cls, industry_dir)


@pytest.mark.unit
class TestDeliveryNoteSeeder:
    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_industry(self, industry_dir: Path) -> None:
        """Every industry has Selling + Stock, so this always fires."""
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Delivery Notes" in labels

    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_generated_script_is_valid_python(self, industry_dir: Path) -> None:
        script = _run(industry_dir)
        assert script
        ast.parse(script)

    def test_payload_carries_volume_and_seed(self) -> None:
        payload = payload_from_script(_run(REPO_ROOT / "industries" / "garment"))
        assert payload["volume"] > 0
        assert isinstance(payload["seed"], int)

    def test_uses_make_delivery_note_mapper(self) -> None:
        script = _run(REPO_ROOT / "industries" / "garment")
        assert (
            "from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note"
            in script
        )

    def test_payload_carries_partial_delivery_config(self) -> None:
        payload = payload_from_script(_run(REPO_ROOT / "industries" / "garment"))
        assert 0 < payload["partial_share"] < 1
        assert 0 < payload["partial_qty_min"] < payload["partial_qty_max"] <= 1

    def test_partial_deliveries_are_trimmed_before_the_fg_reserve_cap(self) -> None:
        script = _run(REPO_ROOT / "industries" / "garment")
        trim_call = script.index("            trim_partial(dn)")
        cap_call = script.index("        cap_finished_goods(dn)")
        assert trim_call < cap_call
