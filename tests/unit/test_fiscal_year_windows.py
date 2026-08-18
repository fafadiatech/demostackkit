"""
Unit tests for demostackkit.seeder.utils.fiscal_year_windows.

The windows produced here are inserted verbatim as ERPNext Fiscal Year records, so
they must satisfy FiscalYear.validate_dates(): end == start + 1 year - 1 day.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from demostackkit.seeder.utils import fiscal_year_windows


def _spans_exactly_one_year(start: date, end: date) -> bool:
    return end == date(start.year + 1, start.month, start.day) - timedelta(days=1)


@pytest.mark.unit
class TestFiscalYearWindows:
    def test_april_start_range_straddling_two_years(self) -> None:
        # The reported chemical case: -180d from 2026-08-18 lands in the previous FY.
        windows = fiscal_year_windows("04-01", date(2026, 2, 19), date(2026, 8, 18))
        assert windows == [
            ("2025-2026", date(2025, 4, 1), date(2026, 3, 31)),
            ("2026-2027", date(2026, 4, 1), date(2027, 3, 31)),
        ]

    def test_calendar_year_start_single_window(self) -> None:
        windows = fiscal_year_windows("01-01", date(2026, 7, 19), date(2026, 8, 18))
        assert windows == [("2026", date(2026, 1, 1), date(2026, 12, 31))]

    def test_range_inside_one_fiscal_year(self) -> None:
        windows = fiscal_year_windows("04-01", date(2026, 5, 1), date(2026, 6, 1))
        assert windows == [("2026-2027", date(2026, 4, 1), date(2027, 3, 31))]

    def test_boundary_dates_are_inclusive(self) -> None:
        # Exactly on the FY start and on the last day of that FY: still one window.
        windows = fiscal_year_windows("04-01", date(2026, 4, 1), date(2027, 3, 31))
        assert windows == [("2026-2027", date(2026, 4, 1), date(2027, 3, 31))]

    def test_reversed_range_is_normalised(self) -> None:
        assert fiscal_year_windows("04-01", date(2026, 8, 18), date(2026, 2, 19)) == (
            fiscal_year_windows("04-01", date(2026, 2, 19), date(2026, 8, 18))
        )

    def test_multi_year_range_has_no_gaps(self) -> None:
        windows = fiscal_year_windows("04-01", date(2023, 1, 1), date(2027, 12, 31))
        assert len(windows) == 6
        for (_, _, prev_end), (_, next_start, _) in zip(windows, windows[1:]):
            assert next_start == prev_end + timedelta(days=1)

    @pytest.mark.parametrize("fy_start", ["01-01", "04-01", "07-01", "10-01", "12-31"])
    def test_every_window_passes_erpnext_validation(self, fy_start: str) -> None:
        windows = fiscal_year_windows(fy_start, date(2024, 3, 5), date(2027, 9, 20))
        assert windows
        for _, start, end in windows:
            assert _spans_exactly_one_year(start, end)

    def test_leap_day_start_is_rejected(self) -> None:
        # 02-29 does not exist in every year, so it can never be a fiscal year start.
        with pytest.raises(ValueError, match="fiscal_year_start"):
            fiscal_year_windows("02-29", date(2026, 1, 1), date(2026, 12, 31))

    def test_malformed_start_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="fiscal_year_start"):
            fiscal_year_windows("13-01", date(2026, 1, 1), date(2026, 12, 31))
