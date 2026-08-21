"""
Seeder: Support Issue Types for Chemical Manufacturing.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Batch Quality Deviation",
    "Equipment Malfunction",
    "Delivery Delay",
    "Documentation Request",
    "Billing Dispute",
    "Safety Concern",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
