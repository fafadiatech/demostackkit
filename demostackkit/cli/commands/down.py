"""demostackkit down <industry> — stop an industry demo environment."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

console = Console()


def down(
    industry: Annotated[str, typer.Argument(help="Industry slug, e.g. garment")],
    volumes: Annotated[
        bool, typer.Option("--volumes", "-v", help="Also remove Docker volumes (destroys data)")
    ] = False,
) -> None:
    """Stop the demo environment for the given industry."""
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root
    from demostackkit.docker.compose_runner import ComposeRunner

    industries_root = get_industries_root()
    registry = IndustryRegistry.from_root(industries_root)
    config = registry.get(industry)

    repo_root = industries_root.parent
    compose_file = repo_root / "infra" / "docker-compose.yml"
    env_file = repo_root / "infra" / ".env"

    runner = ComposeRunner(compose_file=compose_file, env_file=env_file)

    if volumes:
        confirm = typer.confirm(
            f"This will destroy all data for '{industry}'. Are you sure?", default=False
        )
        if not confirm:
            raise typer.Abort()

    console.print(f"[bold]Stopping '{config.name}'...[/bold]")
    runner.down(profile=None, volumes=volumes)
    console.print("[green]Done.[/green]")
