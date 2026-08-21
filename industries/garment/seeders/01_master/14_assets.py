"""
Seeder: in-house Asset Register for Garment Manufacturing.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Cutting Machine", "Delivery Truck", "Forklift", "Sewing Line"]

ASSETS = [
    {
        "asset_name": "Industrial Sewing Line",
        "category": "Sewing Line",
        "location": "Plant Floor",
        "gross_purchase_amount": 1400000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Cutting Machine CM-1",
        "category": "Cutting Machine",
        "location": "Plant Floor",
        "gross_purchase_amount": 850000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Forklift FL-05",
        "category": "Forklift",
        "location": "Warehouse",
        "gross_purchase_amount": 600000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Delivery Truck DT-5",
        "category": "Delivery Truck",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 1800000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
