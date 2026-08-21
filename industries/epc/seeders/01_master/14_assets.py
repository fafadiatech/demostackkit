"""
Seeder: in-house Asset Register for EPC (Engineering, Procurement & Construction).

Shared engine lives in ``demostackkit.seeder.asset_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.asset_seeder import (
    AssetCategorySeeder as _AssetCategorySeederBase,
)
from demostackkit.seeder.asset_seeder import AssetSeeder as _AssetSeederBase

ASSET_CATEGORIES = ["Crane", "Excavator", "Project Vehicle", "Site Office"]

ASSETS = [
    {
        "asset_name": "Site Crane SC-1",
        "category": "Crane",
        "location": "Project Site",
        "gross_purchase_amount": 5500000,
        "purchase_days_ago": 420,
        "useful_life_years": 15,
    },
    {
        "asset_name": "Excavator EX-2",
        "category": "Excavator",
        "location": "Project Site",
        "gross_purchase_amount": 3800000,
        "purchase_days_ago": 420,
        "useful_life_years": 12,
    },
    {
        "asset_name": "Site Office Container",
        "category": "Site Office",
        "location": "Project Site",
        "gross_purchase_amount": 380000,
        "purchase_days_ago": 420,
        "useful_life_years": 10,
    },
    {
        "asset_name": "Project Vehicle PV-4",
        "category": "Project Vehicle",
        "location": "Site Office",
        "gross_purchase_amount": 1200000,
        "purchase_days_ago": 420,
        "useful_life_years": 8,
    },
]


class AssetCategorySeeder(_AssetCategorySeederBase):
    ASSET_CATEGORIES = ASSET_CATEGORIES


class AssetSeeder(_AssetSeederBase):
    ASSETS = ASSETS
