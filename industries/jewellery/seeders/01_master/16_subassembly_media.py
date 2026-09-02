"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for jewellery.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-PRONGSET-01",
        "image": "images/subassemblies/prong_setting_subassembly.jpg",
        "pdf": "pdfs/subassemblies/prong_setting_subassembly_spec.pdf",
    },
    {
        "item_code": "SA-CLASP-01",
        "image": "images/subassemblies/clasp_module.jpg",
        "pdf": "pdfs/subassemblies/clasp_module_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
