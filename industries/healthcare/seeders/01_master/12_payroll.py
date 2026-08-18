"""Seeder: Payroll setup for Healthcare & Pharma."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Hospital Administrator": 1_440_000,
    "Pharmacist": 720_000,
    "Lab Technician": 480_000,
    "Staff Nurse": 540_000,
    "Store Manager": 600_000,
    "Billing Executive": 420_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
