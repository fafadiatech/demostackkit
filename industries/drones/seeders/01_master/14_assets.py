"""
Seeder: in-house Asset Register for Drone Manufacturing.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Assembly Robot", "CNC Machine", "Delivery Van", "Test Rig"]

ASSETS = [
    {
        "asset_name": "CNC Machine CNC-2",
        "category": "CNC Machine",
        "location": "Fabrication Floor",
        "gross_purchase_amount": 2800000,
        "purchase_days_ago": 420,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Drone Test Rig",
        "category": "Test Rig",
        "location": "Test Lab",
        "gross_purchase_amount": 750000,
        "purchase_days_ago": 350,
        "useful_life_years": 6,
    },
    {
        "asset_name": "Assembly Line Robot",
        "category": "Assembly Robot",
        "location": "Assembly Floor",
        "gross_purchase_amount": 3200000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Delivery Van DV-1",
        "category": "Delivery Van",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 1050000,
        "purchase_days_ago": 400,
        "useful_life_years": 7,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
