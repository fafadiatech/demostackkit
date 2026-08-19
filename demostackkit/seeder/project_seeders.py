"""
Shared Project seeder bases for every industry.

Each industry supplies only data — ``PROJECT_TYPES`` / ``TASK_TYPES`` /
``TEMPLATES`` in ``01_master/13_projects.py`` and ``PROJECT_BLUEPRINTS`` in
``02_transactions/04_projects.py``; this module carries the Frappe scripts and
the run logic, the same split ``payroll_seeder.py`` uses.

The planning maths lives in :mod:`demostackkit.seeder.projects`, which is pure
and unit tested. What is left here is the part that genuinely needs a site.

Insert order is not a style choice — ERPNext enforces it:

* ``validate_parent_is_group`` rejects a ``parent_task`` that is not a group, and
  ``validate_parent_expected_end_date`` rejects a child that outlives its parent,
  so phase (group) tasks go in first with subtree-spanning dates.
* ``validate_status`` refuses to save a Task as Completed while anything in its
  ``depends_on`` is unfinished — and that fires on a fresh insert too, because
  ``get_db_value`` returns None for a new document. Every task is therefore
  inserted ``Open`` in topological order here, and the status pass happens later
  in the shared ``260_task_finalize.py`` seeder, after timesheets have had their
  say.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Any

from demostackkit.seeder.base import BaseMasterSeeder, BaseTransactionSeeder
from demostackkit.seeder.projects import (
    expand_blueprint,
    iter_leaf_tasks,
    resolve_assignees,
    template_group_pad_days,
    topological_order,
    validate_plan,
)

#: Marker used to lift the created docname map out of the container's stdout.
PROJECT_PAYLOAD_MARKER = "DSK_PROJECT_TASKS::"

#: Cache key the timesheet, finalize and Kanban seeders read. Absent means the
#: industry seeded no projects, and those seeders no-op.
PROJECT_PLAN_CACHE_KEY = "project_plan"


class ProjectTemplateSeeder(BaseMasterSeeder):
    """Project Types, Task Types and reusable Project Templates."""

    label = "Project Templates"
    priority = 88

    #: ``[{"project_type": "Turnkey EPC", "description": "..."}]``
    PROJECT_TYPES: list[dict[str, Any]] = []

    #: ``[{"name": "Survey", "description": "...", "weight": 1}]``
    TASK_TYPES: list[dict[str, Any]] = []

    #: ``[{"name": ..., "project_type": ..., "phases": [...]}]`` — see the
    #: schema docstring in :mod:`demostackkit.seeder.projects`.
    TEMPLATES: list[dict[str, Any]] = []

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Projects" not in cfg.modules:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        today = date.today()

        payload = {
            "company": company,
            "project_types": self.PROJECT_TYPES,
            "task_types": self.TASK_TYPES,
            "templates": [_flatten_template(t) for t in self.TEMPLATES],
            "holiday_list": {
                "name": f"Demo Holidays - {self.ctx.cache_get('company_abbr', cfg.company.abbr)}",
                "from_date": date(today.year, 1, 1).isoformat(),
                "to_date": date(today.year + 1, 12, 31).isoformat(),
            },
        }
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']

if not frappe.db.exists('DocType', 'Project Template'):
    print('Projects: the Projects module is not available on this site, nothing to seed')
    raise SystemExit(0)

# ── Project Types ────────────────────────────────────────────────────────────
pt_created = pt_skipped = 0
for pt in payload['project_types']:
    if frappe.db.exists('Project Type', pt['project_type']):
        pt_skipped += 1
        continue
    frappe.get_doc(dict(pt, doctype='Project Type')).insert(ignore_permissions=True)
    pt_created += 1

# ── Task Types ───────────────────────────────────────────────────────────────
# Task Type autonames by prompt and has no `task_type` field, so the name has to
# be assigned by hand or the insert fails with "Name is required".
tt_created = tt_skipped = 0
for tt in payload['task_types']:
    if frappe.db.exists('Task Type', tt['name']):
        tt_skipped += 1
        continue
    doc = frappe.new_doc('Task Type')
    doc.name = tt['name']
    doc.description = tt.get('description') or ''
    doc.weight = tt.get('weight') or 0
    doc.insert(ignore_permissions=True)
    tt_created += 1

frappe.db.commit()
print(f'Project Types: created={{pt_created}}, skipped={{pt_skipped}}')
print(f'Task Types: created={{tt_created}}, skipped={{tt_skipped}}')

# ── Default Holiday List ─────────────────────────────────────────────────────
# Project.copy_from_template walks every generated task date forward past
# holidays, and throws outright if the company has no default holiday list.
# Payroll normally sets one; if hrms is not installed it never ran.
if not frappe.db.get_value('Company', company, 'default_holiday_list'):
    hl_name = payload['holiday_list']['name']
    if not frappe.db.exists('Holiday List', hl_name):
        hl = frappe.get_doc({{
            'doctype': 'Holiday List',
            'holiday_list_name': hl_name,
            'from_date': payload['holiday_list']['from_date'],
            'to_date': payload['holiday_list']['to_date'],
        }})
        hl.weekly_off = 'Sunday'
        hl.get_weekly_off_dates()
        hl.insert(ignore_permissions=True)
    frappe.db.set_value('Company', company, 'default_holiday_list', hl_name)
    frappe.db.commit()
    print(f'Holiday List: set {{hl_name}} as the company default')

# ── Project Templates ────────────────────────────────────────────────────────
tpl_created = tpl_updated = tpl_skipped = errors = 0

def _read_template_fingerprint(tpl_name):
    if not frappe.db.exists('Project Template', tpl_name):
        return None
    tpl = frappe.get_doc('Project Template', tpl_name)
    subject_by_name = {{}}
    for row in tpl.tasks:
        subject_by_name[row.task] = frappe.db.get_value('Task', row.task, 'subject')
    groups = []
    tasks = []
    for row in tpl.tasks:
        t = frappe.get_doc('Task', row.task)
        if t.is_group:
            groups.append({{
                'subject': t.subject,
                'start': int(t.start or 0),
                'duration': int(t.duration or 0),
            }})
        else:
            parent = subject_by_name.get(t.parent_task, '') if t.parent_task else ''
            dep_subjects = sorted(
                subject_by_name.get(d.task, d.task)
                for d in (t.depends_on or [])
            )
            tasks.append({{
                'subject': t.subject,
                'parent': parent,
                'start': int(t.start or 0),
                'duration': int(t.duration or 0),
                'depends_on': dep_subjects,
            }})
    return {{'groups': groups, 'tasks': tasks}}

def _delete_template(tpl_name):
    tpl = frappe.get_doc('Project Template', tpl_name)
    # Groups were inserted before leaves; trash leaves first so on_trash passes.
    for task_name in reversed([row.task for row in tpl.tasks]):
        frappe.delete_doc('Task', task_name, force=1)
    frappe.delete_doc('Project Template', tpl_name, force=1)

for tpl in payload['templates']:
    exists = frappe.db.exists('Project Template', tpl['name'])
    if exists:
        stored = _read_template_fingerprint(tpl['name'])
        stale = stored != tpl['fingerprint'] or any(
            g.get('duration', 0) < 1 for g in (stored or {{}}).get('groups', [])
        )
        if not stale:
            tpl_skipped += 1
            continue
        _delete_template(tpl['name'])
        print(f'UPDATED: rebuilding Project Template {{tpl["name"]}} (stored metadata differs)')
    try:
        by_subject = {{}}
        order = []

        # Groups first: a template task's parent_task must itself be a template.
        for grp in tpl['groups']:
            doc = frappe.get_doc({{
                'doctype': 'Task',
                'subject': grp['subject'],
                'is_template': 1,
                'is_group': 1,
                'type': grp.get('type') or None,
                'priority': grp.get('priority') or 'Medium',
                # Spans the whole phase, so the generated parent outlives every
                # child copy_from_template hangs beneath it.
                'start': grp.get('start') or 0,
                'duration': grp.get('duration') or 1,
            }})
            doc.insert(ignore_permissions=True)
            by_subject[grp['subject']] = doc.name
            order.append(doc.name)

        for task in tpl['tasks']:
            doc = frappe.get_doc({{
                'doctype': 'Task',
                'subject': task['subject'],
                'is_template': 1,
                'parent_task': by_subject.get(task['parent']),
                'type': task.get('type') or None,
                'priority': task.get('priority') or 'Medium',
                'start': task.get('start') or 0,
                'duration': task.get('duration') or 1,
                'task_weight': task.get('weight') or 0,
                'description': task.get('description') or '',
                'depends_on': [
                    {{'task': by_subject[d]}}
                    for d in (task.get('depends_on') or [])
                    if d in by_subject
                ],
            }})
            doc.insert(ignore_permissions=True)
            by_subject[task['subject']] = doc.name
            order.append(doc.name)

        # The tasks table must be closed under both parent->child and
        # depends_on: populate_depends_on pushes every child into its parent's
        # depends_on, and validate_dependencies rejects a template that
        # references a task it does not list. Listing the whole tree satisfies
        # both.
        tpl_doc = frappe.new_doc('Project Template')
        tpl_doc.name = tpl['name']
        tpl_doc.project_type = tpl['project_type']
        for task_name in order:
            tpl_doc.append('tasks', {{'task': task_name}})
        tpl_doc.insert(ignore_permissions=True)
        if exists:
            tpl_updated += 1
        else:
            tpl_created += 1
    except Exception as ex:
        print(f"ERROR Project Template {{tpl['name']}}: {{ex}}")
        errors += 1

frappe.db.commit()
print(f'Project Templates: created={{tpl_created}}, updated={{tpl_updated}}, skipped={{tpl_skipped}}, errors={{errors}}')
if errors:
    raise SystemExit(f'{{errors}} project template(s) failed')
"""
        self._exec(script, timeout=600)


