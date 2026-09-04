"""
Wrapper around the Frappe `bench` CLI executed inside the backend container.

All seeder interactions with ERPNext go through `bench execute`
(for Python expressions) or `bench --site <site> <command>` (for bench commands).
This avoids HTTP authentication complexity and is faster than REST calls.
"""

from __future__ import annotations

import json
import subprocess
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from demostackkit.core.config import AppEntry

from demostackkit.core.exceptions import BenchError


class BenchClient:
    """
    Executes bench commands inside a running Docker container.

    All methods raise BenchError on non-zero exit codes.
    """

    def __init__(
        self, container: str, site: str, bench_path: str = "/home/frappe/frappe-bench"
    ) -> None:
        self.container = container
        self.site = site
        self.bench_path = bench_path

    def _docker_exec(
        self, cmd: list[str], *, input_data: str | None = None, timeout: int = 300
    ) -> str:
        """Run a command inside the container and return stdout."""
        full_cmd = ["docker", "exec", "-i", self.container] + cmd
        try:
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                input=input_data,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise BenchError(
                str(full_cmd), -1, f"Command timed out after {timeout} seconds"
            ) from exc

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
        output = self._docker_exec(
            [
                "bash",
                "-c",
                f"cd {self.bench_path} && bench --site {self.site} execute {python_expr!r}",
            ]
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
        return self._docker_exec(["python", "-c", wrapped])

    def insert_doc(self, doctype: str, data: dict[str, Any]) -> str:
        """
        Insert a Frappe document and return its name.

        Uses insert(ignore_if_duplicate=True) for idempotency.
        """
        script = f"""
import frappe
frappe.init(site='{self.site}', sites_path='{self.bench_path}/sites')
frappe.connect()
doc = frappe.get_doc({json.dumps({"doctype": doctype, **data})!r})
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

        for app in install_apps or []:
            if app in ("frappe",):
                continue  # Already installed on new-site
            self.install_app(app)

    def install_app(self, app_name: str) -> None:
        """Install a Frappe app on the site."""
        cmd = f"cd {self.bench_path} && bench --site {self.site} install-app {app_name}"
        self._docker_exec(["bash", "-c", cmd])

    def app_exists_in_bench(self, app_name: str) -> bool:
        """Return True if the app is present in the bench and importable.

        A prior `bench get-app` can leave a stale apps/<name> directory behind
        (e.g. the git clone succeeded but the pip install step was interrupted)
        without the app ever landing in the bench's virtualenv. Checking only
        for the directory would then make callers skip re-fetching it, leaving
        apps.txt pointing at a name Python can't import — which breaks every
        `bench` command with a ModuleNotFoundError. Check importability instead.
        """
        result = self._docker_exec(
            [
                "bash",
                "-c",
                f"{self.bench_path}/env/bin/python -c 'import {app_name}' "
                "> /dev/null 2>&1 && echo yes || echo no",
            ]
        )
        return result.strip() == "yes"

    def apps_txt_entries(self) -> list[str]:
        """Return the app names listed in sites/apps.txt (the bench-wide registry).

        Frappe imports every app named here on any `bench --site` call, so an entry
        without a matching apps/<name> directory breaks all site commands.
        """
        output = self._docker_exec(
            ["bash", "-c", f"cat {self.bench_path}/sites/apps.txt 2>/dev/null || true"]
        )
        return [line.strip() for line in output.splitlines() if line.strip()]

    def write_apps_txt(self, app_names: list[str]) -> None:
        """Overwrite sites/apps.txt with the given app names, one per line."""
        self._docker_exec(
            ["bash", "-c", f"cat > {self.bench_path}/sites/apps.txt"],
            input_data="\n".join(app_names) + "\n",
        )

    def copy_app_from_host(self, host_path: str, app_name: str) -> str:
        """Copy a local app directory from the host into /tmp/<app_name> in the container.

        Returns the container-side path for use with bench get-app.
        """
        from pathlib import Path

        src = Path(host_path)
        if not src.exists():
            raise BenchError(f"docker cp {host_path}", -1, f"Path does not exist: {host_path}")
        dest = f"/tmp/{app_name}"
        result = subprocess.run(
            ["docker", "cp", str(src), f"{self.container}:{dest}"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            raise BenchError(f"docker cp {host_path}", result.returncode, result.stderr)
        return dest

    def build_app_assets(self, app_names: list[str]) -> None:
        """Run bench build for each app (creates JS/CSS bundles and asset symlinks)."""
        for app_name in app_names:
            self._docker_exec(
                ["bash", "-c", f"cd {self.bench_path} && bench build --app {app_name}"],
                timeout=900,
            )

    def materialize_app_assets(self, app_names: list[str]) -> bool:
        """Copy sites/assets/<app> into the sites volume as real files.

        bench get-app / bench build create symlinks under sites/assets/ that point
        into apps/. The frontend nginx container only mounts sites/, so those
        symlinks 404 and /apps icons break for HRMS, Helpdesk, etc.
        """
        if not app_names:
            return False

        apps_shell = " ".join(app_names)
        script = f"""
set -e
cd {self.bench_path}
ASSETS_ROOT=sites/assets
changed=0
materialize_one() {{
  local name="$1"
  local dest="$ASSETS_ROOT/$name"
  if [ -L "$dest" ]; then
    local target
    target=$(readlink -f "$dest" 2>/dev/null || true)
    if [ -n "$target" ] && [ -d "$target" ]; then
      rm -f "$dest"
      cp -aL "$target" "$dest"
      changed=1
      echo "materialized:$name"
    fi
  elif [ ! -e "$dest" ]; then
    local pub=""
    if [ -d "apps/$name/$name/public" ]; then
      pub="apps/$name/$name/public"
    else
      pub=$(find "apps/$name" -mindepth 2 -maxdepth 2 -type d -name public 2>/dev/null | head -1 || true)
    fi
    if [ -n "$pub" ] && [ -d "$pub" ]; then
      mkdir -p "$ASSETS_ROOT"
      cp -aL "$pub" "$dest"
      changed=1
      echo "materialized:$name"
    fi
  fi
}}
for app in {apps_shell}; do
  materialize_one "$app"
done
if [ "$changed" -eq 1 ]; then
  echo done:changed
else
  echo done:unchanged
fi
"""
        output = self._docker_exec(["bash", "-c", script], timeout=300)
        return "done:changed" in output

    def get_app(self, entry: AppEntry) -> None:
        """Fetch a Frappe app into the bench via bench get-app.

        Handles three source types:
          frappe — bench get-app <name>  (fetches from frappe.io)
          github — bench get-app <url>   (fetches from GitHub)
          local  — docker cp host_path into container, then bench get-app /tmp/<name>
        """

        if entry.source == "local":
            fetch_target = self.copy_app_from_host(entry.host_path, entry.name)
        elif entry.source == "github":
            fetch_target = entry.url
        else:
            fetch_target = entry.name

        # --overwrite: callers only reach get_app() after app_exists_in_bench() found
        # the app missing or not importable, which includes a stale apps/<name>
        # directory left by a previously interrupted get-app (repo cloned, pip install
        # never ran). Without --overwrite, bench prompts interactively to overwrite
        # that directory and aborts immediately since docker exec has no stdin.
        cmd = f"cd {self.bench_path} && bench get-app {fetch_target} --overwrite"
        if entry.branch and entry.source != "local":
            cmd += f" --branch {entry.branch}"

        # bench get-app can be slow for large repos; allow up to 10 minutes
        self._docker_exec(["bash", "-c", cmd], timeout=600)

    def drop_site(self, db_root_password: str) -> None:
        """Drop the Frappe site (destructive)."""
        cmd = (
            f"cd {self.bench_path} && "
            f"bench drop-site {self.site} "
            f"--root-password {db_root_password!r} "
            "--archived-sites-path /tmp --force"
        )
        self._docker_exec(["bash", "-c", cmd])

    def backup(self, backup_dir: str) -> str:
        """Run bench backup and return the path to the SQL file."""
        cmd = (
            f"cd {self.bench_path} && bench --site {self.site} backup --backup-path {backup_dir!r}"
        )
        return self._docker_exec(["bash", "-c", cmd])

    def restore(self, sql_gz_path: str, db_root_password: str) -> None:
        """Restore a bench backup from a .sql.gz file."""
        cmd = (
            f"cd {self.bench_path} && "
            f"bench --site {self.site} restore {sql_gz_path!r} "
            f"--mariadb-root-password {db_root_password!r}"
        )
        self._docker_exec(["bash", "-c", cmd])
