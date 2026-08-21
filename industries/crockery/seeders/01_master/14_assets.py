"""
Seeder: in-house Asset Register for Crockery Manufacturing.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Delivery Truck", "Forklift", "Glazing Line", "Kiln"]

ASSETS = [
    {
        "asset_name": "Kiln K-1",
        "category": "Kiln",
        "location": "Plant Floor",
        "gross_purchase_amount": 1600000,
        "purchase_days_ago": 420,
        "useful_life_years": 15,
    },
    {
        "asset_name": "Glazing Line",
        "category": "Glazing Line",
        "location": "Plant Floor",
        "gross_purchase_amount": 950000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Forklift FL-01",
        "category": "Forklift",
        "location": "Warehouse",
        "gross_purchase_amount": 620000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Delivery Truck DT-2",
        "category": "Delivery Truck",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 2100000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
