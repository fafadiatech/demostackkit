"""
Unit tests for the shared Bank Accounts seeder (ref #38).

Same "stub `_exec`, capture the generated script" approach as
test_sales_tax_templates.py — one round trip, then check the embedded
payload and script contents.
"""

from __future__ import annotations

import ast

import pytest
from _seeder_harness import REPO_ROOT, SHARED_SEEDERS, load_seeder_class, payload_from_script

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import SeedContext

SEEDER_PATH = SHARED_SEEDERS / "01_master" / "92_bank_accounts.py"


def _make_seeder(industry_dir, calls: list[str], response: str):
    seeder_cls = load_seeder_class(SEEDER_PATH, "BankAccountSeeder")

    class Recording(seeder_cls):  # type: ignore[valid-type, misc]
        def _exec(self, script: str, timeout: int = 120) -> str:
            calls.append(script)
            return response

    cfg = load_industry_config(industry_dir / "industry.yaml")
    ctx = SeedContext(
        site=cfg.site.name,
        industry_slug=industry_dir.name,
        industry_config=cfg,
        bench_path="/home/frappe/frappe-bench",
        random=__import__("random").Random(cfg.seed.random_seed),
    )
    return Recording(ctx), ctx


@pytest.mark.unit
class TestBankAccountSeeder:
    def test_generated_script_is_valid_python(self) -> None:
        calls: list[str] = []
        seeder, _ = _make_seeder(
            REPO_ROOT / "industries" / "garment",
            calls,
            'DSK_BANK_ACCOUNTS::{"bank_accounts": {}}\n',
        )
        seeder.run()
        assert calls
        ast.parse(calls[0])

    def test_payload_includes_default_single_company(self) -> None:
        calls: list[str] = []
        seeder, _ = _make_seeder(
            REPO_ROOT / "industries" / "garment",
            calls,
            'DSK_BANK_ACCOUNTS::{"bank_accounts": {}}\n',
        )
        seeder.run()
        cfg = load_industry_config(REPO_ROOT / "industries" / "garment" / "industry.yaml")
        payload = payload_from_script(calls[0])
        assert payload["companies"] == [{"name": cfg.company.name, "abbr": cfg.company.abbr}]

    def test_uses_all_companies_cache_for_multi_company_industries(self) -> None:
        seeder_cls = load_seeder_class(SEEDER_PATH, "BankAccountSeeder")
        calls: list[str] = []

        class Recording(seeder_cls):  # type: ignore[valid-type, misc]
            def _exec(self, script: str, timeout: int = 120) -> str:
                calls.append(script)
                return 'DSK_BANK_ACCOUNTS::{"bank_accounts": {}}\n'

        cfg = load_industry_config(REPO_ROOT / "industries" / "electrical" / "industry.yaml")
        ctx = SeedContext(
            site=cfg.site.name,
            industry_slug="electrical",
            industry_config=cfg,
            bench_path="/home/frappe/frappe-bench",
            random=__import__("random").Random(cfg.seed.random_seed),
        )
        all_companies = [{"name": "Sub Co", "abbr": "SUB"}]
        ctx.cache_set("all_companies", all_companies)
        Recording(ctx).run()

        payload = payload_from_script(calls[0])
        assert payload["companies"] == all_companies

    def test_caches_bank_accounts_from_payload(self) -> None:
        calls: list[str] = []
        seeder, ctx = _make_seeder(
            REPO_ROOT / "industries" / "garment",
            calls,
            'DSK_BANK_ACCOUNTS::{"bank_accounts": {"ACME Inc": "ACME Inc Current Account - Demo Bank"}}\n',
        )
        seeder.run()
        assert ctx.cache_get("bank_accounts") == {
            "ACME Inc": "ACME Inc Current Account - Demo Bank"
        }

    def test_script_sets_default_bank_account_only_when_unset(self) -> None:
        calls: list[str] = []
        seeder, _ = _make_seeder(
            REPO_ROOT / "industries" / "garment",
            calls,
            'DSK_BANK_ACCOUNTS::{"bank_accounts": {}}\n',
        )
        seeder.run()
        assert "default_bank_account" in calls[0]
        assert "frappe.db.get_value('Company', company, 'default_bank_account')" in calls[0]
