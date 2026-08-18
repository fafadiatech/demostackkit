"""Seeder: Payroll setup for Drones Manufacturing."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Production Manager": 1_140_000,
    "Assembly Supervisor": 600_000,
    "PCB Assembly Technician": 420_000,
    "Frame Assembly Technician": 396_000,
    "Avionics Technician": 540_000,
    "Firmware Calibration Engineer": 720_000,
    "Flight Test Pilot": 660_000,
    "QC Inspector": 456_000,
    "Packaging Operator": 288_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
