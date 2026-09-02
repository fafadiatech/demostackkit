"""
Unit tests for the shared Customer Returns seeder (ref #35).

Driven by the "delivery_notes" and "sales_invoices" caches
`220_delivery_notes.py` / `221_sales_invoices.py` populate, so tests seed
those caches directly rather than running the full seeder chain.
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

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED_SEEDERS = REPO_ROOT / "demostackkit" / "seeders"
SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "222_customer_returns.py"

_DN_NAMES = [f"DN-{i:04d}" for i in range(10)]
_SALES_INVOICES = {dn: f"SI-{i:04d}" for i, dn in enumerate(_DN_NAMES)}


def _load_seeder_class() -> type[BaseSeeder]:
    spec = importlib.util.spec_from_file_location("_test_customer_returns", SEEDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.CustomerReturnSeeder


def _quality_managed_industry_dir() -> Path:
    for d in sorted((REPO_ROOT / "industries").iterdir()):
        if not d.is_dir() or d.name.startswith("_") or not (d / "industry.yaml").is_file():
            continue
        if "Quality Management" in load_industry_config(d / "industry.yaml").modules:
            return d
    pytest.skip("no Quality Management industry found")


def _run(industry_dir: Path, dn_names: list[str], sales_invoices: dict) -> str:
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
    ctx.cache_set("delivery_notes", dn_names)
    ctx.cache_set("sales_invoices", sales_invoices)
    Recording(ctx).run()
    return captured[0] if captured else ""


@pytest.mark.unit
class TestCustomerReturnSeeder:
    def test_no_op_without_cached_data(self) -> None:
        industry_dir = _quality_managed_industry_dir()
        assert _run(industry_dir, [], {}) == ""

    def test_generated_script_is_valid_python(self) -> None:
        industry_dir = _quality_managed_industry_dir()
        script = _run(industry_dir, _DN_NAMES, _SALES_INVOICES)
        assert script
        ast.parse(script)

    def test_splits_sample_into_physical_and_writeoff(self) -> None:
        industry_dir = _quality_managed_industry_dir()
        script = _run(industry_dir, _DN_NAMES, _SALES_INVOICES)
        payload = json.loads(script.split("payload = json.loads('''", 1)[1].split("''')", 1)[0])
        assert set(payload["physical"]) | set(payload["writeoff"]) <= set(_DN_NAMES)
        assert not (set(payload["physical"]) & set(payload["writeoff"]))
        assert payload["physical"] or payload["writeoff"]

    def test_physical_returns_redirect_to_customer_returns_warehouse(self) -> None:
        industry_dir = _quality_managed_industry_dir()
        script = _run(industry_dir, _DN_NAMES, _SALES_INVOICES)
        assert "Customer Returns -" in script
        assert "make_return_doc('Delivery Note', dn_name)" in script

    def test_writeoff_case_is_stock_less(self) -> None:
        industry_dir = _quality_managed_industry_dir()
        script = _run(industry_dir, _DN_NAMES, _SALES_INVOICES)
        assert "credit_note.update_stock = 0" in script
