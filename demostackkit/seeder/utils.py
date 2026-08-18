"""
Shared utility functions for seeders.

Import from here instead of defining locally in each seeder file.
"""

from __future__ import annotations

import random as _random_module
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


def fiscal_year_windows(
    fy_start_mmdd: str, first: date, last: date
) -> list[tuple[str, date, date]]:
    """Every ERPNext Fiscal Year window needed to cover [first, last], inclusive.

    Returns (year_label, start_date, end_date) tuples, oldest first. `year_label`
    follows ERPNext's own get_fy_details() convention: "2026" when the window sits
    inside one calendar year, "2026-2027" when it straddles two.

    end is always start + 1 year - 1 day, which is exactly what
    FiscalYear.validate_dates() demands — anything else raises InvalidDates.

    Examples:
        fiscal_year_windows("04-01", date(2026, 2, 19), date(2026, 8, 18))
        # [("2025-2026", 2025-04-01, 2026-03-31), ("2026-2027", 2026-04-01, 2027-03-31)]
    """
    month, day = _parse_mmdd(fy_start_mmdd)
    if first > last:
        first, last = last, first

    windows: list[tuple[str, date, date]] = []
    year = _fy_start_year(month, day, first)
    while True:
        start = date(year, month, day)
        if start > last:
            break
        end = date(year + 1, month, day) - timedelta(days=1)
        label = str(year) if end.year == year else f"{year}-{year + 1}"
        windows.append((label, start, end))
        year += 1
    return windows


def _parse_mmdd(value: str) -> tuple[int, int]:
    """Validate a MM-DD fiscal year start and return (month, day)."""
    try:
        month_str, day_str = value.split("-")
        month, day = int(month_str), int(day_str)
        # 2001 is a non-leap year: a fiscal year start must exist in EVERY year,
        # so 02-29 is rejected here rather than silently shifting some windows.
        date(2001, month, day)
    except ValueError as exc:
        raise ValueError(
            f"Invalid fiscal_year_start {value!r}: expected MM-DD that exists in every year"
        ) from exc
    return month, day


def _fy_start_year(month: int, day: int, when: date) -> int:
    """Calendar year of the fiscal year start for the FY containing `when`."""
    return when.year if (when.month, when.day) >= (month, day) else when.year - 1


def opening_stock_date(range_start: date) -> date:
    """Posting date for opening balances: the day before the first seeded transaction.

    Opening stock must predate every seeded document, otherwise a Stock Entry or
    Delivery Note dated earlier would consume stock that does not exist yet. The
    Fiscal Year seeder widens its coverage with this same function, so the opening
    entry always lands inside a Fiscal Year.
    """
    return range_start - timedelta(days=1)


#: (unit value below which the band applies, min qty, max qty), ascending.
#: Opening quantities are banded by unit value rather than fixed, because item
#: rates across industries span six orders of magnitude — from a 0.50 filament
#: gram to a 2,200,000 machine. A flat range would stock either absurd amounts of
#: capital equipment or a token amount of bulk chemicals.
OPENING_STOCK_QTY_BANDS: tuple[tuple[float, int, int], ...] = (
    (10, 2000, 8000),
    (100, 500, 2500),
    (1_000, 100, 600),
    (10_000, 40, 150),
    (100_000, 8, 30),
    (float("inf"), 2, 6),
)

#: Finished goods sit in stock in smaller numbers than the raw materials they
#: consume — a demo that opens with more finished units than components reads wrong.
FINISHED_GOODS_QTY_SCALE = 0.3


def opening_stock_qty(
    unit_value: float,
    rng: _random_module.Random,
    *,
    is_finished_good: bool = False,
    scale: float = 1.0,
) -> int:
    """Deterministic opening quantity for one item, banded by its unit value.

    The bands key off the magnitude of the valuation rate rather than a fixed
    quantity, so a bulk solvent and a machine tool both open at a plausible
    depth. They assume an industrial operation, though — a hobby retailer holds
    far less of a similarly priced SKU, which is what `scale` is for.

    Args:
        unit_value: Item valuation rate. Non-positive values fall into the
            cheapest band, which is the safe direction to guess.
        rng: Seeded Random from SeedContext — never the global random module.
        is_finished_good: True for items with a default BOM.
        scale: Industry multiplier from `seed.opening_stock.qty_scale`.

    Returns at least 1: an item that opens at zero is indistinguishable from one
    that was never opened at all.
    """
    value = max(float(unit_value or 0), 0.0)
    low, high = next((lo, hi) for ceiling, lo, hi in OPENING_STOCK_QTY_BANDS if value < ceiling)
    qty = float(rng.randint(low, high)) * scale
    if is_finished_good:
        qty *= FINISHED_GOODS_QTY_SCALE
    return _round_to_nice(qty)


