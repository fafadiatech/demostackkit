"""
Unit tests for the shared Return to Vendor seeder (ref #35).

Same stub-`_exec`-and-inspect-the-script approach as the other new seeder
tests. This seeder is driven entirely by the "vendor_rtv_candidates" cache
`211_purchase_receipts.py` populates, so tests seed that cache directly
rather than running the full seeder chain.
"""

from __future__ import annotations

import ast
import json

import pytest
from _seeder_harness import REPO_ROOT, SHARED_SEEDERS, load_seeder_class, run_seeder

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


def _run(candidates: list[dict]) -> str:
    seeder_cls = load_seeder_class(SEEDER_PATH, "ReturnToVendorSeeder")
    return run_seeder(
        seeder_cls,
        REPO_ROOT / "industries" / "electrical",
        cache={"vendor_rtv_candidates": candidates},
    )


@pytest.mark.unit
class TestReturnToVendorSeeder:
    def test_no_op_without_candidates(self) -> None:
        assert _run([]) == ""

    def test_generated_script_is_valid_python(self) -> None:
        script = _run(_SAMPLE_CANDIDATES)
        assert script
        ast.parse(script)

    def test_deduplicates_receipts_and_uses_rejected_warehouse_return_mapper(self) -> None:
        script = _run(_SAMPLE_CANDIDATES)
        pr_names = json.loads(script.split("pr_names = json.loads('''", 1)[1].split("''')", 1)[0])
        assert sorted(pr_names) == ["PR-0001", "PR-0002"]
        assert "make_purchase_return_against_rejected_warehouse" in script

    def test_creates_debit_note_against_the_return(self) -> None:
        script = _run(_SAMPLE_CANDIDATES)
        assert "make_purchase_invoice(return_pr.name)" in script
