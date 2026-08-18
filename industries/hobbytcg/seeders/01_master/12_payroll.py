"""Seeder: Payroll setup for Hobby Shop & TCG Retailer (US hourly payroll)."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Store Manager": 65_000,
    "Assistant Manager": 48_000,
    "Sales Associate": 32_000,
    "Inventory Specialist": 42_000,
    "Events Coordinator": 40_000,
}

FALLBACK_CTC = 35_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
