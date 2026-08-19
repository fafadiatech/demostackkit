# Changelog

All notable changes to DemoStackKit, grouped by week. Most recent week first.

---

## Week of 2026-08-17 → 2026-08-23

### Added

- **Project management seeding** — every industry now ships a four-project portfolio with phase (group) tasks, `depends_on` chains for the Gantt chart, per-employee assignment and a full status spread for the Kanban board. New `demostackkit/seeder/projects.py` (pure planning logic) and `project_seeders.py` (shared run logic), per-industry `01_master/13_projects.py` and `02_transactions/04_projects.py`, plus shared seeders for employee logins (84), timesheets (250), the status/assignment pass (260) and the Task Kanban board (270). Adds `Projects` to every industry's modules and `seed.volumes.projects` / `seed.volumes.timesheets`.
- **Logins for seeded employees** — `01_master/84_employee_users.py` creates one User per Employee, links `Employee.user_id` and grants `Projects User`, so tasks can be assigned to the real workforce instead of the four generic demo logins.
- **Payroll seeding** — new `demostackkit/seeder/payroll.py` module plus a chemical-industry payroll seeder (`01_master/12_payroll.py`) and unit tests, so demos ship with realistic payroll data. (`d6bc117`, ref #14)
- **Standard scrap / rejected / rework warehouses** — a shared `01_master/61_standard_warehouses.py` seeder now creates these three warehouses for every industry; the per-industry warehouse seeders (crockery, drones, electrical, evmfg, garment, print3d) were trimmed accordingly. (`6a596ff`, ref #11)
- **Opening stock balances** — new `01_master/90_opening_stock.py` seeder with configuration hooks in `core/config.py`, `industry.yaml` templates, and helpers in `seeder/utils.py`, so demo sites start with non-zero inventory. (`fdcce6f`, ref #13)
- **Employee master data** for chemical, crockery, drones, electrical, evmfg, garment, jewellery, print3d and solar industries (`11_employees.py` per industry). (`f475cf2`, ref #9)

### Fixed

- **Missing Fiscal Year** — added a `01_master/00_fiscal_years.py` seeder and fiscal-year window helpers, wired into `demostackkit up`; every industry's company seeder now relies on it instead of assuming a year exists. (`396aee4`, ref #10)
- **Missing seed data** across industries — corrected workstations, BOM linkage, sales-order generation and print3d item data. (`f475cf2`, ref #9)

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
