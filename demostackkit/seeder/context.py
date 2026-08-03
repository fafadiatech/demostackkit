"""Factory for SeedContext with deterministic random seeding."""

from __future__ import annotations

import hashlib
import random as _random_module
from pathlib import Path
from typing import TYPE_CHECKING

from demostackkit.seeder.base import SeedContext

if TYPE_CHECKING:
    from demostackkit.core.config import IndustryConfig


def build_seed_context(
    config: "IndustryConfig",
    *,
    bench_path: str = "/home/frappe/frappe-bench",
    backend_container: str = "demostackkit-backend-1",
    random_seed: int | None = None,
    dry_run: bool = False,
    verbose: bool = False,
) -> SeedContext:
    """
    Construct a SeedContext from an IndustryConfig.

    The random seed is resolved in priority order:
    1. Explicit `random_seed` argument (e.g. from --seed CLI flag)
    2. `industry.yaml` seed.random_seed
    3. Fallback: deterministic hash of the industry slug

    This ensures `demostackkit reset` always produces the same data.
    """
    effective_seed: int
    if random_seed is not None:
        effective_seed = random_seed
    elif config.seed.random_seed:
        effective_seed = config.seed.random_seed
    else:
        digest = hashlib.sha256(config.slug.encode()).digest()
        effective_seed = int.from_bytes(digest[:8], "big")

    rng = _random_module.Random(effective_seed)

    return SeedContext(
        site=config.site.name,
        industry_slug=config.slug,
        industry_config=config,
        bench_path=bench_path,
        random=rng,
        backend_container=backend_container,
        dry_run=dry_run,
        verbose=verbose,
    )
