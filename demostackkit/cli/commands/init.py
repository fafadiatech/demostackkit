"""demostackkit init — first-time project setup."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console

console = Console()
app = typer.Typer(help="Initialise demostackkit in the current directory.")


@app.callback(invoke_without_command=True)
def init(ctx: typer.Context) -> None:
    """Copy .env.example to infra/.env and prepare the working directory."""
    from demostackkit.core.discovery import get_industries_root

    repo_root = get_industries_root().parent
    infra_dir = repo_root / "infra"
    env_example = infra_dir / ".env.example"
    env_target = infra_dir / ".env"

    # Ensure runtime directories exist
    for d in ["sites", "backups", "logs", ".generated"]:
        (infra_dir / d).mkdir(parents=True, exist_ok=True)

    if env_target.exists():
        console.print(f"[yellow]infra/.env already exists[/yellow] — skipping (edit it manually if needed)")
    elif env_example.exists():
        shutil.copy(env_example, env_target)
        console.print(f"[green]Created infra/.env from infra/.env.example[/green]")
        console.print("[bold]Edit infra/.env to set passwords before running 'demostackkit up'[/bold]")
    else:
        # Write a minimal .env
        env_target.write_text(
            "DB_ROOT_PASSWORD=erpnext\n"
            "SITE_ADMIN_PASSWORD=admin\n"
            "ERPNEXT_VERSION=v15\n",
            encoding="utf-8",
        )
        console.print(f"[green]Created infra/.env with default values[/green]")

    console.print(f"\n[cyan]Run:[/cyan] demostackkit list")
    console.print(f"[cyan]Run:[/cyan] demostackkit doctor")
    console.print(f"[cyan]Run:[/cyan] demostackkit up <industry>")
