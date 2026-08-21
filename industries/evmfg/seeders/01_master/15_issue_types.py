"""
Seeder: Support Issue Types for EV Manufacturing.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Battery Performance Issue",
    "Charging Fault",
    "Delivery Delay",
    "Warranty Repair Request",
    "Software Update Issue",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
