"""Seeder: Payroll setup for Garment Manufacturing."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Production Manager": 1_140_000,
    "Floor Supervisor": 576_000,
    "Cutting Master": 420_000,
    "Sewing Operator": 312_000,
    "Overlock Operator": 300_000,
    "Button Machine Operator": 288_000,
    "Pressing Operator": 276_000,
    "QC Checker": 360_000,
    "Packaging Operator": 264_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
