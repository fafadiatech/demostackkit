"""Seeder: Payroll setup for Jewellery Manufacturing."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Production Manager": 114_000,
    "Karigar Supervisor": 60_000,
    "Melting Furnace Operator": 38_400,
    "Rolling Mill Operator": 36_000,
    "Casting Technician": 39_600,
    "Filing & Shaping Artisan": 42_000,
    "Stone Setter": 45_600,
    "Polishing Artisan": 33_600,
    "Hallmarking Technician": 36_000,
    "QC Inspector": 38_400,
}

FALLBACK_CTC = 30_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
