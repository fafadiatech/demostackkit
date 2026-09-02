"""
Unit tests for demostackkit.core.config — IndustryConfig schema validation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from demostackkit.core.config import load_industry_config


def _write_yaml(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "industry.yaml"
    p.write_text(yaml.dump(data), encoding="utf-8")
    return p


@pytest.mark.unit
class TestIndustryConfigValidation:
    def test_valid_minimal_config(self, tmp_path: Path) -> None:
        path = _write_yaml(
            tmp_path,
            {
                "name": "Test",
                "slug": "test",
                "company": {
                    "name": "Test Co",
                    "abbr": "TC",
                    "currency": "USD",
                    "country": "United States",
                },
                "site": {"name": "test.localhost"},
            },
        )
        config = load_industry_config(path)
        assert config.slug == "test"
        assert config.company.name == "Test Co"

    def test_site_name_auto_set_from_slug(self, tmp_path: Path) -> None:
        """If site.name is absent, it defaults to <slug>.localhost."""
        path = _write_yaml(
            tmp_path,
            {
                "name": "Test",
                "slug": "myindustry",
                "company": {
                    "name": "Co",
                    "abbr": "CO",
                    "currency": "USD",
                    "country": "United States",
                },
            },
        )
        config = load_industry_config(path)
        assert config.site.name == "myindustry.localhost"

    def test_site_name_must_match_slug(self, tmp_path: Path) -> None:
        with pytest.raises(Exception):
            load_industry_config(
                _write_yaml(
                    tmp_path,
                    {
                        "name": "Test",
                        "slug": "garment",
                        "company": {
                            "name": "Co",
                            "abbr": "CO",
                            "currency": "USD",
                            "country": "United States",
                        },
                        "site": {"name": "wrong.localhost"},
                    },
                )
            )

    def test_slug_must_be_lowercase(self, tmp_path: Path) -> None:
        with pytest.raises(Exception):
            load_industry_config(
                _write_yaml(
                    tmp_path,
                    {
                        "name": "Test",
                        "slug": "MyIndustry",
                        "company": {
                            "name": "Co",
                            "abbr": "CO",
                            "currency": "USD",
                            "country": "United States",
                        },
                        "site": {"name": "myindustry.localhost"},
                    },
                )
            )

    def test_missing_company_raises(self, tmp_path: Path) -> None:
        with pytest.raises(Exception):
            load_industry_config(
                _write_yaml(
                    tmp_path,
                    {
                        "name": "Test",
                        "slug": "test",
                    },
                )
            )

    def test_duplicate_user_emails_raise(self, tmp_path: Path) -> None:
        with pytest.raises(Exception):
            load_industry_config(
                _write_yaml(
                    tmp_path,
                    {
                        "name": "Test",
                        "slug": "test",
                        "company": {
                            "name": "Co",
                            "abbr": "CO",
                            "currency": "USD",
                            "country": "United States",
                        },
                        "site": {"name": "test.localhost"},
                        "users": [
                            {"email": "a@test.demo", "full_name": "A"},
                            {"email": "a@test.demo", "full_name": "B"},  # duplicate
                        ],
                    },
                )
            )

    def test_seed_volumes_default_positive(self, tmp_path: Path) -> None:
        config = load_industry_config(
            _write_yaml(
                tmp_path,
                {
                    "name": "Test",
                    "slug": "test",
                    "company": {
                        "name": "Co",
                        "abbr": "CO",
                        "currency": "USD",
                        "country": "United States",
                    },
                    "site": {"name": "test.localhost"},
                },
            )
        )
        assert config.seed.volumes.sales_orders > 0
        assert config.seed.volumes.customers > 0

    def test_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            load_industry_config(tmp_path / "nonexistent.yaml")

    def test_additional_companies_default_empty(self, tmp_path: Path) -> None:
        config = load_industry_config(
            _write_yaml(
                tmp_path,
                {
                    "name": "Test",
                    "slug": "test",
                    "company": {
                        "name": "Co",
                        "abbr": "CO",
                        "currency": "USD",
                        "country": "United States",
                    },
                    "site": {"name": "test.localhost"},
                },
            )
        )
        assert config.additional_companies == []

    def test_additional_companies_parsed(self, tmp_path: Path) -> None:
        config = load_industry_config(
            _write_yaml(
                tmp_path,
                {
                    "name": "Test",
                    "slug": "test",
                    "company": {
                        "name": "Parent Co",
                        "abbr": "PC",
                        "currency": "INR",
                        "country": "India",
                    },
                    "additional_companies": [
                        {
                            "name": "Subsidiary Co",
                            "abbr": "SC",
                            "currency": "INR",
                            "country": "India",
                        },
                    ],
                    "site": {"name": "test.localhost"},
                },
            )
        )
        assert len(config.additional_companies) == 1
        assert config.additional_companies[0].name == "Subsidiary Co"

    def test_duplicate_company_abbr_raises(self, tmp_path: Path) -> None:
        with pytest.raises(Exception):
            load_industry_config(
                _write_yaml(
                    tmp_path,
                    {
                        "name": "Test",
                        "slug": "test",
                        "company": {
                            "name": "Parent Co",
                            "abbr": "CO",
                            "currency": "USD",
                            "country": "United States",
                        },
                        "additional_companies": [
                            {
                                "name": "Sibling Co",
                                "abbr": "CO",  # duplicate abbr
                                "currency": "USD",
                                "country": "United States",
                            },
                        ],
                        "site": {"name": "test.localhost"},
                    },
                )
            )

    def test_duplicate_company_name_raises(self, tmp_path: Path) -> None:
        with pytest.raises(Exception):
            load_industry_config(
                _write_yaml(
                    tmp_path,
                    {
                        "name": "Test",
                        "slug": "test",
                        "company": {
                            "name": "Same Co",
                            "abbr": "SC1",
                            "currency": "USD",
                            "country": "United States",
                        },
                        "additional_companies": [
                            {
                                "name": "Same Co",  # duplicate name
                                "abbr": "SC2",
                                "currency": "USD",
                                "country": "United States",
                            },
                        ],
                        "site": {"name": "test.localhost"},
                    },
                )
            )

    def test_garment_industry_config_is_valid(self) -> None:
        """The real garment industry.yaml must pass validation."""
        repo_root = Path(__file__).parent.parent.parent
        yaml_path = repo_root / "industries" / "garment" / "industry.yaml"
        if not yaml_path.exists():
            pytest.skip("garment industry.yaml not found")
        config = load_industry_config(yaml_path)
        assert config.slug == "garment"
        assert config.company.currency == "INR"
        assert len(config.users) > 0
