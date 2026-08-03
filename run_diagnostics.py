#!/usr/bin/env python3
"""Run all MPC-in-CARLA diagnostic scripts and produce a report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
REPORT_PATH = PROJECT_ROOT / "diagnostics_report.txt"


@dataclass(frozen=True)
class Diagnostic:
    group: str
    path: str
    requires_carla_server: bool = False
    requires_spawned_vehicle: bool = False


DIAGNOSTICS = [
    Diagnostic(
        group="Python and environment",
        path="diagnostics/environment/check_python_system.py",
    ),
    Diagnostic(
        group="Python and environment",
        path="diagnostics/carla/check_carla_client_installation.py",
    ),
    Diagnostic(
        group="Python and environment",
        path="diagnostics/environment/check_supporting_packages.py",
    ),
    Diagnostic(
        group="Optimization solvers",
        path="diagnostics/solvers/check_cvxpy.py",
    ),
    Diagnostic(
        group="Optimization solvers",
        path="diagnostics/solvers/check_osqp.py",
    ),
    Diagnostic(
        group="Combined environment",
        path="diagnostics/environment/check_project_environment.py",
    ),
    Diagnostic(
        group="CARLA server",
        path="diagnostics/carla/check_carla_connection.py",
        requires_carla_server=True,
    ),
    Diagnostic(
        group="CARLA server",
        path="diagnostics/carla/check_carla_version.py",
        requires_carla_server=True,
    ),
    Diagnostic(
        group="CARLA server",
        path="diagnostics/carla/check_world_settings.py",
        requires_carla_server=True,
    ),
    Diagnostic(
        group="CARLA server",
        path="diagnostics/carla/check_simulation_delta.py",
        requires_carla_server=True,
    ),
    Diagnostic(
        group="Vehicles",
        path="diagnostics/vehicles/check_available_vehicles.py",
        requires_carla_server=True,
    ),
    Diagnostic(
        group="Vehicles",
        path="diagnostics/vehicles/check_existing_vehicles.py",
        requires_carla_server=True,
    ),
    Diagnostic(
        group="Vehicles",
        path="diagnostics/vehicles/check_ground_truth_state.py",
        requires_carla_server=True,
        requires_spawned_vehicle=True,
    ),
    Diagnostic(
        group="Vehicles",
        path="diagnostics/vehicles/check_vehicle_blueprint.py",
        requires_carla_server=True,
    ),
    Diagnostic(
        group="Vehicles",
        path="diagnostics/vehicles/check_vehicle_physics.py",
        requires_carla_server=True,
        requires_spawned_vehicle=True,
    ),
    Diagnostic(
        group="CARLA deterministic session",
        path="scenarios/test_synchronous_session.py",
        requires_carla_server=True,
    ),
    Diagnostic(
        group="CARLA performance",
        path="diagnostics/carla/benchmark_carla_tick.py",
        requires_carla_server=True,
    ),
]


def separator(character: str = "=", length: int = 70) -> str:
    return character * length


def check_carla_connection() -> tuple[bool, str]:
    """Check whether a CARLA server is listening on localhost:2000."""
    try:
        import carla

        client = carla.Client("localhost", 2000)
        client.set_timeout(3.0)
        server_version = client.get_server_version()

        return True, f"CARLA server version: {server_version}"

    except Exception as error:
        return False, f"{type(error).__name__}: {error}"


def check_spawned_vehicle() -> tuple[bool, str]:
    """Check whether at least one CARLA vehicle actor exists."""
    try:
        import carla

        client = carla.Client("localhost", 2000)
        client.set_timeout(3.0)

        world = client.get_world()
        vehicles = list(world.get_actors().filter("vehicle.*"))

        if not vehicles:
            return False, "No vehicle actors are currently spawned."

        return True, f"{len(vehicles)} vehicle actor(s) found."

    except Exception as error:
        return False, f"{type(error).__name__}: {error}"


def run_diagnostic(diagnostic: Diagnostic) -> tuple[str, int]:
    script_path = PROJECT_ROOT / diagnostic.path

    if not script_path.is_file():
        output = (
            f"FAIL: Diagnostic file does not exist:\n"
            f"{script_path}\n"
        )
        return output, 127

    process = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    output_parts = []

    if process.stdout:
        output_parts.append(process.stdout.rstrip())

    if process.stderr:
        output_parts.append(
            "STANDARD ERROR:\n"
            + process.stderr.rstrip()
        )

    output = "\n".join(output_parts)

    if not output:
        output = "(The script produced no output.)"

    return output, process.returncode


def main() -> int:
    started_at = datetime.now()

    carla_available, carla_message = check_carla_connection()

    vehicle_available = False
    vehicle_message = "Not checked because CARLA is unavailable."

    if carla_available:
        vehicle_available, vehicle_message = check_spawned_vehicle()

    report_lines = [
        separator(),
        "MPC IN CARLA — DIAGNOSTIC REPORT",
        separator(),
        f"Started: {started_at.isoformat(timespec='seconds')}",
        f"Python executable: {sys.executable}",
        f"Project root: {PROJECT_ROOT}",
        "",
        f"CARLA connection: {'PASS' if carla_available else 'FAIL'}",
        carla_message,
        "",
        f"Spawned vehicle: {'PASS' if vehicle_available else 'NOT AVAILABLE'}",
        vehicle_message,
        "",
    ]

    print("\n".join(report_lines))

    passed = 0
    failed = 0
    skipped = 0
    current_group: str | None = None

    for diagnostic in DIAGNOSTICS:
        if diagnostic.group != current_group:
            current_group = diagnostic.group
            heading = (
                f"\n{separator()}\n"
                f"{current_group.upper()}\n"
                f"{separator()}"
            )

            print(heading)
            report_lines.append(heading)

        title = f"\nRunning: {diagnostic.path}"
        print(title)
        report_lines.append(title)

        if diagnostic.requires_carla_server and not carla_available:
            message = (
                "SKIPPED: This diagnostic requires a running "
                "CARLA server on localhost:2000."
            )
            print(message)
            report_lines.append(message)
            skipped += 1
            continue

        if diagnostic.requires_spawned_vehicle and not vehicle_available:
            message = (
                "SKIPPED: This diagnostic requires at least one "
                "spawned vehicle actor."
            )
            print(message)
            report_lines.append(message)
            skipped += 1
            continue

        output, return_code = run_diagnostic(diagnostic)

        print(output)
        report_lines.append(output)

        status = "PASS" if return_code == 0 else "FAIL"
        status_line = f"Result: {status} — exit code {return_code}"

        print(status_line)
        report_lines.append(status_line)

        if return_code == 0:
            passed += 1
        else:
            failed += 1

    finished_at = datetime.now()
    duration = finished_at - started_at

    summary = [
        "",
        separator(),
        "SUMMARY",
        separator(),
        f"Passed : {passed}",
        f"Failed : {failed}",
        f"Skipped: {skipped}",
        f"Total  : {len(DIAGNOSTICS)}",
        f"Finished: {finished_at.isoformat(timespec='seconds')}",
        f"Duration: {duration}",
        f"Report: {REPORT_PATH}",
    ]

    print("\n".join(summary))
    report_lines.extend(summary)

    REPORT_PATH.write_text(
        "\n".join(report_lines) + "\n",
        encoding="utf-8",
    )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
