"""
Shared pytest fixtures for demostackkit tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


@pytest.fixture
def tmp_industries_root(tmp_path: Path) -> Path:
    """Create a temporary industries/ directory."""
    root = tmp_path / "industries"
    root.mkdir()
    return root


@pytest.fixture
def minimal_industry_yaml() -> dict:
    """Return a minimal valid industry.yaml as a dict."""
    return {
        "name": "Test Industry",
        "slug": "test",
        "company": {
            "name": "Test Co Ltd",
            "abbr": "TCL",
            "currency": "USD",
            "country": "United States",
        },
        "site": {
            "name": "test.localhost",
        },
        "seed": {
            "random_seed": 12345,
        },
    }


@pytest.fixture
def minimal_industry_dir(tmp_industries_root: Path, minimal_industry_yaml: dict) -> Path:
    """Create a minimal but valid industry directory."""
    industry_dir = tmp_industries_root / "test"
    industry_dir.mkdir()
    (industry_dir / "industry.yaml").write_text(yaml.dump(minimal_industry_yaml), encoding="utf-8")
    # Create expected data files (empty CSVs)
    data_dir = industry_dir / "data"
    data_dir.mkdir()
    for fname in ["items.csv", "customers.csv", "suppliers.csv"]:
        (data_dir / fname).write_text("item_code,item_name\n", encoding="utf-8")
    return industry_dir


@pytest.fixture
def garment_industry_dir() -> Path:
    """Return the path to the real garment industry directory."""
    repo_root = Path(__file__).parent.parent
    return repo_root / "industries" / "garment"
