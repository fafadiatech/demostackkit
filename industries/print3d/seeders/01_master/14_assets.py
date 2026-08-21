"""
Seeder: in-house Asset Register for 3D Printing Services.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["3D Printer", "Delivery Van", "Post-Processing Station"]

ASSETS = [
    {
        "asset_name": "Industrial 3D Printer P-1",
        "category": "3D Printer",
        "location": "Print Floor",
        "gross_purchase_amount": 45000,
        "purchase_days_ago": 420,
        "useful_life_years": 6,
    },
    {
        "asset_name": "CNC Post-Processing Station",
        "category": "Post-Processing Station",
        "location": "Print Floor",
        "gross_purchase_amount": 18000,
        "purchase_days_ago": 400,
        "useful_life_years": 6,
    },
    {
        "asset_name": "Delivery Van DV-6",
        "category": "Delivery Van",
        "location": "Warehouse",
        "gross_purchase_amount": 28000,
        "purchase_days_ago": 420,
        "useful_life_years": 7,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
