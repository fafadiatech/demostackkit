"""
Shared engine for attaching bundled images and PDF spec sheets to Items.

Each industry supplies only ``ITEM_MEDIA`` in its
``01_master/16_subassembly_media.py``; this module carries the docker cp +
Frappe script + idempotency logic, the same split ``asset_seeder.py`` uses
for Asset Categories/Assets.

Runs after ``03_items.py`` (priority 30) so the target Items already exist.
Bundled files live under ``industries/<slug>/assets/{images,pdfs}/...`` and
are not mounted into the backend container, so each referenced file is
``docker cp``'d into the container before the Frappe script that attaches it
runs — mirroring ``demostackkit.erpnext.bench.BenchClient.copy_app_from_host``.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from demostackkit.seeder.base import BaseMasterSeeder


class ItemMediaSeeder(BaseMasterSeeder):
    """Attaches a bundled image and/or PDF spec sheet to designated Items."""

    label = "Item Media (images/spec sheets)"
    priority = 31

    #: [{"item_code": "SA-...", "image": "images/subassemblies/foo.jpg",
    #:   "pdf": "pdfs/subassemblies/foo_spec.pdf"}, ...]
    #: Paths are relative to the industry's assets/ dir. "pdf" is optional,
    #: as is "image" (though every entry should carry at least one).
    ITEM_MEDIA: list[dict[str, str]] = []

    def _assets_dir(self) -> Path:
        return self.ctx.industry_config.industry_dir / "assets"

    def validate(self) -> list[str]:
        if not self.ITEM_MEDIA:
            return []
        assets_dir = self._assets_dir()
        errors = []
        for entry in self.ITEM_MEDIA:
            for key in ("image", "pdf"):
                rel = entry.get(key)
                if rel and not (assets_dir / rel).exists():
                    errors.append(
                        f"Missing bundled asset for item {entry['item_code']}: assets/{rel}"
                    )
        return errors

    def run(self) -> None:
        if not self.ITEM_MEDIA:
            return

        assets_dir = self._assets_dir()
        slug = self.ctx.industry_slug
        container_dir = f"/tmp/dsk_assets/{slug}"

        subprocess.run(
            ["docker", "exec", self.ctx.backend_container, "mkdir", "-p", container_dir],
            check=True,
            capture_output=True,
            timeout=30,
        )

        copied: set[str] = set()
        for entry in self.ITEM_MEDIA:
            for key in ("image", "pdf"):
                rel = entry.get(key)
                if rel and rel not in copied:
                    host_path = assets_dir / rel
                    subprocess.run(
                        [
                            "docker",
                            "cp",
                            str(host_path),
                            f"{self.ctx.backend_container}:{container_dir}/{Path(rel).name}",
                        ],
                        check=True,
                        capture_output=True,
                        timeout=60,
                    )
                    copied.add(rel)

        entries: list[dict[str, Any]] = [
            {
                "item_code": entry["item_code"],
                "image_name": Path(entry["image"]).name if entry.get("image") else None,
                "pdf_name": Path(entry["pdf"]).name if entry.get("pdf") else None,
            }
            for entry in self.ITEM_MEDIA
        ]
        entries_json = json.dumps(entries)
        container_dir_json = json.dumps(container_dir)

        script = f"""
import hashlib
import json
import os
from frappe.utils.file_manager import save_file

container_dir = json.loads('''{container_dir_json}''')
entries = json.loads('''{entries_json}''')


def attach(item_code, file_name):
    with open(os.path.join(container_dir, file_name), 'rb') as fh:
        content = fh.read()

    # save_file() renames the stored file with a random hash suffix
    # (foo.jpg -> foo83d599.jpg), so file_name can't be used as the
    # idempotency key on a re-run. content_hash is the same MD5 digest
    # Frappe itself computes in get_content_hash(), so it survives that
    # rename and correctly identifies "this exact file already attached
    # to this exact item" across runs.
    content_hash = hashlib.md5(content, usedforsecurity=False).hexdigest()
    existing = frappe.db.get_value(
        'File',
        {{'attached_to_doctype': 'Item', 'attached_to_name': item_code, 'content_hash': content_hash}},
        'file_url',
    )
    if existing:
        return existing
    file_doc = save_file(file_name, content, 'Item', item_code, is_private=0)
    return file_doc.file_url


processed = skipped = 0
for e in entries:
    if not frappe.db.exists('Item', e['item_code']):
        print(f"SKIP: Item {{e['item_code']}} does not exist")
        skipped += 1
        continue
    if e.get('image_name'):
        file_url = attach(e['item_code'], e['image_name'])
        if frappe.db.get_value('Item', e['item_code'], 'image') != file_url:
            frappe.db.set_value('Item', e['item_code'], 'image', file_url)
    if e.get('pdf_name'):
        attach(e['item_code'], e['pdf_name'])
    processed += 1

frappe.db.commit()
print(f'Item Media: processed={{processed}}, skipped={{skipped}}')
"""
        self._exec(script, timeout=180)
