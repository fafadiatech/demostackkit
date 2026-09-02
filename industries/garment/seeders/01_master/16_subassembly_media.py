"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for garment.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-CUTDIE-01",
        "image": "images/subassemblies/cutting_die_subassembly.jpg",
        "pdf": "pdfs/subassemblies/cutting_die_subassembly_spec.pdf",
    },
    {
        "item_code": "SA-STITCHHEAD-01",
        "image": "images/subassemblies/stitching_head_module.jpg",
        "pdf": "pdfs/subassemblies/stitching_head_module_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
