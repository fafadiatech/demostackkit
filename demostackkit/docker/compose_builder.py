"""
Dynamically generate Docker Compose service snippets for third-party industries.

When `demostackkit up <industry>` is called for an industry not in the
master compose file, ComposeBuilder generates a temporary override file
and passes it to ComposeRunner via the -f flag.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from demostackkit.core.config import IndustryConfig


# These industries have their seeder services baked into the master compose file.
_BUILTIN_INDUSTRIES = {"garment", "chemical", "epc", "solar", "jewellery", "automobile", "distribution", "healthcare"}

_ERPNEXT_ENV_ANCHOR = {
    "FRAPPE_SITE_NAME_HEADER": "$$host",
    "BACKEND": "backend:8000",
    "SOCKETIO": "websocket:9000",
    "DB_HOST": "db",
    "DB_PORT": "3306",
    "REDIS_CACHE": "redis-cache:6379",
    "REDIS_QUEUE": "redis-queue:6379",
}


def build_seeder_service(config: IndustryConfig, industries_root: Path) -> dict:
    """
    Generate the Docker Compose service definition for a seeder container.

    The seeder container uses the demostackkit/seeder image, mounts the
    industry's seeders directory, and exits after completing.
    """
    slug = config.slug
    service_name = f"seeder-{slug}"

    return {
        service_name: {
            "image": "demostackkit/seeder:latest",
            "profiles": [slug],
            "environment": {
                **_ERPNEXT_ENV_ANCHOR,
                "DSK_INDUSTRY": slug,
                "DSK_SITE": config.site.name,
                "DSK_SEED_PHASE": "${DSK_SEED_PHASE:-all}",
                "DSK_RANDOM_SEED": str(config.seed.random_seed),
            },
            "volumes": [
                "sites:/home/frappe/frappe-bench/sites",
                f"{industries_root}:/demostackkit/industries:ro",
                "logs:/home/frappe/frappe-bench/logs",
            ],
            "depends_on": {
                "backend": {"condition": "service_healthy"}
            },
            "restart": "no",
        }
    }


def write_generated_compose(config: IndustryConfig, industries_root: Path, output_dir: Path) -> Path:
    """
    Write a docker-compose override file for the given industry.

    Returns the path to the generated file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{config.slug}-seeder.yml"

    compose_doc = {
        "services": build_seeder_service(config, industries_root),
        "volumes": {
            "sites": {"external": True},
            "logs": {"external": True},
        },
    }

    output_path.write_text(yaml.dump(compose_doc, default_flow_style=False), encoding="utf-8")
    return output_path


def needs_generated_compose(slug: str) -> bool:
    """Return True if the industry requires a dynamically generated compose file."""
    return slug not in _BUILTIN_INDUSTRIES
