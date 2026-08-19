"""
Abstract base classes for all seeders.

Industry packages subclass BaseMasterSeeder or BaseTransactionSeeder.
The framework discovers and instantiates them automatically.

Conventions:
- Seeders are placed in `industries/<slug>/seeders/01_master/` or `02_transactions/`
- Module filenames beginning with a digit are sorted numerically
- Each module may define multiple Seeder classes; all are discovered
- Seeders must use `self.ctx.random` for all random operations, never `random.random()`
"""

from __future__ import annotations

import abc
import random as _random_module
import subprocess
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from demostackkit.core.config import IndustryConfig


@dataclass
class SeedContext:
    """
    Immutable context passed to every seeder instance.

    Carries site coordinates, the validated IndustryConfig, a deterministic
    random instance, and a shared cache for cross-seeder references.
    """

    site: str
    """Frappe site name, e.g. 'garment.localhost'"""

    industry_slug: str
    """Industry identifier, e.g. 'garment'"""

    industry_config: IndustryConfig
    """Parsed and validated industry.yaml contents"""

    bench_path: str
    """Absolute path to frappe-bench inside the container"""

    random: _random_module.Random
    """
    Seeded random instance. ALL seeder code that needs random values
    must use this, never the global random module.
    """

    backend_container: str = "demostackkit-backend-1"
    """Docker container name for the ERPNext backend"""

    dry_run: bool = False
    """If True, print actions but do not execute them"""

    verbose: bool = False
    """If True, emit debug-level output"""

    _cache: dict[str, Any] = field(default_factory=dict, repr=False)

    def cache_set(self, key: str, value: Any) -> None:
        """
        Store a value in the shared cross-seeder cache.

        Example: company seeder stores the company name so BOM seeder can reference it.
        """
        self._cache[key] = value

    def cache_get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value previously stored by another seeder."""
        return self._cache.get(key, default)

    def cache_require(self, key: str) -> Any:
        """
        Retrieve a required cache value.

        Raises:
            KeyError: If key is not found (indicates wrong seeder execution order)
        """
        if key not in self._cache:
            raise KeyError(
                f"SeedContext cache missing required key '{key}'. "
                "Ensure the seeder that populates this key runs before the current seeder."
            )
        return self._cache[key]


class BaseSeeder(abc.ABC):
    """
    Abstract base for all seeders.

    Do not override __init__. The framework instantiates seeders by calling
    __init__(ctx) and expects a consistent signature.
    """

    #: Human-readable label shown in progress output
    label: str = ""

    #: Execution priority within its phase. Lower numbers run first.
    #: Seeders with equal priority execute in alphabetical module order.
    priority: int = 100

    #: If True, an exception in run() aborts the entire seed run.
    #: If False, the error is logged and the next seeder continues.
    required: bool = True

    def __init__(self, ctx: SeedContext) -> None:
        self.ctx = ctx

    @abc.abstractmethod
    def run(self) -> None:
        """
        Execute the seeder.

        Raise any exception on failure. The runner handles retry logging
        and abort-vs-continue based on self.required.
        """
        ...

    def validate(self) -> list[str]:
        """
        Pre-flight validation. Called before run().

        Return a list of error strings. Empty list means OK.
        Typical use: check that required cache keys exist,
        verify referenced files are present.
        """
        return []

    def teardown(self) -> None:
        """
        Optional cleanup called after run() completes (or fails).
        """

    def _exec(self, script: str, timeout: int = 120) -> str:
        """Execute a Python script inside the backend container using the bench virtualenv.

        A Frappe initialisation preamble is automatically prepended so individual
        seeders do not need to repeat the boilerplate:

            import frappe
            frappe.init(site=<site>, sites_path=<bench>/sites)
            frappe.connect()
        """
        preamble = (
            "import frappe\n"
            f"frappe.init(site='{self.ctx.site}', "
            f"sites_path='{self.ctx.bench_path}/sites')\n"
            "frappe.connect()\n"
        )
        full_script = preamble + script
        python = f"{self.ctx.bench_path}/env/bin/python"
        result = subprocess.run(
            [
                "docker",
                "exec",
                "-i",
                "-e",
                "FRAPPE_STREAM_LOGGING=1",
                self.ctx.backend_container,
                python,
                "-c",
                full_script,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if self.ctx.verbose:
            print(result.stdout)
        if result.returncode != 0:
            raise RuntimeError(self._failure_detail(result.stdout, result.stderr))
        return result.stdout

    #: Lines of script output kept when a script fails. Seeders report per-record
    #: problems on stdout and then exit with a bare count, so the count alone —
    #: which is all stderr carries — says nothing about what actually went wrong.
    _FAILURE_OUTPUT_LINES = 40

    @classmethod
    def _failure_detail(cls, stdout: str, stderr: str) -> str:
        """Build an error message that keeps the per-record diagnostics.

        A seeder script prints `ERROR <thing>: <exception>` per failure and then
        raises SystemExit with a summary count. SystemExit's message goes to
        stderr, so reporting stderr alone reduces a real ERPNext validation
        error to something like '1 project(s) failed'.
        """
        tail = stdout.strip().splitlines()[-cls._FAILURE_OUTPUT_LINES :]
        parts = [part for part in (stderr.strip(), "\n".join(tail)) if part]
        return "\n".join(parts) or "script exited non-zero with no output"


class BaseMasterSeeder(BaseSeeder, abc.ABC):
    """
    Base class for master data seeders.

    Master data is IDEMPOTENT: calling run() multiple times must produce
    the same result. Use frappe.db.exists() before every insert.

    Examples: Company, Customers, Suppliers, Items, Warehouses, BOM.
    """

    priority: int = 10


class BaseTransactionSeeder(BaseSeeder, abc.ABC):
    """
    Base class for transactional data seeders.

    Transactional data is NOT required to be idempotent.
    `demostackkit reset` drops and recreates the site before reseeding,
    so duplicate documents are never an issue.

    MUST use self.ctx.random for all random choices to ensure
    `demostackkit reset` produces identical data every time.

    Examples: Sales Orders, Purchase Orders, Stock Entries.
    """

    priority: int = 200

    @property
    def volume(self) -> int:
        """Target number of documents to generate, from industry.yaml seed.volumes."""
        return getattr(
            self.ctx.industry_config.seed.volumes, self._volume_attr, self.default_volume
        )

    #: Attribute name on SeedVolumes to read for this seeder's volume
    _volume_attr: str = ""

    #: Fallback if _volume_attr is not set
    default_volume: int = 20
