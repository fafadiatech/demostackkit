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
