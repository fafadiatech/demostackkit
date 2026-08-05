"""
Unit tests for demostackkit.core.discovery — industry auto-discovery.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from demostackkit.core.discovery import IndustryRegistry, iter_industry_dirs
from demostackkit.core.exceptions import IndustryNotFoundError


def _make_industry(root: Path, slug: str, name: str = "Test") -> Path:
    d = root / slug
    d.mkdir(parents=True)
    (d / "industry.yaml").write_text(
        yaml.dump(
            {
                "name": name,
                "slug": slug,
                "company": {
                    "name": f"{name} Co",
                    "abbr": slug[:3].upper(),
                    "currency": "USD",
                    "country": "United States",
                },
                "site": {"name": f"{slug}.localhost"},
            }
        ),
        encoding="utf-8",
    )
    return d


@pytest.mark.unit
class TestIterIndustryDirs:
    def test_finds_valid_dirs(self, tmp_industries_root: Path) -> None:
        _make_industry(tmp_industries_root, "alpha")
        _make_industry(tmp_industries_root, "beta")
        dirs = list(iter_industry_dirs(tmp_industries_root))
        assert len(dirs) == 2
        slugs = [d.name for d in dirs]
        assert "alpha" in slugs
        assert "beta" in slugs

    def test_excludes_template(self, tmp_industries_root: Path) -> None:
        _make_industry(tmp_industries_root, "_template")
        _make_industry(tmp_industries_root, "real")
        dirs = list(iter_industry_dirs(tmp_industries_root))
        names = [d.name for d in dirs]
        assert "_template" not in names
        assert "real" in names

    def test_excludes_dirs_without_yaml(self, tmp_industries_root: Path) -> None:
        (tmp_industries_root / "nodoc").mkdir()  # no industry.yaml
        _make_industry(tmp_industries_root, "withdoc")
        dirs = list(iter_industry_dirs(tmp_industries_root))
        names = [d.name for d in dirs]
        assert "nodoc" not in names

    def test_empty_root_returns_nothing(self, tmp_path: Path) -> None:
        empty = tmp_path / "empty_industries"
        empty.mkdir()
        assert list(iter_industry_dirs(empty)) == []

    def test_nonexistent_root_returns_nothing(self, tmp_path: Path) -> None:
        assert list(iter_industry_dirs(tmp_path / "nonexistent")) == []


@pytest.mark.unit
class TestIndustryRegistry:
    def test_from_root_discovers_industries(self, tmp_industries_root: Path) -> None:
        _make_industry(tmp_industries_root, "garment", "Garment")
        _make_industry(tmp_industries_root, "chemical", "Chemical")
        registry = IndustryRegistry.from_root(tmp_industries_root)
        assert len(registry) == 2
        assert "garment" in registry
        assert "chemical" in registry

    def test_get_returns_config(self, tmp_industries_root: Path) -> None:
        _make_industry(tmp_industries_root, "garment", "Garment Mfg")
        registry = IndustryRegistry.from_root(tmp_industries_root)
        config = registry.get("garment")
        assert config.name == "Garment Mfg"

    def test_get_raises_for_unknown_slug(self, tmp_industries_root: Path) -> None:
        registry = IndustryRegistry.from_root(tmp_industries_root)
        with pytest.raises(IndustryNotFoundError):
            registry.get("nonexistent")

    def test_all_returns_sorted(self, tmp_industries_root: Path) -> None:
        _make_industry(tmp_industries_root, "zzz")
        _make_industry(tmp_industries_root, "aaa")
        registry = IndustryRegistry.from_root(tmp_industries_root)
        slugs = [c.slug for c in registry.all()]
        assert slugs == sorted(slugs)

    def test_skip_invalid_does_not_raise(self, tmp_industries_root: Path) -> None:
        _make_industry(tmp_industries_root, "good")
        bad = tmp_industries_root / "bad"
        bad.mkdir()
        (bad / "industry.yaml").write_text("not: valid: yaml: at: all:", encoding="utf-8")
        registry = IndustryRegistry.from_root(tmp_industries_root, skip_invalid=True)
        assert "good" in registry
        assert registry.errors()  # bad industry shows up in errors

    def test_slugs_returns_all_slugs(self, tmp_industries_root: Path) -> None:
        _make_industry(tmp_industries_root, "x")
        _make_industry(tmp_industries_root, "y")
        registry = IndustryRegistry.from_root(tmp_industries_root)
        assert set(registry.slugs()) == {"x", "y"}
