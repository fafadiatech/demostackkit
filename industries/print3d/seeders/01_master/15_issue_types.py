"""
Seeder: Support Issue Types for 3D Printing Services.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Print Defect",
    "Material Quality Issue",
    "Delayed Delivery",
    "Billing Dispute",
    "File or Design Support",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
