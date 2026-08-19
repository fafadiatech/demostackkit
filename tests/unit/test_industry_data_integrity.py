"""
Unit tests for industry data integrity.

Validates that each industry's data files are consistent with their seeder
definitions — no runtime Frappe environment required.

Checks performed:
- Every item_group referenced in items.csv is defined in 02_item_groups.py
- Parent item groups are defined before their children in _ITEM_GROUPS
- items.csv has the required header columns
- Project blueprints expand into plans ERPNext will actually accept
- Task types, designations, project types and templates referenced by a
  blueprint are all declared somewhere in the same industry
"""

from __future__ import annotations

import ast
import csv
from datetime import date
from pathlib import Path

import pytest

from demostackkit.seeder.project_seeders import _flatten_template
from demostackkit.seeder.projects import (
    expand_blueprint,
    validate_plan,
    validate_template_spans_with_holidays,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
INDUSTRIES_ROOT = REPO_ROOT / "industries"

# Groups that ERPNext guarantees exist without any seeder creating them.
ALWAYS_AVAILABLE = {"All Item Groups"}


def _all_industry_dirs() -> list[Path]:
    """Return all industry directories that have both a data/ and seeders/ dir."""
    return sorted(
        d
        for d in INDUSTRIES_ROOT.iterdir()
        if d.is_dir()
        and not d.name.startswith("_")
        and (d / "data").is_dir()
        and (d / "seeders").is_dir()
    )


def _read_item_groups_from_seeder(industry_dir: Path) -> list[dict]:
    """
    Import 02_item_groups.py in isolation and return the _ITEM_GROUPS list.

    We do a fresh import so we don't need Frappe installed.
    """
    seeder_path = industry_dir / "seeders" / "01_master" / "02_item_groups.py"
    if not seeder_path.exists():
        return []

    # Parse the AST to extract _ITEM_GROUPS without executing the full module
    # (avoids any import-time side effects that might require Frappe).
    source = seeder_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(seeder_path))

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "_ITEM_GROUPS"
        ):
            return ast.literal_eval(node.value)  # type: ignore[return-value]

    return []


def _read_literal(path: Path, name: str, default=None):
    """Lift a module-level literal out of a seeder without importing it.

    The project and employee seeders declare their data as plain lists of dicts
    precisely so this works — importing them would drag in the seeder framework
    and, through it, Frappe.
    """
    if not path.exists():
        return default
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == name
        ):
            return ast.literal_eval(node.value)
    return default


def _project_data(industry_dir: Path) -> dict:
    """Everything the project seeders declare for one industry."""
    master = industry_dir / "seeders" / "01_master" / "13_projects.py"
    transactions = industry_dir / "seeders" / "02_transactions" / "04_projects.py"
    employees = industry_dir / "seeders" / "01_master" / "11_employees.py"
    return {
        "project_types": _read_literal(master, "PROJECT_TYPES", []),
        "task_types": _read_literal(master, "TASK_TYPES", []),
        "templates": _read_literal(master, "TEMPLATES", []),
        "blueprints": _read_literal(transactions, "PROJECT_BLUEPRINTS", []),
        "designations": _read_literal(employees, "DESIGNATIONS", []),
    }


def _blueprint_tasks(blueprint: dict):
    """Every leaf task in a blueprint, paired with its phase."""
    for phase in blueprint.get("phases", []):
        for task in phase.get("tasks", []):
            yield phase, task


def _read_item_groups_from_csv(industry_dir: Path) -> list[str]:
    """Return all item_group values found in data/items.csv (deduplicated, ordered)."""
    csv_path = industry_dir / "data" / "items.csv"
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list({row["item_group"] for row in reader if row.get("item_group")})


# ---------------------------------------------------------------------------
# Parametrize over all industries
# ---------------------------------------------------------------------------

_INDUSTRY_IDS = [d.name for d in _all_industry_dirs()]
_INDUSTRY_DIRS = _all_industry_dirs()


