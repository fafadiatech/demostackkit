"""
Shared seeder: a login for every seeded Employee.

Employees arrive from `11_employees.py` with no `user_id`, which leaves them
disconnected from everything in ERPNext that works in terms of Users rather than
Employees — most visibly task assignment, which writes a ToDo against a User and
populates the `_assign` column the desk renders as "Assigned To". Without this
seeder a demo can only ever assign work to the four generic logins declared in
`industry.yaml`, and the seeded workforce is decorative.

Creating the User and pointing `Employee.user_id` at it also gives the demo real
ESS surfaces: the employee shows up in Timesheet and Leave pickers, and the
assignment sidebar shows a plausible name rather than `admin`.

Two deliberate departures from the ERPNext defaults:

    create_user_permission = 0
        The default (1) creates a User Permission restricting each login to its
        own Employee record, which cascades into Timesheet, Leave and Attendance
        and makes a demo site look broken when someone signs in to look around.
        A demo wants browsability more than it wants ESS isolation.

    enable_email_notifications = 0
        No demo site has a working outgoing email account, so every assignment
        would otherwise leave an OutgoingEmailError in the Error Log. Clearing
        the flag keeps the in-app bell notifications, which are a nice artifact,
        and drops only the mail that was never going to send.

Priority 84 puts this after Employees (80) and Payroll (82) and ahead of the
Project seeders (88+), which assign tasks to the users it creates.

Idempotent, as master seeders must be: an existing User is reused and an Employee
that already carries a `user_id` is left alone.
"""

from __future__ import annotations

import json
from typing import Any

from demostackkit.seeder.base import BaseMasterSeeder

#: Marker used to lift the resolved directory out of the container's stdout.
_PAYLOAD_MARKER = "DSK_EMPLOYEE_DIRECTORY::"

#: Every seeded login needs this to open a Task at all — `task.json` grants
#: read/write to `Projects User` and nothing else, so without it each assignment
#: silently creates a DocShare instead.
_BASE_ROLES = ("Projects User", "Employee")

#: Designations senior enough to own a project rather than just work on one.
_LEAD_ROLE = "Projects Manager"
_LEAD_MARKERS = ("manager", "head", "lead", "director", "principal", "chief")


class EmployeeUserSeeder(BaseMasterSeeder):
    label = "Employee Logins"
    priority = 84

    def run(self) -> None:
        cfg = self.ctx.industry_config
        company = self.ctx.cache_get("company_name", cfg.company.name)

        payload = {
            "company": company,
            "domain": f"{self.ctx.industry_slug}.demo",
            "password": cfg.seed.demo_password,
            "base_roles": list(_BASE_ROLES),
            "lead_role": _LEAD_ROLE,
            "lead_markers": list(_LEAD_MARKERS),
        }
        payload_json = json.dumps(payload)

        script = f"""
import json
import re

payload = json.loads('''{payload_json}''')
company = payload['company']

# User.before_insert refuses to create more than 60 users an hour per site.
# A full industry seed is comfortably under that, but a re-seed on top of an
# existing site compounds the count. Raising the process-local limit touches no
# persisted config and has no other side effects.
frappe.local.conf['throttle_user_limit'] = 10000


def email_for(employee_name, taken):
    parts = [re.sub(r'[^a-z0-9]', '', p.lower()) for p in employee_name.split()]
    parts = [p for p in parts if p]
    local = '.'.join(parts[:2]) or 'employee'
    candidate = local + '@' + payload['domain']
    suffix = 2
    while candidate in taken:
        candidate = local + str(suffix) + '@' + payload['domain']
        suffix += 1
    taken.add(candidate)
    return candidate


def roles_for(designation):
    roles = list(payload['base_roles'])
    lowered = (designation or '').lower()
    if any(marker in lowered for marker in payload['lead_markers']):
        roles.append(payload['lead_role'])
    return roles


employees = frappe.get_all(
    'Employee',
    filters={{'company': company, 'status': 'Active'}},
    fields=['name', 'employee_name', 'designation', 'user_id'],
    order_by='name',
)

taken = set(frappe.get_all('User', pluck='name'))
created = skipped = linked = errors = 0
directory = []

for emp in employees:
    try:
        email = emp.user_id
        if not email:
            email = email_for(emp.employee_name, taken)

        if frappe.db.exists('User', email):
            skipped += 1
        else:
            parts = emp.employee_name.split()
            user = frappe.new_doc('User')
            user.email = email
            user.first_name = parts[0]
            user.last_name = ' '.join(parts[1:])
            user.user_type = 'System User'
            user.enabled = 1
            user.send_welcome_email = 0
            user.new_password = payload['password']
            user.flags.no_welcome_mail = True
            for role in roles_for(emp.designation):
                if frappe.db.exists('Role', role):
                    user.append('roles', {{'role': role}})
            user.insert(ignore_permissions=True)
            created += 1

        # Notification Settings is auto-created per user; guard anyway in case a
        # future version stops doing that.
        if frappe.db.exists('Notification Settings', email):
            frappe.db.set_value(
                'Notification Settings', email, 'enable_email_notifications', 0
            )

        if not emp.user_id:
            doc = frappe.get_doc('Employee', emp.name)
            # Set before user_id: update_user_permissions() reads this flag in
            # the same on_update pass that first sees the link.
            doc.create_user_permission = 0
            doc.user_id = email
            # save(), not db_set() — on_update is what propagates the Employee
            # role onto the User.
            doc.save(ignore_permissions=True)
            linked += 1

        directory.append({{
            'name': emp.name,
            'employee_name': emp.employee_name,
            'designation': emp.designation or '',
            'user': email,
        }})
    except Exception as ex:
        print(f'ERROR Employee login {{emp.employee_name}}: {{ex}}')
        errors += 1

frappe.db.commit()
print(f'Employee Logins: created={{created}}, existing={{skipped}}, linked={{linked}}, errors={{errors}}')
print('{_PAYLOAD_MARKER}' + json.dumps(directory))
if errors:
    raise SystemExit(f'{{errors}} employee login(s) failed')
"""
        # Employee.on_update calls frappe.clear_cache() once per record, which
        # makes this markedly slower than its row count suggests.
        output = self._exec(script, timeout=600)
        self.ctx.cache_set("employee_directory", self._extract_payload(output))

    @staticmethod
    def _extract_payload(output: str) -> list[dict[str, Any]]:
        for line in output.splitlines():
            if line.startswith(_PAYLOAD_MARKER):
                return json.loads(line[len(_PAYLOAD_MARKER) :])
        raise RuntimeError(
            f"Employee directory not found in seeder output (missing {_PAYLOAD_MARKER!r})"
        )
