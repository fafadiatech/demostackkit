"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for abrasives.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-WHEELHUB-01",
        "image": "images/subassemblies/wheel_hub_assembly.jpg",
        "pdf": "pdfs/subassemblies/wheel_hub_assembly_spec.pdf",
    },
    {
        "item_code": "SA-BELTMOD-01",
        "image": "images/subassemblies/coated_belt_module.jpg",
        "pdf": "pdfs/subassemblies/coated_belt_module_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
