"""
Shared seeder: final task statuses and assignments.

The Projects seeder inserts every task as Open because ERPNext refuses to save a
Task as Completed while anything it depends on is unfinished — a check that
fires on a fresh insert too. This pass walks the same dependency order a second
time and applies the status each task was planned to end up in, which is what
gives the Kanban board cards in every column.

It runs at 260, after timesheets (250), because submitting a Timesheet promotes
an Open task to Working and would otherwise undo half of this.

Order within the pass matters as much as order between passes: leaves are
finished before their phases, because `Task.populate_depends_on` appends every
child into its parent's `depends_on`, so a phase cannot be completed until all
its children are.

Assignment comes last and skips finished tasks: `unassign_todo` closes the ToDo
behind any Completed or Cancelled task, so assigning one writes a row that is
immediately cleared. Those carry `completed_by` instead.

Runs for every industry; no-ops when no projects were seeded.
"""

from __future__ import annotations

import json
from typing import Any

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.project_seeders import PROJECT_PLAN_CACHE_KEY
from demostackkit.seeder.projects import TERMINAL_STATUSES, todo_priority

#: Fields carried across per status. Anything absent is simply not set.
_STATUS_FIELDS = ("progress", "completed_on", "review_date")


class TaskFinalizeSeeder(BaseTransactionSeeder):
    label = "Task Statuses & Assignments"
    priority = 260

    def run(self) -> None:
        plans = self.ctx.cache_get(PROJECT_PLAN_CACHE_KEY) or []
        if not plans:
            return

        directory = self.ctx.cache_get("employee_directory", [])
        documents = [doc for doc in (self._build(plan, directory) for plan in plans) if doc]
        if not documents:
            return

        payload_json = json.dumps({"projects": documents})

        script = f"""
import json
from frappe.desk.form.assign_to import add as assign_to_add

payload = json.loads('''{payload_json}''')
updated = assigned = errors = 0


def apply(row):
    doc = frappe.get_doc('Task', row['task'])
    doc.status = row['status']
    for field in ('progress', 'completed_on', 'review_date', 'completed_by'):
        if row.get(field) is not None:
            doc.set(field, row[field])
    # Let the single project save at the end do the percent-complete maths
    # rather than recomputing it once per task.
    doc.flags.from_project = True
    doc.save(ignore_permissions=True)


for project in payload['projects']:
    # Leaves first, in dependency order, then the phases above them.
    for row in project['tasks'] + project['groups']:
        try:
            apply(row)
            updated += 1
        except Exception as ex:
            print(f"WARN Task status {{row['task']}} -> {{row['status']}}: {{ex}}")
            errors += 1

    for row in project['assignments']:
        try:
            assign_to_add({{
                'assign_to': [row['user']],
                'doctype': 'Task',
                'name': row['task'],
                'description': row['description'],
                # ToDo has no 'Urgent' and its Select validation rejects one.
                'priority': row['priority'],
                'date': row['date'],
            }})
            assigned += 1
        except Exception as ex:
            print(f"WARN Task assignment {{row['task']}} -> {{row['user']}}: {{ex}}")
            errors += 1

    try:
        frappe.get_doc('Project', project['project']).save(ignore_permissions=True)
    except Exception as ex:
        print(f"WARN Project refresh {{project['project']}}: {{ex}}")

    frappe.db.commit()

frappe.db.commit()
print(f'Task Finalize: statuses={{updated}}, assignments={{assigned}}, warnings={{errors}}')
"""
        self._exec(script, timeout=900)

    # ── Payload ───────────────────────────────────────────────────────────────

    def _build(
        self, plan: dict[str, Any], directory: list[dict[str, Any]]
    ) -> dict[str, Any] | None:
        """Status rows and assignment rows for one project, in application order."""
        docnames = plan.get("docnames") or {}
        project = docnames.get("project")
        tasks = docnames.get("tasks") or {}
        if not project or not tasks:
            return None

        status_rows: list[dict[str, Any]] = []
        group_rows: list[dict[str, Any]] = []
        assignments: list[dict[str, Any]] = []

        for planned in plan["tasks"]:
            name = tasks.get(planned["subject"])
            if not name:
                continue
            status_rows.append(self._status_row(name, planned))
            assignment = self._assignment_row(name, planned)
            if assignment:
                assignments.append(assignment)

        for planned in plan["groups"]:
            name = tasks.get(planned["subject"])
            if name:
                group_rows.append(self._status_row(name, planned))

        # A template-instantiated project has no hand-authored rows, so its
        # generated tasks would otherwise end up unowned. Spread them over the
        # workforce so the board and the Gantt still show real names.
        planned_subjects = {t["subject"] for t in plan["tasks"]} | {
            g["subject"] for g in plan["groups"]
        }
        extras = sorted(name for subject, name in tasks.items() if subject not in planned_subjects)
        for index, name in enumerate(extras):
            if not directory:
                break
            employee = directory[index % len(directory)]
            if employee.get("user"):
                assignments.append(
                    {
                        "task": name,
                        "user": employee["user"],
                        "priority": "Medium",
                        "description": f"Assigned on {plan['name']}",
                        "date": plan["expected_end_date"],
                    }
                )

        return {
            "project": project,
            "tasks": status_rows,
            "groups": group_rows,
            "assignments": assignments,
        }

    @staticmethod
    def _status_row(name: str, planned: dict[str, Any]) -> dict[str, Any]:
        row: dict[str, Any] = {"task": name, "status": planned["status"]}
        for field in _STATUS_FIELDS:
            if field in planned:
                row[field] = planned[field]
        if planned["status"] == "Completed" and planned.get("user"):
            row["completed_by"] = planned["user"]
        return row

    @staticmethod
    def _assignment_row(name: str, planned: dict[str, Any]) -> dict[str, Any] | None:
        if planned["status"] in TERMINAL_STATUSES or not planned.get("user"):
            return None
        return {
            "task": name,
            "user": planned["user"],
            "priority": todo_priority(planned.get("priority", "Medium")),
            "description": planned["subject"],
            "date": planned["exp_end_date"],
        }
