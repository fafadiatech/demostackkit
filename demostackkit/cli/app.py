"""
Typer CLI application root.

All sub-commands are registered here and re-exported via the `main` entry point.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from demostackkit import __version__

console = Console()

app = typer.Typer(
    name="demostackkit",
    help="Create, manage and distribute ERPNext demo environments for different industries.",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# ── Global state ──────────────────────────────────────────────────────────────

_state: dict = {}


def _get_industries_root() -> Path:
    from demostackkit.core.discovery import get_industries_root
    return get_industries_root()


def _get_compose_file() -> Path:
    """Resolve the master docker-compose.yml."""
    root = _get_industries_root().parent
    return root / "infra" / "docker-compose.yml"


def _get_env_file() -> Path:
    root = _get_industries_root().parent
    return root / "infra" / ".env"


# ── Sub-command imports (late to avoid circular imports) ───────────────────────

from demostackkit.cli.commands import (  # noqa: E402
    init,
    create,
    up,
    down,
    reset,
    seed,
    backup,
    restore,
    validate,
    list_cmd,
    doctor,
    use,
    purge,
    install_app,
)

app.add_typer(init.app, name="init")
app.command("create")(create.create)
app.command("up")(up.up)
app.command("down")(down.down)
app.command("reset")(reset.reset)
app.command("seed")(seed.seed)
app.command("backup")(backup.backup)
app.command("restore")(restore.restore)
app.command("validate")(validate.validate)
app.command("list")(list_cmd.list_industries)
app.command("doctor")(doctor.doctor)
app.command("use")(use.use)
app.command("purge")(purge.purge)
app.command("install-app")(install_app.install_app)


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option("--version", "-V", help="Show version and exit."),
    ] = False,
) -> None:
    if version:
        console.print(f"demostackkit {__version__}")
        raise typer.Exit()


def main() -> None:
    app()
