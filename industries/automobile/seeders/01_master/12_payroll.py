"""Seeder: Payroll setup for Automobile Dealership & Service."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Service Manager": 960_000,
    "Sales Executive": 540_000,
    "Service Advisor": 480_000,
    "Senior Mechanic": 420_000,
    "Mechanic": 336_000,
    "Parts Executive": 360_000,
    "Receptionist": 264_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
