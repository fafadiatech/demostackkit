"""
Unit tests for the pure opening-stock helpers in demostackkit.seeder.utils.

The quantities produced here go straight onto an ERPNext "Opening Stock" Stock
Reconciliation, so they must be whole, positive, and stable across runs — a
`demostackkit reset` has to reproduce the same opening balance sheet.
"""

from __future__ import annotations

import random
from datetime import date

import pytest

from demostackkit.seeder.utils import (
    FINISHED_GOODS_QTY_SCALE,
    OPENING_STOCK_QTY_BANDS,
    opening_stock_date,
    opening_stock_qty,
)


def _rng(seed: int = 20240104) -> random.Random:
    return random.Random(seed)


@pytest.mark.unit
class TestOpeningStockDate:
    def test_posts_the_day_before_the_range(self) -> None:
        assert opening_stock_date(date(2026, 2, 19)) == date(2026, 2, 18)

    def test_crosses_month_and_year_boundaries(self) -> None:
        assert opening_stock_date(date(2026, 1, 1)) == date(2025, 12, 31)
        assert opening_stock_date(date(2026, 3, 1)) == date(2026, 2, 28)


@pytest.mark.unit
class TestOpeningStockQty:
    def test_deterministic_for_a_given_seed(self) -> None:
        first = [opening_stock_qty(rate, _rng()) for rate in (45, 12500, 850000)]
        second = [opening_stock_qty(rate, _rng()) for rate in (45, 12500, 850000)]
        assert first == second

    def test_quantities_are_whole_and_positive(self) -> None:
        rng = _rng()
        # Spans the real range of seeded valuation rates: 0.50 filament to a
        # 2,200,000 machine tool.
        for rate in (0, 0.5, 4.0, 22.0, 185.0, 2800.0, 19500.0, 185000.0, 2200000.0):
            for fg in (False, True):
                qty = opening_stock_qty(rate, rng, is_finished_good=fg)
                assert isinstance(qty, int)
                assert qty >= 1

    def test_cheaper_items_open_with_more_stock(self) -> None:
        # Compared band-to-band rather than draw-to-draw: within a band the RNG
        # decides, but a bulk chemical must never open below a machine tool.
        cheap = min(opening_stock_qty(2.5, _rng(s)) for s in range(50))
        dear = max(opening_stock_qty(185000, _rng(s)) for s in range(50))
        assert cheap > dear

    def test_finished_goods_open_lighter_than_raw_material(self) -> None:
        for seed in range(25):
            rate = 4500.0
            raw = opening_stock_qty(rate, _rng(seed))
            finished = opening_stock_qty(rate, _rng(seed), is_finished_good=True)
            assert finished <= raw

    def test_scale_is_a_reduction(self) -> None:
        assert 0 < FINISHED_GOODS_QTY_SCALE < 1

    def test_bands_are_ascending_and_total(self) -> None:
        ceilings = [ceiling for ceiling, _, _ in OPENING_STOCK_QTY_BANDS]
        assert ceilings == sorted(ceilings)
        assert ceilings[-1] == float("inf")
        for _, low, high in OPENING_STOCK_QTY_BANDS:
            assert 0 < low <= high

    def test_scale_shrinks_quantities_without_zeroing_them(self) -> None:
        # hobbytcg's 0.03: a USD 45,000 graded card must still open with one copy.
        for rate in (4.5, 72.0, 420.0, 8500.0, 45000.0):
            for seed in range(10):
                scaled = opening_stock_qty(rate, _rng(seed), scale=0.03)
                full = opening_stock_qty(rate, _rng(seed))
                assert 1 <= scaled <= full

    def test_scale_of_one_is_the_default(self) -> None:
        assert opening_stock_qty(185.0, _rng(), scale=1.0) == opening_stock_qty(185.0, _rng())

    def test_missing_rate_falls_into_the_cheapest_band(self) -> None:
        # A zero-rated item is unpriced, not free; guessing "cheap" keeps its
        # opening quantity in the bulk range rather than at 2 units.
        _, low, _ = OPENING_STOCK_QTY_BANDS[0]
        assert opening_stock_qty(0, _rng()) >= low
