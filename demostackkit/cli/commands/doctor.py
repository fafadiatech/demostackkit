"""demostackkit doctor — check host environment requirements."""

from __future__ import annotations

import platform
import shutil
import socket
import subprocess
import sys

from rich.console import Console
from rich.table import Table

console = Console()

_MIN_DOCKER_VERSION = (24, 0, 0)
_MIN_COMPOSE_VERSION = (2, 20, 0)
_MIN_PYTHON = (3, 10)
_MIN_RAM_GB = 4
_MIN_DISK_GB = 10

CheckResult = tuple[bool, str, str]  # (ok, label, detail)


def _check_docker() -> CheckResult:
    if not shutil.which("docker"):
        return (
            False,
            "Docker Engine",
            "Not found in PATH. Install from https://docs.docker.com/get-docker/",
        )
    try:
        out = subprocess.check_output(
            ["docker", "version", "--format", "{{.Server.Version}}"], text=True
        ).strip()
        parts = tuple(int(x) for x in out.split(".")[:3])
        if parts < _MIN_DOCKER_VERSION:
            return (
                False,
                "Docker Engine",
                f"Found {out}, need >= {'.'.join(map(str, _MIN_DOCKER_VERSION))}",
            )
        return True, "Docker Engine", f"v{out}"
    except Exception as exc:
        return False, "Docker Engine", f"Cannot query version: {exc}"


def _check_compose() -> CheckResult:
    try:
        out = subprocess.check_output(
            ["docker", "compose", "version", "--short"], text=True
        ).strip()
        parts = tuple(int(x) for x in out.lstrip("v").split(".")[:3])
        if parts < _MIN_COMPOSE_VERSION:
            return (
                False,
                "Docker Compose",
                f"Found {out}, need >= {'.'.join(map(str, _MIN_COMPOSE_VERSION))}",
            )
        return True, "Docker Compose", f"v{out}"
    except Exception as exc:
        return False, "Docker Compose", f"Cannot query version: {exc}"


def _check_python() -> CheckResult:
    ver = sys.version_info[:2]
    if ver < _MIN_PYTHON:
        return (
            False,
            "Python",
            f"Found {'.'.join(map(str, ver))}, need >= {'.'.join(map(str, _MIN_PYTHON))}",
        )
    return True, "Python", f"{sys.version.split()[0]}"


def _check_disk() -> CheckResult:
    try:
        import shutil as _shutil

        total, used, free = _shutil.disk_usage("/")
        free_gb = free / 1024**3
        if free_gb < _MIN_DISK_GB:
            return False, "Disk Space", f"{free_gb:.1f} GB free (need >= {_MIN_DISK_GB} GB)"
        return True, "Disk Space", f"{free_gb:.1f} GB free"
    except Exception as exc:
        return True, "Disk Space", f"Cannot check: {exc}"  # Non-blocking


def _check_ram() -> CheckResult:
    try:
        if platform.system() == "Darwin":
            import subprocess

            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
            ram_gb = int(out) / 1024**3
        else:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        ram_kb = int(line.split()[1])
                        ram_gb = ram_kb / 1024**2
                        break
                else:
                    return True, "RAM", "Cannot read /proc/meminfo"

        if ram_gb < _MIN_RAM_GB:
            return False, "RAM", f"{ram_gb:.1f} GB (need >= {_MIN_RAM_GB} GB)"
        return True, "RAM", f"{ram_gb:.1f} GB"
    except Exception as exc:
        return True, "RAM", f"Cannot check: {exc}"  # Non-blocking


def _check_port(port: int, label: str) -> CheckResult:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex(("127.0.0.1", port))
    sock.close()
    if result == 0:
        return False, f"Port {port} ({label})", f"Port {port} is already in use"
    return True, f"Port {port} ({label})", "Available"


def _check_env_file() -> CheckResult:
    from demostackkit.core.discovery import get_industries_root

    env_path = get_industries_root().parent / "infra" / ".env"
    if env_path.exists():
        return True, ".env file", str(env_path)
    example = env_path.parent / ".env.example"
    hint = f"Run 'demostackkit init' to create it from {example}"
    return False, ".env file", hint


def _check_industries() -> CheckResult:
    from demostackkit.core.discovery import IndustryRegistry, get_industries_root

    root = get_industries_root()
    registry = IndustryRegistry.from_root(root, skip_invalid=True)
    n = len(registry)
    errors = registry.errors()
    if errors:
        return (
            False,
            "Industry Configs",
            f"{n} valid, {len(errors)} invalid: {', '.join(errors.keys())}",
        )
    return True, "Industry Configs", f"{n} valid"


def doctor() -> None:
    """Check host environment and report any issues."""
    checks = [
        _check_docker,
        _check_compose,
        _check_python,
        _check_disk,
        _check_ram,
        lambda: _check_port(80, "HTTP"),
        lambda: _check_port(3306, "MariaDB"),
        _check_env_file,
        _check_industries,
    ]

    table = Table(title="demostackkit doctor", show_header=True, header_style="bold cyan")
    table.add_column("Status", justify="center", width=8)
    table.add_column("Check", min_width=24)
    table.add_column("Detail")

    all_ok = True
    for check_fn in checks:
        ok, label, detail = check_fn()
        status = "[green]✓[/green]" if ok else "[red]✗[/red]"
        if not ok:
            all_ok = False
        table.add_row(status, label, detail)

    console.print(table)

    if all_ok:
        console.print("\n[bold green]All checks passed. Ready to run demostackkit.[/bold green]")
    else:
        console.print(
            "\n[bold red]Some checks failed. Fix the issues above before continuing.[/bold red]"
        )
        raise SystemExit(1)
