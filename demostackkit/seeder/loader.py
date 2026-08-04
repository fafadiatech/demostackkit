"""
Discover and load seeder classes from an industry package.

Convention:
    industries/<slug>/seeders/
        01_master/          ← BaseMasterSeeder subclasses
            01_company.py
            02_items.py
            ...
        02_transactions/    ← BaseTransactionSeeder subclasses
            01_sales_orders.py
            ...

Each Python module in these directories is imported. Any class that:
  - Is a subclass of BaseSeeder
  - Is not BaseSeeder, BaseMasterSeeder, or BaseTransactionSeeder itself
  - Is not abstract

is collected and returned in execution order (phase → priority → filename).
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from demostackkit.seeder.base import BaseSeeder, BaseMasterSeeder, BaseTransactionSeeder, SeedContext

if TYPE_CHECKING:
    pass

# Phase directories in execution order
_PHASE_DIRS = ["01_master", "02_transactions"]
_ABSTRACT_BASES = {BaseSeeder, BaseMasterSeeder, BaseTransactionSeeder}


def _is_concrete_seeder(obj: object) -> bool:
    return (
        inspect.isclass(obj)
        and issubclass(obj, BaseSeeder)
        and obj not in _ABSTRACT_BASES
        and not inspect.isabstract(obj)
    )


def _load_module_from_path(path: Path, module_name: str) -> object:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def discover_seeders(
    industry_dir: Path,
    shared_dirs: list[Path] | None = None,
) -> list[type[BaseSeeder]]:
    """
    Discover all concrete BaseSeeder subclasses in an industry directory,
    and optionally from additional shared directories.

    Returns a list sorted by:
    1. Phase (01_master before 02_transactions)
    2. Seeder.priority (ascending)
    3. Source filename (alphabetical, for stability within equal priorities)

    Args:
        industry_dir: Path to the industry directory (e.g. industries/garment/)
        shared_dirs: Extra seeders/ roots to scan alongside the industry directory.
            They follow the same phase convention (01_master, 02_transactions).

    Returns:
        Ordered list of seeder classes ready to be instantiated with a SeedContext
    """
    seeders_roots = [industry_dir / "seeders"]
    if shared_dirs:
        seeders_roots.extend(shared_dirs)

    collected: list[tuple[int, int, str, type[BaseSeeder]]] = []

    for seeders_root in seeders_roots:
        if not seeders_root.is_dir():
            continue

        # Namespace prefix prevents sys.modules key collisions between shared and industry seeders
        ns = "shared" if seeders_root.parent.name == "demostackkit" else f"industry_{industry_dir.name}"

        for phase_idx, phase_dir_name in enumerate(_PHASE_DIRS):
            phase_dir = seeders_root / phase_dir_name
            if not phase_dir.is_dir():
                continue

            for py_file in sorted(phase_dir.glob("*.py")):
                if py_file.name.startswith("_"):
                    continue

                module_name = f"_dsk_{ns}_{phase_dir_name}_{py_file.stem}"
                try:
                    module = _load_module_from_path(py_file, module_name)
                except Exception as exc:
                    raise ImportError(f"Failed to load seeder module {py_file}: {exc}") from exc

                for _name, obj in inspect.getmembers(module, _is_concrete_seeder):
                    collected.append((phase_idx, obj.priority, py_file.name, obj))

    # Sort: phase → priority → filename
    collected.sort(key=lambda t: (t[0], t[1], t[2]))
    return [cls for _, _, _, cls in collected]


def instantiate_seeders(seeder_classes: list[type[BaseSeeder]], ctx: SeedContext) -> list[BaseSeeder]:
    """Instantiate each discovered seeder class with the given SeedContext."""
    return [cls(ctx) for cls in seeder_classes]
