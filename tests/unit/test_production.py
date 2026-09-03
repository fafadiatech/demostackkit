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


def _exec_submit_script(script: str, jobs: list[dict]) -> dict[str, Any]:
    """Run the submit half against fakes; assert on resulting counters / calls."""
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

    def fake_make_stock_entry(wo_name: str, purpose: str, qty: float | None = None) -> dict:
        stock_purposes.append(purpose)
        return {
            "doctype": "Stock Entry",
            "purpose": purpose,
            "work_order": wo_name,
            "fg_completed_qty": qty or 1,
            "items": [],
        }

    fake_wo_module = types.ModuleType("erpnext.manufacturing.doctype.work_order.work_order")
    fake_wo_module.make_stock_entry = fake_make_stock_entry  # type: ignore[attr-defined]
    # Ensure parent packages exist for the import inside the script.
    for pkg in (
        "erpnext",
        "erpnext.manufacturing",
        "erpnext.manufacturing.doctype",
        "erpnext.manufacturing.doctype.work_order",
    ):
        sys.modules.setdefault(pkg, types.ModuleType(pkg))
    sys.modules["erpnext.manufacturing.doctype.work_order.work_order"] = fake_wo_module

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

    fake_frappe = SimpleNamespace(
        get_doc=fake_get_doc,
        get_all=fake_get_all,
        get_single=lambda _name: ms,
        db=SimpleNamespace(
            get_value=fake_get_value,
            commit=lambda: None,
            sql_list=lambda *a, **k: [],
        ),
    )

    exec_globals: dict[str, Any] = {"frappe": fake_frappe}
    try:
        exec(compile(script, "<production seeder>", "exec"), exec_globals)
    finally:
        del sys.modules["erpnext.manufacturing.doctype.work_order.work_order"]

    return {
        "production_plans": len(created.get("Production Plan", [])),
        "work_orders_submitted": sum(1 for wo in work_orders if wo.docstatus == 1),
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
