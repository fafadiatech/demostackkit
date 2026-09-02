"""
Unit tests for the shared Return to Vendor seeder (ref #35).

Same stub-`_exec`-and-inspect-the-script approach as the other new seeder
tests. This seeder is driven entirely by the "vendor_rtv_candidates" cache
`211_purchase_receipts.py` populates, so tests seed that cache directly
rather than running the full seeder chain.
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
SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "213_return_to_vendor.py"

_SAMPLE_CANDIDATES = [
    {
        "pr_name": "PR-0001",
        "item_code": "ITEM-001",
        "rejected_qty": 5,
        "warehouse": "Vendor Rejected - ACH",
        "company": "Acme Co",
    },
    {
        "pr_name": "PR-0002",
        "item_code": "ITEM-002",
        "rejected_qty": 3,
        "warehouse": "Vendor Rejected - ACH",
        "company": "Acme Co",
    },
]


def _load_seeder_class() -> type[BaseSeeder]:
    spec = importlib.util.spec_from_file_location("_test_return_to_vendor", SEEDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ReturnToVendorSeeder


def _run(industry_dir: Path, candidates: list[dict]) -> str:
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
    ctx.cache_set("vendor_rtv_candidates", candidates)
    Recording(ctx).run()
    return captured[0] if captured else ""


@pytest.mark.unit
class TestReturnToVendorSeeder:
    def test_no_op_without_candidates(self) -> None:
        assert _run(REPO_ROOT / "industries" / "electrical", []) == ""

    def test_generated_script_is_valid_python(self) -> None:
        script = _run(REPO_ROOT / "industries" / "electrical", _SAMPLE_CANDIDATES)
        assert script
        ast.parse(script)

    def test_deduplicates_receipts_and_uses_rejected_warehouse_return_mapper(self) -> None:
        script = _run(REPO_ROOT / "industries" / "electrical", _SAMPLE_CANDIDATES)
        pr_names = json.loads(script.split("pr_names = json.loads('''", 1)[1].split("''')", 1)[0])
        assert sorted(pr_names) == ["PR-0001", "PR-0002"]
        assert "make_purchase_return_against_rejected_warehouse" in script

    def test_creates_debit_note_against_the_return(self) -> None:
        script = _run(REPO_ROOT / "industries" / "electrical", _SAMPLE_CANDIDATES)
        assert "make_purchase_invoice(return_pr.name)" in script
