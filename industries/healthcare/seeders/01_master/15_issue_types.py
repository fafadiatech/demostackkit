"""
Seeder: Support Issue Types for Healthcare & Pharma.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Equipment Malfunction",
    "Delayed Report Delivery",
    "Billing Dispute",
    "Product Quality Complaint",
    "Cold Chain Deviation",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
