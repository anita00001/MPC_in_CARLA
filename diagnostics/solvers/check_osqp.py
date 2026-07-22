#!/usr/bin/env python3
"""Verify that OSQP is installed and works through CVXPY."""

from __future__ import annotations

import sys

import numpy as np


def main() -> int:
    print("=" * 70)
    print("OSQP SOLVER CHECK")
    print("=" * 70)

    print(f"Python executable: {sys.executable}")

    try:
        import cvxpy as cp
        import osqp
    except ModuleNotFoundError as error:
        print("FAIL: A required optimization package is missing.")
        print(f"Details: {error}")
        return 1
    except Exception as error:
        print("FAIL: An optimization package could not be imported.")
        print(f"Error type: {type(error).__name__}")
        print(f"Details: {error}")
        return 2

    print(f"CVXPY version: {cp.__version__}")
    print(f"OSQP version : {osqp.__version__}")
    print(f"OSQP path    : {osqp.__file__}")

    installed_solvers = cp.installed_solvers()

    if "OSQP" not in installed_solvers:
        print("\nFAIL: CVXPY does not list OSQP as an available solver.")
        print(f"Installed solvers: {installed_solvers}")
        return 3

    # Small quadratic program:
    #
    # Minimize: (x - 3)^2
    # Subject to: 0 <= x <= 10
    x = cp.Variable(name="x")

    objective = cp.Minimize(cp.square(x - 3.0))
    constraints = [
        x >= 0.0,
        x <= 10.0,
    ]

    problem = cp.Problem(objective, constraints)

    try:
        objective_value = problem.solve(
            solver=cp.OSQP,
            warm_start=True,
            verbose=False,
        )
    except Exception as error:
        print("\nFAIL: OSQP raised an exception.")
        print(f"Error type: {type(error).__name__}")
        print(f"Details: {error}")
        return 4

    print("\nOptimization result:")
    print(f"  Status         : {problem.status}")
    print(f"  Objective value: {objective_value}")
    print(f"  Solution x     : {x.value}")
    print(f"  Solver used    : {problem.solver_stats.solver_name}")
    print(f"  Solve time     : {problem.solver_stats.solve_time}")

    valid_statuses = {
        cp.OPTIMAL,
        cp.OPTIMAL_INACCURATE,
    }

    if problem.status not in valid_statuses:
        print("\nFAIL: OSQP did not return an acceptable solution status.")
        return 5

    if x.value is None or not np.isclose(float(x.value), 3.0, atol=1e-4):
        print("\nFAIL: OSQP returned an unexpected solution.")
        return 6

    if problem.solver_stats.solver_name.upper() != "OSQP":
        print("\nFAIL: The problem was not solved by OSQP.")
        return 7

    print("\nPASS: OSQP is installed and solving correctly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
