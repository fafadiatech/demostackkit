"""
Seeder: Support Issue Types for Garment Manufacturing.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Stitching Defect",
    "Size Mismatch",
    "Delivery Delay",
    "Billing Dispute",
    "Fabric Quality Complaint",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
