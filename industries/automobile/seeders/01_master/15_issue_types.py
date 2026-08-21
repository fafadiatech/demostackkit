"""
Seeder: Support Issue Types for Automobile Dealership & Service.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Vehicle Not Starting",
    "Warranty Repair Dispute",
    "Delayed Service Delivery",
    "Parts Backorder",
    "Billing Query",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
