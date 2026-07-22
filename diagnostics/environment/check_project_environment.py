#!/usr/bin/env python3
"""Run a combined environment, solver, and CARLA connectivity check."""

from __future__ import annotations

import platform
import sys


def check_python_packages() -> tuple[dict[str, bool], int]:
    print("=" * 70)
    print("PYTHON PACKAGES")
    print("=" * 70)

    package_results: dict[str, bool] = {}
    failures = 0

    for package_name in [
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
        "yaml",
        "cvxpy",
        "osqp",
        "carla",
    ]:
        try:
            module = __import__(package_name)
            version = getattr(module, "__version__", "not exposed")
            path = getattr(module, "__file__", "not exposed")

            package_results[package_name] = True

            print(f"PASS {package_name}: version={version}")
            print(f"     path={path}")

        except Exception as error:
            package_results[package_name] = False
            failures += 1

            print(
                f"FAIL {package_name}: "
                f"{type(error).__name__}: {error}"
            )

    return package_results, failures


def check_osqp(package_results: dict[str, bool]) -> int:
    if not package_results.get("cvxpy"):
        print("\nSKIPPED: CVXPY is unavailable.")
        return 1

    import cvxpy as cp

    print("\nCVXPY installed solvers:")
    print(cp.installed_solvers())

    if "OSQP" not in cp.installed_solvers():
        print("FAIL: OSQP is not available through CVXPY.")
        return 1

    x = cp.Variable()
    problem = cp.Problem(
        cp.Minimize(cp.square(x - 3.0)),
        [x >= 0.0],
    )

    try:
        problem.solve(
            solver=cp.OSQP,
            verbose=False,
        )
    except Exception as error:
        print(
            "FAIL: OSQP execution failed:",
            type(error).__name__,
            error,
        )
        return 1

    print("OSQP status:", problem.status)
    print("OSQP solution:", x.value)
    print("OSQP solver:", problem.solver_stats.solver_name)

    if problem.status not in {
        cp.OPTIMAL,
        cp.OPTIMAL_INACCURATE,
    }:
        print("FAIL: OSQP did not return an acceptable status.")
        return 1

    print("PASS: OSQP is working.")
    return 0


def check_carla(package_results: dict[str, bool]) -> int:
    print("\n" + "=" * 70)
    print("CARLA")
    print("=" * 70)

    if not package_results.get("carla"):
        print("FAIL: The CARLA Python module is unavailable.")
        return 1

    import carla

    try:
        client = carla.Client("localhost", 2000)
        client.set_timeout(10.0)

        client_version = client.get_client_version()
        server_version = client.get_server_version()

        print("Client version:", client_version)
        print("Server version:", server_version)

        if client_version != server_version:
            print("FAIL: CARLA client and server versions differ.")
            return 1

        world = client.get_world()
        settings = world.get_settings()
        snapshot = world.get_snapshot()

        print("Map:", world.get_map().name)
        print("Synchronous mode:", settings.synchronous_mode)
        print("Fixed delta:", settings.fixed_delta_seconds)
        print(
            "Snapshot delta:",
            snapshot.timestamp.delta_seconds,
        )

        vehicles = list(
            world.get_actors().filter("vehicle.*")
        )

        print("Existing vehicles:", len(vehicles))

        if vehicles:
            vehicle = vehicles[0]
            transform = vehicle.get_transform()
            velocity = vehicle.get_velocity()
            physics = vehicle.get_physics_control()

            print("First vehicle:", vehicle.type_id)
            print("Vehicle position:", transform.location)
            print("Vehicle velocity:", velocity)
            print("Vehicle mass:", physics.mass)
            print("Wheels:", len(physics.wheels))
        else:
            print(
                "No vehicle is spawned; "
                "ground-truth and physics checks were not performed."
            )

        print("PASS: CARLA connection and world access are working.")
        return 0

    except Exception as error:
        print(
            "FAIL: CARLA connection failed:",
            type(error).__name__,
            error,
        )
        return 1


def main() -> int:
    print("=" * 70)
    print("PYTHON")
    print("=" * 70)
    print("Executable:", sys.executable)
    print("Version:", sys.version)
    print("Platform:", platform.platform())

    package_results, package_failures = check_python_packages()
    osqp_failures = check_osqp(package_results)
    carla_failures = check_carla(package_results)

    total_failures = (
        package_failures
        + osqp_failures
        + carla_failures
    )

    print("\n" + "=" * 70)
    print("COMBINED ENVIRONMENT SUMMARY")
    print("=" * 70)

    if total_failures == 0:
        print("PASS: All combined environment checks passed.")
        return 0

    print(f"FAIL: {total_failures} combined check(s) failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
