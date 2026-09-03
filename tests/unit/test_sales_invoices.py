"""
Unit tests for the shared Sales Invoices seeder (ref #35, posting_date/due_date
fix ref #37).
"""

from __future__ import annotations

import ast
import sys
import types
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from _seeder_harness import REPO_ROOT, SHARED_SEEDERS, load_seeder_class, run_seeder

SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "221_sales_invoices.py"


def _run(industry_dir: Path) -> str:
    seeder_cls = load_seeder_class(SEEDER_PATH, "SalesInvoiceSeeder")
    return run_seeder(seeder_cls, industry_dir, cache={"delivery_notes": ["DN-0001"]})


# Distinct from `_MAPPER_TODAY` so a test failure can't pass by accident.
_DN_POSTING_DATE = date(2026, 6, 1)
#: What `make_sales_invoice()`'s postprocess would already have set
#: `due_date`/`posting_date` to (a fresh, unsubmitted doc defaults to today).
_MAPPER_TODAY = date(2026, 9, 3)


class _FakeSalesInvoice:
    """Stands in for the ERPNext Sales Invoice doc `make_sales_invoice()` returns.

    Mimics the two behaviours the real bug (ref #37) hinges on:
      - `posting_date`/`due_date` already come back set (to "today", since the
        mapper's postprocess ran `set_missing_values()` on a fresh doc).
      - `insert()` re-runs that same `set_missing_values()` logic, which only
        fills `due_date` when it is falsy — so a stale non-empty `due_date`
        survives insert() untouched, exactly like real ERPNext.
    """

    def __init__(self) -> None:
        self.name = "SI-AUTO-0001"
        self.cost_center: str | None = None
        self.taxes_and_charges: str | None = None
        self.taxes: list[Any] = []
        self.set_posting_time = 0
        self.posting_date = _MAPPER_TODAY
        self.due_date = _MAPPER_TODAY
        self.docstatus = 0

    def set(self, fieldname: str, value: Any) -> None:
        setattr(self, fieldname, value)

    def insert(self, ignore_permissions: bool = False) -> None:
        if not self.due_date:
            self.due_date = self.posting_date

    def submit(self) -> None:
        self.docstatus = 1


def _exec_generated_script(script: str) -> tuple[dict, list[_FakeSalesInvoice]]:
    """Actually execute the seeder's generated script against fake ERPNext stand-ins.

    Unlike the string-matching tests below, this catches the underlying bug
    regardless of *how* it's fixed: it would fail on the ref #37 regression
    (due_date staying pinned to the mapper's today-dated value) even if the
    fix were reworded or reshuffled, because it asserts on the resulting
    Sales Invoice state rather than on specific source lines.
    """
    created_invoices: list[_FakeSalesInvoice] = []

    def fake_make_sales_invoice(dn_name: str) -> _FakeSalesInvoice:
        si = _FakeSalesInvoice()
        created_invoices.append(si)
        return si

    fake_module = types.ModuleType("erpnext.stock.doctype.delivery_note.delivery_note")
    fake_module.make_sales_invoice = fake_make_sales_invoice  # type: ignore[attr-defined]
    sys.modules["erpnext.stock.doctype.delivery_note.delivery_note"] = fake_module

    def fake_get_value(doctype: str, name: str, field: str) -> Any:
        if field == "posting_date":
            return _DN_POSTING_DATE
        return None  # cost_center / taxes_and_charges: mapper already carried these

    fake_frappe = SimpleNamespace(
        db=SimpleNamespace(get_value=fake_get_value, commit=lambda: None),
        get_all=lambda *a, **k: [],
    )

    exec_globals: dict[str, Any] = {"frappe": fake_frappe}
    try:
        exec(compile(script, "<seeder script>", "exec"), exec_globals)
    finally:
        del sys.modules["erpnext.stock.doctype.delivery_note.delivery_note"]

    return exec_globals, created_invoices


@pytest.mark.unit
class TestSalesInvoiceSeeder:
    def test_generated_script_is_valid_python(self) -> None:
        script = _run(REPO_ROOT / "industries" / "garment")
        assert script
        ast.parse(script)

    def test_uses_make_sales_invoice_mapper(self) -> None:
        script = _run(REPO_ROOT / "industries" / "garment")
        assert (
            "from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice"
            in script
        )

    def test_copies_posting_date_from_delivery_note(self) -> None:
        """ref #37: without this, ERPNext forces every invoice's posting_date to
        "today" on save, collapsing due_date variety and starving Accounts
        Receivable's aging buckets."""
        script = _run(REPO_ROOT / "industries" / "garment")
        assert "si.set_posting_time = 1" in script
        assert (
            "si.posting_date = frappe.db.get_value('Delivery Note', dn_name, 'posting_date')"
            in script
        )

    def test_clears_due_date_after_overriding_posting_date(self) -> None:
        """ref #37 regression: make_sales_invoice()'s postprocess already runs
        set_missing_values(), which computes due_date off the pre-override
        (today-dated) posting_date and only fills due_date when it's falsy.
        Without resetting due_date here too, it stays pinned to the seed run
        date on every invoice no matter what posting_date is corrected to —
        silently defeating the posting_date fix above and starving Accounts
        Receivable's aging buckets exactly as before."""
        script = _run(REPO_ROOT / "industries" / "garment")
        due_date_reset = script.index("si.due_date = None")
        posting_date_override = script.index(
            "si.posting_date = frappe.db.get_value('Delivery Note', dn_name, 'posting_date')"
        )
        insert_call = script.index("si.insert(")
        assert posting_date_override < due_date_reset < insert_call

    def test_recomputes_due_date_off_corrected_posting_date(self) -> None:
        """Behavioural regression test for ref #37: executes the generated
        script against fake ERPNext stand-ins that reproduce the real bug
        (make_sales_invoice() returns a doc whose due_date is already set to
        "today", and insert() only fills due_date when it's falsy) — so this
        fails on the underlying defect regardless of how it's fixed, not just
        on the specific `si.due_date = None` line."""
        script = _run(REPO_ROOT / "industries" / "garment")
        _, created_invoices = _exec_generated_script(script)

        assert len(created_invoices) == 1
        si = created_invoices[0]
        assert si.posting_date == _DN_POSTING_DATE
        assert si.due_date == _DN_POSTING_DATE
        assert si.due_date != _MAPPER_TODAY
