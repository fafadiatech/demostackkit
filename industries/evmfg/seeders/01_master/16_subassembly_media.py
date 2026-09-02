"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for evmfg.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-BATTPACK-01",
        "image": "images/subassemblies/battery_pack_module.jpg",
        "pdf": "pdfs/subassemblies/battery_pack_module_spec.pdf",
    },
    {
        "item_code": "SA-MOTORDRIVE-01",
        "image": "images/subassemblies/motor_drive_subassembly.jpg",
        "pdf": "pdfs/subassemblies/motor_drive_subassembly_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
