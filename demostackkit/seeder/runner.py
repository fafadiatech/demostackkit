"""
Seeder runner: orchestrates discovery, validation, and execution.

Provides progress output via Rich console and handles errors
according to each seeder's `required` flag.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from demostackkit.core.exceptions import SeederError, SeedValidationError
from demostackkit.seeder.base import BaseSeeder, SeedContext
from demostackkit.seeder.loader import discover_seeders, instantiate_seeders

if TYPE_CHECKING:
    pass

console = Console()


class SeedRunner:
    """
    Discovers and runs all seeders for a given industry directory.

    Usage:
        runner = SeedRunner(industry_dir, ctx)
        runner.run(phase="all")  # "all", "master", "transactions"
    """

    def __init__(self, industry_dir: Path, ctx: SeedContext) -> None:
        self.industry_dir = industry_dir
        self.ctx = ctx
        # Resolve demostackkit/seeders/ relative to this file (demostackkit/seeder/runner.py)
        shared_dir = Path(__file__).resolve().parent.parent / "seeders"
        self._seeder_classes = discover_seeders(
            industry_dir,
            shared_dirs=[shared_dir] if shared_dir.is_dir() else None,
        )
        self._seeders = instantiate_seeders(self._seeder_classes, ctx)

    def run(self, phase: str = "all") -> SeedResult:
        """
        Run seeders for the given phase.

        Args:
            phase: "all" | "master" | "transactions"
        """
        from demostackkit.seeder.base import BaseMasterSeeder, BaseTransactionSeeder

        phase_filter: type[BaseSeeder] | None = None
        if phase == "master":
            phase_filter = BaseMasterSeeder
        elif phase == "transactions":
            phase_filter = BaseTransactionSeeder

        seeders = self._seeders
        if phase_filter is not None:
            seeders = [s for s in seeders if isinstance(s, phase_filter)]

        if not seeders:
            console.print(f"[yellow]No seeders found for phase '{phase}'[/yellow]")
            return SeedResult(total=0, succeeded=0, failed=0, skipped=0, errors={})

        console.print(
            f"\n[bold]Running {len(seeders)} seeder(s) for '{self.ctx.industry_slug}'[/bold]"
        )

        result = SeedResult(total=len(seeders), succeeded=0, failed=0, skipped=0, errors={})

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            for seeder in seeders:
                label = seeder.label or type(seeder).__name__
                task = progress.add_task(f"[cyan]{label}[/cyan]", total=None)

                # Pre-flight validation
                errors = seeder.validate()
                if errors:
                    progress.update(task, description=f"[red]✗ {label}[/red]")
                    exc = SeedValidationError(type(seeder).__name__, errors)
                    result.errors[label] = str(exc)
                    result.failed += 1
                    if seeder.required:
                        raise exc
                    progress.advance(task)
                    continue

                # Execution
                try:
                    if not self.ctx.dry_run:
                        seeder.run()
                    progress.update(task, description=f"[green]✓ {label}[/green]")
                    result.succeeded += 1
                except Exception as exc:
                    progress.update(task, description=f"[red]✗ {label}[/red]")
                    seed_err = SeederError(type(seeder).__name__, exc)
                    result.errors[label] = str(seed_err)
                    result.failed += 1
                    if seeder.required:
                        raise seed_err from exc
                    console.print(f"  [yellow]Skipping required=False seeder: {exc}[/yellow]")
                finally:
                    seeder.teardown()
                    progress.advance(task)

        _print_summary(result, console)
        return result


class SeedResult:
    def __init__(
        self, total: int, succeeded: int, failed: int, skipped: int, errors: dict[str, str]
    ) -> None:
        self.total = total
        self.succeeded = succeeded
        self.failed = failed
        self.skipped = skipped
        self.errors = errors

    @property
    def ok(self) -> bool:
        return self.failed == 0


def _print_summary(result: SeedResult, con: Console) -> None:
    table = Table(title="Seed Summary", show_header=True)
    table.add_column("Metric", style="bold")
    table.add_column("Count", justify="right")
    table.add_row("Total", str(result.total))
    table.add_row("[green]Succeeded[/green]", f"[green]{result.succeeded}[/green]")
    table.add_row("[red]Failed[/red]", f"[red]{result.failed}[/red]")
    table.add_row("Skipped", str(result.skipped))
    con.print(table)

    if result.errors:
        con.print("\n[bold red]Errors:[/bold red]")
        for label, msg in result.errors.items():
            con.print(f"  [red]{label}[/red]: {msg}")
