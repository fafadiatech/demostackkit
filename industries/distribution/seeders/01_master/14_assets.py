"""
Seeder: in-house Asset Register for FMCG Distribution.

Categories and equipment come from the warehouse and delivery fleet. Shared
engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = [
    "Warehouse Forklift",
    "Delivery Van",
    "Racking System",
    "Barcode Scanner Fleet",
]

ASSETS = [
    {
        "asset_name": "Forklift WH-01",
        "category": "Warehouse Forklift",
        "location": "Main Warehouse",
        "gross_purchase_amount": 850_000,
        "purchase_days_ago": 400,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Delivery Van DV-04",
        "category": "Delivery Van",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 1_100_000,
        "purchase_days_ago": 420,
        "useful_life_years": 7,
    },
    {
        "asset_name": "Delivery Van DV-05",
        "category": "Delivery Van",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 1_150_000,
        "purchase_days_ago": 300,
        "useful_life_years": 7,
    },
    {
        "asset_name": "Pallet Racking Bay A",
        "category": "Racking System",
        "location": "Main Warehouse",
        "gross_purchase_amount": 420_000,
        "purchase_days_ago": 400,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Handheld Scanner Fleet",
        "category": "Barcode Scanner Fleet",
        "location": "Main Warehouse",
        "gross_purchase_amount": 180_000,
        "purchase_days_ago": 200,
        "useful_life_years": 4,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
