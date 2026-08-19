"""
Planning logic for the Projects seeders — pure functions, no Frappe, no I/O.

The frappe scripts live in ``demostackkit/seeder/project_seeders.py``; everything
that can be decided without a site lives here so it can be unit tested.

Industry packages declare their portfolio as plain lists of dicts (never
dataclasses) so ``tests/unit/test_industry_data_integrity.py`` can lift them
straight out of the module with ``ast.literal_eval`` — the same trick it already
uses for ``_ITEM_GROUPS``.

Blueprint schema (``PROJECT_BLUEPRINTS`` in ``02_transactions/04_projects.py``)::

    {
        "name": "220kV Substation Package - Nashik",
        "project_type": "Turnkey EPC",       # must exist in PROJECT_TYPES
        "priority": "High",                  # Low | Medium | High
        "start_offset_days": -120,           # relative to today; negative = under way
        "notes": "Free text shown on the Project form",
        "phases": [
            {
                "subject": "Design & Approvals",     # becomes a group (parent) Task
                "designation": "Project Manager",
                "tasks": [
                    {
                        "subject": "Topographic Survey",
                        "type": "Survey",            # must exist in TASK_TYPES
                        "start": 0,                  # days after project start
                        "duration": 8,               # days
                        "depends_on": ["..."],       # subjects within the same project
                        "designation": "Site Engineer",
                        "priority": "Urgent",        # Low | Medium | High | Urgent
                        "hours": 40,                 # expected_time
                        "status": "Overdue",         # optional hint, see resolve_status
                        "milestone": True,
                        "description": "...",
                    },
                ],
            },
        ],
    }

A blueprint carrying ``"template": "<Project Template name>"`` instead of
``phases`` is instantiated by ERPNext itself: the Project is inserted with
``project_template`` set and ``Project.copy_from_template`` (which runs in
``after_insert``) generates the task tree, reproducing both the dependencies and
the parent/child hierarchy declared on the template.

Template schema (``TEMPLATES`` in ``01_master/13_projects.py``) reuses the same
``phases``/``tasks`` shape but carries no dates, statuses or designations —
template tasks only have ``start`` and ``duration`` offsets.
"""

from __future__ import annotations

import random as _random_module
from datetime import date, datetime, time, timedelta
from typing import Any

# ── ERPNext vocabularies ──────────────────────────────────────────────────────

#: Task.status select options that a seeded task may carry. 'Template' is
#: excluded deliberately: ERPNext sets it itself whenever is_template is on, and
#: a Template card in the Kanban board is noise.
TASK_STATUSES = ("Open", "Working", "Pending Review", "Overdue", "Completed", "Cancelled")

#: Task.priority select options.
TASK_PRIORITIES = ("Low", "Medium", "High", "Urgent")

#: Project.priority select options — note ERPNext gives Project no 'Urgent'.
PROJECT_PRIORITIES = ("Low", "Medium", "High")

#: Statuses that count as finished. A Task may only be saved as Completed when
#: every task it depends on is already in this set, so these also terminate a
#: dependency chain.
TERMINAL_STATUSES = frozenset({"Completed", "Cancelled"})

#: Activity Types ERPNext ships via its setup wizard. Timesheet rows must point
#: at a real Activity Type or `update_cost` leaves the amounts at zero.
ACTIVITY_TYPES = ("Planning", "Research", "Proposal Writing", "Execution", "Communication")

# ── Tuning constants ──────────────────────────────────────────────────────────

#: Days added after the last task so `validate_parent_project_dates` — which
#: rejects any task (or timesheet-derived actual date) past the project end —
#: has room for the finalize pass and for a demo that sits on a shelf a while.
PROJECT_END_PAD_DAYS = 21

#: A template-instantiated project cannot be measured up front: ERPNext walks
#: each generated task's dates forward past every holiday, and a demo Holiday
#: List runs to ~130 days over two years. Doubling the nominal duration before
#: padding keeps that drift from pushing a task past the project end, which
#: would abort the whole insert from inside `after_insert`.
TEMPLATE_END_PAD_FACTOR = 2
TEMPLATE_END_PAD_DAYS = 21

