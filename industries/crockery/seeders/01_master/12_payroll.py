"""Seeder: Payroll setup for Crockery Manufacturing."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Production Manager": 1_140_000,
    "Kiln Supervisor": 576_000,
    "Throwing Artisan": 360_000,
    "Casting Operator": 336_000,
    "Trimming & Finishing Artisan": 348_000,
    "Glazing Technician": 324_000,
    "Kiln Operator": 384_000,
    "QC Inspector": 396_000,
    "Packaging Operator": 264_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
