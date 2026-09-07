"""
Unit tests for the shared Quality Inspection Templates seeder (ref #1, phase 1).
"""

from __future__ import annotations

import ast
import io
import random
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from _seeder_harness import (
    REPO_ROOT,
    SHARED_SEEDERS,
    industry_dirs_with_module,
    load_seeder_class,
    run_seeder,
)

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.base import SeedContext
from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "01_master" / "95_quality_inspection_templates.py"

_CACHE = {
    "qc_operation_name": "Solar QC Sign-off",
    "qc_inspection_parameters": [
        ("Efficiency %", 18, 22),
        ("Power Output (W)", 300, 400),
    ],
}


class _LinkValidationError(Exception):
    """Stand-in for frappe.exceptions.LinkValidationError."""


class _FakeDoc:
    def __init__(self, values: dict[str, Any]) -> None:
        self.values = values
        self.name = values.get("parameter") or values.get("quality_inspection_template_name")

    def insert(self, ignore_permissions: bool = False) -> _FakeDoc:
        doctype = self.values["doctype"]
        if doctype == "Quality Inspection Template":
            # Mimic ERPNext: specification is a Link to Quality Inspection Parameter.
            missing = [
                row["specification"]
                for row in self.values.get("item_quality_inspection_parameter", [])
                if row["specification"] not in _FakeDb._parameters
            ]
            if missing:
                msg = ", ".join(f"Parameter: {name}" for name in missing)
                raise _LinkValidationError(f"Could not find {msg}")
            _FakeDb._templates.add(self.name)
        elif doctype == "Quality Inspection Parameter":
            _FakeDb._parameters.add(self.values["parameter"])
        return self


class _FakeDb:
    _parameters: set[str] = set()
    _templates: set[str] = set()
    _operations: dict[str, dict[str, Any]] = {}

    @classmethod
    def reset(cls) -> None:
        cls._parameters = set()
        cls._templates = set()
        cls._operations = {
            "Solar QC Sign-off": {"quality_inspection_template": None},
        }

    @classmethod
    def exists(cls, doctype: str, name: str) -> bool:
        if doctype == "Operation":
            return name in cls._operations
        if doctype == "Quality Inspection Parameter":
            return name in cls._parameters
        if doctype == "Quality Inspection Template":
            return name in cls._templates
        return False

    @classmethod
    def get_value(cls, doctype: str, name: str, field: str) -> Any:
        if doctype == "Operation" and name in cls._operations:
            return cls._operations[name].get(field)
        return None

    @classmethod
    def set_value(cls, doctype: str, name: str, field: str, value: Any) -> None:
        if doctype == "Operation" and name in cls._operations:
            cls._operations[name][field] = value

    @classmethod
    def commit(cls) -> None:
        pass


def _exec_generated_script(script: str) -> tuple[set[str], set[str], str | None]:
    """Execute the seeder script against fakes that enforce Link validation.

    Returns (created_parameters, created_templates, linked_template_on_operation).
    Fails with LinkValidationError if the script inserts a template without
    first creating Quality Inspection Parameter masters — the real ERPNext bug.
    """
    _FakeDb.reset()

    fake_frappe = SimpleNamespace(
        db=_FakeDb,
        get_doc=lambda values: _FakeDoc(values),
    )

    stdout = io.StringIO()
    old_stdout = sys.stdout
    exec_globals: dict[str, Any] = {"frappe": fake_frappe, "json": __import__("json")}
    try:
        sys.stdout = stdout
        exec(compile(script, "<seeder script>", "exec"), exec_globals)
    finally:
        sys.stdout = old_stdout

    linked = _FakeDb._operations["Solar QC Sign-off"].get("quality_inspection_template")
    return set(_FakeDb._parameters), set(_FakeDb._templates), linked


@pytest.mark.unit
class TestQualityInspectionTemplateSeeder:
    @pytest.mark.parametrize(
        "industry_dir", industry_dirs_with_module("Manufacturing"), ids=lambda d: d.name
    )
    def test_discovered_for_manufacturing_industries(self, industry_dir: Path) -> None:
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Quality Inspection Templates" in labels

    def test_no_op_when_no_qc_operation_cached(self) -> None:
        """An industry's `08_operations.py` didn't cache a QC operation (or
        hasn't run yet) — the seeder must not touch the container at all."""
        seeder_cls = load_seeder_class(SEEDER_PATH, "QualityInspectionTemplateSeeder")
        cfg = load_industry_config(REPO_ROOT / "industries" / "solar" / "industry.yaml")
        ctx = SeedContext(
            site=cfg.site.name,
            industry_slug="solar",
            industry_config=cfg,
            bench_path="/home/frappe/frappe-bench",
            random=random.Random(1),
        )

        captured: list[str] = []

        class Recording(seeder_cls):  # type: ignore[valid-type, misc]
            def _exec(self, script: str, timeout: int = 120) -> str:
                captured.append(script)
                return ""

        Recording(ctx).run()
        assert captured == []

    def test_generates_template_and_links_operation(self) -> None:
        seeder_cls = load_seeder_class(SEEDER_PATH, "QualityInspectionTemplateSeeder")
        script = run_seeder(seeder_cls, REPO_ROOT / "industries" / "solar", cache=_CACHE)
        assert script, "seeder should not no-op when qc_operation_name is cached"
        ast.parse(script)
        assert "Solar QC Sign-off" in script
        assert "Solar QC Sign-off QC Template" in script
        assert "Efficiency %" in script
        assert "quality_inspection_template" in script

    def test_creates_quality_inspection_parameter_masters(self) -> None:
        """Behavioural regression: template rows Link to Quality Inspection
        Parameter. Without creating those masters first, ERPNext raises
        LinkValidationError (the electrical `demostackkit up` failure)."""
        seeder_cls = load_seeder_class(SEEDER_PATH, "QualityInspectionTemplateSeeder")
        script = run_seeder(seeder_cls, REPO_ROOT / "industries" / "solar", cache=_CACHE)
        assert script

        parameters, templates, linked = _exec_generated_script(script)

        assert parameters == {"Efficiency %", "Power Output (W)"}
        assert templates == {"Solar QC Sign-off QC Template"}
        assert linked == "Solar QC Sign-off QC Template"
