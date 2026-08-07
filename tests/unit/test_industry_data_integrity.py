"""
Unit tests for industry data integrity.

Validates that each industry's data files are consistent with their seeder
definitions — no runtime Frappe environment required.

Checks performed:
- Every item_group referenced in items.csv is defined in 02_item_groups.py
- Parent item groups are defined before their children in _ITEM_GROUPS
- items.csv has the required header columns
"""

from __future__ import annotations

import ast
import csv
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent
INDUSTRIES_ROOT = REPO_ROOT / "industries"

# Groups that ERPNext guarantees exist without any seeder creating them.
ALWAYS_AVAILABLE = {"All Item Groups"}


def _all_industry_dirs() -> list[Path]:
    """Return all industry directories that have both a data/ and seeders/ dir."""
    return sorted(
        d
        for d in INDUSTRIES_ROOT.iterdir()
        if d.is_dir()
        and not d.name.startswith("_")
        and (d / "data").is_dir()
        and (d / "seeders").is_dir()
    )


def _read_item_groups_from_seeder(industry_dir: Path) -> list[dict]:
    """
    Import 02_item_groups.py in isolation and return the _ITEM_GROUPS list.

    We do a fresh import so we don't need Frappe installed.
    """
    seeder_path = industry_dir / "seeders" / "01_master" / "02_item_groups.py"
    if not seeder_path.exists():
        return []

    # Parse the AST to extract _ITEM_GROUPS without executing the full module
    # (avoids any import-time side effects that might require Frappe).
    source = seeder_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(seeder_path))

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "_ITEM_GROUPS"
        ):
            return ast.literal_eval(node.value)  # type: ignore[return-value]

    return []


def _read_item_groups_from_csv(industry_dir: Path) -> list[str]:
    """Return all item_group values found in data/items.csv (deduplicated, ordered)."""
    csv_path = industry_dir / "data" / "items.csv"
    if not csv_path.exists():
        return []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list({row["item_group"] for row in reader if row.get("item_group")})


# ---------------------------------------------------------------------------
# Parametrize over all industries
# ---------------------------------------------------------------------------

_INDUSTRY_IDS = [d.name for d in _all_industry_dirs()]
_INDUSTRY_DIRS = _all_industry_dirs()


@pytest.mark.unit
class TestItemGroupConsistency:
    """Every item_group used in items.csv must be defined in 02_item_groups.py."""

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_all_item_groups_are_defined(self, industry_dir: Path) -> None:
        defined_groups = {
            g["item_group_name"] for g in _read_item_groups_from_seeder(industry_dir)
        } | ALWAYS_AVAILABLE

        csv_groups = set(_read_item_groups_from_csv(industry_dir))

        missing = csv_groups - defined_groups
        assert not missing, (
            f"[{industry_dir.name}] items.csv references item group(s) not defined in "
            f"02_item_groups.py: {sorted(missing)}"
        )

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_item_groups_seeder_exists(self, industry_dir: Path) -> None:
        """Each industry that has items.csv must have 02_item_groups.py."""
        csv_path = industry_dir / "data" / "items.csv"
        if not csv_path.exists():
            pytest.skip("no items.csv")

        seeder_path = industry_dir / "seeders" / "01_master" / "02_item_groups.py"
        assert seeder_path.exists(), (
            f"[{industry_dir.name}] has items.csv but is missing "
            f"seeders/01_master/02_item_groups.py"
        )


@pytest.mark.unit
class TestItemGroupOrdering:
    """Parent item groups must be defined before any of their children."""

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_parents_defined_before_children(self, industry_dir: Path) -> None:
        groups = _read_item_groups_from_seeder(industry_dir)
        if not groups:
            pytest.skip("no _ITEM_GROUPS defined")

        seen: set[str] = set(ALWAYS_AVAILABLE)
        for entry in groups:
            parent = entry.get("parent_item_group", "All Item Groups")
            name = entry["item_group_name"]
            assert parent in seen, (
                f"[{industry_dir.name}] item group '{name}' references parent '{parent}' "
                f"which has not been defined yet in _ITEM_GROUPS. "
                f"Move '{parent}' above '{name}'."
            )
            seen.add(name)


@pytest.mark.unit
class TestItemsCsvFormat:
    """items.csv must have the columns that the ItemSeeder expects."""

    REQUIRED_COLUMNS = {"item_code", "item_name", "item_group"}

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_required_columns_present(self, industry_dir: Path) -> None:
        csv_path = industry_dir / "data" / "items.csv"
        if not csv_path.exists():
            pytest.skip("no items.csv")

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])

        missing = self.REQUIRED_COLUMNS - headers
        assert not missing, (
            f"[{industry_dir.name}] items.csv is missing required column(s): {sorted(missing)}"
        )

    @pytest.mark.parametrize("industry_dir", _INDUSTRY_DIRS, ids=_INDUSTRY_IDS)
    def test_no_blank_item_codes(self, industry_dir: Path) -> None:
        csv_path = industry_dir / "data" / "items.csv"
        if not csv_path.exists():
            pytest.skip("no items.csv")

        with csv_path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            blank_rows = [
                i + 2  # +1 for header, +1 for 1-based line numbers
                for i, row in enumerate(reader)
                if not row.get("item_code", "").strip()
            ]

        assert not blank_rows, (
            f"[{industry_dir.name}] items.csv has blank item_code on line(s): {blank_rows}"
        )
