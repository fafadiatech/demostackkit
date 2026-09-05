# Changelog

All notable changes to DemoStackKit, grouped by week. Most recent week first.

---

## Week of 2026-08-31 → 2026-09-06

### Added

- **Batch & Serial No forward/backward traceability** — new shared `01_master/86_batch_tracking.py` flags every item referenced by a submitted default BOM for Manufacturing industries: components/sub-assemblies get `has_batch_no` + `create_new_batch` + `batch_number_series`, top-level finished goods get `has_serial_no` + `serial_no_series` instead by default (individually-identifiable, VIN-style — configurable via new `serialize_top_level_fg`). `02_transactions/215_production.py` (Work Order Material Transfer + Manufacture Stock Entries) and `220_delivery_notes.py` now explicitly select a real, already-in-stock batch/serial (FIFO or FEFO) for every outward row via ERPNext's own `get_auto_data`/`add_serial_batch_ledgers` — incoming movements (Purchase Receipt, Manufacture output) need no extra code since ERPNext auto-creates a new lot there once the naming series is set. `211_purchase_receipts.py` additionally stamps a cosmetic Vendor Batch identifier + the supplier link onto every auto-created Batch. New `seed.batch_tracking` config (`enabled`, `serialize_top_level_fg`, `based_on`) in `core/config.py`, enabled for all 11 Manufacturing-module industries. Also fixed a fresh-install-only bug found while verifying this end to end: `abrasives` and `electrical` had their Workstations/Operations/Routing/BOM seeders at priority 100 (vs. 70 everywhere else), running after Opening Stock (90) — renumbered to 62/64/66/68 so BOM data is always ready before the new seeder runs. (ref #4)
- **Production Plans, Work Orders & Job Cards** — new shared `02_transactions/215_production.py` seeds the manufacturing execution chain for every Manufacturing industry with an operation-backed BOM: submitted Production Plans (optionally linked to Sales Orders), Work Orders via ERPNext's own `make_work_order()`, and Job Cards with time logs / employees. Deliberate completed / in-progress / not-started mix so Production Analytics and Production Plan Summary have shop-floor data. Driven by the existing `seed.volumes.production_orders` knob (0 skips). (ref #40)
- **Bank + Bank Account masters and reconciliation data** — new shared `01_master/92_bank_accounts.py` creates a single demo Bank plus a leaf "Bank Accounts" ledger and Bank Account master per company, and points `Company.default_bank_account` at it, so Payment Entries stop silently posting to Cash. New `02_transactions/224_bank_transactions.py` then generates matched / pending / mismatch Bank Transactions against seeded Payment Entries — reconciling the "matched" ones via ERPNext's own `reconcile_vouchers()` — so the Bank Reconciliation Tool and Statement have real clearance activity to work with. (ref #38)
- **Payment Entries against Sales Invoices** — new shared `02_transactions/223_payment_entries.py` assigns each non-return Sales Invoice with an outstanding balance one of four outcomes (paid in full on time, paid in full late, partially paid, unpaid) via ERPNext's own `get_payment_entry()` mapper, so Accounts Receivable aging and the Customer Ledger Summary show realistic variety instead of every invoice sitting fully unpaid since posting. (ref #37)
- **Shared Sales Orders + Sales Tax Templates** — the 17 near-duplicate per-industry `02_sales_orders.py` seeders are replaced by one shared `02_transactions/210_sales_orders.py`, priced as a markup on each item's real valuation/standard rate (instead of a flat, value-disconnected rate band that showed deeply negative margins for high-value items on the Gross Profit report) and banding qty/lead-time off that same value via a new `sales_order_qty_and_lead()` helper in `demostackkit/seeder/utils.py`. New shared `01_master/91_sales_tax_templates.py` creates a GST-style or flat Sales Taxes and Charges Template per company (previously no industry ever created one, so every order/invoice went out tax-free) so the Sales Register report has something to cross-cut by, and orders are spread across `89_budgets.py`'s Cost Centers too. Each line's warehouse is now pinned to wherever the item actually carries opening-stock qty for that company, fixing rows that Delivery Notes' finished-goods reserve cap was silently trimming to nothing. (ref #36)
- **Multi-company seeding for `electrical`** — `electrical` now seeds an additional company (alongside per-company stock-quantity scaling) so its group's Stock Balance report visibly differs by legal entity, not just by warehouse. New `IndustryConfig.additional_companies` and `CompanyConfig.opening_stock_qty_scale` in `core/config.py`, with a validator rejecting duplicate company names/abbreviations across `company` + `additional_companies`. (ref #34)
- **ASCII art startup banner** — `demostackkit` now prints an ASCII-art banner on CLI invocation (`demostackkit/cli/banner.py`). (ref #41)
- **Multiple BOMs per item** — 11 manufacturing industries (abrasives, chemical, crockery, drones, electrical, evmfg, garment, ingredientmfg, jewellery, print3d, solar) now seed more than one BOM per finished item, so BOM-related reports reflect items with alternate/versioned routings instead of a single fixed recipe. (ref #28)
- **Rejection & Returns demo data** — every industry now seeds a full receiving-through-invoicing chain (Purchase Receipts, Purchase Invoices, Delivery Notes, Sales Invoices) via ERPNext's own mapper functions. Industries carrying the Quality Management module layer a quality-driven rejection trail on top: new shared `01_master/61_standard_warehouses.py` warehouses `Vendor Rejected` and `Customer Returns`, `02_transactions/211_purchase_receipts.py` (rejected-qty splitting + linked Quality Inspections via `reference_type`/`reference_name`), `212_purchase_invoices.py`, `213_return_to_vendor.py` (Return to Vendor + Debit Note via `make_purchase_return_against_rejected_warehouse`), `220_delivery_notes.py`, `221_sales_invoices.py`, and `222_customer_returns.py` (physical Customer Return + Credit Note, and stock-less write-off Credit Notes). The 11 per-industry `03_quality_inspections.py` seeders no longer generate "Incoming" inspections, since those are now created and linked by `211_purchase_receipts.py`. Adds `seed.volumes.purchase_receipts` / `seed.volumes.delivery_notes` to `core/config.py`. (ref #35)
- **Budget Variance actuals** — new shared `02_transactions/230_budget_actuals.py` posts Journal Entries against every submitted Budget from `89_budgets.py`, with a deliberate under / on-target / over mix so the Budget Variance Report has a meaningful actual side. Credits Cash (not the bank ledger) so Bank Reconciliation from #38 stays intact; P&L lines always carry a leaf Cost Center (Company default when the Budget is against a Project). (ref #39)

### Changed

- **`jewellery` company currency** — switched from INR to USD in `industry.yaml`, with BOM, workstation, operation, payroll and asset seed values converted to match. (ref #24)

### Fixed

- **Budgets left as Draft** — `01_master/89_budgets.py` now submits each Budget after insert. ERPNext v15's Budget Variance Report only reads `docstatus=1`, so Draft budgets left the report empty even when actual spend existed. (ref #20, #39)
- **Missing app icons on `/apps`** — `demostackkit up` and `install-app` now also materialize extra-app assets inside the frontend container, not just the backend. The frontend (nginx) container that serves `/apps` icons is a separate container over the same `sites` volume as the backend that runs `bench get-app`/`bench build`; asset files written from the backend container weren't reliably visible from the frontend, so HRMS/Helpdesk/Telephony icons could 404 even after the earlier symlink-materialization fix. (ref #30)

---

## Week of 2026-08-24 → 2026-08-30

### Added

- **Subcontracting demo data** — new shared `01_master/71_subcontracting.py` and `02_transactions/205_subcontracting_orders.py` seeders flag a few BOM-backed finished goods as subcontractable, create the "Sub Contractors" Supplier Group with two Suppliers, a Warehouse per Supplier, a non-stock Service Item per flagged item, an Outsourced Workstation per Supplier and a shared "Subcontracted Processing" Operation, then raise and submit subcontracted Purchase Orders and the Subcontracting Orders against them (raw-material consumption derived from each item's BOM via ERPNext's own `make_subcontracting_order`). Runs for every industry carrying the Manufacturing module; adds `seed.volumes.subcontracting_orders` to `core/config.py`. (ref #32)
- **`demostackkit status`** — new command showing shared-infrastructure health and, per industry, whether its site is created/reachable and its URL, so users no longer need to interpret raw `docker ps` output to know what's running. (ref #31)
- **Budgeting demo data** — new shared `01_master/89_budgets.py` seeder creates leaf Cost Centers mirroring a company's auto-created Departments (Sales, Marketing, Purchase, Management, and Production when the industry runs Manufacturing) and books an annual `Budget` against each, plus against up to two seeded Projects, using accounts from the Standard chart of accounts. All actions are `Warn`, never `Stop`, so seeded Purchase/Sales Orders are never blocked. (ref #20)
- **Ingredient Trading & Distribution industry (`ingredienttrade`)** — Ingredient Traders & Distributors Pvt Ltd, a bulk food-ingredient trading and distribution company procuring from commodity growers, processors and broad-line distributors, with no manufacturing (`production_orders: 0`). 20 customers, 17 suppliers, multi-warehouse stock management, Assets and Support modules for maintenance seeding. (`e508a62`, ref #27)
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
