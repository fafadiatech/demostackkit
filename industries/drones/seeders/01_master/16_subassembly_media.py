"""
Seeder: Sub Assembly item media (images + PDF spec sheets) for drones.

Shared engine lives in ``demostackkit.seeder.subassembly_seeder``.
Asset licenses/sources: see ../../assets/ATTRIBUTION.md
"""

from __future__ import annotations

from demostackkit.seeder.subassembly_seeder import ItemMediaSeeder as _ItemMediaSeederBase

ITEM_MEDIA = [
    {
        "item_code": "SA-FCMOD-01",
        "image": "images/subassemblies/flight_controller_module.jpg",
        "pdf": "pdfs/subassemblies/flight_controller_module_spec.pdf",
    },
    {
        "item_code": "SA-MOTORESC-01",
        "image": "images/subassemblies/motor_esc_subassembly.jpg",
        "pdf": "pdfs/subassemblies/motor_esc_subassembly_spec.pdf",
    },
]


class ItemMediaSeeder(_ItemMediaSeederBase):
    ITEM_MEDIA = ITEM_MEDIA
