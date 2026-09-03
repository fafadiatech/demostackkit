"""
Unit tests for the shared Bank Transactions seeder (ref #38).

Two `_exec` round trips (fetch reconcilable Payment Entries, then submit
Bank Transactions) — same dispatcher approach as test_payment_entries.py.
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

SEEDER_PATH = SHARED_SEEDERS / "02_transactions" / "224_bank_transactions.py"

_TODAY = date.today()

_BANK_ACCOUNTS = {"ACME Inc": "ACME Inc Current Account - Demo Bank"}

_PE_ROW = {
    "name": "ACC-PAY-2026-00001",
    "bank_account": _BANK_ACCOUNTS["ACME Inc"],
    "posting_date": (_TODAY - timedelta(days=10)).isoformat(),
    "reference_no": "PMT-SI-0001",
    "paid_amount": 1000.0,
    "party": "Some Customer",
}


def _run(industry_dir: Path, cache: dict, plan_rows: list[dict], seed: int = 0) -> tuple[str, str]:
    seeder_cls = load_seeder_class(SEEDER_PATH, "BankTransactionSeeder")
    calls: list[str] = []

    class Recording(seeder_cls):  # type: ignore[valid-type, misc]
        def _exec(self, script: str, timeout: int = 120) -> str:
            calls.append(script)
            if len(calls) == 1:
                return f"DSK_BANK_TXN_PLAN::{json.dumps({'payment_entries': plan_rows})}\n"
            return (
                "DSK_BANK_TXN::" + json.dumps({"created": 1, "reconciled": 0, "errors": 0}) + "\n"
            )

    cfg = load_industry_config(industry_dir / "industry.yaml")
    ctx = SeedContext(
        site=cfg.site.name,
        industry_slug=industry_dir.name,
        industry_config=cfg,
        bench_path="/home/frappe/frappe-bench",
        random=random.Random(seed),
    )
    for key, value in cache.items():
        ctx.cache_set(key, value)
    Recording(ctx).run()
    return (calls[0] if calls else "", calls[1] if len(calls) > 1 else "")


@pytest.mark.unit
class TestBankTransactionSeeder:
    def test_noop_without_bank_accounts_cache(self) -> None:
        plan_script, submit_script = _run(
            REPO_ROOT / "industries" / "garment", cache={}, plan_rows=[]
        )
        assert plan_script == ""
        assert submit_script == ""

    def test_validate_requires_bank_accounts_cache(self) -> None:
        seeder_cls = load_seeder_class(SEEDER_PATH, "BankTransactionSeeder")
        cfg = load_industry_config(REPO_ROOT / "industries" / "garment" / "industry.yaml")
        ctx = SeedContext(
            site=cfg.site.name,
            industry_slug="garment",
            industry_config=cfg,
            bench_path="/home/frappe/frappe-bench",
            random=random.Random(0),
        )
        assert seeder_cls(ctx).validate()

        ctx.cache_set("bank_accounts", _BANK_ACCOUNTS)
        assert seeder_cls(ctx).validate() == []

    def test_generated_scripts_are_valid_python(self) -> None:
        plan_script, submit_script = _run(
            REPO_ROOT / "industries" / "garment",
            cache={"bank_accounts": _BANK_ACCOUNTS},
            plan_rows=[_PE_ROW],
        )
        assert plan_script
        ast.parse(plan_script)
        assert submit_script
        ast.parse(submit_script)

    def test_noop_when_no_reconcilable_payment_entries(self) -> None:
        _, submit_script = _run(
            REPO_ROOT / "industries" / "garment",
            cache={"bank_accounts": _BANK_ACCOUNTS},
            plan_rows=[],
        )
        assert submit_script == ""

    def test_uses_reconcile_vouchers_for_matched_outcome(self) -> None:
        # Run across seeds until one lands on "matched" (status assignment is
        # randomised), then check the submit script calls reconcile_vouchers
        # for that Payment Entry.
        for seed in range(50):
            _, submit_script = _run(
                REPO_ROOT / "industries" / "garment",
                cache={"bank_accounts": _BANK_ACCOUNTS},
                plan_rows=[_PE_ROW],
                seed=seed,
            )
            if (
                submit_script
                and "reconcile_vouchers" in submit_script
                and (f'"payment_entry": "{_PE_ROW["name"]}"' in submit_script.replace("'", '"'))
            ):
                assert (
                    "from erpnext.accounts.doctype.bank_reconciliation_tool"
                    ".bank_reconciliation_tool import" in submit_script
                )
                return
        pytest.fail("no seed in range produced a matched/reconciled transaction")

    def test_every_row_produces_exactly_one_transaction(self) -> None:
        rows = [{**_PE_ROW, "name": f"ACC-PAY-2026-0000{i}"} for i in range(1, 4)]
        _, submit_script = _run(
            REPO_ROOT / "industries" / "garment",
            cache={"bank_accounts": _BANK_ACCOUNTS},
            plan_rows=rows,
            seed=3,
        )
        transactions_json = submit_script.split("transactions = json.loads('''", 1)[1].split(
            "''')", 1
        )[0]
        transactions = json.loads(transactions_json)
        assert len(transactions) == len(rows)
        assert {t["reference_number"] for t in transactions} == {
            row["reference_no"] for row in rows
        }
