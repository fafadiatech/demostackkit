"""
Seeder: Support Issue Types for Ingredient Manufacturing.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Batch Quality Deviation",
    "Specification Non-conformance",
    "Equipment Malfunction",
    "Delivery Delay",
    "Documentation Request",
    "Billing Dispute",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