class ProjectSeeder(BaseTransactionSeeder):
    """Projects with their phase/task trees, dependencies and assignees."""

    label = "Projects & Tasks"
    priority = 240
    _volume_attr = "projects"
    default_volume = 4

    #: ``[{"name": ..., "project_type": ..., "phases": [...]}]`` — see the
    #: schema docstring in :mod:`demostackkit.seeder.projects`.
    PROJECT_BLUEPRINTS: list[dict[str, Any]] = []

    def validate(self) -> list[str]:
        """Catch an authoring mistake before anything touches the site."""
        if "Projects" not in self.ctx.industry_config.modules:
            return []
        errors = []
        for blueprint in self.PROJECT_BLUEPRINTS:
            try:
                plan = expand_blueprint(blueprint, date.today())
            except ValueError as exc:
                errors.append(f"{blueprint.get('name', '?')}: {exc}")
                continue
            errors.extend(f"{plan['name']}: {problem}" for problem in validate_plan(plan))
        return errors

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if "Projects" not in cfg.modules:
            return
        if not self.PROJECT_BLUEPRINTS:
            return

        company = self.ctx.cache_get("company_name", cfg.company.name)
        directory = self.ctx.cache_get("employee_directory", [])
        customers = self.ctx.cache_get("customer_names", [])
        today = date.today()

        plans = []
        for index, blueprint in enumerate(self.PROJECT_BLUEPRINTS[: self.volume]):
            plan = resolve_assignees(expand_blueprint(blueprint, today), directory)
            # A project the demo can trace back to a real customer reads better
            # than an unattached one, and it lights up the customer's dashboard.
            plan["customer"] = (
                customers[index % len(customers)]
                if customers and blueprint.get("with_customer", True)
                else ""
            )
            plans.append(plan)

        payload = {"company": company, "projects": plans}
        payload_json = json.dumps(payload)

        script = f"""
import json

payload = json.loads('''{payload_json}''')
company = payload['company']

if not frappe.db.exists('DocType', 'Project'):
    print('Projects: the Projects module is not available on this site, nothing to seed')
    raise SystemExit(0)

task_meta = frappe.get_meta('Task')


def build_task(fields):
    \"\"\"Drop fields this ERPNext build does not carry, then keep the project's
    percent-complete recalculation from firing once per task save.\"\"\"
    clean = {{
        key: value
        for key, value in fields.items()
        if value not in (None, '')
        and (key in ('doctype', 'depends_on') or task_meta.has_field(key))
    }}
    doc = frappe.get_doc(clean)
    doc.flags.from_project = True
    return doc


created = skipped = errors = 0
result = {{}}

for p in payload['projects']:
    existing = frappe.db.get_value('Project', {{'project_name': p['name']}}, 'name')
    if existing:
        skipped += 1
        result[p['name']] = {{
            'project': existing,
            'tasks': {{
                row.subject: row.name
                for row in frappe.get_all(
                    'Task', filters={{'project': existing}}, fields=['name', 'subject']
                )
            }},
        }}
        continue

    try:
        proj = frappe.get_doc({{
            'doctype': 'Project',
            'project_name': p['name'],
            'company': company,
            'status': 'Open',
            'is_active': 'Yes',
            'project_type': p['project_type'],
            'priority': p['priority'],
            'percent_complete_method': 'Task Completion',
            'expected_start_date': p['expected_start_date'],
            'expected_end_date': p['expected_end_date'],
            'customer': p.get('customer') or None,
            'notes': p.get('notes') or '',
            # project_template makes after_insert generate the whole task tree,
            # reproducing the template's dependencies and parent/child nesting.
            'project_template': p.get('template') or None,
        }})
        # Populating Project.users sends a real welcome email per row and adds
        # docshares; assignment via ToDo gives the same demo value without either.
        proj.insert(ignore_permissions=True)

        by_subject = {{}}

        # Groups top-down, spanning their subtree: a child may not end after its
        # parent, and parent_task must already exist and be a group.
        for grp in p['groups']:
            doc = build_task({{
                'doctype': 'Task',
                'subject': grp['subject'],
                'project': proj.name,
                'company': company,
                'is_group': 1,
                'status': 'Open',
                'type': grp.get('type'),
                'priority': grp.get('priority'),
                'exp_start_date': grp['exp_start_date'],
                'exp_end_date': grp['exp_end_date'],
            }})
            doc.insert(ignore_permissions=True)
            by_subject[grp['subject']] = doc.name

        # Leaves in topological order, all Open — the status pass runs later.
        for task in p['tasks']:
            doc = build_task({{
                'doctype': 'Task',
                'subject': task['subject'],
                'project': proj.name,
                'company': company,
                'status': 'Open',
                'parent_task': by_subject.get(task['parent']),
                'type': task.get('type'),
                'priority': task.get('priority'),
                'exp_start_date': task['exp_start_date'],
                'exp_end_date': task['exp_end_date'],
                'expected_time': task.get('expected_time'),
                'is_milestone': task.get('is_milestone'),
                'description': task.get('description'),
                # Task Depends On.project is left unset on purpose: it is the
                # only thing keeping reschedule_dependent_tasks from rewriting
                # these hand-authored dates behind our backs.
                'depends_on': [
                    {{'task': by_subject[d]}}
                    for d in (task.get('depends_on') or [])
                    if d in by_subject
                ],
            }})
            doc.insert(ignore_permissions=True)
            by_subject[task['subject']] = doc.name

        # A template-built project has no hand-authored rows; read back whatever
        # copy_from_template generated so the later passes can reach it.
        if p.get('template'):
            by_subject = {{
                row.subject: row.name
                for row in frappe.get_all(
                    'Task', filters={{'project': proj.name}}, fields=['name', 'subject']
                )
            }}

        # One project save now that every task is in, rather than the dozens
        # Task.on_update would otherwise trigger.
        frappe.get_doc('Project', proj.name).save(ignore_permissions=True)
        frappe.db.commit()

        result[p['name']] = {{'project': proj.name, 'tasks': by_subject}}
        created += 1
        print(f"CREATED: {{proj.name}} — {{p['name']}} ({{len(by_subject)}} task(s))")
    except Exception as ex:
        frappe.db.rollback()
        print(f"ERROR Project {{p['name']}}: {{ex}}")
        errors += 1

frappe.db.commit()
print(f'Projects: created={{created}}, skipped={{skipped}}, errors={{errors}}')
print('{PROJECT_PAYLOAD_MARKER}' + json.dumps(result))
if errors:
    raise SystemExit(f'{{errors}} project(s) failed')
"""
        output = self._exec(script, timeout=900)
        created = _extract_payload(output)

        for plan in plans:
            plan["docnames"] = created.get(plan["name"], {})
        self.ctx.cache_set(PROJECT_PLAN_CACHE_KEY, plans)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _flatten_template(template: dict[str, Any]) -> dict[str, Any]:
    """Split an authored template into insert-ordered groups and leaf tasks."""
    leaves = [
        {
            "subject": task["subject"],
            "parent": phase_subject,
            "type": task.get("type", ""),
            "priority": task.get("priority", "Medium"),
            "start": int(task.get("start", 0)),
            "duration": max(int(task.get("duration", 1)), 1),
            "weight": task.get("weight", 0),
            "description": task.get("description", ""),
            "depends_on": list(task.get("depends_on", ())),
        }
        for phase_subject, task in iter_leaf_tasks(template["phases"])
    ]

    by_phase: dict[str, list[dict[str, Any]]] = {}
    for leaf in leaves:
        by_phase.setdefault(leaf["parent"], []).append(leaf)

    groups = []
    for phase in template["phases"]:
        children = by_phase.get(phase["subject"], [])
        if not children:
            raise ValueError(f"template phase {phase['subject']!r} has no tasks")
        start = min(child["start"] for child in children)
        end = max(child["start"] + child["duration"] for child in children)
        span = end - start
        groups.append(
            {
                "subject": phase["subject"],
                "type": phase.get("type", ""),
                "priority": phase.get("priority", "Medium"),
                # A group needs a span of its own. ERPNext builds every generated
                # task's dates from `start` and `duration` alone, so a group left
                # at the default 0/0 comes out ending on the project start date —
                # and then validate_parent_expected_end_date rejects the first
                # child that outlives it, taking the whole Project insert down
                # with it from inside after_insert.
                "start": start,
                "duration": span + template_group_pad_days(span),
            }
        )

    flat = {
        "name": template["name"],
        "project_type": template["project_type"],
        "groups": groups,
        "tasks": topological_order(leaves),
    }
    flat["fingerprint"] = _template_fingerprint(flat)
    return flat


def _template_fingerprint(flat: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Comparable metadata used to detect stale Project Templates on the site."""
    return {
        "groups": [
            {"subject": g["subject"], "start": g["start"], "duration": g["duration"]}
            for g in flat["groups"]
        ],
        "tasks": [
            {
                "subject": t["subject"],
                "parent": t["parent"],
                "start": t["start"],
                "duration": t["duration"],
                "depends_on": sorted(t.get("depends_on", ())),
            }
            for t in flat["tasks"]
        ],
    }


def _extract_payload(output: str) -> dict[str, Any]:
    for line in output.splitlines():
        if line.startswith(PROJECT_PAYLOAD_MARKER):
            return json.loads(line[len(PROJECT_PAYLOAD_MARKER) :])
    raise RuntimeError(
        f"Project docnames not found in seeder output (missing {PROJECT_PAYLOAD_MARKER!r})"
    )
