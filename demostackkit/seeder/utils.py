"""
Shared utility functions for seeders.

Import from here instead of defining locally in each seeder file.
"""

from __future__ import annotations

from datetime import date, timedelta


def parse_relative_date(value: str) -> date:
    """Parse -180d style relative dates or YYYY-MM-DD absolute dates.

    Examples:
        parse_relative_date("-180d")  # 180 days ago
        parse_relative_date("2024-01-15")  # fixed date
    """
    today = date.today()
    if value.startswith("-") and value.endswith("d"):
        days = int(value[1:-1])
        return today - timedelta(days=days)
    return date.fromisoformat(value)
