"""Seeder: Payroll setup for Alpha Abrasives (India monthly payroll convention)."""

from __future__ import annotations

from demostackkit.seeder.payroll_seeder import PayrollSeeder as _PayrollSeederBase

ANNUAL_CTC = {
    "Production Manager": 1_020_000,
    "Shop Floor Supervisor": 540_000,
    "Mixing & Bonding Technician": 348_000,
    "Press Operator": 372_000,
    "Curing Oven Operator": 336_000,
    "QC Inspector": 396_000,
    "Packing Operator": 288_000,
    "Import & Procurement Executive": 480_000,
    "Traded Goods Warehouse Executive": 360_000,
    "Dispatch Operator": 300_000,
}

FALLBACK_CTC = 300_000


class PayrollSeeder(_PayrollSeederBase):
    ANNUAL_CTC = ANNUAL_CTC
    FALLBACK_CTC = FALLBACK_CTC
