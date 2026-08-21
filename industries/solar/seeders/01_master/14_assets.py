"""
Seeder: in-house Asset Register for Solar Energy Manufacturing.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Assembly Line", "Forklift", "Installation Truck", "Test Rig"]

ASSETS = [
    {
        "asset_name": "Panel Assembly Line",
        "category": "Assembly Line",
        "location": "Plant Floor",
        "gross_purchase_amount": 3600000,
        "purchase_days_ago": 420,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Testing Rig TR-2",
        "category": "Test Rig",
        "location": "QC Lab",
        "gross_purchase_amount": 640000,
        "purchase_days_ago": 400,
        "useful_life_years": 6,
    },
    {
        "asset_name": "Forklift FL-06",
        "category": "Forklift",
        "location": "Warehouse",
        "gross_purchase_amount": 600000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Installation Truck IT-1",
        "category": "Installation Truck",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 1700000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
