"""
Seeder: Support Issue Types for Jewellery Manufacturing.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Product Quality Defect",
    "Sizing Issue",
    "Delivery Delay",
    "Billing Dispute",
    "Certification Request",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
