"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for ingredientmfg.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-MIXHEAD-01",
        "image": "images/subassemblies/mixing_head_subassembly.jpg",
        "pdf": "pdfs/subassemblies/mixing_head_subassembly_spec.pdf",
    },
    {
        "item_code": "SA-DOSEPUMP-01",
        "image": "images/subassemblies/dosing_pump_module.jpg",
        "pdf": "pdfs/subassemblies/dosing_pump_module_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
