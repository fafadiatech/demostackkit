"""Unit tests for extra app asset sync in `demostackkit up`."""

from __future__ import annotations

from pathlib import Path

from demostackkit.cli.commands.up import _sync_extra_app_assets
from demostackkit.core.config import load_industry_config
from demostackkit.erpnext.bench import BenchClient

REPO_ROOT = Path(__file__).parent.parent.parent
INDUSTRIES = REPO_ROOT / "industries"


class FakeBench(BenchClient):
    def __init__(self) -> None:
        super().__init__(container="fake", site="fake.localhost")
        self.built: list[str] = []
        self.materialized: list[str] = []
        self.materialize_returns: bool = False

    def build_app_assets(self, app_names: list[str]) -> None:
        self.built.extend(app_names)

    def materialize_app_assets(self, app_names: list[str]) -> bool:
        self.materialized.extend(app_names)
        return self.materialize_returns


def _config(slug: str):
    return load_industry_config(INDUSTRIES / slug / "industry.yaml")


def test_sync_builds_and_materializes_extra_apps() -> None:
    config = _config("electrical")
    bench = FakeBench()
    bench.materialize_returns = True

    assert _sync_extra_app_assets(config, bench, build=True) is True
    assert bench.built == ["hrms", "telephony", "helpdesk"]
    assert bench.materialized == ["hrms", "telephony", "helpdesk"]


def test_sync_skips_build_when_not_requested() -> None:
    config = _config("electrical")
    bench = FakeBench()

    assert _sync_extra_app_assets(config, bench, build=False) is False
    assert bench.built == []
    assert bench.materialized == ["hrms", "telephony", "helpdesk"]


def test_sync_returns_false_when_nothing_materialized() -> None:
    config = _config("electrical")
    bench = FakeBench()
    bench.materialize_returns = False

    assert _sync_extra_app_assets(config, bench, build=False) is False
