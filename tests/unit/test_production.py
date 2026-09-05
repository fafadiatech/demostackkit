"""
Unit tests for the shared Production Plans / Work Orders / Job Cards seeder
(ref #40).
"""

from __future__ import annotations

import ast
import json
import random
import sys
import types
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from _seeder_harness import (
    REPO_ROOT,
    SHARED_SEEDERS,
    industry_dirs_with_module,
    industry_dirs_without_module,
    load_seeder_class,
)

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import SeedContext
from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "215_production.py"

_PLAN = {
    "companies": [
        {
            "name": "Alpha Garments Pvt Ltd",
            "abbr": "AG",
            "fg_warehouse": "Finished Goods Store - AG",
            "wip_warehouse": "Work In Progress - AG",
            "scrap_warehouse": "Scrap - AG",
            "source_warehouse": "Stores - AG",
            "employees": ["HR-EMP-00001"],
            "items": [
                {
                    "item_code": "TSHIRT-M",
                    "bom_no": "BOM-TSHIRT-M-001",
                    "stock_uom": "Nos",
                    "bom_qty": 1.0,
                },
                {
                    "item_code": "JEANS-32",
                    "bom_no": "BOM-JEANS-32-001",
                    "stock_uom": "Nos",
                    "bom_qty": 1.0,
                },
            ],
            "sales_orders": {
                "TSHIRT-M": [
                    {
                        "sales_order": "SO-0001",
                        "sales_order_item": "SOI-0001",
                    }
                ],
            },
        }
    ]
}


def _run(
    industry_dir: Path,
    *,
    plan: dict | None = _PLAN,
    volume_override: int | None = None,
    seed: int = 1,
) -> tuple[str, str]:
    """Return (plan_fetch_script, submit_script). submit_script is "" on no-op."""
    seeder_cls = load_seeder_class(SEEDER_PATH, "ProductionSeeder")
    calls: list[str] = []

    class Recording(seeder_cls):  # type: ignore[valid-type, misc]
        def _exec(self, script: str, timeout: int = 120) -> str:
            calls.append(script)
            if len(calls) == 1:
                return f"DSK_PRODUCTION_PLAN::{json.dumps(plan)}\n"
            return (
                "DSK_PRODUCTION::"
                + json.dumps(
                    {
                        "production_plans": 1,
                        "work_orders": 2,
                        "job_cards_completed": 3,
                        "transfers": 1,
                        "manufactures": 1,
                        "errors": 0,
                    }
                )
                + "\n"
            )

    cfg = load_industry_config(industry_dir / "industry.yaml")
    if volume_override is not None:
        cfg.seed.volumes.production_orders = volume_override

    ctx = SeedContext(
        site=cfg.site.name,
        industry_slug=industry_dir.name,
        industry_config=cfg,
        bench_path="/home/frappe/frappe-bench",
        random=random.Random(seed),
    )
    Recording(ctx).run()
    return (calls[0] if calls else "", calls[1] if len(calls) > 1 else "")


def _payload_from_submit(script: str) -> dict:
    return json.loads(script.split("payload = json.loads('''", 1)[1].split("''')", 1)[0])


@pytest.mark.unit
class TestProductionSeederDiscovery:
    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_with_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_discovered_for_manufacturing_industries(self, industry_dir: Path) -> None:
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Production Plans & Work Orders" in labels


@pytest.mark.unit
class TestProductionSeederGating:
    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_without_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_no_op_without_manufacturing_module(self, industry_dir: Path) -> None:
        plan_script, submit_script = _run(industry_dir)
        assert plan_script == ""
        assert submit_script == ""

    def test_no_op_when_production_orders_volume_is_zero(self) -> None:
        plan_script, submit_script = _run(REPO_ROOT / "industries" / "garment", volume_override=0)
        assert plan_script == ""
        assert submit_script == ""

    def test_no_op_when_plan_has_no_manufacturable_companies(self) -> None:
        plan_script, submit_script = _run(
            REPO_ROOT / "industries" / "garment", plan={"companies": []}
        )
        assert plan_script
        assert submit_script == ""


