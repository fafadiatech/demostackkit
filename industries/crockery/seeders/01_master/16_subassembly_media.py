"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for crockery.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-KILNMOD-01",
        "image": "images/subassemblies/kiln_firing_module.jpg",
        "pdf": "pdfs/subassemblies/kiln_firing_module_spec.pdf",
    },
    {
        "item_code": "SA-GLAZEBOOTH-01",
        "image": "images/subassemblies/glaze_spray_booth_subassembly.jpg",
        "pdf": "pdfs/subassemblies/glaze_spray_booth_subassembly_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
