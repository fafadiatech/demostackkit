"""demostackkit purge — destroy all containers, volumes and images for this project."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

console = Console()


def purge(
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Skip confirmation prompt")] = False,
    images: Annotated[
        bool, typer.Option("--images", help="Also remove pulled ERPNext Docker images")
    ] = False,
) -> None:
    """Destroy all containers, volumes (all site data), and optionally images.

    Use this when switching ERPNext versions or starting completely fresh.
    All industry sites and their data will be permanently deleted.
    """
    from demostackkit.core.discovery import get_industries_root
    from demostackkit.docker.compose_runner import ComposeRunner

    if not yes:
        msg = "This will DESTROY all containers and site data"
        if images:
            msg += ", and remove all pulled ERPNext images"
        confirm = typer.confirm(f"{msg}. Continue?", default=False)
        if not confirm:
            raise typer.Abort()

    repo_root = get_industries_root().parent
    compose_file = repo_root / "infra" / "docker-compose.yml"
    env_file = repo_root / "infra" / ".env"

    runner = ComposeRunner(compose_file=compose_file, env_file=env_file)

    console.print("[bold red]Stopping all containers and removing volumes...[/bold red]")
    runner.down(profile=None, volumes=True, remove_images=images)

    console.print("[bold green]Purge complete.[/bold green]")
    if images:
        console.print(
            "[dim]Run [bold]demostackkit up <industry>[/bold] to pull fresh images and start again.[/dim]"
        )
    else:
        console.print("[dim]Run [bold]demostackkit up <industry>[/bold] to start again.[/dim]")
