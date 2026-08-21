"""
Seeder: in-house Asset Register for Chemical Manufacturing.

Categories and equipment come from the plant floor: reactors, boilers,
material handling and dispatch. Shared engine lives in
``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = [
    "Reactor Vessel",
    "Boiler",
    "Forklift",
    "Delivery Tanker",
    "Laboratory Equipment",
]

ASSETS = [
    {
        "asset_name": "Reactor R-101",
        "category": "Reactor Vessel",
        "location": "Plant Floor",
        "gross_purchase_amount": 4_500_000,
        "purchase_days_ago": 420,
        "useful_life_years": 15,
    },
    {
        "asset_name": "Steam Boiler B-1",
        "category": "Boiler",
        "location": "Plant Floor",
        "gross_purchase_amount": 1_800_000,
        "purchase_days_ago": 380,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Forklift FL-02",
        "category": "Forklift",
        "location": "Warehouse",
        "gross_purchase_amount": 650_000,
        "purchase_days_ago": 400,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Delivery Tanker DT-1",
        "category": "Delivery Tanker",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 3_200_000,
        "purchase_days_ago": 400,
        "useful_life_years": 10,
    },
    {
        "asset_name": "QC Lab Analyzer",
        "category": "Laboratory Equipment",
        "location": "QC Lab",
        "gross_purchase_amount": 950_000,
        "purchase_days_ago": 300,
        "useful_life_years": 7,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
