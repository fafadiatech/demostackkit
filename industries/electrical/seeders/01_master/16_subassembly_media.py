"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for electrical.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-CTRLPANEL-01",
        "image": "images/subassemblies/control_panel_subassembly.jpg",
        "pdf": "pdfs/subassemblies/control_panel_subassembly_spec.pdf",
    },
    {
        "item_code": "SA-HARNESS-01",
        "image": "images/subassemblies/wiring_harness_module.jpg",
        "pdf": "pdfs/subassemblies/wiring_harness_module_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
