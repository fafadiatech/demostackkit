# Changelog

All notable changes to DemoStackKit, grouped by week. Most recent week first.

---

## Week of 2026-08-24 → 2026-08-30

### Added

- **Ingredient Trading & Distribution industry (`ingredienttrade`)** — Ingredient Traders & Distributors Pvt Ltd, a bulk food-ingredient trading and distribution company procuring from commodity growers, processors and broad-line distributors, with no manufacturing (`production_orders: 0`). 20 customers, 20 suppliers, multi-warehouse stock management, Assets and Support modules for maintenance seeding. (`e508a62`, ref #27)
- **Ingredient Manufacturing industry (`ingredientmfg`)** — Alpha Ingredient Manufacturing Pvt Ltd, a batch-process food and nutraceutical ingredient manufacturer covering raw botanical/chemical procurement, solvent extraction, standardisation, quality testing and B2B dispatch. 6-step routing (weighing/dosing → solvent extraction → filtration/clarification → drying/standardization → quality testing → filling/packing), 14 finished-goods BOMs, 15 customers, 15 suppliers, full HR/payroll/asset/project seeding. (`d11ac84`, ref #26)
- **Abrasives & Industrial Polishing Equipment industry (`abrasives`)** — Alpha Abrasives Pvt Ltd, a hybrid abrasives manufacturer and industrial-tools wholesaler modelled on AJ Abrasives. Combines `electrical`'s in-house BOM/routing/QC pattern (bonded abrasive wheels, abrasive/flap discs, coated abrasive belts through a 5-step mixing-bonding → pressing → curing → grading/QC → packing routing, with grit consistency/wheel balance/burst-RPM/bond hardness quality checks) with `automobile`/`distribution`'s buy-and-resell pattern (polishing machines, power/pneumatic tools, polishing consumables — no BOM) in a single company. 18 customers, 12 suppliers split raw-material vs. machine-import, three-warehouse layout, 13 manufactured BOMs, split sales/purchase generation (~40% manufactured / ~60% traded), full HR/payroll/asset/project seeding.

---

## Week of 2026-08-17 → 2026-08-23

### Added

- **Maintenance & Support seeding** — every industry now seeds an in-house Asset Register (`Asset Category`, `Asset`, `Asset Maintenance` with a Completed log in the past and a Planned one in the future) plus customer-facing `Maintenance Schedule`/`Maintenance Visit`, `Warranty Claim`, `Issue` and `Issue Type`. New shared engine in `demostackkit/seeder/asset_seeder.py` and `support_seeder.py` (per-industry `01_master/14_assets.py` and `15_issue_types.py`), plus fully shared, no-per-industry-data seeders: `demostackkit/seeders/01_master/90_asset_maintenance.py` and `02_transactions/{245_maintenance_contracts,246_warranty_claims,247_issues}.py`. Adds `Assets` and `Support` to every industry's modules.
- **Multi-level BOM support** — chemical, crockery, drones, electrical, evmfg, garment, jewellery, print3d and solar industries now seed sub-assembly/intermediate BOMs (e.g. electrical's wound HV/LV coils, core and switchgear busbar assembly; chemical's intermediates) that finished-good BOMs consume, so BOM reports explode two levels deep instead of listing raw materials directly. New sub-assembly/intermediate items added to each industry's `items.csv`. (`b0f48d6`, ref #21)
- **Project management seeding** — every industry now ships a four-project portfolio with phase (group) tasks, `depends_on` chains for the Gantt chart, per-employee assignment and a full status spread for the Kanban board. New `demostackkit/seeder/projects.py` (pure planning logic) and `project_seeders.py` (shared run logic), per-industry `01_master/13_projects.py` and `02_transactions/04_projects.py`, plus shared seeders for employee logins (84), timesheets (250), the status/assignment pass (260) and the Task Kanban board (270). Adds `Projects` to every industry's modules and `seed.volumes.projects` / `seed.volumes.timesheets`. (`024adb9`, ref #15)
- **Logins for seeded employees** — `01_master/84_employee_users.py` creates one User per Employee, links `Employee.user_id` and grants `Projects User`, so tasks can be assigned to the real workforce instead of the four generic demo logins. (`024adb9`, ref #15)
- **Payroll seeding** — new `demostackkit/seeder/payroll.py` module with shared run logic in `payroll_seeder.py`; every industry now carries a thin `01_master/12_payroll.py` with its own `ANNUAL_CTC` table. India industries get monthly structures; US industries (`print3d`, `hobbytcg`, `vanilla`) get hourly/timesheet payroll automatically from the company's country. (`d6bc117`, `ed31806`, ref #14)
- **Standard scrap / rejected / rework warehouses** — a shared `01_master/61_standard_warehouses.py` seeder now creates these three warehouses for every industry; the per-industry warehouse seeders (crockery, drones, electrical, evmfg, garment, print3d) were trimmed accordingly. (`6a596ff`, ref #11)
- **Opening stock balances** — new `01_master/90_opening_stock.py` seeder with configuration hooks in `core/config.py`, `industry.yaml` templates, and helpers in `seeder/utils.py`, so demo sites start with non-zero inventory. (`fdcce6f`, ref #13)
- **Employee master data** for automobile, chemical, crockery, distribution, drones, electrical, epc, evmfg, garment, healthcare, hobbytcg, jewellery, print3d, solar and vanilla industries (`11_employees.py` per industry). (`f475cf2`, `ed31806`, ref #9)

### Changed

- **`electrical` and `hobbytcg`** — `industry.yaml` now declares HRMS, telephony and Helpdesk in `extra_apps`, matching the other industries that ship HR & Payroll by default. (`7d0a770`)

### Fixed

- **Stale `apps.txt` after container recreation** — `demostackkit up` now prunes `sites/apps.txt` entries whose app directory is missing from the bench (while preserving apps the current industry will re-fetch), so a backend image bump or compose down/up no longer raises `ModuleNotFoundError` before seeding starts. (`7d0a770`)
- **Extra app assets 404 in the frontend** — `demostackkit up` and `install-app` now build and materialize static assets for `extra_apps` into `sites/assets/` as real files instead of symlinks, so nginx can serve HRMS, Helpdesk and other app icons. (`5024503`)
- **Missing Fiscal Year** — added a `01_master/00_fiscal_years.py` seeder and fiscal-year window helpers, wired into `demostackkit up`; every industry's company seeder now relies on it instead of assuming a year exists. (`396aee4`, ref #10)
- **Missing seed data** across industries — corrected workstations, BOM linkage, sales-order generation and print3d item data. (`f475cf2`, ref #9)
- **`ModuleNotFoundError` for extra apps in background workers** — `infra/docker-compose.yml` now shares the `apps` and `env` volumes with the scheduler, queue and websocket containers (previously only `sites` and `logs` were shared), so apps fetched via `bench get-app` on the backend are importable everywhere, not just in the container that ran `get-app`. (`dc4ccaa`, ref #3)

---

## Week of 2026-08-10 → 2026-08-16

### Added

- **Hobby Shop & TCG Retail industry (`hobbytcg`)** — full industry pack: company, item groups, items, customers, suppliers, warehouses, purchase orders and sales orders, with CSV fixtures. (`e66f250`, ref #2)
- **Electrical industry seed data** — new `electrical` industry with masters, transactions and CSV fixtures. (`3d3baea`)

### Changed

- README restructured with a navigable index for easier browsing. (`eafba7f`)
- Logos reworked to render correctly in dark mode. (`0429fe4`, `aefe574`)

### Fixed

- Minor typos throughout the docs. (`5d97a11`)

---

## Week of 2026-08-03 → 2026-08-09

### Added

- **Initial DemoStackKit implementation** — CLI, Docker/infra stack and seeder framework for spinning up ERPNext demo environments. (`44ed950`)
- **Industry fixtures and seed data** for the first wave of industries. (`44203b7`)
- **Manufacturing seeding** — BOMs, Workstations, Operations and Routes. (`dbd1226`)
- **Quality Inspection** generation for manufacturing industries. (`7508bc4`)
- **App installation support** — install additional Frappe apps into a demo site. (`ac1732a`)
- **Version toggle and `purge` command** for switching ERPNext versions and doing a full wipe. (`fc51f76`)
- **Drone and Crockery industries.** (`cbe9f60`)
- **EV manufacturing demo data.** (`9fd6998`)
- **3D Printing Service (`print3d`) and Vanilla options** — Vanilla bootstraps users and a company only. (`720329e`, `e5f2dd8`)
- **Helpdesk and HRMS installed by default** for all industries. (`e7c1e4c`)
- Multi-user creation during bootstrap. (`f622e26`)

### Changed

- Large DRY refactor across the seeder codebase (141 files). (`9a701c3`)
- Repo-wide lint cleanup (167 files). (`7bf16ca`)
- README expanded with usage and architecture details. (`de58c3c`, `42f8543`)
- Project logo updated. (`16d4259`)

### Fixed

- Solar industry Item Group loading. (`7c8a202`)
- Docker instances not starting correctly. (`2f66f92`)
- Seeder image pull error on `demostackkit up`. (`abd9a64`)
- Backend health check failure caused by a missing gunicorn path and site config. (`26150a7`)
- CLI command invocation. (`b3e8883`, `1948a86`)