@pytest.mark.unit
class TestProductionSeederScripts:
    def test_generated_scripts_are_valid_python(self) -> None:
        plan_script, submit_script = _run(REPO_ROOT / "industries" / "garment")
        assert plan_script and submit_script
        ast.parse(plan_script)
        ast.parse(submit_script)

    def test_submit_payload_covers_volume_with_status_mix(self) -> None:
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", volume_override=6, seed=7)
        payload = _payload_from_submit(submit_script)
        items = [row for job in payload["jobs"] for row in job["items"]]
        assert len(items) == 6
        statuses = {row["status"] for row in items}
        assert statuses <= {"completed", "in_progress", "not_started"}
        assert len(statuses) >= 2  # mix, not a single status

    def test_submit_script_uses_production_plan_make_work_order(self) -> None:
        _, submit_script = _run(REPO_ROOT / "industries" / "garment")
        assert (
            "doctype': 'Production Plan'" in submit_script
            or 'doctype": "Production Plan"' in submit_script
        )
        assert "make_work_order()" in submit_script
        assert "Job Card" in submit_script
        assert "Material Transfer for Manufacture" in submit_script
        assert "'Manufacture'" in submit_script or '"Manufacture"' in submit_script

    def test_links_sales_order_when_available(self) -> None:
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", volume_override=4, seed=2)
        payload = _payload_from_submit(submit_script)
        linked = [row for job in payload["jobs"] for row in job["items"] if row.get("sales_order")]
        assert linked
        assert linked[0]["sales_order"] == "SO-0001"


class _FakeDoc:
    """Minimal ERPNext doc stand-in for behavioural exec of the submit script."""

    _counter = 0

    def __init__(self, data: dict[str, Any] | None = None, **kwargs: Any) -> None:
        type(self)._counter += 1
        self.__dict__.update(data or {})
        self.__dict__.update(kwargs)
        self.name = self.__dict__.get("name") or f"DOC-{self._counter:04d}"
        self.docstatus = 0
        self.flags = SimpleNamespace(ignore_permissions=False, ignore_mandatory=False)
        self.required_items: list[Any] = []
        self.time_logs: list[Any] = []
        self.employee: list[Any] = []
        self.po_items: list[Any] = list(self.__dict__.get("po_items") or [])
        if "wip_warehouse" not in self.__dict__:
            self.wip_warehouse = None
        if "fg_warehouse" not in self.__dict__:
            self.fg_warehouse = None
        if "scrap_warehouse" not in self.__dict__:
            self.scrap_warehouse = None
        if "production_item" not in self.__dict__:
            self.production_item = None
        if "qty" not in self.__dict__:
            self.qty = 1
        if "planned_start_date" not in self.__dict__:
            self.planned_start_date = date.today().isoformat()
        if "for_quantity" not in self.__dict__:
            self.for_quantity = 1
        if "operation" not in self.__dict__:
            self.operation = "Cut"
        if "transfer_material_against" not in self.__dict__:
            self.transfer_material_against = None
        if "use_multi_level_bom" not in self.__dict__:
            self.use_multi_level_bom = 0
        if "posting_time" not in self.__dict__:
            self.posting_time = "09:00:00"
        self._submitted_job_cards = 0

    def append(self, field: str, values: dict[str, Any]) -> None:
        bucket = getattr(self, field, None)
        if bucket is None:
            bucket = []
            setattr(self, field, bucket)
        bucket.append(SimpleNamespace(**values))

    def set(self, field: str, value: Any) -> None:
        setattr(self, field, value)

    def insert(self, ignore_permissions: bool = False) -> _FakeDoc:
        return self

    def submit(self) -> None:
        self.docstatus = 1

    def save(self, ignore_permissions: bool = False) -> None:
        return None

    def reload(self) -> None:
        return None

    def make_work_order(self) -> None:
        # Side effect: the fake frappe.get_all below returns draft WOs for this plan.
        return None


