"""
Subprocess wrapper around `docker compose`.

All Docker operations in demostackkit go through ComposeRunner.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from rich.console import Console

from demostackkit.core.exceptions import DockerError

console = Console()


class ComposeRunner:
    """
    Wraps `docker compose` CLI for a specific project.

    Args:
        compose_file: Path to the master docker-compose.yml
        project_name: Docker Compose project name (default: demostackkit)
        env_file: Path to .env file to load
    """

    def __init__(
        self,
        compose_file: Path,
        project_name: str = "demostackkit",
        env_file: Path | None = None,
        extra_compose_files: list[Path] | None = None,
    ) -> None:
        self.compose_file = compose_file
        self.project_name = project_name
        self.env_file = env_file
        self.extra_compose_files = extra_compose_files or []

    def _base_cmd(self) -> list[str]:
        cmd = ["docker", "compose", "-p", self.project_name, "-f", str(self.compose_file)]
        for f in self.extra_compose_files:
            cmd += ["-f", str(f)]
        if self.env_file and self.env_file.exists():
            cmd += ["--env-file", str(self.env_file)]
        return cmd

    def _run(
        self,
        args: list[str],
        *,
        env: dict[str, str] | None = None,
        stream: bool = False,
    ) -> str:
        cmd = self._base_cmd() + args
        merged_env = {**os.environ, **(env or {})}

        if stream:
            process = subprocess.Popen(
                cmd,
                stdout=sys.stdout,
                stderr=sys.stderr,
                env=merged_env,
            )
            process.wait()
            if process.returncode != 0:
                raise DockerError(str(cmd), process.returncode, "")
            return ""

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=merged_env,
            timeout=600,
        )
        if result.returncode != 0:
            raise DockerError(str(cmd), result.returncode, result.stderr)
        return result.stdout.strip()

    def up(self, profile: str | None = None, *, detach: bool = True) -> None:
        """
        Start services.

        When `profile` is None, only profile-less (shared) services are started.
        This is the correct mode for the CLI path: shared infra only, seeders
        run on the host via `docker exec`.

        When `profile` is set, services tagged with that profile are also started.
        Use this only when the seeder image has been built locally first.
        """
        args = []
        if profile:
            args += ["--profile", profile]
        args += ["up"]
        if detach:
            args.append("-d")
        args.append("--remove-orphans")
        self._run(args, stream=not detach)

    def down(self, profile: str | None = None, *, volumes: bool = False, remove_images: bool = False) -> None:
        """Stop services. Pass profile=None to stop only shared services."""
        args = []
        if profile:
            args += ["--profile", profile]
        args += ["down"]
        if volumes:
            args.append("-v")
        if remove_images:
            args += ["--rmi", "all"]
        self._run(args, stream=True)

    def ps(self) -> str:
        """Show status of all running services."""
        return self._run(["ps"])

    def logs(self, service: str | None = None, *, follow: bool = False, tail: int = 50) -> None:
        """Stream logs for a service (or all services)."""
        args = ["logs", f"--tail={tail}"]
        if follow:
            args.append("-f")
        if service:
            args.append(service)
        self._run(args, stream=True)

    def exec(self, service: str, command: list[str]) -> str:
        """Execute a command in a running service container."""
        args = ["exec", service] + command
        return self._run(args)

    def pull(self) -> None:
        """Pull latest images."""
        self._run(["pull"], stream=True)

    def is_running(self, service: str) -> bool:
        """Return True if the named service is currently running."""
        try:
            output = self._run(["ps", "-q", service])
            return bool(output.strip())
        except DockerError:
            return False
