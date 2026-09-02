"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for print3d.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-HOTEND-01",
        "image": "images/subassemblies/hotend_module.jpg",
        "pdf": "pdfs/subassemblies/hotend_module_spec.pdf",
    },
    {
        "item_code": "SA-CARRIAGE-01",
        "image": "images/subassemblies/motion_carriage.jpg",
        "pdf": "pdfs/subassemblies/motion_carriage_spec.pdf",
    },
    {
        "item_code": "SA-BEDLEVEL-01",
        "image": "images/subassemblies/bed_leveling_module.jpg",
        "pdf": "pdfs/subassemblies/bed_leveling_module_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
