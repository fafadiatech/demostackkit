"""
Unit tests for apps.txt reconciliation in `demostackkit up`.

sites/apps.txt lives in the persistent `sites` volume while apps/ lives in the
backend container's writable layer, so recreating that container leaves apps.txt
naming apps that are no longer on disk. Frappe imports every app in apps.txt on
any `bench --site` call, so a stale entry raises ModuleNotFoundError before any
seeding happens. These tests stub the BenchClient and assert on what the
reconciler would have written back.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from demostackkit.cli.commands.up import _reconcile_apps_txt
from demostackkit.core.config import load_industry_config
from demostackkit.erpnext.bench import BenchClient

REPO_ROOT = Path(__file__).parent.parent.parent
INDUSTRIES = REPO_ROOT / "industries"

# Apps every industry fetches via bench get-app; helpdesk depends on telephony.
EXPECTED_EXTRA_APPS = {"hrms", "telephony", "helpdesk"}


class FakeBench(BenchClient):
    """BenchClient with the container round-trips replaced by in-memory state."""

    def __init__(self, listed: list[str], on_disk: set[str]) -> None:
        super().__init__(container="fake", site="fake.localhost")
        self.listed = list(listed)
        self.on_disk = set(on_disk)
        self.writes: list[list[str]] = []

    def apps_txt_entries(self) -> list[str]:
        return list(self.listed)

    def app_exists_in_bench(self, app_name: str) -> bool:
        return app_name in self.on_disk

    def write_apps_txt(self, app_names: list[str]) -> None:
        self.writes.append(list(app_names))
        self.listed = list(app_names)


def _config(slug: str):
    return load_industry_config(INDUSTRIES / slug / "industry.yaml")


def test_stale_entry_not_declared_by_industry_is_pruned() -> None:
    """The reported bug: apps.txt names telephony, apps/ does not have it."""
    config = _config("electrical")
    config.extra_apps = []
    bench = FakeBench(
        listed=["frappe", "erpnext", "telephony", "helpdesk", "hrms"],
        on_disk={"frappe", "erpnext"},
    )

    assert _reconcile_apps_txt(config, bench) is True
    assert bench.writes == [["frappe", "erpnext"]]


def test_missing_apps_the_industry_declares_are_left_for_refetch() -> None:
    """extra_apps entries stay in apps.txt — _fetch_extra_apps restores them next."""
    config = _config("electrical")
    bench = FakeBench(
        listed=["frappe", "erpnext", "telephony", "helpdesk", "hrms"],
        on_disk={"frappe", "erpnext"},
    )

    assert _reconcile_apps_txt(config, bench) is False
    assert bench.writes == []


def test_healthy_bench_is_left_untouched() -> None:
    config = _config("electrical")
    bench = FakeBench(
        listed=["frappe", "erpnext", "telephony", "helpdesk", "hrms"],
        on_disk={"frappe", "erpnext", "telephony", "helpdesk", "hrms"},
    )

    assert _reconcile_apps_txt(config, bench) is False
    assert bench.writes == []


def test_partial_drift_prunes_only_the_missing_entries() -> None:
    config = _config("electrical")
    config.extra_apps = []
    bench = FakeBench(
        listed=["frappe", "erpnext", "telephony", "helpdesk", "hrms"],
        on_disk={"frappe", "erpnext", "hrms"},
    )

    assert _reconcile_apps_txt(config, bench) is True
    assert bench.writes == [["frappe", "erpnext", "hrms"]]


def test_empty_apps_txt_is_a_noop() -> None:
    config = _config("electrical")
    bench = FakeBench(listed=[], on_disk=set())

    assert _reconcile_apps_txt(config, bench) is False
    assert bench.writes == []


@pytest.mark.parametrize(
    "slug",
    sorted(
        p.parent.name for p in INDUSTRIES.glob("*/industry.yaml") if p.parent.name != "_template"
    ),
)
def test_every_industry_declares_the_standard_extra_apps(slug: str) -> None:
    """An industry with an empty extra_apps cannot self-heal a drifted bench.

    It skips get-app entirely and goes straight to a `bench --site` call, so it
    inherits whatever stale entries another industry's run left behind.
    """
    config = _config(slug)
    assert EXPECTED_EXTRA_APPS.issubset({e.name for e in config.extra_apps})
