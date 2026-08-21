"""
Seeder: in-house Asset Register for Electrical Equipment Manufacturing.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Delivery Truck", "Forklift", "Test Rig", "Winding Machine"]

ASSETS = [
    {
        "asset_name": "CNC Winding Machine",
        "category": "Winding Machine",
        "location": "Plant Floor",
        "gross_purchase_amount": 2400000,
        "purchase_days_ago": 420,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Testing Rig TR-1",
        "category": "Test Rig",
        "location": "QC Lab",
        "gross_purchase_amount": 680000,
        "purchase_days_ago": 400,
        "useful_life_years": 6,
    },
    {
        "asset_name": "Forklift FL-03",
        "category": "Forklift",
        "location": "Warehouse",
        "gross_purchase_amount": 600000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Delivery Truck DT-3",
        "category": "Delivery Truck",
        "location": "Dispatch Yard",
        "gross_purchase_amount": 1900000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
