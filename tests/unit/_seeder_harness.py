"""
Shared harness for the "stub `_exec`, capture the generated Frappe script"
style of unit test used by every shared-seeder test file: test_standard_
warehouses.py, test_subcontracting_setup.py, test_purchase_receipts.py,
test_return_to_vendor.py, test_delivery_notes.py, test_customer_returns.py.

Not a test module itself — the leading underscore keeps pytest from
collecting it. Sibling files import it directly (`from _seeder_harness
import ...`), which works because there is no `__init__.py` under tests/,
so pytest's rootless "prepend" import mode puts tests/unit/ on sys.path.
"""

from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path
from typing import Any

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import BaseSeeder, SeedContext

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED_SEEDERS = REPO_ROOT / "demostackkit" / "seeders"


def load_seeder_class(seeder_path: Path, class_name: str) -> type[BaseSeeder]:
    """Import a seeder module straight from its file path and return one class.

    Seeder filenames carry a numeric priority prefix (e.g.
    `211_purchase_receipts.py`), which isn't a valid Python module name, so
    they're loaded by path — the same way
    `demostackkit.seeder.loader.discover_seeders` does — rather than via a
    normal import.
    """
    spec = importlib.util.spec_from_file_location(f"_test_{class_name}", seeder_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)


def all_industry_dirs() -> list[Path]:
    """Every real industry package (excludes `_template` and anything without industry.yaml)."""
    return sorted(
        d
        for d in (REPO_ROOT / "industries").iterdir()
        if d.is_dir() and not d.name.startswith("_") and (d / "industry.yaml").is_file()
    )


def industry_dirs_with_module(module: str) -> list[Path]:
    return [
        d
        for d in all_industry_dirs()
        if module in load_industry_config(d / "industry.yaml").modules
    ]


def industry_dirs_without_module(module: str) -> list[Path]:
    have = set(industry_dirs_with_module(module))
    return [d for d in all_industry_dirs() if d not in have]


def run_seeder(
    seeder_cls: type[BaseSeeder],
    industry_dir: Path,
    cache: dict[str, Any] | None = None,
) -> str:
    """Run a seeder against an industry, returning the script it would have executed.

    `_exec` is stubbed to capture rather than run the script, so this never
    touches Docker/Frappe. `cache` seeds `SeedContext`'s cross-seeder cache
    before `run()`, for seeders driven by another seeder's cached output
    rather than by module gating alone. Returns "" if the seeder no-oped.
    """
    captured: list[str] = []

    class Recording(seeder_cls):  # type: ignore[valid-type, misc]
        def _exec(self, script: str, timeout: int = 120) -> str:
            captured.append(script)
            return ""

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
    return captured[0] if captured else ""


def payload_from_script(script: str) -> dict:
    """Extract the `payload = json.loads('''...''')` JSON blob a seeder script embeds."""
    return json.loads(script.split("payload = json.loads('''", 1)[1].split("''')", 1)[0])