def _round_to_nice(qty: float) -> int:
    """Round to a step that matches the magnitude, so quantities read as stock
    counts (1,200) rather than as random draws (1,237). Never returns below 1."""
    if qty >= 1000:
        step = 100
    elif qty >= 100:
        step = 10
    elif qty >= 20:
        step = 5
    else:
        step = 1
    return max(1, int(round(qty / step)) * step)


ITEM_ROW_HELPERS = '''
from fractions import Fraction as _DskFraction
from math import gcd as _dsk_gcd

_dsk_uom_cache = {}
_dsk_mult_cache = {}


def dsk_stock_uom(item_code):
    """Stock UOM of an item, cached. Never guess 'Nos' — order lines must
    carry the item's real UOM or the demo data reads as nonsense (e.g. a
    Litre product sold as 'Nos')."""
    if item_code not in _dsk_uom_cache:
        _dsk_uom_cache[item_code] = frappe.db.get_value('Item', item_code, 'stock_uom') or 'Nos'
    return _dsk_uom_cache[item_code]


def dsk_qty_multiple(item_code):
    """Smallest order-qty step that keeps every whole-number BOM component integral.

    A Work Order scales required items by order_qty / bom_quantity. When a
    component's stock UOM has 'Must be Whole Number' set (Box, Nos, Pair,
    Set, Unit), a scale factor that lands the component on a fraction makes
    the Work Order un-saveable.

    For a component of qty c in a BOM of batch b, required_qty is
    c * order_qty / b. Reduce c/b to lowest terms p/q: since gcd(p, q) = 1,
    p * order_qty / q is integral exactly when q divides order_qty. So the
    step for one component is q, and for the BOM it is the LCM of those.

    Working in exact rationals (not ints) matters — a fractional component
    qty such as 0.1 Nos in a batch of 1 needs a step of 10, which integer
    arithmetic would miss entirely.

    Only direct BOM rows are considered — no industry currently nests
    sub-assembly BOMs. Returns 1 when the item has no default BOM.
    """
    if item_code in _dsk_mult_cache:
        return _dsk_mult_cache[item_code]
    mult = 1
    bom = frappe.db.get_value(
        'BOM',
        {'item': item_code, 'is_active': 1, 'is_default': 1, 'docstatus': 1},
        ['name', 'quantity'],
        as_dict=True,
    )
    if bom and bom.quantity:
        batch = _DskFraction(str(float(bom.quantity)))
        rows = frappe.get_all(
            'BOM Item', filters={'parent': bom.name}, fields=['stock_qty', 'stock_uom']
        )
        for row in rows:
            if not frappe.db.get_value('UOM', row.stock_uom, 'must_be_whole_number', cache=True):
                continue
            comp = _DskFraction(str(float(row.stock_qty or 0)))
            if not comp:
                continue
            need = (comp / batch).denominator
            mult = mult * need // _dsk_gcd(mult, need)
    _dsk_mult_cache[item_code] = mult
    return mult


def dsk_align_qty(item_code, qty):
    """Round qty to the nearest BOM-compatible multiple, never below one batch."""
    mult = dsk_qty_multiple(item_code)
    if mult <= 1:
        return max(1, int(round(float(qty))))
    return max(mult, int(round(float(qty) / mult)) * mult)


def dsk_item_row(item_code, qty, **extra):
    """Build a sales/order line with the item's real UOM and a manufacturable qty."""
    uom = dsk_stock_uom(item_code)
    row = {
        'item_code': item_code,
        'qty': dsk_align_qty(item_code, qty),
        'uom': uom,
        'stock_uom': uom,
        'conversion_factor': 1,
    }
    row.update(extra)
    return row
'''
"""Server-side helpers injected into generated Frappe scripts.

Prepend to a script string (by concatenation, not f-string interpolation —
the snippet contains literal braces) to get `dsk_item_row`, which replaces
hand-rolled item dicts that hardcode `'uom': 'Nos'`.
"""