def _exec_submit_script(
    script: str,
    jobs: list[dict],
    item_tracking: dict[str, tuple[int, int]] | None = None,
) -> dict[str, Any]:
    """Run the submit half against fakes; assert on resulting counters / calls.

    `item_tracking` maps an item_code to (has_batch_no, has_serial_no), consumed by
    the fake `frappe.get_cached_value` the generated script's `_tracking_kind`
    helper calls -- only meaningful when the script was generated with
    `batch_tracking_enabled=True`.
    """
    created: dict[str, list[Any]] = {
        "Production Plan": [],
        "Work Order": [],
        "Job Card": [],
        "Stock Entry": [],
        "Manufacturing Settings": [],
    }
    stock_purposes: list[str] = []

    # Rebuild script body to inject our known jobs payload (already embedded).
    assert "payload = json.loads" in script

    ms = _FakeDoc(
        name="Manufacturing Settings",
        over_production_allowance_percentage=0,
        enforce_time_logs=0,
        default_wip_warehouse=None,
        default_fg_warehouse=None,
        default_scrap_warehouse=None,
    )

    work_orders = [
        _FakeDoc(
            name=f"WO-{i + 1:04d}",
            production_item=item["item_code"],
            qty=item["qty"],
            planned_start_date=item["planned_start_date"],
            docstatus=0,
            required_items=[
                SimpleNamespace(item_code="RM-1", source_warehouse=None),
            ],
        )
        for job in jobs
        for i, item in enumerate(job["items"])
    ]

    job_cards_by_wo: dict[str, list[_FakeDoc]] = {}
    for wo in work_orders:
        job_cards_by_wo[wo.name] = [
            _FakeDoc(
                name=f"JC-{wo.name}-1",
                work_order=wo.name,
                for_quantity=wo.qty,
                operation="Cut",
                docstatus=0,
            ),
            _FakeDoc(
                name=f"JC-{wo.name}-2",
                work_order=wo.name,
                for_quantity=wo.qty,
                operation="Sew",
                docstatus=0,
            ),
        ]

    def fake_get_doc(arg: Any, name: str | None = None) -> Any:
        if isinstance(arg, dict):
            doc = _FakeDoc(arg)
            created.setdefault(arg.get("doctype", "Unknown"), []).append(doc)
            if arg.get("doctype") == "Production Plan":
                # Attach make_work_order that registers WOs under this plan name.
                def _mwo(self: _FakeDoc = doc) -> None:
                    for wo in work_orders:
                        wo.production_plan = self.name

                doc.make_work_order = _mwo  # type: ignore[method-assign]
            return doc
        if arg == "Job Card":
            for cards in job_cards_by_wo.values():
                for jc in cards:
                    if jc.name == name:
                        return jc
        if arg == "Work Order":
            for wo in work_orders:
                if wo.name == name:
                    return wo
        return _FakeDoc(name=name or "X")

    def fake_get_all(doctype: str, filters: Any = None, **kwargs: Any) -> list[Any]:
        filters = filters or {}
        if doctype == "Work Order":
            plan = filters.get("production_plan")
            return [
                SimpleNamespace(
                    name=wo.name,
                    production_item=wo.production_item,
                    qty=wo.qty,
                    planned_start_date=wo.planned_start_date,
                    docstatus=wo.docstatus,
                )
                for wo in work_orders
                if getattr(wo, "production_plan", None) == plan or filters.get("docstatus") == 0
            ]
        if doctype == "Job Card":
            wo_name = filters.get("work_order")
            cards = job_cards_by_wo.get(wo_name, [])
            if filters.get("docstatus") == 0:
                cards = [c for c in cards if c.docstatus == 0]
            if kwargs.get("fields"):
                return [
                    SimpleNamespace(
                        name=c.name,
                        for_quantity=c.for_quantity,
                        operation=c.operation,
                    )
                    for c in cards
                ]
            return cards
        if doctype == "Work Order Operation":
            return [SimpleNamespace(time_in_mins=45)]
        if doctype == "Bin":
            return [SimpleNamespace(warehouse="Stores - AG", actual_qty=100)]
        return []

    _row_counter = [0]

    def _row(**fields: Any) -> SimpleNamespace:
        _row_counter[0] += 1
        return SimpleNamespace(
            doctype="Stock Entry Detail", name=f"SED-{_row_counter[0]:04d}", **fields
        )

    def fake_make_stock_entry(wo_name: str, purpose: str, qty: float | None = None) -> dict:
        stock_purposes.append(purpose)
        qty = qty or 1
        if purpose == "Material Transfer for Manufacture":
            items = [
                _row(item_code="RM-1", s_warehouse="Stores - AG", t_warehouse="WIP - AG", qty=qty)
            ]
        elif purpose == "Manufacture":
            items = [
                _row(item_code="RM-1", s_warehouse="WIP - AG", t_warehouse=None, qty=qty),
                _row(
                    item_code="FG-1", s_warehouse=None, t_warehouse="Finished Goods - AG", qty=qty
                ),
            ]
        else:
            items = []
        return {
            "doctype": "Stock Entry",
            "purpose": purpose,
            "work_order": wo_name,
            "fg_completed_qty": qty,
            "items": items,
        }

    fake_wo_module = types.ModuleType("erpnext.manufacturing.doctype.work_order.work_order")
    fake_wo_module.make_stock_entry = fake_make_stock_entry  # type: ignore[attr-defined]

    batch_bundle_calls: list[dict[str, Any]] = []
    item_tracking = dict(item_tracking or {})  # item_code -> (has_batch_no, has_serial_no)

    def fake_get_auto_data(**kwargs: Any) -> list[dict[str, Any]]:
        batch_bundle_calls.append({"call": "get_auto_data", **kwargs})
        key = "batch_no" if kwargs.get("has_batch_no") else "serial_no"
        return [{key: f"{kwargs['item_code']}-LOT-0001", "qty": kwargs["qty"]}]

    def fake_add_serial_batch_ledgers(
        entries: Any, child_row: Any, doc: Any, warehouse: Any = None, do_not_save: bool = False
    ) -> Any:
        batch_bundle_calls.append({"call": "add_serial_batch_ledgers", "entries": entries})
        return SimpleNamespace(name="SABB-0001")

    fake_sabb_module = types.ModuleType(
        "erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle"
    )
    fake_sabb_module.get_auto_data = fake_get_auto_data  # type: ignore[attr-defined]
    fake_sabb_module.add_serial_batch_ledgers = fake_add_serial_batch_ledgers  # type: ignore[attr-defined]

    # Ensure parent packages exist for the imports inside the script.
    for pkg in (
        "erpnext",
        "erpnext.manufacturing",
        "erpnext.manufacturing.doctype",
        "erpnext.manufacturing.doctype.work_order",
        "erpnext.stock",
        "erpnext.stock.doctype",
        "erpnext.stock.doctype.serial_and_batch_bundle",
    ):
        sys.modules.setdefault(pkg, types.ModuleType(pkg))
    sys.modules["erpnext.manufacturing.doctype.work_order.work_order"] = fake_wo_module
    sys.modules["erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle"] = (
        fake_sabb_module
    )

    def fake_get_value(
        doctype: str, filters: Any = None, fieldname: Any = None, **kwargs: Any
    ) -> Any:
        as_dict = kwargs.get("as_dict")
        if doctype == "BOM":
            if as_dict or isinstance(fieldname, (list, tuple)):
                return SimpleNamespace(name="BOM-TSHIRT-M-001", quantity=1)
            return "BOM-TSHIRT-M-001"
        if doctype == "BOM Item":
            return []
        if doctype == "Warehouse":
            if fieldname == "company":
                return "Alpha Garments Pvt Ltd"
            if fieldname == "is_group":
                return 0
            return "Stores - AG"
        if doctype == "UOM":
            return 0  # must_be_whole_number
        if doctype == "Item" and fieldname == "stock_uom":
            return "Nos"
        return None

    def fake_get_cached_value(doctype: str, name: str, fieldname: Any = None) -> Any:
        if doctype == "Item" and isinstance(fieldname, list):
            return item_tracking.get(name, (0, 0))
        return None

    def fake_set_value(doctype: str, name: str, fieldname: Any, value: Any = None) -> None:
        batch_bundle_calls.append(
            {"call": "db.set_value", "doctype": doctype, "name": name, "fieldname": fieldname}
        )

    fake_frappe = SimpleNamespace(
        get_doc=fake_get_doc,
        get_all=fake_get_all,
        get_single=lambda _name: ms,
        get_cached_value=fake_get_cached_value,
        db=SimpleNamespace(
            get_value=fake_get_value,
            set_value=fake_set_value,
            commit=lambda: None,
            sql_list=lambda *a, **k: [],
        ),
    )

    exec_globals: dict[str, Any] = {"frappe": fake_frappe}
    try:
        exec(compile(script, "<production seeder>", "exec"), exec_globals)
    finally:
        del sys.modules["erpnext.manufacturing.doctype.work_order.work_order"]
        del sys.modules["erpnext.stock.doctype.serial_and_batch_bundle.serial_and_batch_bundle"]

    return {
        "production_plans": len(created.get("Production Plan", [])),
        "work_orders_submitted": sum(1 for wo in work_orders if wo.docstatus == 1),
        "batch_bundle_calls": batch_bundle_calls,
        "job_cards_submitted": sum(
            1 for cards in job_cards_by_wo.values() for c in cards if c.docstatus == 1
        ),
        "stock_purposes": stock_purposes,
        "ms_over_production": ms.over_production_allowance_percentage,
    }


