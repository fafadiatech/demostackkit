"""Seeder: Payroll setup for 3D Printing Services (US hourly payroll)."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

#: US print-farm rates — one Salary Structure per designation (hourly/timesheet).
ANNUAL_CTC = {
    "Production Manager": 120_000,
    "Print Floor Supervisor": 75_000,
    "FDM Print Technician": 52_000,
    "SLA Print Technician": 55_000,
    "Post-Processing Technician": 48_000,
    "Finishing Technician": 46_000,
    "QC Inspector": 58_000,
    "Shipping Associate": 42_000,
}

FALLBACK_CTC = 45_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
