"""
Seeder: Payroll setup for Chemical Manufacturing.

Turns the shop-floor workforce created by the Employee seeder into a payable
one. Component and structure shapes come from ``demostackkit.seeder.payroll``;
this file only carries what a chemical plant pays each role.

Idempotent — existing components, structures and assignments are left alone.
"""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

#: Mid-market Indian speciality chemicals rates.
ANNUAL_CTC = {
    "Production Manager": 1_140_000,
    "Production Supervisor": 660_000,
    "Shift Supervisor": 576_000,
    "Maintenance Technician": 420_000,
    "Quality Analyst": 456_000,
    "Plant Operator": 384_000,
    "Process Operator": 336_000,
    "Machine Operator": 312_000,
    "Packaging Operator": 264_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
