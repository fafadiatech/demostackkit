"""
Seeder: in-house Asset Register for Automobile Dealership & Service.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Courtesy Vehicle", "Diagnostic Equipment", "Service Lift", "Tow Truck"]

ASSETS = [
    {
        "asset_name": "Service Bay Lift 1",
        "category": "Service Lift",
        "location": "Service Center",
        "gross_purchase_amount": 450000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Diagnostic Scanner Fleet",
        "category": "Diagnostic Equipment",
        "location": "Service Center",
        "gross_purchase_amount": 320000,
        "purchase_days_ago": 250,
        "useful_life_years": 5,
    },
    {
        "asset_name": "Tow Truck TT-1",
        "category": "Tow Truck",
        "location": "Service Center",
        "gross_purchase_amount": 1400000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Courtesy Car Fleet",
        "category": "Courtesy Vehicle",
        "location": "Showroom",
        "gross_purchase_amount": 900000,
        "purchase_days_ago": 400,
        "useful_life_years": 6,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
