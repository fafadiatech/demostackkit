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


@pytest.mark.unit
class TestPurchaseReceiptSeederBatchTracking:
    """ref #4: the (cosmetic) Vendor Batch stamp only fires when batch
    tracking is enabled, and only touches Batches ERPNext actually
    auto-created for this receipt."""

    def test_payload_carries_batch_tracking_flag(self) -> None:
        payload = payload_from_script(_run(REPO_ROOT / "industries" / "evmfg"))
        assert payload["batch_tracking_enabled"] is True

    def test_stamp_helper_called_only_when_enabled(self) -> None:
        enabled_script = _run(REPO_ROOT / "industries" / "evmfg")
        assert "stamp_vendor_batch(pr)" in enabled_script

        disabled_script = _run(REPO_ROOT / "industries" / "epc")
        payload = payload_from_script(disabled_script)
        assert payload["batch_tracking_enabled"] is False

    def test_exec_stamps_only_batches_from_this_receipt(self) -> None:
        from types import SimpleNamespace

        script = _run(REPO_ROOT / "industries" / "evmfg")

        class _FakePR(SimpleNamespace):
            def insert(self, ignore_permissions=False):
                return self

            def submit(self):
                self.docstatus = 1

        pr = _FakePR(
            name="MAT-PR-0001",
            company="Voltara EV Manufacturing Pvt Ltd",
            supplier="Acme Cells Ltd",
            items=[
                SimpleNamespace(
                    item_code="MAT-LICELL-21700", received_qty=100, qty=100, name="PRI-1"
                ),
            ],
            docstatus=0,
        )
        fake_po_module_calls = {"make_purchase_receipt": lambda po_name: pr}

        set_value_calls: list[tuple] = []

        def fake_get_all(doctype, filters=None, pluck=None, **kwargs):
            if doctype == "Purchase Order":
                return ["PO-0001"]
            if doctype == "Serial and Batch Bundle":
                return ["SABB-0001"]
            if doctype == "Serial and Batch Entry":
                return ["MAT-LICELL-21700-BATCH-0001"]
            return []

        fake_frappe = SimpleNamespace(
            get_all=fake_get_all,
            get_cached_value=lambda doctype, name, fieldname=None: (
                "PEL" if doctype == "Company" else None
            ),
            db=SimpleNamespace(
                exists=lambda *a, **k: True,
                commit=lambda: None,
                set_value=lambda doctype, name, values: set_value_calls.append(
                    (doctype, name, values)
                ),
            ),
        )

        import sys
        import types

        fake_po_module = types.ModuleType("erpnext.buying.doctype.purchase_order.purchase_order")
        fake_po_module.make_purchase_receipt = fake_po_module_calls["make_purchase_receipt"]
        for pkg in (
            "erpnext",
            "erpnext.buying",
            "erpnext.buying.doctype",
            "erpnext.buying.doctype.purchase_order",
        ):
            sys.modules.setdefault(pkg, types.ModuleType(pkg))
        sys.modules["erpnext.buying.doctype.purchase_order.purchase_order"] = fake_po_module

        try:
            exec(compile(script, "<purchase receipt seeder>", "exec"), {"frappe": fake_frappe})
        finally:
            del sys.modules["erpnext.buying.doctype.purchase_order.purchase_order"]

        assert len(set_value_calls) == 1
        doctype, batch_no, values = set_value_calls[0]
        assert doctype == "Batch"
        assert batch_no == "MAT-LICELL-21700-BATCH-0001"
        assert values["supplier"] == "Acme Cells Ltd"
        assert values["description"].startswith("Vendor Batch: VB-")
