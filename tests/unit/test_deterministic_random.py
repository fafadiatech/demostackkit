"""
Unit tests proving that the same random seed always produces the same output.

This is the core guarantee behind `demostackkit reset`.
"""

from __future__ import annotations

import pytest

from demostackkit.seeder.context import build_seed_context


def _make_config(seed: int):
    """Build a minimal IndustryConfig with the given random seed."""
    from demostackkit.core.config import IndustryConfig, CompanyConfig, SiteConfig, SeedConfig

    return IndustryConfig(
        name="Test",
        slug="test",
        company=CompanyConfig(name="Test Co", abbr="TC", currency="USD", country="United States"),
        site=SiteConfig(name="test.localhost"),
        seed=SeedConfig(random_seed=seed),
    )


@pytest.mark.unit
class TestDeterministicRandom:
    def test_same_seed_same_sequence(self) -> None:
        config = _make_config(12345)
        ctx1 = build_seed_context(config)
        ctx2 = build_seed_context(config)

        seq1 = [ctx1.random.randint(1, 1000) for _ in range(20)]
        seq2 = [ctx2.random.randint(1, 1000) for _ in range(20)]
        assert seq1 == seq2

    def test_different_seeds_different_sequences(self) -> None:
        ctx1 = build_seed_context(_make_config(111))
        ctx2 = build_seed_context(_make_config(222))

        seq1 = [ctx1.random.randint(1, 1000) for _ in range(20)]
        seq2 = [ctx2.random.randint(1, 1000) for _ in range(20)]
        assert seq1 != seq2

    def test_explicit_seed_overrides_config(self) -> None:
        config = _make_config(99999)
        ctx1 = build_seed_context(config, random_seed=42)
        ctx2 = build_seed_context(config, random_seed=42)

        seq1 = [ctx1.random.choice(["a", "b", "c"]) for _ in range(10)]
        seq2 = [ctx2.random.choice(["a", "b", "c"]) for _ in range(10)]
        assert seq1 == seq2

    def test_slug_fallback_is_deterministic(self) -> None:
        """When random_seed=0 in config, slug hash is used — must be stable."""
        from demostackkit.core.config import IndustryConfig, CompanyConfig, SiteConfig, SeedConfig
        config = IndustryConfig(
            name="Test",
            slug="garment",
            company=CompanyConfig(name="Co", abbr="CO", currency="USD", country="United States"),
            site=SiteConfig(name="garment.localhost"),
            seed=SeedConfig(random_seed=0),
        )
        ctx1 = build_seed_context(config)
        ctx2 = build_seed_context(config)

        n1 = ctx1.random.random()
        n2 = ctx2.random.random()
        assert n1 == n2

    def test_cache_stores_and_retrieves(self) -> None:
        config = _make_config(1)
        ctx = build_seed_context(config)

        ctx.cache_set("company_name", "Acme Corp")
        assert ctx.cache_get("company_name") == "Acme Corp"
        assert ctx.cache_get("missing_key", "default") == "default"

    def test_cache_require_raises_on_missing(self) -> None:
        config = _make_config(1)
        ctx = build_seed_context(config)

        with pytest.raises(KeyError):
            ctx.cache_require("not_set")
