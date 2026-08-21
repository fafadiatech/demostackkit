"""
Seeder: Support Issue Types for FMCG Distribution.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Delayed Delivery",
    "Damaged Goods on Arrival",
    "Short Shipment",
    "Billing Discrepancy",
    "Return Request",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
