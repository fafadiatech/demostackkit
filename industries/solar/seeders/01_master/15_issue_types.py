"""
Seeder: Support Issue Types for Solar Energy Manufacturing.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Panel Underperformance",
    "Installation Issue",
    "Delivery Delay",
    "Billing Dispute",
    "Warranty Repair Request",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
