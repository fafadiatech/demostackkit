# DemoStackKit

<div align="center">
  <img src="logo.png" alt="DemoStackKit" width="400"/>
</div>

> Create, manage and distribute ERPNext demo environments for different industries — with a single command.

DemoStackKit is an open-source toolkit for quickly spinning up industry-specific ERPNext demo environments with realistic sample data. It includes ready-to-use demos for Garment Manufacturing, Chemical Manufacturing, Engineering Procurement & Construction (EPC), Solar Manufacturing, Auto Dealerships, and Jewellery Manufacturing.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

## What is demostackkit?

demostackkit makes it trivial to spin up a **fully seeded** ERPNext demo environment for any industry vertical. After one command, you get:

- ERPNext v15 or v16 installed and running
- A demo company configured
- Master data loaded (customers, suppliers, items, warehouses, BOMs)
- Transactional data seeded (sales orders, purchase orders, stock entries, quality inspections)
- Sample users with appropriate roles
- Dashboards, reports, workspaces and print formats
- **Ready to demonstrate immediately**

## Supported Industries

| Industry | Slug | URL | Quality Inspections |
|---|---|---|---|
| Garment Manufacturing | `garment` | http://garment.localhost | ✓ |
| Chemical Manufacturing | `chemical` | http://chemical.localhost | ✓ |
| Solar Manufacturing | `solar` | http://solar.localhost | ✓ |
| Jewellery Manufacturing | `jewellery` | http://jewellery.localhost | ✓ |
| Drones Manufacturing | `drones` | http://drones.localhost | ✓ |
| Crockery Manufacturing | `crockery` | http://crockery.localhost | ✓ |
| 3D Printing Services | `print3d` | http://print3d.localhost | ✓ |
| EV Manufacturing | `evmfg` | http://evmfg.localhost | ✓ |
| Engineering Procurement & Construction | `epc` | http://epc.localhost | — |
| Automobile Dealership | `automobile` | http://automobile.localhost | — |
| Distribution | `distribution` | http://distribution.localhost | — |
| Healthcare | `healthcare` | http://healthcare.localhost | — |
| Vanilla (clean slate) | `vanilla` | http://vanilla.localhost | — |

### Garment Manufacturing (`garment`)

Alpha Garments Pvt Ltd — apparel manufacturer producing T-shirts, shirts, jeans, jackets, and dresses through a complete cut-make-trim workflow. Includes:

- **7 workstations** — Cutting Table, Sewing Machine, Overlock Machine, Button Machine, Pressing Station, QC Table, Packaging Station
- **Single CMT routing** — 7 sequential operations totalling ~2.5 hrs per garment
- **11 finished-goods BOMs** — fabric + thread + trims + packaging per garment type
- **Quality inspections** — thread count, tensile strength, colour fastness, shrinkage (30 QIs, 85% pass rate)
- **HR & Payroll enabled** — 20 customers, 15 suppliers, 50 sales orders, 30 purchase orders

### Chemical Manufacturing (`chemical`)

Alpha Chemicals Pvt Ltd — batch-process chemical manufacturer covering raw material procurement, formulation, quality testing, and finished goods dispatch. Includes:

- **Batch production** — manufacture orders against BOMs with raw material consumption by weight and volume
- **Quality management** — chemical composition, viscosity, pH, and purity inspection parameters
- **50 sales orders, 30 purchase orders** — industrial buyers and chemical raw material vendors seeded over 180 days
- **25 quality inspections** across incoming, in-process, and outgoing stages

### Solar Energy (`solar`)

SunPower Solar Pvt Ltd — solar equipment distributor and EPC contractor. Covers panel and inverter procurement, balance-of-system components, battery storage, and project-based customer installations. Includes:

