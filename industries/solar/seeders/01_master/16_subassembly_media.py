"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for solar.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-JBOX-01",
        "image": "images/subassemblies/panel_junction_box_module.jpg",
        "pdf": "pdfs/subassemblies/panel_junction_box_module_spec.pdf",
    },
    {
        "item_code": "SA-MICROINV-01",
        "image": "images/subassemblies/microinverter_module.jpg",
        "pdf": "pdfs/subassemblies/microinverter_module_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