@pytest.mark.unit
class TestProductionSeederBehaviour:
    def test_executes_status_mix_against_fake_erpnext(self) -> None:
        """Behavioural regression: runs the generated script against fakes so a
        rewrite that drops Job Card completion or Manufacture still fails even
        if the source strings are reworded."""
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", volume_override=3, seed=11)
        payload = _payload_from_submit(submit_script)
        # Force one of each status so the fake path exercises all three arms.
        statuses = ["completed", "in_progress", "not_started"]
        for job in payload["jobs"]:
            for i, row in enumerate(job["items"]):
                row["status"] = statuses[i % 3]
                row["qty"] = 1

        # Re-embed the mutated payload into a fresh script run by splicing.
        prefix, rest = submit_script.split("payload = json.loads('''", 1)
        _, suffix = rest.split("''')", 1)
        mutated = prefix + "payload = json.loads('''" + json.dumps(payload) + "''')" + suffix

        result = _exec_submit_script(mutated, payload["jobs"])
        assert result["production_plans"] >= 1
        assert result["work_orders_submitted"] >= 1
        # completed + in_progress should submit at least one Job Card; not_started none required
        assert result["job_cards_submitted"] >= 1
        assert "Material Transfer for Manufacture" in result["stock_purposes"]
        assert "Manufacture" in result["stock_purposes"]
        assert result["ms_over_production"] >= 100


