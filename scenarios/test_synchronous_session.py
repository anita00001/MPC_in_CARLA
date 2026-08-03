#!/usr/bin/env python3
"""Validate deterministic synchronous CARLA stepping."""

from __future__ import annotations

from pathlib import Path
import math
import sys
import time


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation.carla_session import (  # noqa: E402
    CarlaSession,
    load_simulation_config,
)


CONFIG_PATH = (
    PROJECT_ROOT
    / "config"
    / "project_config.yaml"
)

NUMBER_OF_TEST_TICKS = 100
DELTA_TOLERANCE = 1e-6


def main() -> int:
    config = load_simulation_config(CONFIG_PATH)

    print("=" * 70)
    print("SYNCHRONOUS CARLA SESSION TEST")
    print("=" * 70)

    print(f"Host                 : {config.host}")
    print(f"Port                 : {config.port}")
    print(
        f"Requested sync mode  : "
        f"{config.synchronous_mode}"
    )
    print(
        f"Requested fixed delta: "
        f"{config.fixed_delta_seconds:.6f} s"
    )

    session = CarlaSession(config)

    original_synchronous_mode: bool | None = None
    original_fixed_delta: float | None = None

    frame_numbers: list[int] = []
    snapshot_deltas: list[float] = []
    wall_times: list[float] = []

    try:
        world = session.connect()

        original_settings = world.get_settings()
        original_synchronous_mode = (
            original_settings.synchronous_mode
        )
        original_fixed_delta = (
            original_settings.fixed_delta_seconds
        )

        print("\nOriginal world settings:")
        print(
            f"  Synchronous mode: "
            f"{original_synchronous_mode}"
        )
        print(
            f"  Fixed delta      : "
            f"{original_fixed_delta}"
        )

        session.enable()

        active_settings = world.get_settings()

        print("\nActive world settings:")
        print(
            f"  Synchronous mode: "
            f"{active_settings.synchronous_mode}"
        )
        print(
            f"  Fixed delta      : "
            f"{active_settings.fixed_delta_seconds}"
        )

        if (
            active_settings.synchronous_mode
            != config.synchronous_mode
        ):
            print(
                "FAIL: Synchronous mode was not applied."
            )
            return 1

        if not math.isclose(
            active_settings.fixed_delta_seconds,
            config.fixed_delta_seconds,
            rel_tol=0.0,
            abs_tol=DELTA_TOLERANCE,
        ):
            print(
                "FAIL: Fixed delta was not applied."
            )
            return 2

        print(
            f"\nAdvancing {NUMBER_OF_TEST_TICKS} frames..."
        )

        for _ in range(NUMBER_OF_TEST_TICKS):
            start_time = time.perf_counter()

            returned_frame = session.tick()

            wall_time = (
                time.perf_counter() - start_time
            )

            snapshot = session.snapshot()

            if snapshot.frame != returned_frame:
                print(
                    "FAIL: world.tick() frame does not "
                    "match snapshot frame."
                )
                print(
                    f"Returned frame: {returned_frame}"
                )
                print(
                    f"Snapshot frame: {snapshot.frame}"
                )
                return 3

            frame_numbers.append(snapshot.frame)
            snapshot_deltas.append(
                snapshot.timestamp.delta_seconds
            )
            wall_times.append(wall_time)

        frame_steps = [
            current - previous
            for previous, current in zip(
                frame_numbers,
                frame_numbers[1:],
            )
        ]

        invalid_frame_steps = [
            step
            for step in frame_steps
            if step != 1
        ]

        invalid_deltas = [
            delta
            for delta in snapshot_deltas
            if not math.isclose(
                delta,
                config.fixed_delta_seconds,
                rel_tol=0.0,
                abs_tol=DELTA_TOLERANCE,
            )
        ]

        print("\nFrame validation:")
        print(f"  First frame      : {frame_numbers[0]}")
        print(f"  Last frame       : {frame_numbers[-1]}")
        print(
            f"  Invalid frame jumps: "
            f"{len(invalid_frame_steps)}"
        )
        print(
            f"  Invalid deltas     : "
            f"{len(invalid_deltas)}"
        )

        mean_wall_time = (
            sum(wall_times) / len(wall_times)
        )
        maximum_wall_time = max(wall_times)

        print("\nTiming:")
        print(
            f"  Simulation delta : "
            f"{config.fixed_delta_seconds:.6f} s"
        )
        print(
            f"  Mean tick time   : "
            f"{mean_wall_time * 1000:.3f} ms"
        )
        print(
            f"  Maximum tick time: "
            f"{maximum_wall_time * 1000:.3f} ms"
        )

        if invalid_frame_steps:
            print(
                "FAIL: One or more frame increments "
                "were not equal to one."
            )
            return 4

        if invalid_deltas:
            print(
                "FAIL: One or more snapshot deltas "
                "did not match the fixed time step."
            )
            return 5

        print(
            "\nPASS: Deterministic stepping is working."
        )
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by the user.")
        return 130

    except Exception as error:
        print(
            f"\nFAIL: {type(error).__name__}: {error}"
        )
        return 10

    finally:
        session.close()

        if session.world is None:
            # Reconnect temporarily only to verify restoration.
            try:
                verification_session = CarlaSession(config)
                verification_world = (
                    verification_session.connect()
                )

                restored_settings = (
                    verification_world.get_settings()
                )

                print("\nRestored world settings:")
                print(
                    f"  Synchronous mode: "
                    f"{restored_settings.synchronous_mode}"
                )
                print(
                    f"  Fixed delta      : "
                    f"{restored_settings.fixed_delta_seconds}"
                )

                if (
                    original_synchronous_mode is not None
                    and restored_settings.synchronous_mode
                    != original_synchronous_mode
                ):
                    print(
                        "WARNING: Original synchronous mode "
                        "was not restored."
                    )

                if (
                    original_fixed_delta is not None
                    and restored_settings.fixed_delta_seconds
                    != original_fixed_delta
                ):
                    print(
                        "WARNING: Original fixed delta "
                        "was not restored."
                    )

                verification_session.close()

            except Exception as error:
                print(
                    "WARNING: Could not verify restored "
                    f"settings: {error}"
                )


if __name__ == "__main__":
    raise SystemExit(main())