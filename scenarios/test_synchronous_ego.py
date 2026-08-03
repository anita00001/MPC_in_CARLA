#!/usr/bin/env python3
"""Spawn the ego vehicle inside a deterministic CARLA session."""

from __future__ import annotations

from pathlib import Path
import math
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from simulation.carla_session import (  # noqa: E402
    CarlaSession,
    load_simulation_config,
)
from vehicles.ego_vehicle import (  # noqa: E402
    EgoVehicleManager,
    load_project_config,
)


CONFIG_PATH = (
    PROJECT_ROOT
    / "config"
    / "project_config.yaml"
)

NUMBER_OF_TICKS = 100


def calculate_speed(velocity) -> float:
    return math.sqrt(
        velocity.x**2
        + velocity.y**2
        + velocity.z**2
    )


def main() -> int:
    simulation_config = load_simulation_config(
        CONFIG_PATH
    )
    project_config = load_project_config(
        CONFIG_PATH
    )

    session = CarlaSession(simulation_config)
    vehicle_manager: EgoVehicleManager | None = None

    try:
        session.connect()
        session.enable()

        if session.world is None:
            raise RuntimeError(
                "CARLA world is unavailable."
            )

        vehicle_manager = EgoVehicleManager(
            world=session.world,
            config=project_config.vehicle,
        )

        vehicle = vehicle_manager.spawn()
        session.tick()
        
        if project_config.vehicle.follow_with_spectator:
    	    vehicle_manager.position_spectator()

        print("=" * 70)
        print("SYNCHRONOUS EGO-VEHICLE TEST")
        print("=" * 70)
        print(f"Actor ID  : {vehicle.id}")
        print(f"Blueprint : {vehicle.type_id}")
        print(
            f"Spawn index: "
            f"{vehicle_manager.spawn_point_index}"
        )

        first_frame: int | None = None
        last_frame: int | None = None

        for step in range(NUMBER_OF_TICKS):
            frame = session.tick()

            if first_frame is None:
                first_frame = frame

            last_frame = frame

            if step % 20 == 0:
                transform = vehicle.get_transform()
                velocity = vehicle.get_velocity()

                print(
                    f"Step={step:03d} "
                    f"frame={frame} "
                    f"speed={calculate_speed(velocity):.4f} m/s "
                    f"location={transform.location}"
                )

        expected_frame_difference = (
            NUMBER_OF_TICKS - 1
        )
        actual_frame_difference = (
            last_frame - first_frame
        )

        print("\nFrame summary:")
        print(f"First frame     : {first_frame}")
        print(f"Last frame      : {last_frame}")
        print(
            f"Frame difference: "
            f"{actual_frame_difference}"
        )

        if (
            actual_frame_difference
            != expected_frame_difference
        ):
            print(
                "FAIL: Unexpected frame progression."
            )
            return 1

        print(
            "\nPASS: Ego vehicle remained active "
            "during deterministic stepping."
        )
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by the user.")
        return 130

    except Exception as error:
        print(
            f"FAIL: {type(error).__name__}: {error}"
        )
        return 2

    finally:
        if vehicle_manager is not None:
            if vehicle_manager.destroy():
                print("PASS: Ego vehicle destroyed.")

        session.close()
        print("PASS: CARLA settings restored.")


if __name__ == "__main__":
    raise SystemExit(main())
