"""
Unit tests for the project planning logic in demostackkit/seeder/projects.py.

Pure functions only — no Frappe, no Docker, no site. The rules being checked here
are the ones ERPNext would otherwise enforce halfway through a live seed run:
dependency ordering, parent spans, and statuses that survive the daily
`set_tasks_as_overdue` scheduler job.
"""

from __future__ import annotations

import random
from datetime import date, datetime, timedelta

import pytest

from demostackkit.seeder.projects import (
    ACTIVITY_TYPES,
    TASK_PRIORITIES,
    TASK_STATUSES,
    activity_rates,
    erpnext_template_task_dates,
    expand_blueprint,
    group_status,
    india_demo_holidays,
    resolve_status,
    template_group_pad_days,
    timesheet_entries,
    todo_priority,
    topological_order,
    validate_plan,
    validate_template_spans_with_holidays,
    window_kind,
)

TODAY = date(2026, 6, 15)


def _blueprint(**overrides):
    """A small two-phase blueprint spanning past, present and future."""
    blueprint = {
        "name": "Test Project",
        "project_type": "Internal",
        "priority": "High",
        "start_offset_days": -60,
        "phases": [
            {
                "subject": "Phase One",
                "designation": "Manager",
                "tasks": [
                    {"subject": "Alpha", "start": 0, "duration": 10, "designation": "Manager"},
                    {
                        "subject": "Beta",
                        "start": 10,
                        "duration": 15,
                        "depends_on": ["Alpha"],
                        "designation": "Engineer",
                    },
                ],
            },
            {
                "subject": "Phase Two",
                "designation": "Manager",
                "tasks": [
                    {
                        "subject": "Gamma",
                        "start": 55,
                        "duration": 20,
                        "depends_on": ["Beta"],
                        "designation": "Engineer",
                    },
                    {"subject": "Delta", "start": 90, "duration": 10, "designation": "Engineer"},
                ],
            },
        ],
    }
    blueprint.update(overrides)
    return blueprint


# ── topological_order ─────────────────────────────────────────────────────────


@pytest.mark.unit
class TestTopologicalOrder:
    def test_dependencies_come_first(self) -> None:
        tasks = [
            {"subject": "c", "depends_on": ["b"]},
            {"subject": "a", "depends_on": []},
            {"subject": "b", "depends_on": ["a"]},
        ]
        assert [t["subject"] for t in topological_order(tasks)] == ["a", "b", "c"]

    def test_diamond_dependency(self) -> None:
        tasks = [
            {"subject": "d", "depends_on": ["b", "c"]},
            {"subject": "b", "depends_on": ["a"]},
            {"subject": "c", "depends_on": ["a"]},
            {"subject": "a", "depends_on": []},
        ]
        order = [t["subject"] for t in topological_order(tasks)]
        assert order[0] == "a"
        assert order[-1] == "d"

    def test_cycle_is_rejected(self) -> None:
        tasks = [
            {"subject": "a", "depends_on": ["b"]},
            {"subject": "b", "depends_on": ["a"]},
        ]
        with pytest.raises(ValueError, match="dependency cycle"):
            topological_order(tasks)

    def test_unknown_dependency_is_rejected(self) -> None:
        tasks = [{"subject": "a", "depends_on": ["nope"]}]
        with pytest.raises(ValueError, match="unknown task"):
            topological_order(tasks)

    def test_order_is_stable(self) -> None:
        """Ties break on blueprint position, so a reset reproduces the run."""
        tasks = [{"subject": s, "depends_on": []} for s in ("x", "y", "z")]
        assert [t["subject"] for t in topological_order(tasks)] == ["x", "y", "z"]


# ── Status derivation ─────────────────────────────────────────────────────────


@pytest.mark.unit
class TestStatusDerivation:
    def test_window_kind(self) -> None:
        assert window_kind(TODAY - timedelta(days=10), TODAY - timedelta(days=5), TODAY) == "past"
        assert window_kind(TODAY - timedelta(days=5), TODAY + timedelta(days=5), TODAY) == "current"
        assert window_kind(TODAY + timedelta(days=5), TODAY + timedelta(days=10), TODAY) == "future"

    def test_window_boundaries_are_inclusive(self) -> None:
        assert window_kind(TODAY, TODAY, TODAY) == "current"

    def test_defaults_per_window(self) -> None:
        assert resolve_status("past") == "Completed"
        assert resolve_status("current") == "Working"
        assert resolve_status("future") == "Open"

    @pytest.mark.parametrize(
        ("kind", "hint"),
        [
            ("past", "Overdue"),
            ("past", "Cancelled"),
            ("current", "Open"),
            ("current", "Pending Review"),
        ],
    )
    def test_valid_hints_are_honoured(self, kind: str, hint: str) -> None:
        assert resolve_status(kind, hint) == hint

    @pytest.mark.parametrize(
        ("kind", "hint"),
        [
            # An Open or Working task whose end date has passed is flipped to
            # Overdue by the daily scheduler, draining the Kanban column.
            ("past", "Open"),
            ("past", "Working"),
            # Nothing in the future can already be overdue or complete.
            ("future", "Overdue"),
            ("future", "Completed"),
            ("current", "Overdue"),
            ("current", "Completed"),
        ],
    )
    def test_unstable_hints_are_rejected(self, kind: str, hint: str) -> None:
        with pytest.raises(ValueError, match="not stable"):
            resolve_status(kind, hint)

    def test_group_completes_only_when_all_children_are_terminal(self) -> None:
        past = TODAY - timedelta(days=1)
        assert group_status(["Completed", "Cancelled"], past, TODAY) == "Completed"
        assert group_status(["Completed", "Working"], past, TODAY) == "Overdue"

    def test_group_in_flight(self) -> None:
        future = TODAY + timedelta(days=30)
        assert group_status(["Completed", "Open"], future, TODAY) == "Working"
        assert group_status(["Open", "Open"], future, TODAY) == "Open"


