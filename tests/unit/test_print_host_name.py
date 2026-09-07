"""Unit tests for Print → PDF host_name wiring in Docker.

wkhtmltopdf fetches print assets via get_url(). Without host_name pointing at the
frontend container, that URL is http://<site>.localhost and fails inside Docker
with HostNotFoundError (frappe_docker#1547).
"""

from __future__ import annotations

from pathlib import Path

from demostackkit.cli.commands.up import PRINT_HOST_NAME, _ensure_print_host_name
from demostackkit.erpnext.bench import BenchClient

REPO_ROOT = Path(__file__).parent.parent.parent
CONFIGURE_SH = REPO_ROOT / "infra" / "configure.sh"


class FakeBench(BenchClient):
    def __init__(self) -> None:
        super().__init__(container="fake", site="fake.localhost")
        self.configs: list[tuple[str, str]] = []

    def set_config(self, key: str, value: str) -> None:
        self.configs.append((key, value))


def test_ensure_print_host_name_sets_frontend_url() -> None:
    bench = FakeBench()
    _ensure_print_host_name(bench)
    assert bench.configs == [("host_name", PRINT_HOST_NAME)]
    assert PRINT_HOST_NAME == "http://frontend:8080"


def test_configure_sh_writes_host_name_for_all_sites() -> None:
    """common_site_config must carry host_name so every site gets it on stack start."""
    text = CONFIGURE_SH.read_text()
    assert '"host_name": "http://frontend:8080"' in text