def _all_project_industry_dirs() -> list[Path]:
    """Industries to check project data for.

    Deliberately not `_all_industry_dirs()`: that one requires a `data/`
    directory, which is right for the item-group checks but would silently skip
    `vanilla` — an industry that ships no CSVs yet still seeds a full project
    portfolio through the shared seeders.
    """
    return sorted(
        p.parent
        for p in INDUSTRIES_ROOT.glob("*/industry.yaml")
        if not p.parent.name.startswith("_")
    )


_PROJECT_DIRS = _all_project_industry_dirs()
_PROJECT_IDS = [d.name for d in _PROJECT_DIRS]


@pytest.mark.unit
class TestItemGroupConsistency:
    """Every item_group used in items.csv must be defined in 02_item_groups.py."""

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_all_item_groups_are_defined(self, industry_dir: Path) -> None:
        defined_groups = {
            g["item_group_name"] for g in _read_item_groups_from_seeder(industry_dir)
        } | ALWAYS_AVAILABLE

        csv_groups = set(_read_item_groups_from_csv(industry_dir))

        missing = csv_groups - defined_groups
        assert not missing, (
            f"[{industry_dir.name}] items.csv references item group(s) not defined in "
            f"02_item_groups.py: {sorted(missing)}"
        )

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_item_groups_seeder_exists(self, industry_dir: Path) -> None:
        """Each industry that has items.csv must have 02_item_groups.py."""
        csv_path = industry_dir / "data" / "items.csv"
        if not csv_path.exists():
            pytest.skip("no items.csv")

        seeder_path = industry_dir / "seeders" / "01_master" / "02_item_groups.py"
        assert seeder_path.exists(), (
            f"[{industry_dir.name}] has items.csv but is missing "
            f"seeders/01_master/02_item_groups.py"
        )


@pytest.mark.unit
class TestItemGroupOrdering:
    """Parent item groups must be defined before any of their children."""

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_parents_defined_before_children(self, industry_dir: Path) -> None:
        groups = _read_item_groups_from_seeder(industry_dir)
        if not groups:
            pytest.skip("no _ITEM_GROUPS defined")

        seen: set[str] = set(ALWAYS_AVAILABLE)
        for entry in groups:
            parent = entry.get("parent_item_group", "All Item Groups")
            name = entry["item_group_name"]
            assert parent in seen, (
                f"[{industry_dir.name}] item group '{name}' references parent '{parent}' "
                f"which has not been defined yet in _ITEM_GROUPS. "
                f"Move '{parent}' above '{name}'."
            )
            seen.add(name)


@pytest.mark.unit
class TestItemsCsvFormat:
    """items.csv must have the columns that the ItemSeeder expects."""

    REQUIRED_COLUMNS = {"item_code", "item_name", "item_group"}

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_required_columns_present(self, industry_dir: Path) -> None:
        csv_path = industry_dir / "data" / "items.csv"
        if not csv_path.exists():
            pytest.skip("no items.csv")

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

        missing = self.REQUIRED_COLUMNS - headers
        assert not missing, (
            f"[{industry_dir.name}] items.csv is missing required column(s): {sorted(missing)}"
        )

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_no_blank_item_codes(self, industry_dir: Path) -> None:
        csv_path = industry_dir / "data" / "items.csv"
        if not csv_path.exists():
            pytest.skip("no items.csv")

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            blank_rows = [
                i + 2  # +1 for header, +1 for 1-based line numbers
                for i, row in enumerate(reader)
                if not row.get("item_code", "").strip()
            ]

        assert not blank_rows, (
            f"[{industry_dir.name}] items.csv has blank item_code on line(s): {blank_rows}"
        )


# ---------------------------------------------------------------------------
# Project blueprints
# ---------------------------------------------------------------------------

#: Project Types ERPNext creates during setup, so an industry need not declare them.
STOCK_PROJECT_TYPES = {"Internal", "External", "Other"}


@pytest.mark.unit
class TestProjectSeedersExist:
    """Every industry ships both halves of the project seeding pair."""

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_both_project_seeders_present(self, industry_dir: Path) -> None:
        for relative in (
            "seeders/01_master/13_projects.py",
            "seeders/02_transactions/04_projects.py",
        ):
            assert (industry_dir / relative).exists(), (
                f"[{industry_dir.name}] is missing {relative}"
            )

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_blueprints_are_declared(self, industry_dir: Path) -> None:
        assert _project_data(industry_dir)["blueprints"], (
            f"[{industry_dir.name}] declares no PROJECT_BLUEPRINTS"
        )


