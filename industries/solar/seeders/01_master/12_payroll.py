"""Seeder: Payroll setup for Solar Energy."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Production Manager": 1_140_000,
    "Installation Supervisor": 600_000,
    "Panel Assembly Technician": 384_000,
    "Cable Technician": 360_000,
    "Inverter Technician": 420_000,
    "Commissioning Engineer": 660_000,
    "QC Inspector": 420_000,
    "Site Safety Officer": 480_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
