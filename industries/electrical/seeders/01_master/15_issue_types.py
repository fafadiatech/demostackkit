"""
Seeder: Support Issue Types for Electrical Equipment Manufacturing.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Equipment Malfunction",
    "Insulation Failure",
    "Delivery Delay",
    "Billing Dispute",
    "Installation Support",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
