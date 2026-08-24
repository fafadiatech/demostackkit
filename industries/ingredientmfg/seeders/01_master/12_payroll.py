"""
Seeder: Payroll setup for Ingredient Manufacturing.

Turns the shop-floor workforce created by the Employee seeder into a payable
one. Component and structure shapes come from ``demostackkit.seeder.payroll``;
this file only carries what an ingredient plant pays each role.

Idempotent — existing components, structures and assignments are left alone.
"""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

#: Mid-market Indian food/nutraceutical ingredient manufacturer rates.
ANNUAL_CTC = {
    "Production Manager": 1_150_000,
    "Production Supervisor": 650_000,
    "Shift Supervisor": 570_000,
    "Microbiologist": 500_000,
    "QC Chemist": 480_000,
    "Maintenance Technician": 410_000,
    "Plant Operator": 380_000,
    "Extraction Operator": 340_000,
    "Packaging Operator": 260_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
