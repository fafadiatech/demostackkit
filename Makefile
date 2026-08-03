# demostackkit Makefile
# Run `make help` to see available targets.

.DEFAULT_GOAL := help
.PHONY: help install dev lint format test test-unit test-integration validate \
        up-garment down-garment reset-garment seed-garment \
        build-seeder docker-pull clean

PYTHON      := python3
PIP         := pip
PYTEST      := pytest
DSK         := demostackkit
COMPOSE_DIR := infra

# ── Development ───────────────────────────────────────────────────────────────

install:  ## Install demostackkit in the current virtualenv
	$(PIP) install -e .

dev:  ## Install with dev dependencies
	$(PIP) install -e ".[dev]"
	pre-commit install

lint:  ## Run ruff linter
	ruff check demostackkit/ tests/

format:  ## Auto-format code with ruff
	ruff format demostackkit/ tests/

typecheck:  ## Run mypy type checker
	mypy demostackkit/

test:  ## Run all non-e2e tests
	$(PYTEST) tests/unit/ tests/integration/ -m "not e2e" -v

test-unit:  ## Run unit tests only (fast, no Docker required)
	$(PYTEST) tests/unit/ -v --tb=short

test-integration:  ## Run integration tests (filesystem, no Docker)
	$(PYTEST) tests/integration/ -v --tb=short

test-e2e:  ## Run end-to-end tests (requires Docker + running stack)
	$(PYTEST) tests/e2e/ -v --tb=short -m e2e

coverage:  ## Run tests with coverage report
	$(PYTEST) tests/unit/ --cov=demostackkit --cov-report=html --cov-report=term
	@echo "Open htmlcov/index.html in browser"

validate:  ## Validate all industry configs
	$(DSK) validate

# ── Initialisation ────────────────────────────────────────────────────────────

init:  ## First-time setup: create infra/.env
	$(DSK) init

doctor:  ## Check host environment
	$(DSK) doctor

list:  ## List available industries
	$(DSK) list

# ── Garment Manufacturing ─────────────────────────────────────────────────────

up-garment:  ## Start garment demo environment
	$(DSK) up garment

down-garment:  ## Stop garment demo environment
	$(DSK) down garment

reset-garment:  ## Completely reset garment demo (destructive)
	$(DSK) reset garment --yes

seed-garment:  ## Re-run seeders for garment (master + transactions)
	$(DSK) seed garment

seed-garment-master:  ## Seed only master data for garment
	$(DSK) seed garment --phase master

seed-garment-tx:  ## Seed only transactional data for garment
	$(DSK) seed garment --phase transactions

backup-garment:  ## Backup garment site
	$(DSK) backup garment

# ── Docker ────────────────────────────────────────────────────────────────────

build-seeder:  ## Build the demostackkit seeder Docker image
	docker build \
		--file docker/images/seeder/Dockerfile \
		--tag demostackkit/seeder:latest \
		.

docker-pull:  ## Pull latest ERPNext images
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml pull

docker-ps:  ## Show running containers
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml ps

docker-logs:  ## Stream logs from all containers
	docker compose -f $(COMPOSE_DIR)/docker-compose.yml logs -f --tail=100

# ── Scaffolding ───────────────────────────────────────────────────────────────

new-industry:  ## Scaffold a new industry: make new-industry SLUG=furniture
ifndef SLUG
	$(error SLUG is required: make new-industry SLUG=furniture)
endif
	@bash scripts/generate-industry.sh $(SLUG)

# ── Housekeeping ──────────────────────────────────────────────────────────────

clean:  ## Remove Python build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/ .coverage

help:  ## Show this help message
	@echo ""
	@echo "demostackkit Makefile targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2}'
	@echo ""
