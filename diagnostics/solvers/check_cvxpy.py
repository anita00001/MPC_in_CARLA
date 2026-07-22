#!/usr/bin/env python3
"""Check the CVXPY installation and available solvers."""

from __future__ import annotations

import sys


def main() -> int:
    print("=" * 70)
    print("CVXPY INSTALLATION")
    print("=" * 70)

    print(f"Python executable: {sys.executable}")

    try:
        import cvxpy as cp
    except ModuleNotFoundError as error:
        print("FAIL: CVXPY is not installed.")
        print(f"Details: {error}")
        return 1
    except Exception as error:
        print("FAIL: CVXPY was found but could not be imported.")
        print(f"Error type: {type(error).__name__}")
        print(f"Details: {error}")
        return 2

    print("PASS: CVXPY imported successfully.")
    print(f"CVXPY version: {cp.__version__}")
    print(f"Module path   : {cp.__file__}")

    try:
        installed_solvers = cp.installed_solvers()
    except Exception as error:
        print("FAIL: Could not obtain the installed-solver list.")
        print(f"Details: {error}")
        return 3

    print("\nInstalled CVXPY solvers:")

    if not installed_solvers:
        print("  None")
        print("\nFAIL: CVXPY has no available solver.")
        return 4

    for solver in installed_solvers:
        print(f"  - {solver}")

    required_solver = "OSQP"

    if required_solver not in installed_solvers:
        print(f"\nFAIL: {required_solver} is not available through CVXPY.")
        return 5

    print(f"\nPASS: {required_solver} is available through CVXPY.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
