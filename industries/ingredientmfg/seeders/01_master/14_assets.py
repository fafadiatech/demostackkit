"""
Seeder: in-house Asset Register for Ingredient Manufacturing.

Categories and equipment come from the plant floor: extraction vessels,
dryers, material handling and the QC lab. Shared engine lives in
``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = [
    "Extraction Vessel",
    "Dryer",
    "Forklift",
    "Delivery Van",
    "Laboratory Equipment",
]

ASSETS = [
    {
        "asset_name": "Extraction Vessel EV-101",
        "category": "Extraction Vessel",
        "location": "Plant Floor",
        "gross_purchase_amount": 3_800_000,
        "purchase_days_ago": 410,
        "useful_life_years": 15,
    },
    {
        "asset_name": "Vacuum Dryer VD-1",
        "category": "Dryer",
        "location": "Plant Floor",
        "gross_purchase_amount": 1_600_000,
        "purchase_days_ago": 370,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Forklift FL-01",
        "category": "Forklift",
        "location": "Warehouse",
        "gross_purchase_amount": 650_000,
        "purchase_days_ago": 400,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Delivery Van DV-1",
        "category": "Delivery Van",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 1_200_000,
        "purchase_days_ago": 390,
        "useful_life_years": 10,
    },
    {
        "asset_name": "QC Lab HPLC Analyzer",
        "category": "Laboratory Equipment",
        "location": "QC Lab",
        "gross_purchase_amount": 1_100_000,
        "purchase_days_ago": 300,
        "useful_life_years": 7,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
