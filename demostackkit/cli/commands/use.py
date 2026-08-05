"""demostackkit use <version> — switch the active ERPNext version."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

console = Console()

SUPPORTED_VERSIONS = {"v14", "v15", "v16"}


def use(
    version: Annotated[str, typer.Argument(help="ERPNext version to activate, e.g. v15 or v16")],
) -> None:
    """Switch the active ERPNext version in infra/.env.

    After switching you must restart any running stack so the new image is used:

        demostackkit down <industry>
        demostackkit up <industry>

    Rebuild the seeder image if you use docker compose profiles directly:

        make build-seeder
    """
    from demostackkit.core.discovery import get_industries_root

    version = version.strip().lower()
    if not re.fullmatch(r"v\d+", version):
        console.print(f"[red]Invalid version '{version}'. Expected format: v15, v16, ...[/red]")
        raise typer.Exit(code=1)

    if version not in SUPPORTED_VERSIONS:
        console.print(
            f"[yellow]Warning: '{version}' is not in the tested set {sorted(SUPPORTED_VERSIONS)}. "
            "Proceeding anyway.[/yellow]"
        )

    repo_root = get_industries_root().parent
    env_file = repo_root / "infra" / ".env"

    if not env_file.exists():
        console.print("[red]infra/.env not found. Run [bold]demostackkit init[/bold] first.[/red]")
        raise typer.Exit(code=1)

    current = _read_version(env_file)
    if current == version:
        console.print(f"[dim]Already on ERPNext {version}, nothing to do.[/dim]")
        raise typer.Exit()

    _write_version(env_file, version)
    console.print(f"[bold green]Switched ERPNext version: {current} → {version}[/bold green]")
    console.print("\nNext steps:")
    console.print("  1. Restart any running industry stack:")
    console.print("       [bold]demostackkit down <industry>[/bold]")
    console.print("       [bold]demostackkit up <industry>[/bold]")
    console.print("  2. (Optional) Rebuild seeder image if using compose profiles:")
    console.print("       [bold]make build-seeder[/bold]")


def _read_version(env_file: Path) -> str:
    """Return the current ERPNEXT_VERSION from .env, or 'unknown'."""
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("ERPNEXT_VERSION="):
            return line.split("=", 1)[1].strip()
    return "unknown"


def _write_version(env_file: Path, version: str) -> None:
    """Update ERPNEXT_VERSION in .env in-place."""
    lines = env_file.read_text(encoding="utf-8").splitlines(keepends=True)
    updated = False
    for i, line in enumerate(lines):
        if line.strip().startswith("ERPNEXT_VERSION="):
            lines[i] = f"ERPNEXT_VERSION={version}\n"
            updated = True
            break
    if not updated:
        lines.append(f"ERPNEXT_VERSION={version}\n")
    env_file.write_text("".join(lines), encoding="utf-8")
