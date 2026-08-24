"""
Seeder: in-house Asset Register for Alpha Abrasives.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Mixer", "Hydraulic Press", "Curing Oven", "Balancing Machine", "Forklift"]

ASSETS = [
    {
        "asset_name": "Resin Bond Mixer RM-1",
        "category": "Mixer",
        "location": "Plant Floor",
        "gross_purchase_amount": 1_450_000,
        "purchase_days_ago": 480,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Hydraulic Wheel Press HP-2",
        "category": "Hydraulic Press",
        "location": "Plant Floor",
        "gross_purchase_amount": 2_800_000,
        "purchase_days_ago": 450,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Curing Oven CO-1",
        "category": "Curing Oven",
        "location": "Plant Floor",
        "gross_purchase_amount": 1_950_000,
        "purchase_days_ago": 450,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Wheel Balancing Machine WB-1",
        "category": "Balancing Machine",
        "location": "QC Lab",
        "gross_purchase_amount": 620_000,
        "purchase_days_ago": 400,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Forklift FL-02",
        "category": "Forklift",
        "location": "Warehouse",
        "gross_purchase_amount": 580_000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