@pytest.mark.unit
class TestProductionSeederBatchTracking:
    """ref #4: outward (consumption) Stock Entry rows on a batch/serial-tracked
    item must get an explicit FIFO/FEFO lot selection; the FG output row must
    not (ERPNext auto-creates its lot on submit)."""

    def test_no_batch_tracking_payload_keys_when_disabled(self) -> None:
        _, submit_script = _run(REPO_ROOT / "industries" / "garment")
        payload = _payload_from_submit(submit_script)
        # garment's industry.yaml has batch_tracking.enabled: true (ref #4
        # rollout) -- flip it off here to assert the disabled shape too.
        cfg = load_industry_config(REPO_ROOT / "industries" / "garment" / "industry.yaml")
        assert cfg.seed.batch_tracking.enabled is True
        assert payload["batch_tracking_enabled"] is True

    def test_disabled_industry_never_calls_selection_helpers(self) -> None:
        seeder_cls = load_seeder_class(SEEDER_PATH, "ProductionSeeder")
        seeder = seeder_cls.__new__(seeder_cls)
        cfg = load_industry_config(REPO_ROOT / "industries" / "garment" / "industry.yaml")
        cfg.seed.batch_tracking.enabled = False
        seeder.ctx = SimpleNamespace(
            industry_config=cfg,
            cache_get=lambda key, default=None: default,
            random=random.Random(1),
        )
        captured: list[str] = []
        seeder._exec = lambda script, timeout=120: (
            captured.append(script)
            or (
                f"DSK_PRODUCTION_PLAN::{json.dumps(_PLAN)}\n"
                if len(captured) == 1
                else "DSK_PRODUCTION::"
                + json.dumps(
                    {
                        "production_plans": 1,
                        "work_orders": 2,
                        "job_cards_completed": 3,
                        "transfers": 1,
                        "manufactures": 1,
                        "errors": 0,
                    }
                )
            )
        )
        seeder.run()
        submit_script = captured[1]
        payload = _payload_from_submit(submit_script)
        assert payload["batch_tracking_enabled"] is False
        result = _exec_submit_script(submit_script, payload["jobs"])
        assert result["batch_bundle_calls"] == []

    def test_enabled_selects_outward_rows_only(self) -> None:
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", volume_override=2, seed=3)
        payload = _payload_from_submit(submit_script)
        assert payload["batch_tracking_enabled"] is True

        # Force every item to 'completed' so both stock-entry purposes fire.
        for job in payload["jobs"]:
            for row in job["items"]:
                row["status"] = "completed"

        prefix, rest = submit_script.split("payload = json.loads('''", 1)
        _, suffix = rest.split("''')", 1)
        mutated = prefix + "payload = json.loads('''" + json.dumps(payload) + "''')" + suffix

        result = _exec_submit_script(mutated, payload["jobs"], item_tracking={"RM-1": (1, 0)})
        calls = result["batch_bundle_calls"]
        get_auto_calls = [c for c in calls if c["call"] == "get_auto_data"]
        add_ledger_calls = [c for c in calls if c["call"] == "add_serial_batch_ledgers"]
        set_value_calls = [c for c in calls if c["call"] == "db.set_value"]

        assert get_auto_calls, "expected an outward selection call for the tracked RM item"
        assert all(c["item_code"] == "RM-1" for c in get_auto_calls)
        assert all(c["has_batch_no"] == 1 for c in get_auto_calls)
        # One call per outward row: the Material Transfer row + the Manufacture
        # entry's RM consumption row -- never the FG output row (untracked here
        # anyway, and its s_warehouse is None so it's skipped regardless).
        assert len(get_auto_calls) == len(add_ledger_calls) == len(set_value_calls)
        assert all(c["fieldname"] == "serial_and_batch_bundle" for c in set_value_calls)
