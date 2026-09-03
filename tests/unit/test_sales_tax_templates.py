"""
Unit tests for the shared Sales Tax Templates seeder (ref #36).

Same "stub `_exec`, capture the generated Frappe script" approach as
test_delivery_notes.py.
"""

from __future__ import annotations

import ast
import json

import pytest
from _seeder_harness import (
    REPO_ROOT,
    SHARED_SEEDERS,
    all_industry_dirs,
    load_seeder_class,
    run_seeder,
)

from demostackkit.core.config import load_industry_config
from demostackkit.seeder.loader import discover_seeders

SEEDER_PATH = SHARED_SEEDERS / "01_master" / "91_sales_tax_templates.py"


def _run(industry_dir) -> str:
    seeder_cls = load_seeder_class(SEEDER_PATH, "SalesTaxTemplateSeeder")
    return run_seeder(seeder_cls, industry_dir)


@pytest.mark.unit
class TestSalesTaxTemplateSeeder:
    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_runs_for_every_industry(self, industry_dir) -> None:
        labels = [cls.label for cls in discover_seeders(industry_dir, shared_dirs=[SHARED_SEEDERS])]
        assert "Sales Tax Templates" in labels

    @pytest.mark.parametrize("industry_dir", all_industry_dirs(), ids=lambda d: d.name)
    def test_generated_script_is_valid_python(self, industry_dir) -> None:
        script = _run(industry_dir)
        assert script
        ast.parse(script)

    def test_india_gets_gst_style_templates(self) -> None:
        india_dirs = [
            d
            for d in all_industry_dirs()
            if load_industry_config(d / "industry.yaml").company.country == "India"
        ]
        if not india_dirs:
            pytest.skip("no India-flagged industry found")
        script = _run(india_dirs[0])
        payload_json = script.split("payload = json.loads('''", 1)[1].split("''')", 1)[0]
        payload = json.loads(payload_json)
        titles = {tpl["title"] for tpl in payload["plan"]}
        assert titles == {"GST 18%", "GST 5%"}

    def test_non_india_gets_flat_sales_tax_template(self) -> None:
        other_dirs = [
            d
            for d in all_industry_dirs()
            if load_industry_config(d / "industry.yaml").company.country != "India"
        ]
        if not other_dirs:
            pytest.skip("no non-India industry found")
        script = _run(other_dirs[0])
        payload_json = script.split("payload = json.loads('''", 1)[1].split("''')", 1)[0]
        payload = json.loads(payload_json)
        titles = {tpl["title"] for tpl in payload["plan"]}
        assert titles == {"Sales Tax 8%"}

    def test_degrades_gracefully_when_no_tax_account_is_found(self) -> None:
        script = _run(REPO_ROOT / "industries" / "garment")
        assert "no tax account found, skipped" in script
