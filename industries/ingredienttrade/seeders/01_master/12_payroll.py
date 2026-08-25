"""Seeder: Payroll setup for Ingredient Trading & Distribution."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Warehouse Manager": 900_000,
    "Procurement Executive": 660_000,
    "Dispatch Supervisor": 540_000,
    "Quality & Compliance Coordinator": 600_000,
    "Sales Executive": 480_000,
    "Accounts Executive": 420_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
