"""
Seeder: Support Issue Types for Drone Manufacturing.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Flight Malfunction",
    "Firmware Issue",
    "Battery Defect",
    "Delivery Delay",
    "Warranty Repair Request",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
