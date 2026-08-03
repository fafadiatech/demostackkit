"""
Industry auto-discovery engine.

Scans a root `industries/` directory for subdirectories containing
`industry.yaml`. Any such directory is treated as an industry package.
The `_template` directory is excluded by convention.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from demostackkit.core.config import IndustryConfig, load_industry_config
from demostackkit.core.exceptions import IndustryNotFoundError, InvalidIndustryConfigError


# Directories that are not real industries
_EXCLUDED_SLUGS = {"_template"}


def iter_industry_dirs(industries_root: Path) -> Iterator[Path]:
    """
    Yield subdirectories of `industries_root` that contain an `industry.yaml`.
    Excludes directories in _EXCLUDED_SLUGS.
    """
    if not industries_root.is_dir():
        return

    for child in sorted(industries_root.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("."):
            continue
        if child.name in _EXCLUDED_SLUGS:
            continue
        if (child / "industry.yaml").is_file():
            yield child


class IndustryRegistry:
    """
    Holds all discovered industries for a given run.

    Usage:
        registry = IndustryRegistry.from_root(Path("industries"))
        config = registry.get("garment")
        all_configs = registry.all()
    """

    def __init__(self) -> None:
        self._configs: dict[str, IndustryConfig] = {}
        self._errors: dict[str, str] = {}

    @classmethod
    def from_root(cls, industries_root: Path, *, skip_invalid: bool = False) -> "IndustryRegistry":
        """
        Build a registry by scanning industries_root.

        Args:
            industries_root: Path to the `industries/` directory
            skip_invalid: If True, log errors and continue. If False, raise on first error.
        """
        registry = cls()
        for industry_dir in iter_industry_dirs(industries_root):
            yaml_path = industry_dir / "industry.yaml"
            try:
                config = load_industry_config(yaml_path)
                registry._configs[config.slug] = config
            except InvalidIndustryConfigError as exc:
                if skip_invalid:
                    registry._errors[industry_dir.name] = str(exc)
                else:
                    raise
        return registry

    def get(self, slug: str) -> IndustryConfig:
        """
        Return config for the given slug.

        Raises:
            IndustryNotFoundError: If slug is not registered
        """
        if slug not in self._configs:
            raise IndustryNotFoundError(slug)
        return self._configs[slug]

    def all(self) -> list[IndustryConfig]:
        """Return all valid industry configs, sorted by slug."""
        return sorted(self._configs.values(), key=lambda c: c.slug)

    def slugs(self) -> list[str]:
        """Return all registered slugs."""
        return sorted(self._configs.keys())

    def errors(self) -> dict[str, str]:
        """Return mapping of slug/dirname → error message for invalid industries."""
        return dict(self._errors)

    def __len__(self) -> int:
        return len(self._configs)

    def __contains__(self, slug: str) -> bool:
        return slug in self._configs


def get_industries_root() -> Path:
    """
    Resolve the industries/ directory relative to the demostackkit repo root.
    Works whether running installed or from source.
    """
    # Walk up from this file to find the repo root (contains industries/)
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "industries"
        if candidate.is_dir():
            return candidate
    # Fallback: CWD/industries
    return Path.cwd() / "industries"
