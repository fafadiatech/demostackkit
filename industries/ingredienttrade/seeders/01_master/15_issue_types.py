"""
Seeder: Support Issue Types for Ingredient Trading & Distribution.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Delayed Shipment",
    "Contamination / Quality Complaint",
    "Short Weight Delivery",
    "Billing Discrepancy",
    "Return / Rejection Request",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
