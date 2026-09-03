"""
Unit tests for the shared Payment Entries seeder (ref #37).

Two `_exec` round trips (fetch invoice/mode-of-payment plan, then submit
Payment Entries), so this stubs `_exec` with a small dispatcher — same
approach as test_sales_orders.py.
"""

from __future__ import annotations

import ast
import json
import random
from datetime import date, timedelta
from pathlib import Path

import pytest
from _seeder_harness import REPO_ROOT, SHARED_SEEDERS, load_seeder_class

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import SeedContext

SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "223_payment_entries.py"

_TODAY = date.today()


def _plan(rows: list[dict], modes: list[str] | None = None) -> dict:
    return {"invoices": rows, "modes_of_payment": modes or ["Cash", "Wire Transfer"]}


def _run(industry_dir: Path, cache: dict, plan: dict) -> tuple[str, str]:
    """Run the seeder, returning (plan_fetch_script, submit_script).

    submit_script is "" if the seeder no-oped before the second round trip
    (e.g. no invoices ended up with a payment).
    """
    seeder_cls = load_seeder_class(SEEDER_PATH, "PaymentEntrySeeder")
    calls: list[str] = []

    class Recording(seeder_cls):  # type: ignore[valid-type, misc]
        def _exec(self, script: str, timeout: int = 120) -> str:
            calls.append(script)
            if len(calls) == 1:
                return f"DSK_PAYMENT_ENTRIES_PLAN::{json.dumps(plan)}\n"
            return "DSK_PAYMENT_ENTRIES::" + json.dumps({"created": 1, "errors": 0}) + "\n"

    cfg = load_industry_config(industry_dir / "industry.yaml")
    ctx = SeedContext(
        site=cfg.site.name,
        industry_slug=industry_dir.name,
        industry_config=cfg,
        bench_path="/home/frappe/frappe-bench",
        random=random.Random(cfg.seed.random_seed),
    )
    for key, value in cache.items():
        ctx.cache_set(key, value)
    Recording(ctx).run()
    return (calls[0] if calls else "", calls[1] if len(calls) > 1 else "")


_CACHE = {"sales_invoices": {"DN-0001": "SI-0001", "DN-0002": "SI-0002"}}


@pytest.mark.unit
class TestPaymentEntrySeeder:
    def test_noop_without_sales_invoices_cache(self) -> None:
        plan_script, submit_script = _run(
            REPO_ROOT / "industries" / "garment", cache={}, plan=_plan([])
        )
        assert plan_script == ""
        assert submit_script == ""

    def test_generated_scripts_are_valid_python(self) -> None:
        rows = [
            {
                "name": "SI-0001",
                "posting_date": (_TODAY - timedelta(days=60)).isoformat(),
                "due_date": (_TODAY - timedelta(days=30)).isoformat(),
                "grand_total": 1000.0,
                "outstanding_amount": 1000.0,
            }
        ]
        plan_script, submit_script = _run(
            REPO_ROOT / "industries" / "garment", cache=_CACHE, plan=_plan(rows)
        )
        assert plan_script
        ast.parse(plan_script)
        # Some fraction of runs land on "unpaid" (no submit script); force
        # determinism isn't needed here, just that whatever script we did
        # get is valid.
        if submit_script:
            ast.parse(submit_script)

    def test_uses_get_payment_entry_mapper(self) -> None:
        rows = [
            {
                "name": "SI-0001",
                "posting_date": (_TODAY - timedelta(days=60)).isoformat(),
                "due_date": (_TODAY - timedelta(days=30)).isoformat(),
                "grand_total": 1000.0,
                "outstanding_amount": 1000.0,
            }
        ]
        # Run a handful of seeds until we get at least one payment through,
        # since status assignment is randomised.
        for seed in range(20):
            seeder_cls = load_seeder_class(SEEDER_PATH, "PaymentEntrySeeder")
            calls: list[str] = []

            class Recording(seeder_cls):  # type: ignore[valid-type, misc]
                def _exec(self, script: str, timeout: int = 120) -> str:
                    calls.append(script)
                    if len(calls) == 1:
                        return f"DSK_PAYMENT_ENTRIES_PLAN::{json.dumps(_plan(rows))}\n"
                    return "DSK_PAYMENT_ENTRIES::" + json.dumps({"created": 1, "errors": 0}) + "\n"

            cfg = load_industry_config(REPO_ROOT / "industries" / "garment" / "industry.yaml")
            ctx = SeedContext(
                site=cfg.site.name,
                industry_slug="garment",
                industry_config=cfg,
                bench_path="/home/frappe/frappe-bench",
                random=random.Random(seed),
            )
            for key, value in _CACHE.items():
                ctx.cache_set(key, value)
            Recording(ctx).run()
            if len(calls) > 1:
                assert (
                    "from erpnext.accounts.doctype.payment_entry.payment_entry "
                    "import get_payment_entry" in calls[1]
                )
                return
        pytest.fail("no seed in range produced a submitted payment")

    def test_skips_invoices_with_zero_outstanding(self) -> None:
        rows = [
            {
                "name": "SI-0001",
                "posting_date": (_TODAY - timedelta(days=60)).isoformat(),
                "due_date": (_TODAY - timedelta(days=30)).isoformat(),
                "grand_total": 1000.0,
                "outstanding_amount": 0.0,
            }
        ]
        _, submit_script = _run(
            REPO_ROOT / "industries" / "garment", cache=_CACHE, plan=_plan(rows)
        )
        assert submit_script == ""

    def test_full_late_never_predates_due_date_or_exceeds_today(self) -> None:
        seeder_cls = load_seeder_class(SEEDER_PATH, "PaymentEntrySeeder")
        seeder = seeder_cls.__new__(seeder_cls)
        rng = random.Random(1)
        posting_date = _TODAY - timedelta(days=200)
        due_date = _TODAY - timedelta(days=170)
        for _ in range(200):
            pay_date = seeder._pick_pay_date(rng, "full_late", posting_date, due_date, _TODAY)
            assert due_date < pay_date <= _TODAY

    def test_full_on_time_never_exceeds_due_date_or_today(self) -> None:
        seeder_cls = load_seeder_class(SEEDER_PATH, "PaymentEntrySeeder")
        seeder = seeder_cls.__new__(seeder_cls)
        rng = random.Random(2)
        posting_date = _TODAY - timedelta(days=10)
        due_date = _TODAY + timedelta(days=20)
        for _ in range(200):
            pay_date = seeder._pick_pay_date(rng, "full_on_time", posting_date, due_date, _TODAY)
            assert posting_date <= pay_date <= min(due_date, _TODAY)
