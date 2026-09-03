"""
Unit tests for the shared Sales Orders seeder (ref #36).

Two `_exec` round trips (a live item/cost-center plan fetch, then order
submission), so these tests stub `_exec` with a small dispatcher rather than
reusing `_seeder_harness.run_seeder`, which only ever captures/replays one
script.
"""

from __future__ import annotations

import ast
import json
import random
from pathlib import Path

import pytest
from _seeder_harness import REPO_ROOT, SHARED_SEEDERS, all_industry_dirs, load_seeder_class

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import SeedContext
from demostackkit.seeder.loader import discover_seeders
from demostackkit.seeder.utils import SALES_ORDER_BANDS, sales_order_qty_and_lead

SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "210_sales_orders.py"

_DEFAULT_COMPANY = "Garment Co - GRM"

_PLAN = {
    "items": {
        _DEFAULT_COMPANY: [
            {"item_code": "CHEAP-ITEM", "stock_uom": "Nos", "value": 50.0, "warehouse": "FG - GRM"},
            {
                "item_code": "PRICEY-ITEM",
                "stock_uom": "Kg",
                "value": 750_000.0,
                "warehouse": "FG - GRM",
            },
        ]
    },
    "cost_centers": {_DEFAULT_COMPANY: ["Sales - GRM", "Marketing - GRM"]},
}


def _run(
    industry_dir: Path, cache: dict | None = None, plan: dict | None = None
) -> tuple[str, str]:
    """Run the seeder, returning (plan_fetch_script, submit_script).

    submit_script is "" if the seeder no-oped before the second round trip
    (e.g. no customers/items in cache).
    """
    seeder_cls = load_seeder_class(SEEDER_PATH, "SalesOrderSeeder")
    calls: list[str] = []
    plan = plan if plan is not None else _PLAN

    class Recording(seeder_cls):  # type: ignore[valid-type, misc]
        def _exec(self, script: str, timeout: int = 120) -> str:
            calls.append(script)
            if len(calls) == 1:
                return f"DSK_SALES_ORDERS_PLAN::{json.dumps(plan)}\n"
            return "DSK_SALES_ORDERS::" + json.dumps({"sales_orders": ["SO-0001"]}) + "\n"

    cfg = load_industry_config(industry_dir / "industry.yaml")
    ctx = SeedContext(
        site=cfg.site.name,
        industry_slug=industry_dir.name,
        industry_config=cfg,
        bench_path="/home/frappe/frappe-bench",
        random=random.Random(cfg.seed.random_seed),
    )
    for key, value in (cache or {}).items():
        ctx.cache_set(key, value)
    Recording(ctx).run()
    return (calls[0] if calls else "", calls[1] if len(calls) > 1 else "")


_CACHE = {
    "customer_names": ["Acme Corp"],
    "fg_item_codes": [item["item_code"] for item in _PLAN["items"][_DEFAULT_COMPANY]],
    "company_name": _DEFAULT_COMPANY,
}


