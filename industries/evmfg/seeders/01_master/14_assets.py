"""
Seeder: in-house Asset Register for EV Manufacturing.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Assembly Line", "Delivery Truck", "Forklift", "Welding Robot"]

ASSETS = [
    {
        "asset_name": "Battery Pack Assembly Line",
        "category": "Assembly Line",
        "location": "Plant Floor",
        "gross_purchase_amount": 6500000,
        "purchase_days_ago": 420,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Robotic Welding Arm",
        "category": "Welding Robot",
        "location": "Plant Floor",
        "gross_purchase_amount": 4200000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Forklift FL-04",
        "category": "Forklift",
        "location": "Warehouse",
        "gross_purchase_amount": 640000,
        "purchase_days_ago": 400,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Delivery Truck DT-4",
        "category": "Delivery Truck",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 2200000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
