"""
Seeder: in-house Asset Register for Jewellery Manufacturing.

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Casting Machine", "Delivery Vehicle", "Polishing Machine", "Security Vault"]

ASSETS = [
    {
        "asset_name": "Casting Machine CM-2",
        "category": "Casting Machine",
        "location": "Workshop",
        "gross_purchase_amount": 180000,
        "purchase_days_ago": 420,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Polishing Machine PM-1",
        "category": "Polishing Machine",
        "location": "Workshop",
        "gross_purchase_amount": 62000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
    {
        "asset_name": "Vault",
        "category": "Security Vault",
        "location": "Head Office",
        "gross_purchase_amount": 95000,
        "purchase_days_ago": 420,
        "useful_life_years": 20,
    },
    {
        "asset_name": "Delivery Vehicle DV-3",
        "category": "Delivery Vehicle",
        "location": "Head Office",
        "gross_purchase_amount": 110000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
