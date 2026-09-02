"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for chemical.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-REACTOR-01",
        "image": "images/subassemblies/reactor_agitator_subassembly.jpg",
        "pdf": "pdfs/subassemblies/reactor_agitator_subassembly_spec.pdf",
    },
    {
        "item_code": "SA-VALVEMANIFOLD-01",
        "image": "images/subassemblies/valve_manifold_module.jpg",
        "pdf": "pdfs/subassemblies/valve_manifold_module_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