@pytest.mark.unit
class TestProjectPlansAreValid:
    """A blueprint must expand into something ERPNext will accept.

    This is the check that keeps an authoring slip — a task completed before the
    work it depends on, a phase that ends before its own children — out of a live
    seed run, where it would surface as a mid-run exception.
    """

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_plans_validate(self, industry_dir: Path) -> None:
        today = date.today()
        for blueprint in _project_data(industry_dir)["blueprints"]:
            plan = expand_blueprint(blueprint, today)
            problems = validate_plan(plan)
            assert not problems, f"[{industry_dir.name}] {blueprint['name']}: {problems}"

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_task_subjects_are_unique_per_project(self, industry_dir: Path) -> None:
        """Subjects key the docname lookup the timesheet and status passes use."""
        for blueprint in _project_data(industry_dir)["blueprints"]:
            subjects = [task["subject"] for _, task in _blueprint_tasks(blueprint)]
            phases = [phase["subject"] for phase in blueprint.get("phases", [])]
            duplicates = {s for s in subjects + phases if (subjects + phases).count(s) > 1}
            assert not duplicates, (
                f"[{industry_dir.name}] {blueprint['name']} reuses subject(s): {sorted(duplicates)}"
            )

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_dependencies_stay_inside_the_project(self, industry_dir: Path) -> None:
        """A cross-project dependency inserts fine but never renders on the Gantt."""
        for blueprint in _project_data(industry_dir)["blueprints"]:
            subjects = {task["subject"] for _, task in _blueprint_tasks(blueprint)}
            for _, task in _blueprint_tasks(blueprint):
                unknown = set(task.get("depends_on", ())) - subjects
                assert not unknown, (
                    f"[{industry_dir.name}] {blueprint['name']} / {task['subject']} "
                    f"depends on task(s) outside the project: {sorted(unknown)}"
                )

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_every_status_column_is_represented(self, industry_dir: Path) -> None:
        """The Kanban board is the point — empty columns make a poor demo."""
        today = date.today()
        seen = set()
        for blueprint in _project_data(industry_dir)["blueprints"]:
            plan = expand_blueprint(blueprint, today)
            seen.update(task["status"] for task in plan["tasks"])
        missing = {"Open", "Working", "Pending Review", "Overdue", "Completed", "Cancelled"} - seen
        assert not missing, f"[{industry_dir.name}] no task lands in: {sorted(missing)}"


@pytest.mark.unit
class TestProjectReferences:
    """Everything a blueprint points at must be declared in the same industry."""

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_task_types_are_declared(self, industry_dir: Path) -> None:
        data = _project_data(industry_dir)
        declared = {tt["name"] for tt in data["task_types"]}
        for blueprint in data["blueprints"]:
            for _, task in _blueprint_tasks(blueprint):
                used = task.get("type")
                assert not used or used in declared, (
                    f"[{industry_dir.name}] {blueprint['name']} / {task['subject']} uses "
                    f"task type {used!r}, which is not in TASK_TYPES"
                )

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_designations_match_the_workforce(self, industry_dir: Path) -> None:
        """An unknown designation silently falls back to a random employee."""
        data = _project_data(industry_dir)
        known = set(data["designations"])
        if not known:
            pytest.skip("no DESIGNATIONS declared")
        for blueprint in data["blueprints"]:
            for phase, task in _blueprint_tasks(blueprint):
                for label, value in (
                    ("phase", phase.get("designation")),
                    ("task", task.get("designation")),
                ):
                    assert not value or value in known, (
                        f"[{industry_dir.name}] {blueprint['name']}: {label} designation "
                        f"{value!r} is not in 11_employees.py DESIGNATIONS"
                    )

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_project_types_are_declared(self, industry_dir: Path) -> None:
        data = _project_data(industry_dir)
        declared = {pt["project_type"] for pt in data["project_types"]} | STOCK_PROJECT_TYPES
        for blueprint in data["blueprints"]:
            assert blueprint["project_type"] in declared, (
                f"[{industry_dir.name}] {blueprint['name']} uses project type "
                f"{blueprint['project_type']!r}, which is not in PROJECT_TYPES"
            )
        for template in data["templates"]:
            assert template["project_type"] in declared, (
                f"[{industry_dir.name}] template {template['name']} uses project type "
                f"{template['project_type']!r}, which is not in PROJECT_TYPES"
            )

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_referenced_templates_exist(self, industry_dir: Path) -> None:
        data = _project_data(industry_dir)
        declared = {template["name"] for template in data["templates"]}
        used = {b["template"] for b in data["blueprints"] if b.get("template")}
        assert used, f"[{industry_dir.name}] no project is built from a Project Template"
        assert used <= declared, (
            f"[{industry_dir.name}] blueprints reference undeclared template(s): "
            f"{sorted(used - declared)}"
        )


