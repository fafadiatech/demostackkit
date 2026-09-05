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


@pytest.mark.unit
class TestDeliveryNoteSeederBatchTracking:
    """ref #4: a shipped batch/serial-tracked FG row must get an explicit
    FIFO/FEFO lot selection before submit -- a Delivery Note is always an
    outward move, so nothing here can auto-create a lot."""

    def test_payload_carries_batch_tracking_flag(self) -> None:
        payload = payload_from_script(_run(REPO_ROOT / "industries" / "evmfg"))
        assert payload["batch_tracking_enabled"] is True
        assert payload["based_on"] == "FIFO"

    def test_selection_helpers_wired_before_submit(self) -> None:
        script = _run(REPO_ROOT / "industries" / "evmfg")
        insert_call = script.index("        dn.insert(ignore_permissions=True)")
        select_call = script.index("            _select_outward_lots(dn)")
        submit_call = script.index("        dn.submit()")
        assert insert_call < select_call < submit_call

    def test_exec_selects_only_tracked_rows(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sys
        import types
        from types import SimpleNamespace

        script = _run(REPO_ROOT / "industries" / "evmfg")

        calls: list[dict] = []

        def fake_get_auto_data(**kwargs):
            calls.append({"call": "get_auto_data", **kwargs})
            return [{"batch_no": f"{kwargs['item_code']}-LOT-0001", "qty": kwargs["qty"]}]

        def fake_add_serial_batch_ledgers(
            entries, child_row, doc, warehouse=None, do_not_save=False
        ):
            calls.append({"call": "add_serial_batch_ledgers"})
            return SimpleNamespace(name="SABB-0001")

        fake_module = types.ModuleType(
            "erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle"
        )
        fake_module.get_auto_data = fake_get_auto_data
        fake_module.add_serial_batch_ledgers = fake_add_serial_batch_ledgers
        for pkg in (
            "erpnext",
            "erpnext.selling",
            "erpnext.selling.doctype",
            "erpnext.selling.doctype.sales_order",
            "erpnext.stock",
            "erpnext.stock.doctype",
            "erpnext.stock.doctype.serial_and_batch_bundle",
        ):
            sys.modules.setdefault(pkg, types.ModuleType(pkg))
        fake_so_module = types.ModuleType("erpnext.selling.doctype.sales_order.sales_order")

        class _Row(SimpleNamespace):
            pass

        rows = [
            _Row(
                doctype="Delivery Note Item",
                name="DNI-1",
                item_code="TRACKED-FG",
                warehouse="FG Store - X",
                qty=2,
            ),
            _Row(
                doctype="Delivery Note Item",
                name="DNI-2",
                item_code="PLAIN-ITEM",
                warehouse="FG Store - X",
                qty=3,
            ),
        ]

        class _FakeDN(SimpleNamespace):
            def insert(self, ignore_permissions=False):
                return self

            def submit(self):
                self.docstatus = 1

            def reload(self):
                return None

            def set(self, field, value):
                setattr(self, field, value)

        dn = _FakeDN(
            doctype="Delivery Note",
            name="DN-0001",
            items=rows,
            posting_date="2026-01-01",
            posting_time="09:00:00",
            docstatus=0,
        )
        fake_so_module.make_delivery_note = lambda so_name: dn
        sys.modules["erpnext.selling.doctype.sales_order.sales_order"] = fake_so_module
        sys.modules["erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle"] = (
            fake_module
        )

        tracking = {"TRACKED-FG": (1, 0), "PLAIN-ITEM": (0, 0)}
        set_value_calls: list[tuple] = []

        fake_frappe = SimpleNamespace(
            utils=SimpleNamespace(getdate=lambda: "2026-01-01"),
            get_cached_value=lambda doctype, name, fields: tracking.get(name, (0, 0)),
            get_all=lambda *a, **k: ["SO-0001"],
            db=SimpleNamespace(
                get_value=lambda *a, **k: "2026-01-01",
                commit=lambda: None,
                set_value=lambda doctype, name, fieldname, value=None: set_value_calls.append(
                    (doctype, name, fieldname)
                ),
            ),
        )

        try:
            exec(compile(script, "<delivery note seeder>", "exec"), {"frappe": fake_frappe})
        finally:
            del sys.modules["erpnext.selling.doctype.sales_order.sales_order"]
            del sys.modules["erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle"]

        get_auto_calls = [c for c in calls if c["call"] == "get_auto_data"]
        assert len(get_auto_calls) == 1
        assert get_auto_calls[0]["item_code"] == "TRACKED-FG"
        assert len(set_value_calls) == 1
        assert set_value_calls[0][2] == "serial_and_batch_bundle"