- **Projects module** — project-linked sales orders with milestone billing for installation contracts
- **BOMs with routing** — panel assembly workstations and operations for system integration
- **Items across technologies** — monocrystalline panels, string/micro inverters, MPPT charge controllers, lithium battery banks, mounting structures
- **12 customers, 10 suppliers** — EPC contractors, housing societies, commercial buyers, equipment vendors

### Jewellery Manufacturing (`jewellery`)

GoldStar Jewellers Pvt Ltd — jewellery manufacturer and wholesaler producing gold, silver, diamond, and platinum pieces. Covers precious metal procurement by weight, gemstone inventory, manufacturing orders, and retail/wholesale sales. Includes:

- **Precious metal procurement** — gold alloy, silver granules, platinum by gram and troy oz
- **Gemstone inventory** — diamonds, rubies, emeralds, sapphires tracked by carat and quality grade
- **Manufacturing BOMs** — rings, necklaces, bangles, earrings with metal + stone + setting components
- **50 sales orders** — retail boutiques and wholesale buyers across 180 days

### Drones Manufacturing (`drones`)

SkyForge Drones Pvt Ltd — drone manufacturer covering component procurement, PCB and frame assembly, firmware calibration, flight testing, quality inspection, and dispatch. Includes:

- **Full assembly routing** — from component sourcing through PCB assembly, frame build, calibration, and flight test
- **Quality inspections** — flight performance, sensor accuracy, communication range, hover stability (25 QIs)
- **HR & Payroll enabled** — 15 customers, 10 suppliers, 40 sales orders, 25 purchase orders
- **Featured reports** — Drone Assembly Report, Component Consumption Report

### Crockery Manufacturing (`crockery`)

PotteryPro Ceramics Pvt Ltd — ceramics and crockery manufacturer covering clay procurement, throwing, casting, bisque firing, glazing, and kiln firing. Includes:

- **Multi-stage kiln routing** — throwing/casting → bisque firing → glaze application → glaze firing → QC inspection
- **Quality inspections** — glaze coverage, dimensional tolerance, chip resistance, colour consistency (20 QIs)
- **HR & Payroll enabled** — 12 customers, 8 suppliers, 40 sales orders, 20 purchase orders
- **Featured reports** — Kiln Firing Report, Glaze Consumption Report

### 3D Printing Services (`print3d`)

A 3D print farm (PrintForge 3D Services) taking customer orders for parts printed via FDM (fused deposition modeling) and SLA (stereolithography) technologies. Includes:

- **Printers modelled as workstations** — FDM Printer Bank, SLA Printer Bank, Washing Station, UV Curing Chamber, Post-Processing Bench
- **Two production routings** — FDM Standard Route (5 steps) and SLA Standard Route (7 steps, adding IPA washing and UV curing)
- **Material procurement** — filaments (PLA, ABS, PETG, TPU) and resins (standard, engineering, ABS-like) with correct UOM per material (Kg / Litre)
- **9 finished-goods BOMs** — small/medium/large prototypes, functional parts, display models, each linked to its routing
- **Quality inspections** — dimensional accuracy (mm), surface roughness Ra (μm), layer adhesion, print completion (%)

### EV Manufacturing (`evmfg`)

Voltara EV Manufacturing Pvt Ltd — Indian EV manufacturer producing both electric cars and electric bikes. The central demo story is **shared component procurement** — the DC-DC converter, CCS2 charging port, instrument cluster, HV contactor, HV fuse, disc brake assemblies, copper busbars, and thermal pads all appear in BOMs for both vehicle families, naturally driving consolidated purchasing scenarios. Includes:

- **3 electric cars** — Sedan (72 kWh dual-motor), SUV (90 kWh dual-motor), Hatchback (54 kWh single-motor)
- **3 electric bikes** — Sport, City Commuter, Cargo; each using 18650-cell packs and hub motors
- **Two manufacturing routings** — EV Car Route (9 steps, ~40 hrs) and EV Bike Route (8 steps, ~6.5 hrs)
- **6 BOMs with 19–21 components each** — car BOMs use 21700 cells + 60 kW PMSM motors; bike BOMs use 18650 cells + 3 kW hub motors
- **Split sales order generation** — 40% car orders (qty 1–3, ₹12–22 lakh, 30–90 day lead) and 60% bike orders (qty 1–15, ₹80k–1.8 lakh, 7–30 day lead)

