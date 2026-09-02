"""
Unit tests for the shared Delivery Notes seeder (ref #35).

Same approach as test_purchase_receipts.py.
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
SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "220_delivery_notes.py"


def _load_seeder_class() -> type[BaseSeeder]:
    spec = importlib.util.spec_from_file_location("_test_delivery_notes", SEEDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DeliveryNoteSeeder


def _all_industry_dirs() -> list[Path]:
    return sorted(
        d
        for d in (REPO_ROOT / "industries").iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "industry.yaml").is_file()
    )


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


@pytest.mark.unit
class TestDeliveryNoteSeeder:
    @pytest.mark.parametrize("industry_dir", _all_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_industry(self, industry_dir: Path) -> None:
        """Every industry has Selling + Stock, so this always fires."""
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Delivery Notes" in labels

    @pytest.mark.parametrize("industry_dir", _all_industry_dirs(), ids=lambda d: d.name)
    def test_generated_script_is_valid_python(self, industry_dir: Path) -> None:
        script = _run(industry_dir)
        assert script
        ast.parse(script)

    def test_payload_carries_volume_and_seed(self) -> None:
        script = _run(REPO_ROOT / "industries" / "garment")
        payload = json.loads(script.split("payload = json.loads('''", 1)[1].split("''')", 1)[0])
        assert payload["volume"] > 0
        assert isinstance(payload["seed"], int)

    def test_uses_make_delivery_note_mapper(self) -> None:
        script = _run(REPO_ROOT / "industries" / "garment")
        assert (
            "from erpnext.selling.doctype.sales_order.sales_order import make_delivery_note"
            in script
        )
