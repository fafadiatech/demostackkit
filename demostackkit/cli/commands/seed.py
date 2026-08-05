"""demostackkit seed <industry> — run data seeders."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

console = Console()


def seed(
    industry: Annotated[str, typer.Argument(help="Industry slug, e.g. garment")],
    phase: Annotated[
        str,
        typer.Option("--phase", "-p", help="Seed phase: all | master | transactions"),
    ] = "all",
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Show what would run without executing")
    ] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    random_seed: Annotated[int | None, typer.Option("--seed", help="Override random seed")] = None,
    currency: Annotated[
        str | None,
        typer.Option("--currency", help="Override currency ISO 4217 code, e.g. USD, INR"),
    ] = None,
) -> None:
    """Run master and/or transactional data seeders for an industry."""
    from demostackkit.core.discovery import get_industries_root

    if phase not in ("all", "master", "transactions"):
        console.print("[red]--phase must be one of: all, master, transactions[/red]")
        raise typer.Exit(1)

    repo_root = get_industries_root().parent
    _do_seed(
        industry,
        phase=phase,
        repo_root=repo_root,
        dry_run=dry_run,
        verbose=verbose,
        random_seed=random_seed,
        currency=currency,
    )


def _do_seed(
    industry: str,
    *,
    phase: str = "all",
    repo_root: Path,
    dry_run: bool = False,
    verbose: bool = False,
    random_seed: int | None = None,
    currency: str | None = None,
) -> None:
    """Internal seed runner, callable from other commands (e.g. up)."""
    from demostackkit.core.discovery import IndustryRegistry
    from demostackkit.seeder.context import build_seed_context
    from demostackkit.seeder.runner import SeedRunner

    industries_root = repo_root / "industries"
    registry = IndustryRegistry.from_root(industries_root)
    config = registry.get(industry)
    if currency:
        config.company.currency = currency

    ctx = build_seed_context(
        config,
        dry_run=dry_run,
        verbose=verbose,
        random_seed=random_seed,
    )

    runner = SeedRunner(config.industry_dir, ctx)
    result = runner.run(phase=phase)

    if not result.ok:
        raise typer.Exit(1)
