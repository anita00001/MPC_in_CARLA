#!/usr/bin/env python3
"""Check packages required by the CARLA MPC project."""

from __future__ import annotations

import importlib
import importlib.metadata
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class PackageCheck:
    distribution_name: str
    import_name: str


REQUIRED_PACKAGES = [
    PackageCheck("numpy", "numpy"),
    PackageCheck("scipy", "scipy"),
    PackageCheck("pandas", "pandas"),
    PackageCheck("matplotlib", "matplotlib"),
    PackageCheck("PyYAML", "yaml"),
    PackageCheck("cvxpy", "cvxpy"),
    PackageCheck("osqp", "osqp"),
]


def get_package_version(
    distribution_name: str,
    module: object,
) -> str:
    module_version = getattr(module, "__version__", None)

    if module_version is not None:
        return str(module_version)

    try:
        return importlib.metadata.version(distribution_name)
    except importlib.metadata.PackageNotFoundError:
        return "not exposed"


def main() -> int:
    print("=" * 70)
    print("SUPPORTING PYTHON PACKAGES")
    print("=" * 70)

    print(f"Python executable: {sys.executable}\n")

    failed_packages: list[str] = []

    for package in REQUIRED_PACKAGES:
        try:
            module = importlib.import_module(package.import_name)
            version = get_package_version(
                package.distribution_name,
                module,
            )
            module_path = getattr(
                module,
                "__file__",
                "not exposed",
            )

            print(f"PASS: {package.distribution_name}")
            print(f"      Version: {version}")
            print(f"      Path   : {module_path}")

        except Exception as error:
            failed_packages.append(package.distribution_name)

            print(f"FAIL: {package.distribution_name}")
            print(
                f"      {type(error).__name__}: {error}"
            )

        print()

    if failed_packages:
        print("FAIL: One or more required packages are unavailable:")
        for package_name in failed_packages:
            print(f"  - {package_name}")
        return 1

    print("PASS: All required supporting packages are available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