#: Minimum slack appended to every template group span beyond its widest child.
#: ERPNext adjusts parent and child dates against the Holiday List independently;
#: a longer pad keeps ``validate_parent_expected_end_date`` from aborting the
#: Project insert when public holidays push a child forward more than its parent.
TEMPLATE_GROUP_PAD_MIN_DAYS = 30

#: Days before a Pending Review task's review date. `set_tasks_as_overdue` skips
#: rows whose review_date is still in the future, which is what pins the status
#: against the daily scheduler job.
REVIEW_LEAD_DAYS = 10

#: Working-hour slots for seeded timesheets. ERPNext's overlap predicate is
#: strict at the boundaries, so back-to-back logs never collide; two slots a day
#: reads as a plausible working pattern without risking an overlap.
TIMESHEET_SLOTS: tuple[tuple[time, float], ...] = ((time(9, 0), 4.0), (time(14, 0), 3.5))

#: Hourly (costing, billing) rate per Activity Type, in INR. A USD site divides
#: these by _USD_DIVISOR so a hobby retailer isn't billing $1,800 an hour.
_ACTIVITY_RATES_INR: dict[str, tuple[float, float]] = {
    "Planning": (900.0, 1800.0),
    "Research": (750.0, 1500.0),
    "Proposal Writing": (700.0, 1400.0),
    "Execution": (600.0, 1200.0),
    "Communication": (500.0, 1000.0),
}

#: Rough INR→USD divisor. Exactness does not matter — plausibility does.
_USD_DIVISOR = 80.0


def activity_rates(currency: str) -> dict[str, dict[str, float]]:
    """Costing and billing rate per Activity Type, scaled to the site currency.

    Seeding the rate on the Activity Type master rather than on every timesheet
    row is both less code and closer to how a real deployment is configured, and
    it makes Project gross margin and the Project Profitability report light up
    without any extra work.
    """
    divisor = 1.0 if currency.upper() == "INR" else _USD_DIVISOR
    return {
        name: {
            "costing_rate": round(costing / divisor, 2),
            "billing_rate": round(billing / divisor, 2),
        }
        for name, (costing, billing) in _ACTIVITY_RATES_INR.items()
    }