### Engineering Procurement & Construction (`epc`)

BuildRight EPC Pvt Ltd — EPC company running project-based operations covering material procurement per site, equipment tracking, sub-contractor billing, and milestone-based customer invoicing. No manufacturing. Includes:

- **Projects module** — project costing, milestone tracking, and material consumption linked per project
- **Pure procurement + billing** — no BOMs or production orders; workflow is PO → stock → project billing
- **50 sales orders, 30 purchase orders** — project milestones and material POs over 180 days
- **Featured reports** — Project Costing Report, Material Procurement Summary

### Automobile Dealership (`automobile`)

AutoDrive Motors Pvt Ltd — automobile dealership and service centre. Vehicle sales, spare parts procurement, lubricants, tyres, and fleet customer management — no manufacturing. Includes:

- **Sales-focused** — vehicles as stock items sold directly; no BOMs or production orders
- **Spare parts inventory** — multi-category parts catalogue across vehicle makes and models
- **20 customers, 15 suppliers** — fleet operators, individual buyers, OEM and aftermarket parts vendors
- **50 sales orders** — vehicle and parts sales with Featured reports: Vehicle Sales Report, Spare Parts Consumption

### FMCG Distribution (`distribution`)

QuickMove Distributors Pvt Ltd — FMCG distributor procuring from brands and fulfilling orders to supermarket chains and retail customers. No manufacturing. Includes:

- **High-volume trade flow** — 50 sales orders, 30 purchase orders across 20 customers and 15 suppliers
- **Multi-warehouse stock management** — regional warehouses with dispatch area and stock ageing tracking
- **Order fulfilment focus** — procurement, stock receipts, and delivery notes as the primary workflow
- **Featured reports** — Stock Ageing, Delivery Note Trends, Purchase Analytics

### Healthcare & Pharma (`healthcare`)

MedCare Healthcare Pvt Ltd — healthcare and pharmaceutical distributor covering medicine procurement, medical device stock, pharmacy dispensing, and hospital supply chain. Includes:

- **Healthcare module enabled** — patient registration, prescriptions, and clinical procedures
- **Pharma inventory** — medicines tracked by batch and expiry, controlled substance handling
- **Medical devices** — surgical instruments, diagnostic equipment, PPE alongside medicines
- **12 customers** — hospitals, clinics, pharmacies, and institutional buyers

### Vanilla (`vanilla`)

A minimal environment with only a company (Acme Corp) and demo users created — no master data or transactions are seeded. Use this as a clean slate for custom demonstrations, onboarding sessions, or interactive workshops where the audience populates data live.

```bash
demostackkit up vanilla
demostackkit up vanilla --currency EUR   # currency override works as usual
```

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

# Spin up any industry — examples:
demostackkit up garment    # Garment Manufacturing → http://garment.localhost
demostackkit up evmfg      # EV Manufacturing      → http://evmfg.localhost
demostackkit up print3d    # 3D Printing Services  → http://print3d.localhost
demostackkit up vanilla    # Clean slate            → http://vanilla.localhost

