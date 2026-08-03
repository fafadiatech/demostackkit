You are an experienced ERPNext, Frappe, Docker and Python architect.

I want to build an open-source project called "demostackkit".

## Objective

demostackkit should make it extremely easy to create, manage and distribute ERPNext demo environments for different industries.

Examples:

- Garment Manufacturing
- Chemical Manufacturing
- Engineering Procurement & Construction (EPC)
- Solar Manufacturing
- Jewellery Manufacturing
- Automobile Dealership
- Distribution
- Healthcare

The goal is that anyone can clone the repository and bring up a fully working industry-specific ERPNext demo using a single command.

For example:

docker compose up garment

or

demostackkit up garment

After startup the user should have:

- ERPNext installed
- Demo company created
- Master data loaded
- Demo transactions loaded
- Dashboards
- Reports
- Print Formats
- Workspaces
- Sample Users
- Ready to demonstrate immediately

--------------------------------------------------

## High Level Requirements

### 1. Open Source

The project should be MIT licensed.

Repository should be clean, modular and easy to contribute to.

--------------------------------------------------

### 2. Technology Stack

- Docker Compose
- ERPNext
- Frappe
- Python
- Bash
- Makefile
- YAML configuration

No Kubernetes.

--------------------------------------------------

### 3. Architecture

Design the project so that:

Infrastructure

↓

ERPNext/Frappe

↓

Industry Package

↓

Master Data

↓

Business Scenarios

Everything should be modular.

--------------------------------------------------

### 4. Industry Packages

Each industry should be completely isolated.

Example

industries/

    garment/

    chemical/

    epc/

    solar/

    jewellery/

Each package should contain

- fixtures
- seed scripts
- CSV files
- sample images
- print formats
- workspace
- reports
- dashboards

--------------------------------------------------

### 5. Data Loading

Separate

MASTER DATA

from

TRANSACTIONAL DATA

Master Data examples

- Company
- Customers
- Suppliers
- Item Groups
- Items
- Warehouses
- UOM
- BOM
- Operations
- Workstations
- Cost Centers

Transactional Data examples

- Sales Orders
- Purchase Orders
- Production Orders
- Projects
- Tasks
- Stock Entries
- Material Requests

Master data should be idempotent.

Transactional data should be generated via Python seed scripts.

--------------------------------------------------

### 6. CLI

Design a CLI called

demostackkit

Commands should include

demostackkit init

demostackkit create garment

demostackkit up garment

demostackkit down garment

demostackkit reset garment

demostackkit seed garment

demostackkit backup garment

demostackkit restore garment

demostackkit export garment

demostackkit validate garment

demostackkit list

demostackkit doctor

--------------------------------------------------

### 7. Configuration

Each industry should have

industry.yaml

Example

name:

version:

company:

currency:

country:

modules:

seed:

fixtures:

users:

dashboards:

reports:

workspaces:

--------------------------------------------------

### 8. Docker

Infrastructure should be shared.

Avoid duplicating containers.

Support

docker compose up garment

docker compose up epc

using compose overrides or profiles.

--------------------------------------------------

### 9. Reproducibility

Running

demostackkit reset garment

should always recreate exactly the same demo.

Random values should use deterministic seeds.

--------------------------------------------------

### 10. Extensibility

Third-party developers should be able to create

industries/furniture

without changing the core framework.

The framework should automatically discover industries.

--------------------------------------------------

### 11. Documentation

Generate documentation for

Installation

Architecture

Creating a new industry

Adding fixtures

Writing seed scripts

Docker

Troubleshooting

FAQ

--------------------------------------------------

### 12. CI/CD

GitHub Actions should

- lint
- run tests
- validate fixtures
- ensure seed scripts execute
- build Docker images
- verify industries can be created

--------------------------------------------------

### 13. Testing

Use pytest.

Test

- seed scripts
- fixture validation
- CLI
- Docker startup
- industry discovery

--------------------------------------------------

### 14. Deliverables

Produce

1. Overall architecture

2. Repository structure

3. Package layout

4. Python package architecture

5. CLI architecture

6. Docker architecture

7. Configuration format

8. Seed framework

9. Plugin architecture

10. Example industry

11. Makefile

12. GitHub Actions

13. Future roadmap

14. Coding standards

15. Contribution guide

--------------------------------------------------

### Important

Do NOT immediately generate implementation code.

Instead, act like a software architect.

Challenge assumptions.

Identify weaknesses.

Suggest improvements.

Recommend better folder structures if appropriate.

Explain why each design decision is made.

The resulting architecture should be suitable for an open-source project that will be maintained for many years and attract community contributions.