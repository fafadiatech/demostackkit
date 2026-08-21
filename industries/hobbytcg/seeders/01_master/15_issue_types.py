"""
Seeder: Support Issue Types for Hobby Shop & TCG Retail.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Damaged Item on Arrival",
    "Missing Item in Order",
    "Delayed Shipment",
    "Billing Dispute",
    "Product Authenticity Question",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