# ── expand_blueprint ──────────────────────────────────────────────────────────


@pytest.mark.unit
class TestExpandBlueprint:
    def test_plan_is_valid(self) -> None:
        assert validate_plan(expand_blueprint(_blueprint(), TODAY)) == []

    def test_dates_are_anchored_to_the_offset(self) -> None:
        plan = expand_blueprint(_blueprint(), TODAY)
        assert plan["expected_start_date"] == (TODAY - timedelta(days=60)).isoformat()

    def test_project_ends_after_every_task(self) -> None:
        plan = expand_blueprint(_blueprint(), TODAY)
        last = max(date.fromisoformat(t["exp_end_date"]) for t in plan["tasks"])
        assert date.fromisoformat(plan["expected_end_date"]) > last

    def test_group_spans_enclose_their_children(self) -> None:
        plan = expand_blueprint(_blueprint(), TODAY)
        groups = {g["subject"]: g for g in plan["groups"]}
        for task in plan["tasks"]:
            group = groups[task["parent"]]
            assert group["exp_start_date"] <= task["exp_start_date"]
            assert group["exp_end_date"] >= task["exp_end_date"]

    def test_tasks_are_topologically_ordered(self) -> None:
        plan = expand_blueprint(_blueprint(), TODAY)
        seen: set[str] = set()
        for task in plan["tasks"]:
            assert set(task["depends_on"]).issubset(seen)
            seen.add(task["subject"])

    def test_completed_tasks_carry_a_past_completion_date(self) -> None:
        plan = expand_blueprint(_blueprint(), TODAY)
        for task in plan["tasks"]:
            if task["status"] == "Completed":
                assert date.fromisoformat(task["completed_on"]) <= TODAY
                assert task["progress"] == 100

    def test_pending_review_is_pinned_with_a_future_review_date(self) -> None:
        blueprint = _blueprint()
        blueprint["phases"][1]["tasks"][0]["status"] = "Pending Review"
        plan = expand_blueprint(blueprint, TODAY)
        task = next(t for t in plan["tasks"] if t["subject"] == "Gamma")
        assert date.fromisoformat(task["review_date"]) > TODAY

    def test_statuses_are_all_known_to_erpnext(self) -> None:
        plan = expand_blueprint(_blueprint(), TODAY)
        for task in [*plan["groups"], *plan["tasks"]]:
            assert task["status"] in TASK_STATUSES

    def test_empty_phase_is_rejected(self) -> None:
        blueprint = _blueprint()
        blueprint["phases"][1]["tasks"] = []
        with pytest.raises(ValueError, match="has no tasks"):
            expand_blueprint(blueprint, TODAY)

    def test_template_project_has_no_authored_tasks(self) -> None:
        plan = expand_blueprint(
            {
                "name": "From Template",
                "project_type": "Internal",
                "template": "Standard Delivery Programme",
                "start_offset_days": -20,
                "duration": 100,
            },
            TODAY,
        )
        assert plan["template"] == "Standard Delivery Programme"
        assert plan["tasks"] == []
        # Padded well past the nominal duration: ERPNext walks each generated
        # task date forward past every holiday, and a task landing beyond the
        # project end aborts the whole insert.
        end = date.fromisoformat(plan["expected_end_date"])
        start = date.fromisoformat(plan["expected_start_date"])
        assert (end - start).days > 100


