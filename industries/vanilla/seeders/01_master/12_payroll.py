"""Seeder: Payroll setup for Vanilla demo (US hourly payroll)."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "General Manager": 95_000,
    "Accountant": 62_000,
    "Sales Representative": 52_000,
    "Warehouse Associate": 38_000,
}

FALLBACK_CTC = 40_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
