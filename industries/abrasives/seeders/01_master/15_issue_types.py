"""
Seeder: Support Issue Types for Alpha Abrasives.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Wheel Breakage Complaint",
    "Machine Malfunction",
    "Delivery Delay",
    "Billing Dispute",
    "Spare Parts Request",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
