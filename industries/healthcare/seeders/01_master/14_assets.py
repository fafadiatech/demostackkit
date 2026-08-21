"""
Seeder: in-house Asset Register for Healthcare & Pharma.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Ambulance", "Cold Storage", "Diagnostic Equipment", "Patient Monitor"]

ASSETS = [
    {
        "asset_name": "Diagnostic Imaging Unit",
        "category": "Diagnostic Equipment",
        "location": "Diagnostics Center",
        "gross_purchase_amount": 4800000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Ambulance AMB-1",
        "category": "Ambulance",
        "location": "Main Facility",
        "gross_purchase_amount": 2600000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Cold Storage Unit",
        "category": "Cold Storage",
        "location": "Pharmacy",
        "gross_purchase_amount": 720000,
        "purchase_days_ago": 400,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Patient Monitor Fleet",
        "category": "Patient Monitor",
        "location": "Main Facility",
        "gross_purchase_amount": 540000,
        "purchase_days_ago": 300,
        "useful_life_years": 6,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
