"""
Pydantic v2 models for industry.yaml schema validation.

This module is the schema contract between industry packages and the framework.
All other components import IndustryConfig from here.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

SCHEMA_VERSION = "1"

_SLUG_RE = re.compile(r"^[a-z][a-z0-9_-]*$")


# ── Sub-models ────────────────────────────────────────────────────────────────


class CompanyConfig(BaseModel):
    name: str = Field(description="Full legal company name used in ERPNext")
    abbr: str = Field(min_length=1, max_length=10, description="Company abbreviation (2-10 chars)")
    currency: str = Field(default="USD", description="ISO 4217 currency code")
    country: str = Field(default="United States", description="Country name as per ERPNext list")
    default_letter_head: str = Field(
        default="", description="Name of the default letter head document"
    )
    tax_id: str = Field(default="", description="Demo tax ID / GST number")
    fiscal_year_start: str = Field(
        default="01-01",
        pattern=r"^\d{2}-\d{2}$",
        description="Fiscal year start in MM-DD format",
    )


class SiteConfig(BaseModel):
    name: str = Field(description="Frappe site name, e.g. garment.localhost")
    admin_password: str = Field(
        default="${SITE_ADMIN_PASSWORD:-admin}",
        description="Admin password (supports env var substitution)",
    )
    language: str = Field(default="en")
    timezone: str = Field(default="UTC")


class SeedVolumes(BaseModel):
    sales_orders: int = Field(default=50, ge=1)
    purchase_orders: int = Field(default=30, ge=1)
    production_orders: int = Field(default=25, ge=0)
    stock_entries: int = Field(default=100, ge=1)
    customers: int = Field(default=20, ge=1)
    suppliers: int = Field(default=15, ge=1)
    quality_inspections: int = Field(default=30, ge=1)


class OpeningStockConfig(BaseModel):
    """Where the shared Opening Stock seeder parks each item's starting balance.

    Warehouse names are given without the company abbreviation suffix; the seeder
    appends it (``Stores`` → ``Stores - ACH``). The defaults are the warehouses
    ERPNext creates with every company, so an industry that defines its own
    themed warehouses can point at them here instead.
    """

    enabled: bool = Field(default=True, description="Set false to skip opening balances")
    warehouse: str = Field(
        default="Stores", description="Warehouse for purchased/raw items, without ' - ABBR'"
    )
    fg_warehouse: str = Field(
        default="Finished Goods",
        description="Warehouse for items with a default BOM, without ' - ABBR'",
    )
    qty_scale: float = Field(
        default=1.0,
        gt=0,
        description=(
            "Multiplier on the value-banded opening quantities. The bands assume an "
            "industrial operation holding INR-scale inventory; a small retail or "
            "hobby business should dial this down (e.g. 0.03)."
        ),
    )


class SeedDateRange(BaseModel):
    start: str = Field(
        default="-180d", description="Relative date like -180d or absolute YYYY-MM-DD"
    )
    end: str = Field(default="-1d")


class SeedConfig(BaseModel):
    random_seed: int = Field(
        default=20240101,
        description="Integer seed for deterministic random data generation",
    )
    demo_password: str = Field(
        default="Demo@1234",
        description="Password set for all seeded demo users",
    )
    volumes: SeedVolumes = Field(default_factory=SeedVolumes)
    date_range: SeedDateRange = Field(default_factory=SeedDateRange)
    opening_stock: OpeningStockConfig = Field(default_factory=OpeningStockConfig)


class FixturesConfig(BaseModel):
    load_order: list[str] = Field(default_factory=list)
    print_formats: str = Field(default="fixtures/print_formats/*.json")
    reports: str = Field(default="fixtures/reports/*.json")
    workspaces: str = Field(default="fixtures/workspaces/*.json")
    dashboards: str = Field(default="fixtures/dashboards/*.json")


class DataConfig(BaseModel):
    items: str = Field(default="data/items.csv")
    customers: str = Field(default="data/customers.csv")
    suppliers: str = Field(default="data/suppliers.csv")


class UserConfig(BaseModel):
    email: str = Field(description="Demo user email address")
    full_name: str
    roles: list[str] = Field(default_factory=list)

    @field_validator("email")
    @classmethod
    def email_must_be_valid(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("must be a valid email address")
        return v


class DashboardsConfig(BaseModel):
    default: str = Field(default="")


class ReportsConfig(BaseModel):
    featured: list[str] = Field(default_factory=list)


class WorkspacesConfig(BaseModel):
    default: str = Field(default="")


class ValidateConfig(BaseModel):
    min_sales_orders: int = Field(default=0, ge=0)
    min_items: int = Field(default=0, ge=0)
    min_customers: int = Field(default=0, ge=0)
    required_doctypes: list[str] = Field(default_factory=list)


# ── App entry ─────────────────────────────────────────────────────────────────

_RESERVED_APPS = {"frappe"}


class AppEntry(BaseModel):
    """A Frappe app to fetch (bench get-app) and install at site-creation time."""

    name: str
    source: Literal["frappe", "github", "local"] = "frappe"
    url: str | None = None  # required when source="github"
    branch: str | None = None  # optional for frappe/github; ignored for local
    host_path: str | None = None  # required when source="local" (absolute host path)

    @model_validator(mode="after")
    def validate_source_fields(self) -> AppEntry:
        if self.source == "github" and not self.url:
            raise ValueError("url is required when source='github'")
        if self.source == "local" and not self.host_path:
            raise ValueError("host_path is required when source='local'")
        if self.source == "frappe" and self.url:
            raise ValueError("url must not be set when source='frappe'")
        return self


# ── Root model ────────────────────────────────────────────────────────────────


class IndustryConfig(BaseModel):
    """Root configuration model for industry.yaml."""

    # Identity
    name: str = Field(description="Display name, e.g. 'Garment Manufacturing'")
    slug: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_-]*$")] = Field(
        description="URL-safe identifier matching the directory name"
    )
    version: str = Field(default="1.0.0", description="Industry package version (semver)")
    description: str = Field(default="")
    maintainer: str = Field(default="")
    license: str = Field(default="MIT")

    # ERPNext / Frappe
    erpnext_version: str = Field(default="v15", description="ERPNext image tag")
    required_apps: list[str] = Field(
        default_factory=lambda: ["frappe", "erpnext"],
        description="Frappe apps already in the Docker image (install-only, no fetch needed).",
    )
    extra_apps: list[AppEntry] = Field(
        default_factory=list,
        description="Apps to fetch (bench get-app) and install; NOT pre-baked in the Docker image.",
    )

    # Sub-configs
    company: CompanyConfig
    site: SiteConfig = Field(default_factory=lambda: SiteConfig(name="demo.localhost"))
    modules: list[str] = Field(default_factory=list, description="ERPNext modules to enable")
    seed: SeedConfig = Field(default_factory=SeedConfig)
    fixtures: FixturesConfig = Field(default_factory=FixturesConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    users: list[UserConfig] = Field(default_factory=list)
    dashboards: DashboardsConfig = Field(default_factory=DashboardsConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)
    workspaces: WorkspacesConfig = Field(default_factory=WorkspacesConfig)
    validate_config: ValidateConfig = Field(
        default_factory=ValidateConfig,
        alias="validate",
    )

    # Runtime-injected (not from YAML)
    industry_dir: Path = Field(
        default=Path("."), exclude=True, description="Absolute path to industry directory"
    )

    model_config = {"populate_by_name": True}

    @model_validator(mode="after")
    def site_name_matches_slug(self) -> IndustryConfig:
        expected = f"{self.slug}.localhost"
        if self.site.name != expected:
            raise ValueError(
                f"site.name must be '{expected}' (got '{self.site.name}'). "
                "This convention ensures consistent routing."
            )
        return self

    @model_validator(mode="after")
    def validate_extra_apps(self) -> IndustryConfig:
        extra_names = [e.name for e in self.extra_apps]
        for name in extra_names:
            if name in _RESERVED_APPS:
                raise ValueError(f"'{name}' is a reserved app and cannot appear in extra_apps")
            if name in self.required_apps:
                raise ValueError(
                    f"App '{name}' appears in both required_apps and extra_apps. "
                    "Remove it from required_apps; extra_apps handles fetching + installing."
                )
        if len(extra_names) != len(set(extra_names)):
            raise ValueError("extra_apps contains duplicate app names")
        return self

    @model_validator(mode="after")
    def no_duplicate_user_emails(self) -> IndustryConfig:
        emails = [u.email for u in self.users]
        if len(emails) != len(set(emails)):
            raise ValueError("users list contains duplicate email addresses")
        return self


# ── Loader ────────────────────────────────────────────────────────────────────


def load_industry_config(yaml_path: Path) -> IndustryConfig:
    """
    Parse and validate an industry.yaml file.

    Args:
        yaml_path: Absolute path to industry.yaml

    Returns:
        Validated IndustryConfig instance

    Raises:
        InvalidIndustryConfigError: If the file is missing required fields or fails validation
        FileNotFoundError: If yaml_path does not exist
    """
    from demostackkit.core.exceptions import InvalidIndustryConfigError

    if not yaml_path.exists():
        raise FileNotFoundError(f"industry.yaml not found: {yaml_path}")

    try:
        raw: dict[str, Any] = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise InvalidIndustryConfigError(str(yaml_path), [f"YAML parse error: {exc}"]) from exc

    if not isinstance(raw, dict):
        raise InvalidIndustryConfigError(str(yaml_path), ["industry.yaml must be a YAML mapping"])

    # Auto-set site name from slug if not provided
    slug = raw.get("slug", "")
    if "site" not in raw:
        raw["site"] = {"name": f"{slug}.localhost"}
    elif "name" not in raw.get("site", {}):
        raw["site"]["name"] = f"{slug}.localhost"

    try:
        config = IndustryConfig.model_validate(raw)
    except Exception as exc:
        raw_errors = getattr(exc, "errors", None)
        errors = [str(e) for e in raw_errors()] if callable(raw_errors) else [str(exc)]
        raise InvalidIndustryConfigError(str(yaml_path), errors) from exc

    config.industry_dir = yaml_path.parent
    return config
