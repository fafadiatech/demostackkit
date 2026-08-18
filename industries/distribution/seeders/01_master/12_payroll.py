"""Seeder: Payroll setup for FMCG Distribution."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Warehouse Manager": 840_000,
    "Dispatch Supervisor": 540_000,
    "Warehouse Picker": 312_000,
    "Delivery Driver": 336_000,
    "Sales Representative": 480_000,
    "Accounts Executive": 420_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
