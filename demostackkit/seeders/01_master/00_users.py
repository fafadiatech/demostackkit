"""
Shared seeder: Demo Users.

Creates ERPNext User documents and assigns roles for all users
defined in the industry's `users:` section of industry.yaml.

Idempotent — skips users that already exist.
Priority 5 ensures this runs before all industry-specific master seeders.
"""

from __future__ import annotations

import json

from demostackkit.seeder.base import BaseMasterSeeder


class UserSeeder(BaseMasterSeeder):
    label = "Demo Users"
    priority = 5

    def run(self) -> None:
        cfg = self.ctx.industry_config
        if not cfg.users:
            return

        password = cfg.seed.demo_password
        users_data = [
            {"email": u.email, "full_name": u.full_name, "roles": u.roles}
            for u in cfg.users
        ]
        users_json = json.dumps(users_data)

        script = f"""
import frappe, json
from frappe.utils.password import update_password

frappe.init(site='{self.ctx.site}', sites_path='{self.ctx.bench_path}/sites')
frappe.connect()

users = json.loads('''{users_json}''')
password = '{password}'
created = skipped = 0

for u in users:
    email = u['email']
    if frappe.db.exists('User', email):
        skipped += 1
        print(f'EXISTS: User {{email}}')
        continue

    parts = u['full_name'].split()
    doc = frappe.get_doc({{
        'doctype': 'User',
        'email': email,
        'first_name': parts[0],
        'last_name': ' '.join(parts[1:]),
        'send_welcome_email': 0,
        'enabled': 1,
    }})
    for role in u['roles']:
        doc.append('roles', {{'role': role}})
    doc.insert(ignore_permissions=True)
    update_password(email, password)
    created += 1
    print(f'CREATED: User {{email}}')

frappe.db.commit()
print(f'Users: created={{created}}, skipped={{skipped}}')
"""
        self._exec(script)