def template_group_pad_days(span: int) -> int:
    """Slack beyond the widest child in a template phase, scaled to phase length."""
    return max(TEMPLATE_GROUP_PAD_MIN_DAYS, span // 5)


def erpnext_template_task_dates(
    project_start: date,
    task_start: int,
    task_duration: int,
    holidays: frozenset[date],
) -> tuple[date, date]:
    """Mirror ERPNext ``Project.calculate_{start,end}_date`` for unit tests."""

    def skip_holidays(day: date) -> date:
        while day in holidays:
            day += timedelta(days=1)
        return day

    start = skip_holidays(project_start + timedelta(days=task_start))
    end = skip_holidays(start + timedelta(days=task_duration))
    return start, end


def india_demo_holidays(project_start: date, span_days: int) -> frozenset[date]:
    """Sundays plus fixed Indian public holidays across a template span."""
    horizon = project_start + timedelta(days=span_days + 60)
    holidays: set[date] = set()
    day = project_start
    while day <= horizon:
        if day.weekday() == 6:
            holidays.add(day)
        day += timedelta(days=1)
    for year in range(project_start.year, horizon.year + 1):
        for month, day_num in ((1, 26), (8, 15), (10, 2), (12, 25)):
            try:
                holidays.add(date(year, month, day_num))
            except ValueError:
                pass
    return frozenset(holidays)


def validate_template_spans_with_holidays(
    flat_template: dict[str, Any],
    project_start: date,
    holidays: frozenset[date] | None = None,
) -> list[str]:
    """Catch template groups that a holiday-adjusted copy_from_template would reject."""
    if holidays is None:
        max_end = max(task["start"] + task["duration"] for task in flat_template["tasks"])
        holidays = india_demo_holidays(project_start, max_end)

    children_by_parent: dict[str, list[dict[str, Any]]] = {}
    for task in flat_template["tasks"]:
        children_by_parent.setdefault(task["parent"], []).append(task)

    errors: list[str] = []
    for group in flat_template["groups"]:
        _, parent_end = erpnext_template_task_dates(
            project_start, group["start"], group["duration"], holidays
        )
        for child in children_by_parent.get(group["subject"], []):
            _, child_end = erpnext_template_task_dates(
                project_start, child["start"], child["duration"], holidays
            )
            if child_end > parent_end:
                errors.append(
                    f"{child['subject']}: holiday-adjusted end {child_end} "
                    f"exceeds parent {group['subject']!r} end {parent_end}"
                )
    return errors


# ── Blueprint traversal ───────────────────────────────────────────────────────


def iter_leaf_tasks(phases: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    """Every leaf task in a blueprint or template, paired with its phase subject."""
    return [(phase["subject"], task) for phase in phases for task in phase.get("tasks", [])]


def topological_order(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order tasks so every task follows the ones it depends on.

    ERPNext refuses to save a Task as Completed while any task in its
    ``depends_on`` is unfinished, and that check fires on a fresh insert too
    (``get_db_value`` returns None for a new doc, which is not 'Completed'). So
    both the insert pass and the status pass have to walk the graph in this
    order.

    Ties are broken by the task's position in the blueprint, keeping the output
    stable without consulting the RNG.

    Raises:
        ValueError: on an unknown dependency or a dependency cycle.
    """
    by_subject = {task["subject"]: task for task in tasks}
    for task in tasks:
        for dep in task.get("depends_on", ()):
            if dep not in by_subject:
                raise ValueError(f"task {task['subject']!r} depends on unknown task {dep!r}")

    ordered: list[dict[str, Any]] = []
    placed: set[str] = set()
    remaining = list(tasks)

    while remaining:
        ready = [t for t in remaining if all(d in placed for d in t.get("depends_on", ()))]
        if not ready:
            stuck = sorted(t["subject"] for t in remaining)
            raise ValueError(f"dependency cycle among tasks: {stuck}")
        for task in ready:
            ordered.append(task)
            placed.add(task["subject"])
        remaining = [t for t in remaining if t["subject"] not in placed]

    return ordered


# ── Status derivation ─────────────────────────────────────────────────────────


def window_kind(start: date, end: date, today: date) -> str:
    """Where a task's date window sits relative to today: past, current or future."""
    if end < today:
        return "past"
    if start > today:
        return "future"
    return "current"


#: Statuses that are stable for each window kind. 'Stable' means the daily
#: `set_tasks_as_overdue` scheduler job will not rewrite them: an Open or
#: Working task whose exp_end_date has passed silently becomes Overdue within a
#: day of the demo being stood up, which would quietly drain the Kanban columns.
_STATUS_CHOICES: dict[str, tuple[str, ...]] = {
    "past": ("Completed", "Cancelled", "Overdue"),
    "current": ("Working", "Open", "Pending Review"),
    "future": ("Open",),
}


def resolve_status(kind: str, hint: str = "") -> str:
    """Final Task status for a window, honouring an optional authored hint.

    Dates drive the status rather than the other way round, so a blueprint can
    never declare a state ERPNext would immediately overwrite. The hint only
    picks among the statuses that are legal for that window; the first choice is
    the default.

    Raises:
        ValueError: if the hint is not stable for this window kind.
    """
    choices = _STATUS_CHOICES[kind]
    if not hint:
        return choices[0]
    if hint not in choices:
        raise ValueError(
            f"status {hint!r} is not stable for a {kind} task window "
            f"(allowed: {', '.join(choices)}). Adjust the task's start/duration instead."
        )
    return hint


def group_status(child_statuses: list[str], end: date, today: date) -> str:
    """Status for a phase (group) task, derived from its children.

    ``Task.populate_depends_on`` appends every child into its parent's
    ``depends_on``, so a group is only completable once all its children are —
    the derivation here is what ERPNext would enforce anyway.
    """
    if child_statuses and all(s in TERMINAL_STATUSES for s in child_statuses):
        return "Completed"
    if end < today:
        # A phase still holding unfinished work past its end date really is
        # overdue; saying so explicitly keeps the scheduler from doing it later.
        return "Overdue"
    if any(s != "Open" for s in child_statuses):
        return "Working"
    return "Open"


# ── Expansion ─────────────────────────────────────────────────────────────────


def expand_blueprint(blueprint: dict[str, Any], today: date) -> dict[str, Any]:
    """Turn an authored blueprint into a fully dated, ordered seeding plan.

    Returns a dict with resolved ISO dates, statuses and ordering:

        {
          "name", "project_type", "priority", "notes", "template",
          "expected_start_date", "expected_end_date",
          "groups": [{subject, exp_start_date, exp_end_date, status, ...}],
          "tasks":  [{subject, parent, depends_on, exp_start_date, ..., status}],
        }

    ``groups`` is ordered outermost-first and ``tasks`` topologically, which is
    the order both must be inserted in: ``validate_parent_is_group`` needs the
    parent to exist, and a child's ``exp_end_date`` may not exceed its parent's.
    """
    start = today + timedelta(days=int(blueprint.get("start_offset_days", 0)))

    if blueprint.get("template"):
        return _expand_template_project(blueprint, start)

    phases = blueprint["phases"]
    leaves = _expand_leaves(phases, start, today)
    groups = _expand_groups(phases, leaves, today)

    last_end = max(_parse(t["exp_end_date"]) for t in leaves)
    project_end = last_end + timedelta(days=PROJECT_END_PAD_DAYS)

    return {
        "name": blueprint["name"],
        "project_type": blueprint["project_type"],
        "priority": blueprint.get("priority", "Medium"),
        "notes": blueprint.get("notes", ""),
        "template": "",
        "expected_start_date": start.isoformat(),
        "expected_end_date": project_end.isoformat(),
        "groups": groups,
        "tasks": topological_order(leaves),
    }


def _expand_template_project(blueprint: dict[str, Any], start: date) -> dict[str, Any]:
    """Plan for a project ERPNext builds itself from a Project Template."""
    duration = int(blueprint.get("duration", 90))
    project_end = start + timedelta(days=duration * TEMPLATE_END_PAD_FACTOR + TEMPLATE_END_PAD_DAYS)
    return {
        "name": blueprint["name"],
        "project_type": blueprint["project_type"],
        "priority": blueprint.get("priority", "Medium"),
        "notes": blueprint.get("notes", ""),
        "template": blueprint["template"],
        "expected_start_date": start.isoformat(),
        "expected_end_date": project_end.isoformat(),
        "groups": [],
        "tasks": [],
    }


def _expand_leaves(phases: list[dict[str, Any]], start: date, today: date) -> list[dict[str, Any]]:
    """Resolve every leaf task's dates, status and assignment metadata."""
    leaves: list[dict[str, Any]] = []

    for phase_subject, task in iter_leaf_tasks(phases):
        task_start = start + timedelta(days=int(task.get("start", 0)))
        task_end = task_start + timedelta(days=max(int(task.get("duration", 1)), 1))
        kind = window_kind(task_start, task_end, today)

        try:
            status = resolve_status(kind, task.get("status", ""))
        except ValueError as exc:
            raise ValueError(f"task {task['subject']!r}: {exc}") from exc

        resolved: dict[str, Any] = {
            "subject": task["subject"],
            "parent": phase_subject,
            "type": task.get("type", ""),
            "priority": task.get("priority", "Medium"),
            "designation": task.get("designation", ""),
            "depends_on": list(task.get("depends_on", ())),
            "expected_time": float(task.get("hours", 8)),
            "is_milestone": int(bool(task.get("milestone"))),
            "description": task.get("description", ""),
            "exp_start_date": task_start.isoformat(),
            "exp_end_date": task_end.isoformat(),
            "status": status,
        }

        if status == "Completed":
            # completed_on is rejected if it is in the future.
            resolved["progress"] = 100
            resolved["completed_on"] = min(task_end, today).isoformat()
        elif status == "Pending Review":
            resolved["review_date"] = (today + timedelta(days=REVIEW_LEAD_DAYS)).isoformat()
            resolved["progress"] = 90
        elif status == "Working":
            resolved["progress"] = 50
        elif status == "Overdue":
            resolved["progress"] = 70

        leaves.append(resolved)

    return leaves


def _expand_groups(
    phases: list[dict[str, Any]], leaves: list[dict[str, Any]], today: date
) -> list[dict[str, Any]]:
    """Build one group Task per phase, spanning its whole subtree."""
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for leaf in leaves:
        by_parent.setdefault(leaf["parent"], []).append(leaf)

    groups = []
    for phase in phases:
        children = by_parent.get(phase["subject"], [])
        if not children:
            raise ValueError(f"phase {phase['subject']!r} has no tasks")

        # The span must enclose every child: validate_parent_expected_end_date
        # rejects a child that ends after its parent.
        group_start = min(_parse(c["exp_start_date"]) for c in children)
        group_end = max(_parse(c["exp_end_date"]) for c in children)

        groups.append(
            {
                "subject": phase["subject"],
                "type": phase.get("type", ""),
                "designation": phase.get("designation", ""),
                "priority": phase.get("priority", "Medium"),
                "exp_start_date": group_start.isoformat(),
                "exp_end_date": group_end.isoformat(),
                "status": group_status([c["status"] for c in children], group_end, today),
            }
        )

    return groups


def validate_plan(plan: dict[str, Any]) -> list[str]:
    """Problems ERPNext would reject at insert time. Empty list means OK.

    Called from the unit tests so an authoring mistake in an industry blueprint
    surfaces in CI rather than halfway through a live seed run.
    """
    errors: list[str] = []
    project_end = _parse(plan["expected_end_date"])
    status_by_subject = {t["subject"]: t["status"] for t in plan["tasks"]}

    for task in plan["tasks"]:
        if _parse(task["exp_end_date"]) > project_end:
            errors.append(f"{task['subject']}: ends after the project's expected_end_date")
        if _parse(task["exp_start_date"]) > _parse(task["exp_end_date"]):
            errors.append(f"{task['subject']}: starts after it ends")
        if task["status"] == "Completed":
            unfinished = [
                dep
                for dep in task["depends_on"]
                if status_by_subject.get(dep) not in TERMINAL_STATUSES
            ]
            if unfinished:
                errors.append(
                    f"{task['subject']}: is Completed but depends on unfinished "
                    f"{', '.join(sorted(unfinished))} — ERPNext rejects this on insert"
                )

    groups = {g["subject"]: g for g in plan["groups"]}
    for task in plan["tasks"]:
        group = groups.get(task["parent"])
        if group is None:
            errors.append(f"{task['subject']}: parent phase {task['parent']!r} is missing")
            continue
        if _parse(task["exp_end_date"]) > _parse(group["exp_end_date"]):
            errors.append(f"{task['subject']}: ends after its parent phase {task['parent']!r}")

    return errors


# ── Assignment ────────────────────────────────────────────────────────────────


def resolve_assignees(plan: dict[str, Any], directory: list[dict[str, Any]]) -> dict[str, Any]:
    """Attach a concrete employee (and their login) to every task in the plan.

    ``directory`` is what the site actually holds — ``[{name, employee_name,
    designation, user}]`` as published by the Employee Users seeder. Employees
    are handed out round-robin within a designation so a demo does not end up
    with one person owning everything, and the walk is index-based rather than
    random so a reset reproduces the same roster.

    Tasks whose designation has nobody behind it fall back to the full roster;
    an empty directory leaves the task unassigned rather than failing.
    """
    by_designation: dict[str, list[dict[str, Any]]] = {}
    for employee in directory:
        by_designation.setdefault(employee.get("designation", ""), []).append(employee)

    cursors: dict[str, int] = {}

    def take(designation: str) -> dict[str, Any] | None:
        pool = by_designation.get(designation) or directory
        if not pool:
            return None
        index = cursors.get(designation, 0)
        cursors[designation] = index + 1
        return pool[index % len(pool)]

    for task in [*plan["groups"], *plan["tasks"]]:
        employee = take(task.get("designation", ""))
        if employee:
            task["employee"] = employee["name"]
            task["employee_name"] = employee["employee_name"]
            task["user"] = employee.get("user") or ""

    return plan


#: Task priority maps onto ToDo priority when assigning. ToDo has no 'Urgent'
#: and its Select validation rejects one.
_TODO_PRIORITY = {"Low": "Low", "Medium": "Medium", "High": "High", "Urgent": "High"}


def todo_priority(task_priority: str) -> str:
    """ToDo priority for a Task priority."""
    return _TODO_PRIORITY.get(task_priority, "Medium")


# ── Timesheets ────────────────────────────────────────────────────────────────


def timesheet_entries(
    plans: list[dict[str, Any]],
    today: date,
    rng: _random_module.Random,
    *,
    limit: int,
) -> list[dict[str, Any]]:
    """Non-overlapping time logs against tasks that have actually started.

    ERPNext blocks two time logs for the same employee whose intervals overlap,
    counting drafts, and treats an identical or fully enclosing interval as an
    overlap (the boundaries themselves are exclusive, so back-to-back logs are
    fine). Every (employee, day, slot) triple is therefore handed out at most
    once here.

    Only past work is logged: a timesheet dated in the future is nonsense, and
    submitting one writes ``act_end_date`` onto the task, which ERPNext then
    validates against the project's expected end date.
    """
    taken: set[tuple[str, str, int]] = set()
    entries: list[dict[str, Any]] = []

    for plan in plans:
        for task in plan["tasks"]:
            if len(entries) >= limit:
                return entries
            employee = task.get("employee")
            if not employee:
                continue

            start = _parse(task["exp_start_date"])
            if start > today:
                continue
            end = min(_parse(task["exp_end_date"]), today)

            for day in _working_days(start, end, rng):
                if len(entries) >= limit:
                    return entries
                slot = _free_slot(taken, employee, day)
                if slot is None:
                    continue
                slot_start, hours = TIMESHEET_SLOTS[slot]
                taken.add((employee, day.isoformat(), slot))
                entries.append(
                    {
                        "employee": employee,
                        "employee_name": task.get("employee_name", ""),
                        "project": plan["name"],
                        "task_subject": task["subject"],
                        "from_time": datetime.combine(day, slot_start).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                        "hours": hours,
                        "billing_hours": hours,
                        "activity_type": ACTIVITY_TYPES[len(entries) % len(ACTIVITY_TYPES)],
                        # A mix keeps both the billable and the internal-cost
                        # side of Project Profitability populated.
                        "is_billable": int(len(entries) % 4 != 0),
                        "description": f"Work logged on {task['subject']}",
                    }
                )

    return entries


#: Days of work logged per task. Enough to move actual_time off zero without
#: burying the Timesheet list under thousands of rows.
_DAYS_PER_TASK = 2


def _working_days(start: date, end: date, rng: _random_module.Random) -> list[date]:
    """Up to _DAYS_PER_TASK weekdays inside a window, chosen deterministically."""
    candidates = [
        start + timedelta(days=offset)
        for offset in range((end - start).days + 1)
        if (start + timedelta(days=offset)).weekday() < 5
    ]
    if not candidates:
        return []
    if len(candidates) <= _DAYS_PER_TASK:
        return candidates
    return sorted(rng.sample(candidates, _DAYS_PER_TASK))


def _free_slot(taken: set[tuple[str, str, int]], employee: str, day: date) -> int | None:
    """First unused slot for this employee on this day, or None if both are gone."""
    for slot in range(len(TIMESHEET_SLOTS)):
        if (employee, day.isoformat(), slot) not in taken:
            return slot
    return None


# ── Helpers ───────────────────────────────────────────────────────────────────


def _parse(value: str) -> date:
    return date.fromisoformat(value)
