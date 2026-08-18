"""Seeder: Payroll setup for EV Manufacturing."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Production Manager": 1_140_000,
    "Line Supervisor": 660_000,
    "Battery Assembly Technician": 480_000,
    "Pack Integration Engineer": 720_000,
    "Motor Assembly Technician": 456_000,
    "Chassis Welder": 420_000,
    "Body Fitment Technician": 396_000,
    "EV Electrical Technician": 540_000,
    "PDI Test Engineer": 600_000,
    "QC Inspector": 456_000,
    "Dispatch Operator": 312_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
