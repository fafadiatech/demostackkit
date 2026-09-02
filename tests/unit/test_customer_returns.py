"""
Unit tests for the shared Customer Returns seeder (ref #35).

Driven by the "delivery_notes" and "sales_invoices" caches
`220_delivery_notes.py` / `221_sales_invoices.py` populate, so tests seed
those caches directly rather than running the full seeder chain.
"""

from __future__ import annotations

import ast

import pytest
from _seeder_harness import (
    SHARED_SEEDERS,
    industry_dirs_with_module,
    load_seeder_class,
    payload_from_script,
    run_seeder,
)

SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "222_customer_returns.py"

_DN_NAMES = [f"DN-{i:04d}" for i in range(10)]
_SALES_INVOICES = {dn: f"SI-{i:04d}" for i, dn in enumerate(_DN_NAMES)}


def _quality_managed_industry_dir():
    dirs = industry_dirs_with_module("Quality Management")
    if not dirs:
        pytest.skip("no Quality Management industry found")
    return dirs[0]


def _run(dn_names: list[str], sales_invoices: dict) -> str:
    seeder_cls = load_seeder_class(SEEDER_PATH, "CustomerReturnSeeder")
    return run_seeder(
        seeder_cls,
        _quality_managed_industry_dir(),
        cache={"delivery_notes": dn_names, "sales_invoices": sales_invoices},
    )


@pytest.mark.unit
class TestCustomerReturnSeeder:
    def test_no_op_without_cached_data(self) -> None:
        assert _run([], {}) == ""

    def test_generated_script_is_valid_python(self) -> None:
        script = _run(_DN_NAMES, _SALES_INVOICES)
        assert script
        ast.parse(script)

    def test_splits_sample_into_physical_and_writeoff(self) -> None:
        script = _run(_DN_NAMES, _SALES_INVOICES)
        payload = payload_from_script(script)
        assert set(payload["physical"]) | set(payload["writeoff"]) <= set(_DN_NAMES)
        assert not (set(payload["physical"]) & set(payload["writeoff"]))
        assert payload["physical"] or payload["writeoff"]

    def test_physical_returns_redirect_to_customer_returns_warehouse(self) -> None:
        script = _run(_DN_NAMES, _SALES_INVOICES)
        assert "Customer Returns -" in script
        assert "make_return_doc('Delivery Note', dn_name)" in script

    def test_writeoff_case_is_stock_less(self) -> None:
        script = _run(_DN_NAMES, _SALES_INVOICES)
        assert "credit_note.update_stock = 0" in script