# Login: Administrator / admin (or any seeded user at Demo@1234)
```

### CLI Reference

```
demostackkit init              # First-time setup (creates infra/.env)
demostackkit list              # Show all available industries
demostackkit doctor            # Check host prerequisites
demostackkit use v16           # Switch active ERPNext version (v15 or v16)
demostackkit create garment    # Create Frappe site (no seeding)
demostackkit up garment        # Start stack + seed data
demostackkit down garment      # Stop stack
demostackkit reset garment     # Destroy and rebuild (deterministic)
demostackkit seed garment      # Re-run seeders
demostackkit seed garment --phase master       # Master data only
demostackkit seed garment --phase transactions # Transactions only
demostackkit up jewellery --currency USD       # Override currency at startup
demostackkit seed garment --currency INR       # Override currency for seeding
demostackkit backup garment    # bench backup
demostackkit restore garment <file>  # bench restore
demostackkit validate          # Validate all industry configs
demostackkit validate garment  # Validate one industry
demostackkit purge             # Destroy all containers and volumes
demostackkit purge --images    # Also remove pulled ERPNext images
demostackkit install-app garment hrms                          # Install app from frappe.io
demostackkit install-app garment hrms --source github --url … # Install from GitHub
demostackkit install-app garment myapp --source local --path … # Install from local directory
```

### Switching ERPNext Versions

You can run industries on either ERPNext v15 or v16. The version applies to the entire stack (all active industries share one ERPNext installation).

```bash
# Switch to v16
demostackkit use v16

# Bring down any running industry and restart it
demostackkit down garment
demostackkit up garment

# Switch back to v15 later
demostackkit use v15
demostackkit down garment
demostackkit up garment
```

The active version is stored in `infra/.env` as `ERPNEXT_VERSION`. Docker Compose uses this to pull the correct `frappe/erpnext` image tag automatically on the next `up`.

### Using Different Currencies per Industry

Each industry's default currency is set in its `industry.yaml` under `company.currency`. You can override it at runtime with `--currency` (ISO 4217 code) without touching any config files:

```bash
# Spin up EV Manufacturing with USD instead of default INR
demostackkit up evmfg --currency USD

# Spin up Jewellery with USD, 3D Printing with GBP
demostackkit up jewellery --currency USD
demostackkit up print3d --currency GBP

# Override currency when re-running seeders on an existing site
demostackkit seed evmfg --currency USD
```

The override applies to both the ERPNext setup wizard (company default currency) and all seeders.

### Full Wipe (purge)

`demostackkit purge` destroys all containers and Docker volumes (all site data). Add `--images` to also remove the cached ERPNext image layers.

```bash
# Wipe data, keep images cached (faster next startup)
demostackkit purge

# Wipe everything including images
demostackkit purge --images

# Skip confirmation
demostackkit purge --yes --images
```

Recommended workflow when switching versions:

```bash
demostackkit use v16
demostackkit purge --yes    # clear old site data
demostackkit up evmfg       # fresh v16 site — works for any industry
```

### Installing Extra Apps

Each industry can declare additional Frappe apps in `industry.yaml` under `extra_apps`. These are fetched via `bench get-app` and installed automatically on every `up`, `create`, and `reset`.

All industries ship with **HRMS** and **Helpdesk** pre-configured:

```yaml
# industries/evmfg/industry.yaml (all industries follow the same pattern)
extra_apps:
  - name: hrms          # Frappe HRMS — payroll, leaves, appraisals
    source: frappe
    branch: version-15
  - name: helpdesk      # Frappe Helpdesk — customer support tickets
    source: frappe
```

You can also add apps from GitHub or a local directory:

```yaml
extra_apps:
  - name: hrms
    source: github
    url: https://github.com/frappe/hrms
    branch: version-15

  - name: my_custom_app  # from a local directory on the host
    source: local
    host_path: /Users/me/projects/my_custom_app
```

To install an app into a **running stack** without modifying `industry.yaml`:

```bash
# From frappe.io
demostackkit install-app garment hrms
demostackkit install-app garment hrms --branch version-15

# From GitHub
demostackkit install-app garment hrms --source github --url https://github.com/frappe/hrms

# From a local directory
demostackkit install-app garment my_app --source local --path /Users/me/projects/my_app
```

If the app is already present in the bench, `get-app` is skipped and only `install-app` is run (idempotent).

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