@pytest.mark.unit
class TestTemplateHolidaySpans:
    def test_group_pad_scales_with_phase_length(self) -> None:
        assert template_group_pad_days(20) == 30
        assert template_group_pad_days(100) == 30
        assert template_group_pad_days(200) == 40

    def test_erpnext_date_math_skips_sundays(self) -> None:
        # 2026-07-25 is a Saturday; 2026-07-26 is Sunday and should be skipped.
        holidays = india_demo_holidays(date(2026, 7, 25), 10)
        start, end = erpnext_template_task_dates(date(2026, 7, 25), 0, 1, holidays)
        assert start == date(2026, 7, 25)
        assert end == date(2026, 7, 27)

    def test_electrical_npd_template_survives_india_holidays(self) -> None:
        import ast
        from pathlib import Path

        from demostackkit.seeder.project_seeders import _flatten_template

        path = Path("industries/electrical/seeders/01_master/13_projects.py")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        templates = None
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Assign)
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "TEMPLATES"
            ):
                templates = ast.literal_eval(node.value)
                break
        assert templates is not None
        flat = _flatten_template(templates[0])
        project_start = date(2026, 7, 25)
        assert validate_template_spans_with_holidays(flat, project_start) == []
        assert flat["groups"][0]["duration"] >= 69


@pytest.mark.unit
class TestValidatePlan:
    def test_completed_task_depending_on_unfinished_work_is_caught(self) -> None:
        plan = expand_blueprint(_blueprint(), TODAY)
        # Force the situation ERPNext rejects on insert.
        by_subject = {t["subject"]: t for t in plan["tasks"]}
        by_subject["Alpha"]["status"] = "Working"
        by_subject["Beta"]["status"] = "Completed"
        problems = validate_plan(plan)
        assert any("depends on unfinished" in p for p in problems)

    def test_task_past_the_project_end_is_caught(self) -> None:
        plan = expand_blueprint(_blueprint(), TODAY)
        plan["expected_end_date"] = plan["tasks"][0]["exp_start_date"]
        assert any("expected_end_date" in p for p in validate_plan(plan))


# ── Timesheets ────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestTimesheetEntries:
    def _plan(self):
        plan = expand_blueprint(_blueprint(), TODAY)
        for index, task in enumerate(plan["tasks"]):
            task["employee"] = f"HR-EMP-0000{index % 2}"
            task["employee_name"] = "Someone"
        return plan

    def test_no_overlap_per_employee(self) -> None:
        """ERPNext rejects two time logs for one employee that overlap at all."""
        entries = timesheet_entries([self._plan()], TODAY, random.Random(7), limit=100)
        assert entries

        spans: dict[str, list[tuple[datetime, datetime]]] = {}
        for entry in entries:
            start = datetime.strptime(entry["from_time"], "%Y-%m-%d %H:%M:%S")
            spans.setdefault(entry["employee"], []).append(
                (start, start + timedelta(hours=entry["hours"]))
            )

        for windows in spans.values():
            windows.sort()
            for earlier, later in zip(windows, windows[1:]):
                assert earlier[1] <= later[0], "overlapping time logs for one employee"

    def test_only_past_work_is_logged(self) -> None:
        entries = timesheet_entries([self._plan()], TODAY, random.Random(7), limit=100)
        for entry in entries:
            assert datetime.strptime(entry["from_time"], "%Y-%m-%d %H:%M:%S").date() <= TODAY

    def test_weekends_are_skipped(self) -> None:
        entries = timesheet_entries([self._plan()], TODAY, random.Random(7), limit=100)
        for entry in entries:
            assert datetime.strptime(entry["from_time"], "%Y-%m-%d %H:%M:%S").weekday() < 5

    def test_limit_is_respected(self) -> None:
        entries = timesheet_entries([self._plan()], TODAY, random.Random(7), limit=3)
        assert len(entries) == 3

    def test_activity_types_are_ones_erpnext_ships(self) -> None:
        entries = timesheet_entries([self._plan()], TODAY, random.Random(7), limit=100)
        for entry in entries:
            assert entry["activity_type"] in ACTIVITY_TYPES

    def test_billing_hours_are_always_set(self) -> None:
        """Left blank, billing_amount computes to zero on the first validate pass."""
        entries = timesheet_entries([self._plan()], TODAY, random.Random(7), limit=100)
        assert all(entry["billing_hours"] for entry in entries)

    def test_is_deterministic(self) -> None:
        first = timesheet_entries([self._plan()], TODAY, random.Random(7), limit=50)
        second = timesheet_entries([self._plan()], TODAY, random.Random(7), limit=50)
        assert first == second

    def test_unassigned_tasks_are_skipped(self) -> None:
        plan = expand_blueprint(_blueprint(), TODAY)
        assert timesheet_entries([plan], TODAY, random.Random(7), limit=50) == []


# ── Small helpers ─────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestHelpers:
    def test_urgent_maps_onto_a_todo_priority(self) -> None:
        """ToDo's Select has no 'Urgent' and rejects one outright."""
        assert todo_priority("Urgent") == "High"
        for priority in TASK_PRIORITIES:
            assert todo_priority(priority) in ("Low", "Medium", "High")

    def test_activity_rates_scale_with_currency(self) -> None:
        inr = activity_rates("INR")
        usd = activity_rates("USD")
        assert set(inr) == set(ACTIVITY_TYPES)
        assert usd["Execution"]["billing_rate"] < inr["Execution"]["billing_rate"]
        assert all(rate["costing_rate"] < rate["billing_rate"] for rate in inr.values())
