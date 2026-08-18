"""Seeder: Payroll setup for Electrical Equipment Manufacturing."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Production Manager": 1_140_000,
    "Shop Floor Supervisor": 576_000,
    "Coil Winding Technician": 396_000,
    "Core Assembly Technician": 384_000,
    "Tank Fabricator": 420_000,
    "Oil Filling Operator": 336_000,
    "HV Test Engineer": 600_000,
    "Switchgear Assembler": 408_000,
    "QC Inspector": 420_000,
    "Dispatch Operator": 300_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
