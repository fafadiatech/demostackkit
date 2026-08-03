# demostackkit

> Create, manage and distribute ERPNext demo environments for different industries — with a single command.

[![CI](https://github.com/demostackkit/demostackkit/actions/workflows/ci.yml/badge.svg)](https://github.com/demostackkit/demostackkit/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

## What is demostackkit?

demostackkit makes it trivial to spin up a **fully seeded** ERPNext demo environment for any industry vertical. After one command, you get:

- ERPNext v15 installed and running
- A demo company configured
- Master data loaded (customers, suppliers, items, warehouses, BOMs)
- Transactional data seeded (sales orders, purchase orders, stock entries)
- Sample users with appropriate roles
- Dashboards, reports, workspaces and print formats
- **Ready to demonstrate immediately**

## Supported Industries

| Industry | Slug | URL |
|---|---|---|
| Garment Manufacturing | `garment` | http://garment.localhost |
| Chemical Manufacturing | `chemical` | http://chemical.localhost |
| Engineering Procurement & Construction | `epc` | http://epc.localhost |
| Solar Manufacturing | `solar` | http://solar.localhost |
| Jewellery Manufacturing | `jewellery` | http://jewellery.localhost |
| Automobile Dealership | `automobile` | http://automobile.localhost |
| Distribution | `distribution` | http://distribution.localhost |
| Healthcare | `healthcare` | http://healthcare.localhost |

## Quick Start

### Prerequisites

- Docker Engine >= 24
- Docker Compose plugin >= 2.20
- Python >= 3.10
- 4 GB RAM, 10 GB disk

### Installation

```bash
git clone https://github.com/demostackkit/demostackkit.git
cd demostackkit
pip install -e .
```

### Start a Demo

```bash
# First-time setup
demostackkit init
demostackkit doctor

# Spin up the garment demo
demostackkit up garment

# Access at http://garment.localhost
# Login: Administrator / admin
```

### CLI Reference

```
demostackkit init              # First-time setup (creates infra/.env)
demostackkit list              # Show all available industries
demostackkit doctor            # Check host prerequisites
demostackkit create garment    # Create Frappe site (no seeding)
demostackkit up garment        # Start stack + seed data
demostackkit down garment      # Stop stack
demostackkit reset garment     # Destroy and rebuild (deterministic)
demostackkit seed garment      # Re-run seeders
demostackkit seed garment --phase master       # Master data only
demostackkit seed garment --phase transactions # Transactions only
demostackkit backup garment    # bench backup
demostackkit restore garment <file>  # bench restore
demostackkit validate          # Validate all industry configs
demostackkit validate garment  # Validate one industry
```

## Architecture

```
Infrastructure (MariaDB, Redis, Traefik)
        ↓
ERPNext / Frappe (shared, multi-site)
        ↓
Industry Package (garment/, chemical/, ...)
        ↓
Master Data Seeders (idempotent)
        ↓
Transaction Seeders (deterministic random)
```

All industries share a **single ERPNext installation**. Each industry gets its own Frappe site (`garment.localhost`, `chemical.localhost`, etc.). This keeps memory usage at ~500 MB per additional site instead of ~5 GB per industry.

## Repository Structure

```
demostackkit/
├── demostackkit/          # Python package (CLI + framework)
│   ├── cli/               # Typer commands
│   ├── core/              # Config, discovery, exceptions
│   ├── seeder/            # BaseSeeder, runner, loader
│   ├── erpnext/           # bench CLI wrapper
│   └── docker/            # compose runner, builder
├── industries/
│   ├── _template/         # Copy this to add a new industry
│   ├── garment/           # Garment Manufacturing
│   ├── chemical/
│   └── ...
├── infra/
│   └── docker-compose.yml # Master compose (shared infra + profiles)
├── tests/
└── docs/
```

## Adding a New Industry

```bash
# Scaffold from template
make new-industry SLUG=furniture

# Edit the generated files
$EDITOR industries/furniture/industry.yaml
# ... add seeders, CSV data, fixtures

# Validate and test
demostackkit validate furniture
demostackkit up furniture
```

See [docs/creating-an-industry.md](docs/creating-an-industry.md) for the full guide.

## Deterministic Resets

`demostackkit reset garment` always produces **byte-for-byte identical data**. All transactional seeders use a seeded `random.Random` instance (never `random.random()`), with the seed taken from `industry.yaml`. This makes demo environments reproducible and reliable.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). All contributions welcome — especially new industry packages!

## License

MIT © DemoStackKit Contributors
