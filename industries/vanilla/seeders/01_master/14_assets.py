"""
Seeder: a small in-house Asset Register for the Vanilla demo company.

vanilla is otherwise a deliberate clean slate (no items, customers or
transactions), but a couple of internal fixed assets — a vehicle and some
office equipment — don't carry the same "domain master data" weight, so it
still gets an Asset Register. Shared engine lives in
``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = [
    "Company Vehicle",
    "Office Equipment",
]

ASSETS = [
    {
        "asset_name": "Company Van",
        "category": "Company Vehicle",
        "location": "Head Office",
        "gross_purchase_amount": 28_000,
        "purchase_days_ago": 400,
        "useful_life_years": 6,
    },
    {
        "asset_name": "Office Laptop Fleet",
        "category": "Office Equipment",
        "location": "Head Office",
        "gross_purchase_amount": 12_000,
        "purchase_days_ago": 250,
        "useful_life_years": 3,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
