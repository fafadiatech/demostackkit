"""Seeder: Payroll setup for EPC."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Project Manager": 1_560_000,
    "Site Engineer": 720_000,
    "Quantity Surveyor": 660_000,
    "Safety Officer": 540_000,
    "Foreman": 480_000,
    "Electrician": 384_000,
    "Plumber": 360_000,
    "Carpenter": 348_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
