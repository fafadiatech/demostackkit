"""
Seeder: in-house Asset Register for Hobby Shop & TCG Retail.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Delivery Van", "POS Terminal", "Store Fixtures"]

ASSETS = [
    {
        "asset_name": "POS Terminal Fleet",
        "category": "POS Terminal",
        "location": "Main Store",
        "gross_purchase_amount": 8000,
        "purchase_days_ago": 300,
        "useful_life_years": 5,
    },
    {
        "asset_name": "Delivery Van DV-2",
        "category": "Delivery Van",
        "location": "Warehouse",
        "gross_purchase_amount": 32000,
        "purchase_days_ago": 420,
        "useful_life_years": 7,
    },
    {
        "asset_name": "Store Display Fixtures",
        "category": "Store Fixtures",
        "location": "Main Store",
        "gross_purchase_amount": 15000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
