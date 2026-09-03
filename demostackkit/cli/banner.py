"""Startup banner shown for the bare `demostackkit` invocation."""

from __future__ import annotations

from rich.console import Console

ASCII_ART = r"""
 ____                      ____  _             _    _  ___ _
|  _ \  ___ _ __ ___   ___/ ___|| |_ __ _  ___| | _| |/ (_) |_
| | | |/ _ \ '_ ` _ \ / _ \___ \| __/ _` |/ __| |/ / ' /| | __|
| |_| |  __/ | | | | | (_) |__) | || (_| | (__|   <| . \| | |_
|____/ \___|_| |_| |_|\___/____/ \__\__,_|\___|_|\_\_|\_\_|\__|
""".strip("\n")


def print_banner(console: Console) -> None:
    console.print()
    console.print(ASCII_ART, style="bold cyan")
    console.print("SPIN • EXPLORE • LEARN", style="cyan")
    console.print("Industry-ready ERPNext demo environments, in minutes.", style="italic")
    console.print()
