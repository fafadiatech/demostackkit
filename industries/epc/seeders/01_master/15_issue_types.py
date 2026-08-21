"""
Seeder: Support Issue Types for EPC (Engineering, Procurement & Construction).

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Site Safety Concern",
    "Schedule Delay",
    "Material Shortage",
    "Billing Dispute",
    "Change Order Request",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