@pytest.mark.unit
class TestSalesOrderSeeder:
    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_industry(self, industry_dir: Path) -> None:
        """Every industry has Selling + Stock, so this always fires."""
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Sales Orders" in labels

    def test_no_op_without_customers_or_items(self) -> None:
        plan_script, submit_script = _run(REPO_ROOT / "industries" / "garment")
        assert plan_script == ""
        assert submit_script == ""

    def test_generated_scripts_are_valid_python(self) -> None:
        plan_script, submit_script = _run(REPO_ROOT / "industries" / "garment", cache=_CACHE)
        assert plan_script and submit_script
        ast.parse(plan_script)
        ast.parse(submit_script)

    def test_rate_is_a_markup_on_item_value_not_a_flat_band(self) -> None:
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", cache=_CACHE)
        orders_json = submit_script.split("orders = json.loads('''", 1)[1].split("''')", 1)[0]
        orders = json.loads(orders_json)
        assert orders
        plan_items = _PLAN["items"][_DEFAULT_COMPANY]
        for order in orders:
            for row in order["items"]:
                value = next(i["value"] for i in plan_items if i["item_code"] == row["item_code"])
                assert value * 1.15 <= row["rate"] <= value * 1.40

    def test_uom_comes_from_the_item_not_a_hardcoded_nos(self) -> None:
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", cache=_CACHE)
        orders_json = submit_script.split("orders = json.loads('''", 1)[1].split("''')", 1)[0]
        orders = json.loads(orders_json)
        uoms = {row["uom"] for order in orders for row in order["items"]}
        assert uoms <= {"Nos", "Kg"}

    def test_warehouse_comes_from_the_plan_not_left_blank(self) -> None:
        """A blank warehouse falls back to the Item's own default warehouse,
        which can hold no opening stock at all — see the seeder's docstring."""
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", cache=_CACHE)
        orders_json = submit_script.split("orders = json.loads('''", 1)[1].split("''')", 1)[0]
        orders = json.loads(orders_json)
        assert orders
        assert all(row["warehouse"] == "FG - GRM" for o in orders for row in o["items"])

    def test_cost_center_and_tax_template_are_assigned_from_the_plan(self) -> None:
        _, submit_script = _run(
            REPO_ROOT / "industries" / "garment",
            cache={**_CACHE, "sales_tax_templates": ["GST 18% - GRM"]},
        )
        orders_json = submit_script.split("orders = json.loads('''", 1)[1].split("''')", 1)[0]
        orders = json.loads(orders_json)
        assert all(o["cost_center"] in _PLAN["cost_centers"][_DEFAULT_COMPANY] for o in orders)
        assert all(o["taxes_and_charges"] == "GST 18% - GRM" for o in orders)

    def test_orders_spread_across_every_company_in_all_companies(self) -> None:
        """electrical-style multi-company groups must not starve non-default companies."""
        second_company = "Switchgear Co - PSN"
        plan = {
            "items": {
                _DEFAULT_COMPANY: _PLAN["items"][_DEFAULT_COMPANY],
                second_company: [
                    {
                        "item_code": "PANEL",
                        "stock_uom": "Nos",
                        "value": 200_000.0,
                        "warehouse": "FG - PSN",
                    }
                ],
            },
            "cost_centers": {_DEFAULT_COMPANY: ["Sales - GRM"], second_company: ["Sales - PSN"]},
        }
        cache = {
            **_CACHE,
            "all_companies": [{"name": _DEFAULT_COMPANY}, {"name": second_company}],
        }
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", cache=cache, plan=plan)
        orders_json = submit_script.split("orders = json.loads('''", 1)[1].split("''')", 1)[0]
        orders = json.loads(orders_json)
        companies = {o["company"] for o in orders}
        assert companies == {_DEFAULT_COMPANY, second_company}

    def test_item_row_warehouse_matches_its_own_companys_plan(self) -> None:
        """A company only sells items its own Bin data says it has stock of."""
        second_company = "Switchgear Co - PSN"
        plan = {
            "items": {
                _DEFAULT_COMPANY: _PLAN["items"][_DEFAULT_COMPANY],
                second_company: [
                    {
                        "item_code": "PANEL",
                        "stock_uom": "Nos",
                        "value": 200_000.0,
                        "warehouse": "FG - PSN",
                    }
                ],
            },
            "cost_centers": {_DEFAULT_COMPANY: ["Sales - GRM"], second_company: ["Sales - PSN"]},
        }
        cache = {
            **_CACHE,
            "all_companies": [{"name": _DEFAULT_COMPANY}, {"name": second_company}],
        }
        _, submit_script = _run(REPO_ROOT / "industries" / "garment", cache=cache, plan=plan)
        orders_json = submit_script.split("orders = json.loads('''", 1)[1].split("''')", 1)[0]
        orders = json.loads(orders_json)
        for order in orders:
            expected_warehouse = "FG - PSN" if order["company"] == second_company else "FG - GRM"
            assert all(row["warehouse"] == expected_warehouse for row in order["items"])

    def test_caches_sales_order_names(self) -> None:
        seeder_cls = load_seeder_class(SEEDER_PATH, "SalesOrderSeeder")
        calls: list[str] = []

        class Recording(seeder_cls):  # type: ignore[valid-type, misc]
            def _exec(self, script: str, timeout: int = 120) -> str:
                calls.append(script)
                if len(calls) == 1:
                    return f"DSK_SALES_ORDERS_PLAN::{json.dumps(_PLAN)}\n"
                return "DSK_SALES_ORDERS::" + json.dumps({"sales_orders": ["SO-0001"]}) + "\n"

        industry_dir = REPO_ROOT / "industries" / "garment"
        cfg = load_industry_config(industry_dir / "industry.yaml")
        ctx = SeedContext(
            site=cfg.site.name,
            industry_slug=industry_dir.name,
            industry_config=cfg,
            bench_path="/home/frappe/frappe-bench",
            random=random.Random(cfg.seed.random_seed),
        )
        for key, value in _CACHE.items():
            ctx.cache_set(key, value)
        Recording(ctx).run()
        assert ctx.cache_get("sales_orders") == ["SO-0001"]


def _rng(seed: int = 20240104) -> random.Random:
    return random.Random(seed)


@pytest.mark.unit
class TestSalesOrderBands:
    def test_bands_are_ascending_and_total(self) -> None:
        ceilings = [ceiling for ceiling, _, _ in SALES_ORDER_BANDS]
        assert ceilings == sorted(ceilings)
        assert ceilings[-1] == float("inf")

    def test_deterministic_for_a_given_seed(self) -> None:
        first = [sales_order_qty_and_lead(v, _rng()) for v in (45, 12500, 850000)]
        second = [sales_order_qty_and_lead(v, _rng()) for v in (45, 12500, 850000)]
        assert first == second

    def test_expensive_items_sell_in_smaller_quantities(self) -> None:
        cheap = [sales_order_qty_and_lead(50, _rng(s))[0] for s in range(50)]
        dear = [sales_order_qty_and_lead(850_000, _rng(s))[0] for s in range(50)]
        assert min(cheap) > max(dear)

    def test_expensive_items_have_longer_lead_times(self) -> None:
        cheap = [sales_order_qty_and_lead(50, _rng(s))[1] for s in range(50)]
        dear = [sales_order_qty_and_lead(850_000, _rng(s))[1] for s in range(50)]
        assert max(cheap) <= min(dear)

    def test_missing_value_falls_into_the_cheapest_band(self) -> None:
        qty_range, _ = SALES_ORDER_BANDS[0][1], SALES_ORDER_BANDS[0][2]
        qty, _ = sales_order_qty_and_lead(0, _rng())
        assert qty_range[0] <= qty <= qty_range[1]
