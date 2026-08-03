"""
Wrapper around the Frappe `bench` CLI executed inside the backend container.

All seeder interactions with ERPNext go through `bench execute`
(for Python expressions) or `bench --site <site> <command>` (for bench commands).
This avoids HTTP authentication complexity and is faster than REST calls.
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from demostackkit.core.exceptions import BenchError


class BenchClient:
    """
    Executes bench commands inside a running Docker container.

    All methods raise BenchError on non-zero exit codes.
    """

    def __init__(self, container: str, site: str, bench_path: str = "/home/frappe/frappe-bench") -> None:
        self.container = container
        self.site = site
        self.bench_path = bench_path

    def _docker_exec(self, cmd: list[str], *, input_data: str | None = None) -> str:
        """Run a command inside the container and return stdout."""
        full_cmd = ["docker", "exec", "-i", self.container] + cmd
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                input=input_data,
                timeout=300,
            )
        except subprocess.TimeoutExpired as exc:
            raise BenchError(str(full_cmd), -1, "Command timed out after 300 seconds") from exc

        if result.returncode != 0:
            raise BenchError(str(full_cmd), result.returncode, result.stderr or result.stdout)

        return result.stdout.strip()

    def execute(self, python_expr: str) -> Any:
        """
        Run a Python expression via `bench execute` and return the result.

        The expression is executed in the Frappe context with the site
        already initialised. The return value is JSON-serialised.

        Example:
            client.execute("frappe.db.count('Customer')")
        """
        cmd = [
            "bench",
            "--site", self.site,
            "execute",
            f"--args={json.dumps([])}",
            "--kwargs={}",
            python_expr,
        ]
        output = self._docker_exec(
            ["bash", "-c", f"cd {self.bench_path} && bench --site {self.site} execute {python_expr!r}"]
        )
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output

    def execute_script(self, script: str) -> str:
        """
        Execute a multi-line Python script inside Frappe context.

        The script is piped to `bench execute` via stdin.
        """
        wrapped = (
            "import frappe; "
            f"frappe.init(site='{self.site}', sites_path='{self.bench_path}/sites'); "
            "frappe.connect(); "
            f"{script}; "
            "frappe.db.commit()"
        )
        return self._docker_exec(
            ["python", "-c", wrapped]
        )

    def insert_doc(self, doctype: str, data: dict[str, Any]) -> str:
        """
        Insert a Frappe document and return its name.

        Uses insert(ignore_if_duplicate=True) for idempotency.
        """
        script = f"""
import frappe
frappe.init(site='{self.site}', sites_path='{self.bench_path}/sites')
frappe.connect()
doc = frappe.get_doc({json.dumps({'doctype': doctype, **data})!r})
doc.insert(ignore_if_duplicate=True)
frappe.db.commit()
print(doc.name)
"""
        return self._docker_exec(["python", "-c", script])

    def doc_exists(self, doctype: str, name: str) -> bool:
        """Return True if a document exists in the DB."""
        script = f"""
import frappe
frappe.init(site='{self.site}', sites_path='{self.bench_path}/sites')
frappe.connect()
print('1' if frappe.db.exists('{doctype}', '{name}') else '0')
"""
        output = self._docker_exec(["python", "-c", script])
        return output.strip() == "1"

    def new_site(
        self,
        admin_password: str,
        db_root_password: str,
        install_apps: list[str] | None = None,
    ) -> None:
        """Create a new Frappe site."""
        cmd = (
            f"cd {self.bench_path} && "
            f"bench new-site {self.site} "
            f"--admin-password {admin_password!r} "
            f"--mariadb-root-password {db_root_password!r} "
            "--no-mariadb-socket"
        )
        self._docker_exec(["bash", "-c", cmd])

        for app in (install_apps or []):
            if app in ("frappe",):
                continue  # Already installed on new-site
            self.install_app(app)

    def install_app(self, app_name: str) -> None:
        """Install a Frappe app on the site."""
        cmd = f"cd {self.bench_path} && bench --site {self.site} install-app {app_name}"
        self._docker_exec(["bash", "-c", cmd])

    def drop_site(self, db_root_password: str) -> None:
        """Drop the Frappe site (destructive)."""
        cmd = (
            f"cd {self.bench_path} && "
            f"bench drop-site {self.site} "
            f"--root-password {db_root_password!r} "
            "--archived-sites /tmp --force"
        )
        self._docker_exec(["bash", "-c", cmd])

    def backup(self, backup_dir: str) -> str:
        """Run bench backup and return the path to the SQL file."""
        cmd = f"cd {self.bench_path} && bench --site {self.site} backup --backup-path {backup_dir!r}"
        return self._docker_exec(["bash", "-c", cmd])

    def restore(self, sql_gz_path: str, db_root_password: str) -> None:
        """Restore a bench backup from a .sql.gz file."""
        cmd = (
            f"cd {self.bench_path} && "
            f"bench --site {self.site} restore {sql_gz_path!r} "
            f"--mariadb-root-password {db_root_password!r}"
        )
        self._docker_exec(["bash", "-c", cmd])
