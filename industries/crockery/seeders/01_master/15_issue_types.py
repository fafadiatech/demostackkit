"""
Seeder: Support Issue Types for Crockery Manufacturing.

Shared engine lives in ``demostackkit.seeder.support_seeder``.
"""

from __future__ import annotations

from demostackkit.seeder.support_seeder import IssueTypeSeeder as _IssueTypeSeederBase

ISSUE_TYPES = [
    "Cracked or Chipped Product",
    "Glaze Defect",
    "Delivery Delay",
    "Billing Dispute",
    "Return Request",
]


class IssueTypeSeeder(_IssueTypeSeederBase):
    ISSUE_TYPES = ISSUE_TYPES