@pytest.mark.unit
class TestProjectTemplates:
    """Template task trees have to satisfy the same ordering rules as projects."""

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_templates_flatten_without_cycles(self, industry_dir: Path) -> None:
        for template in _project_data(industry_dir)["templates"]:
            flat = _flatten_template(template)
            assert flat["groups"], f"[{industry_dir.name}] {template['name']} has no phases"
            assert flat["tasks"], f"[{industry_dir.name}] {template['name']} has no tasks"

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_group_spans_enclose_their_children(self, industry_dir: Path) -> None:
        """A template group must outlive every task hung beneath it.

        ERPNext builds each generated task's dates from `start` and `duration`
        alone, so a group left at the default 0/0 comes out ending on the project
        start date. The first child that ends later then trips
        `validate_parent_expected_end_date` inside `after_insert`, which takes
        the entire Project insert down with it.
        """
        for template in _project_data(industry_dir)["templates"]:
            flat = _flatten_template(template)
            children: dict[str, list[dict]] = {}
            for task in flat["tasks"]:
                children.setdefault(task["parent"], []).append(task)

            for group in flat["groups"]:
                kids = children[group["subject"]]
                group_end = group["start"] + group["duration"]
                assert group["start"] <= min(k["start"] for k in kids), (
                    f"[{industry_dir.name}] {template['name']} / {group['subject']} "
                    f"starts after one of its tasks"
                )
                assert group_end >= max(k["start"] + k["duration"] for k in kids), (
                    f"[{industry_dir.name}] {template['name']} / {group['subject']} "
                    f"ends before one of its tasks"
                )

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_group_spans_survive_holiday_adjustment(self, industry_dir: Path) -> None:
        """Holiday-skewed copy_from_template must not outlive a phase group parent."""
        project_start = date(2026, 7, 25)
        for template in _project_data(industry_dir)["templates"]:
            flat = _flatten_template(template)
            problems = validate_template_spans_with_holidays(flat, project_start)
            assert not problems, f"[{industry_dir.name}] {template['name']}: {problems}"

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_template_task_subjects_are_unique(self, industry_dir: Path) -> None:
        for template in _project_data(industry_dir)["templates"]:
            subjects = [task["subject"] for _, task in _blueprint_tasks(template)]
            phases = [phase["subject"] for phase in template["phases"]]
            combined = subjects + phases
            duplicates = {s for s in combined if combined.count(s) > 1}
            assert not duplicates, (
                f"[{industry_dir.name}] template {template['name']} reuses "
                f"subject(s): {sorted(duplicates)}"
            )

    @pytest.mark.parametrize("industry_dir", _PROJECT_DIRS, ids=_PROJECT_IDS)
    def test_template_dependencies_resolve(self, industry_dir: Path) -> None:
        """ProjectTemplate.validate_dependencies rejects a dangling reference."""
        for template in _project_data(industry_dir)["templates"]:
            subjects = {task["subject"] for _, task in _blueprint_tasks(template)}
            for _, task in _blueprint_tasks(template):
                unknown = set(task.get("depends_on", ())) - subjects
                assert not unknown, (
                    f"[{industry_dir.name}] template {template['name']} / "
                    f"{task['subject']} depends on unknown task(s): {sorted(unknown)}"
                )
