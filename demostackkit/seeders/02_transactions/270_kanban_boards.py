"""
Shared seeder: a ready-made Kanban board for Tasks.

ERPNext ships no Task Kanban board, so `/app/task/view/kanban` opens on a
"create a board first" prompt — which is a poor way to start a demo of the
feature. This seeds one board grouped by status, with the columns curated and
coloured.

Built by hand rather than through `quick_kanban_board`, which derives its
columns from the full `Task.status` select list and therefore emits a `Template`
column holding the Project Template scaffolding tasks. That column is noise on a
demo board.

Priority 270 puts it after the tasks exist, which matters: `before_insert`
snapshots each column's card order, and a board created against an empty Task
table persists empty orders.

Runs for every industry; no-ops when no projects were seeded.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseTransactionSeeder
from demostackkit.seeder.project_seeders import PROJECT_PLAN_CACHE_KEY

#: Board name. Kanban Board autonames off this field, so it is also the docname
#: and the URL segment: /app/task/view/kanban/Project Tasks. Each industry is
#: its own site, so a constant name stays unambiguous and keeps demo scripts and
#: bookmarks identical everywhere.
BOARD_NAME = "Project Tasks"

#: Column order and indicator colour. Deliberately excludes 'Template' — those
#: are the Project Template scaffolding tasks, not real work.
_COLUMNS: tuple[tuple[str, str], ...] = (
    ("Open", "Blue"),
    ("Working", "Orange"),
    ("Pending Review", "Purple"),
    ("Overdue", "Red"),
    ("Completed", "Green"),
    ("Cancelled", "Gray"),
)


class KanbanBoardSeeder(BaseTransactionSeeder):
    label = "Task Kanban Board"
    priority = 270

    def run(self) -> None:
        if not self.ctx.cache_get(PROJECT_PLAN_CACHE_KEY):
            return

        payload_json = json.dumps(
            {
                "name": BOARD_NAME,
                "columns": [
                    {"column_name": name, "indicator": colour} for name, colour in _COLUMNS
                ],
            }
        )

        script = f"""
import json

payload = json.loads('''{payload_json}''')

if frappe.db.exists('Kanban Board', payload['name']):
    print(f"Kanban Board: {{payload['name']}} already exists")
    raise SystemExit(0)

board = frappe.new_doc('Kanban Board')
board.kanban_board_name = payload['name']
board.reference_doctype = 'Task'
board.field_name = 'status'
# Shared, not private: every demo login should land on the same board.
board.private = 0
for column in payload['columns']:
    board.append('columns', {{
        'column_name': column['column_name'],
        'indicator': column['indicator'],
        'status': 'Active',
    }})
board.insert(ignore_permissions=True)
frappe.db.commit()
print(f"Kanban Board: created {{board.name}} with {{len(board.columns)}} column(s)")
"""
        self._exec(script, timeout=180)
