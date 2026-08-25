"""
Seeder: in-house Asset Register for Ingredient Trading & Distribution.

Categories and equipment come from the warehouse, weighing and dispatch fleet.
Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = [
    "Warehouse Forklift",
    "Pallet Truck Fleet",
    "Weighbridge",
    "Racking & Silo System",
    "Cold Storage Unit",
]

ASSETS = [
    {
        "asset_name": "Forklift MD-01",
        "category": "Warehouse Forklift",
        "location": "Mundra Depot",
        "gross_purchase_amount": 950_000,
        "purchase_days_ago": 400,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Electric Pallet Truck Fleet",
        "category": "Pallet Truck Fleet",
        "location": "Mundra Depot",
        "gross_purchase_amount": 320_000,
        "purchase_days_ago": 300,
        "useful_life_years": 6,
    },
    {
        "asset_name": "Weighbridge WB-02",
        "category": "Weighbridge",
        "location": "Kandla Depot",
        "gross_purchase_amount": 1_400_000,
        "purchase_days_ago": 420,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Bulk Storage Racking Bay A",
        "category": "Racking & Silo System",
        "location": "Mundra Depot",
        "gross_purchase_amount": 560_000,
        "purchase_days_ago": 400,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Cold Storage Chamber CS-01",
        "category": "Cold Storage Unit",
        "location": "Chennai Regional Godown",
        "gross_purchase_amount": 1_850_000,
        "purchase_days_ago": 200,
        "useful_life_years": 10,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
