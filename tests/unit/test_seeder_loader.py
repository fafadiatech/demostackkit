"""
Unit tests for the seeder discovery / loader.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

from demostackkit.seeder.loader import discover_seeders

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _write_seeder(
    path: Path, class_name: str, base: str = "BaseMasterSeeder", priority: int = 100
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        textwrap.dedent(f"""
        from demostackkit.seeder.base import {base}
        class {class_name}({base}):
            label = "{class_name}"
            priority = {priority}
            def run(self): pass
    """),
        encoding="utf-8",
    )


@pytest.mark.unit
class TestDiscoverSeeders:
    def test_discovers_master_seeders(self, tmp_path: Path) -> None:
        industry_dir = tmp_path / "test_ind"
        _write_seeder(industry_dir / "seeders" / "01_master" / "01_company.py", "CompanySeeder")
        _write_seeder(industry_dir / "seeders" / "01_master" / "02_items.py", "ItemSeeder")

        classes = discover_seeders(industry_dir)
        names = [c.__name__ for c in classes]
        assert "CompanySeeder" in names
        assert "ItemSeeder" in names

    def test_master_before_transactions(self, tmp_path: Path) -> None:
        industry_dir = tmp_path / "ordered"
        _write_seeder(industry_dir / "seeders" / "01_master" / "01_co.py", "MasterSeeder")
        _write_seeder(
            industry_dir / "seeders" / "02_transactions" / "01_so.py",
            "TransSeeder",
            base="BaseTransactionSeeder",
        )
        classes = discover_seeders(industry_dir)
        names = [c.__name__ for c in classes]
        assert names.index("MasterSeeder") < names.index("TransSeeder")

    def test_sorted_by_priority(self, tmp_path: Path) -> None:
        industry_dir = tmp_path / "prio"
        _write_seeder(industry_dir / "seeders" / "01_master" / "z_low.py", "LowPrio", priority=50)
        _write_seeder(industry_dir / "seeders" / "01_master" / "a_high.py", "HighPrio", priority=10)

        classes = discover_seeders(industry_dir)
        names = [c.__name__ for c in classes]
        assert names.index("HighPrio") < names.index("LowPrio")

    def test_skips_dunder_files(self, tmp_path: Path) -> None:
        industry_dir = tmp_path / "dunder"
        (industry_dir / "seeders" / "01_master").mkdir(parents=True)
        (industry_dir / "seeders" / "01_master" / "__init__.py").write_text("", encoding="utf-8")
        classes = discover_seeders(industry_dir)
        assert classes == []

    def test_no_seeders_dir_returns_empty(self, tmp_path: Path) -> None:
        industry_dir = tmp_path / "empty"
        industry_dir.mkdir()
        assert discover_seeders(industry_dir) == []

    def test_abstract_bases_not_collected(self, tmp_path: Path) -> None:
        """BaseMasterSeeder itself must not appear in the discovered list."""
        industry_dir = tmp_path / "abstract"
        _write_seeder(industry_dir / "seeders" / "01_master" / "concrete.py", "ConcreteSeeder")
        classes = discover_seeders(industry_dir)
        from demostackkit.seeder.base import BaseMasterSeeder, BaseSeeder

        for cls in classes:
            assert cls not in (BaseMasterSeeder, BaseSeeder)

    def test_skips_imported_concrete_seeder(self, tmp_path: Path) -> None:
        """A subclass of an imported concrete seeder must be the only class collected."""
        shared = tmp_path / "shared_payroll_base.py"
        shared.write_text(
            textwrap.dedent("""
                from demostackkit.seeder.base import BaseMasterSeeder
                class PayrollSeeder(BaseMasterSeeder):
                    label = "Imported Base"
                    priority = 82
                    def run(self): pass
            """),
            encoding="utf-8",
        )
        sys.path.insert(0, str(tmp_path))
        try:
            industry_dir = tmp_path / "ind"
            path = industry_dir / "seeders" / "01_master" / "12_payroll.py"
            path.parent.mkdir(parents=True)
            path.write_text(
                textwrap.dedent("""
                    from shared_payroll_base import PayrollSeeder as _PayrollSeederBase
                    class PayrollSeeder(_PayrollSeederBase):
                        label = "Industry Payroll"
                        ANNUAL_CTC = {"Operator": 300_000}
                """),
                encoding="utf-8",
            )
            classes = discover_seeders(industry_dir)
        finally:
            sys.path.remove(str(tmp_path))
            sys.modules.pop("shared_payroll_base", None)

        assert [c.__name__ for c in classes] == ["PayrollSeeder"]
        assert classes[0].label == "Industry Payroll"
        assert classes[0].__module__.startswith("_dsk_industry_ind_")

    def test_electrical_discovers_one_payroll_seeder(self) -> None:
        industry_dir = REPO_ROOT / "industries" / "electrical"
        payroll = [cls for cls in discover_seeders(industry_dir) if cls.__name__ == "PayrollSeeder"]
        assert len(payroll) == 1
        assert hasattr(payroll[0], "ANNUAL_CTC")
        assert payroll[0].ANNUAL_CTC
