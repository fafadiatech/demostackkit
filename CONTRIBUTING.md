# Contributing to demostackkit

Thank you for your interest in contributing! This guide explains how to contribute new industry packages, bug fixes, and improvements.

## Getting Started

```bash
git clone https://github.com/demostackkit/demostackkit.git
cd demostackkit
pip install -e ".[dev]"
pre-commit install
```

Run the test suite:

```bash
make test-unit
```

## Adding a New Industry

The fastest path to contributing is adding a new industry package.

### 1. Scaffold the directory

```bash
make new-industry SLUG=furniture
```

This copies `industries/_template/` to `industries/furniture/`.

### 2. Edit industry.yaml

At minimum, update:
- `name`, `slug`, `description`
- `company` (name, abbr, currency, country)
- `seed.random_seed` — pick a unique integer not used by other industries
- `users` — add 3-5 demo users with realistic roles

### 3. Add data files

Populate CSV files in `industries/furniture/data/`:
- `items.csv` — 20-50 items with realistic codes, names, groups, and rates
- `customers.csv` — 15-20 customers
- `suppliers.csv` — 10-15 suppliers

Column headers must match the garment example exactly.

### 4. Write seeders

Seeders live in `industries/furniture/seeders/`:
- `01_master/` — idempotent master data (Company, Items, Customers, Suppliers, Warehouses)
- `02_transactions/` — transactional data (Sales Orders, Purchase Orders, etc.)

**Critical rule**: All seeders must inherit from `BaseMasterSeeder` or `BaseTransactionSeeder`. All random values must use `self.ctx.random`, never `random.random()`.

### 5. Validate

```bash
demostackkit validate furniture
```

### 6. Submit a PR

- Run `make lint` and `make test-unit` before pushing
- Include a short description of the industry and the demo scenario it covers

## Writing Seeders

### Master Seeder

```python
from demostackkit.seeder.base import BaseMasterSeeder


class ItemSeeder(BaseMasterSeeder):
    label = "Items"
    priority = 30  # Lower = runs first

    def validate(self):
        # Return errors if preconditions are not met
        if not self.ctx.cache_get("company_name"):
            return ["company_name not in cache"]
        return []

    def run(self):
        # All inserts must be idempotent
        # Use frappe.db.exists() before every insert
        ...
```

### Transaction Seeder

```python
from demostackkit.seeder.base import BaseTransactionSeeder


class SalesOrderSeeder(BaseTransactionSeeder):
    label = "Sales Orders"
    _volume_attr = "sales_orders"  # reads from industry.yaml seed.volumes

    def run(self):
        rng = self.ctx.random  # ALWAYS use this, never random.random()
        customers = self.ctx.cache_get("customer_names", [])
        for _ in range(self.volume):
            customer = rng.choice(customers)
            # ... create the order
```

## Code Style

- Python 3.10+
- Ruff for linting and formatting (`make lint`, `make format`)
- Type annotations required for all public functions
- Tests for any new framework code (`tests/unit/`)

## Commit Style

Use conventional commits:
- `feat: add solar manufacturing industry`
- `fix: correct warehouse parent in garment seeder`
- `docs: add architecture diagram`
- `test: add discovery edge cases`

## Questions?

Open a GitHub Discussion or file an issue.
