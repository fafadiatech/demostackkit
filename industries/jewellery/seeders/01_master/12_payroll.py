"""Seeder: Payroll setup for Jewellery Manufacturing."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Production Manager": 1_140_000,
    "Karigar Supervisor": 600_000,
    "Melting Furnace Operator": 384_000,
    "Rolling Mill Operator": 360_000,
    "Casting Technician": 396_000,
    "Filing & Shaping Artisan": 420_000,
    "Stone Setter": 456_000,
    "Polishing Artisan": 336_000,
    "Hallmarking Technician": 360_000,
    "QC Inspector": 384_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
