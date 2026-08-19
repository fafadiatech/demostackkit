"""
Every Frappe script the project seeders generate must be valid Python.

The seeders build their scripts as f-strings, which means each literal brace in
the remote code has to be doubled. Miss one and the seeder still imports, still
passes every other test, and only fails when it reaches a real container — after
a full site build. Compiling the generated source here turns that into a
sub-second check.

The `_exec` boundary is replaced with a stub that compiles the script and hands
back the stdout markers the seeders parse, so the whole chain runs: the employee
directory flows into the project plan, and the plan's docnames flow into the
timesheet, status and Kanban passes.
"""

from __future__ import annotations

import ast
import json
import random
from datetime import date
from pathlib import Path

import pytest

from demostackkit.core.config import load_industry_config
from demostackkit.seeder import base
from demostackkit.seeder.base import SeedContext
from demostackkit.seeder.loader import discover_seeders
from demostackkit.seeder.project_seeders import PROJECT_PAYLOAD_MARKER
from demostackkit.seeder.projects import expand_blueprint

REPO_ROOT = Path(__file__).parent.parent.parent
SHARED_SEEDERS = REPO_ROOT / "demostackkit" / "seeders"

#: Marker the employee login seeder prints its directory on.
EMPLOYEE_MARKER = "DSK_EMPLOYEE_DIRECTORY::"

#: The seeders this module exercises. Everything else needs a live site.
PROJECT_SEEDERS = {
    "EmployeeUserSeeder",
    "ProjectTemplateSeeder",
    "ProjectSeeder",
    "ProjectTimesheetSeeder",
    "TaskFinalizeSeeder",
    "KanbanBoardSeeder",
}

_INDUSTRY_DIRS = sorted(
    p.parent
    for p in (REPO_ROOT / "industries").glob("*/industry.yaml")
    if p.parent.name != "_template"
)
_INDUSTRY_IDS = [d.name for d in _INDUSTRY_DIRS]


def _designations(industry_dir: Path) -> list[str]:
    """DESIGNATIONS from the industry's employee seeder, read without importing it."""
    path = industry_dir / "seeders" / "01_master" / "11_employees.py"
    if not path.exists():
        return ["Manager"]
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "DESIGNATIONS"
        ):
            return ast.literal_eval(node.value)
    return ["Manager"]


def _fake_directory(industry_dir: Path) -> list[dict]:
    """A workforce shaped like the one the login seeder publishes."""
    slug = industry_dir.name
    return [
        {
            "name": f"HR-EMP-{index:05d}",
            "employee_name": f"Person {index}",
            "designation": designation,
            "user": f"person{index}@{slug}.demo",
        }
        for index, designation in enumerate(_designations(industry_dir))
    ]


def _make_exec(directory: list[dict], compiled: list[str]):
    """A `_exec` stand-in that compiles the script and replays the stdout markers."""

    def _exec(self, script: str, timeout: int = 120) -> str:
        name = type(self).__name__
        # Raises SyntaxError on an undoubled brace, which is the whole point.
        compile(script, f"<{name}>", "exec")
        compiled.append(name)

        if name == "EmployeeUserSeeder":
            return EMPLOYEE_MARKER + json.dumps(directory) + "\n"

        if name == "ProjectSeeder":
            # Stand in for the docnames ERPNext would have minted, so the
            # downstream passes have something real to resolve against.
            created = {}
            for index, blueprint in enumerate(self.PROJECT_BLUEPRINTS[: self.volume]):
                plan = expand_blueprint(blueprint, date.today())
                subjects = [t["subject"] for t in plan["tasks"]]
                subjects += [g["subject"] for g in plan["groups"]]
                created[plan["name"]] = {
                    "project": f"PROJ-{index:04d}",
                    "tasks": {s: f"TASK-2026-{n:05d}" for n, s in enumerate(subjects)},
                }
            return PROJECT_PAYLOAD_MARKER + json.dumps(created) + "\n"

        return ""

    return _exec


def _context(industry_dir: Path) -> SeedContext:
    config = load_industry_config(industry_dir / "industry.yaml")
    ctx = SeedContext(
        site=config.site.name,
        industry_slug=industry_dir.name,
        industry_config=config,
        bench_path="/home/frappe/frappe-bench",
        random=random.Random(1),
    )
    # What the earlier seeders would have left behind.
    ctx.cache_set("company_name", config.company.name)
    ctx.cache_set("company_abbr", config.company.abbr)
    ctx.cache_set("customer_names", ["Acme Ltd", "Globex Corp"])
    return ctx


@pytest.mark.unit
class TestGeneratedScriptsCompile:
    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_every_project_seeder_runs_end_to_end(
        self, industry_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        compiled: list[str] = []
        monkeypatch.setattr(
            base.BaseSeeder, "_exec", _make_exec(_fake_directory(industry_dir), compiled)
        )

        ctx = _context(industry_dir)
        for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS]):
            if cls.__name__ not in PROJECT_SEEDERS:
                continue
            seeder = cls(ctx)
            assert seeder.validate() == [], f"{industry_dir.name}/{cls.__name__} failed validate()"
            seeder.run()

        # Every seeder in the chain must have got far enough to emit a script;
        # a silent no-op here would mean a broken cache handoff.
        assert set(compiled) == PROJECT_SEEDERS, (
            f"[{industry_dir.name}] these seeders never generated a script: "
            f"{sorted(PROJECT_SEEDERS - set(compiled))}"
        )
