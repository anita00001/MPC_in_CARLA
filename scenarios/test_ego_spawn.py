#!/usr/bin/env python3
"""Spawn the configured ego vehicle, inspect it, and clean it up."""

from __future__ import annotations

from pathlib import Path
import math
import sys
import time

import carla


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vehicles.ego_vehicle import (  # noqa: E402
    EgoVehicleManager,
    load_project_config,
)


CONFIG_PATH = PROJECT_ROOT / "config" / "project_config.yaml"
DISPLAY_SECONDS = 10.0


def calculate_speed(
    velocity: carla.Vector3D,
) -> float:
    return math.sqrt(
        velocity.x**2
        + velocity.y**2
        + velocity.z**2
    )


def main() -> int:
    config = load_project_config(CONFIG_PATH)

    client = carla.Client(
        config.connection.host,
        config.connection.port,
    )
    client.set_timeout(
        config.connection.timeout_seconds
    )

    world = client.get_world()
    manager = EgoVehicleManager(
        world=world,
        config=config.vehicle,
    )

    try:
        vehicle = manager.spawn()

        print("=" * 70)
        print("EGO VEHICLE SPAWNED")
        print("=" * 70)
        print(f"Actor ID          : {vehicle.id}")
        print(f"Blueprint         : {vehicle.type_id}")
        print(
            f"Role name         : "
            f"{vehicle.attributes.get('role_name', 'not available')}"
        )
        print(
            f"Spawn-point index : {manager.spawn_point_index}"
        )
        print(f"Autopilot         : {config.vehicle.autopilot}")

        transform = vehicle.get_transform()
        velocity = vehicle.get_velocity()

        print("\nInitial state:")
        print(f"Location          : {transform.location}")
        print(f"Rotation          : {transform.rotation}")
        print(
            f"Speed             : "
            f"{calculate_speed(velocity):.3f} m/s"
        )

        # In asynchronous mode, wait briefly so the vehicle is visible.
        # In synchronous mode, this script advances the world itself.
        settings = world.get_settings()
        start_time = time.monotonic()

        while time.monotonic() - start_time < DISPLAY_SECONDS:
            if settings.synchronous_mode:
                world.tick()
            else:
                time.sleep(0.05)

        if not vehicle.is_alive:
            print("FAIL: The ego vehicle did not remain alive.")
            return 1

        print("\nPASS: Ego vehicle remained alive during the test.")
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by the user.")
        return 130

    except Exception as error:
        print(
            f"FAIL: {type(error).__name__}: {error}"
        )
        return 1

    finally:
        destroyed = manager.destroy()

        if destroyed:
            print("PASS: Ego vehicle was destroyed during cleanup.")
        else:
            print(
                "Cleanup: No live managed vehicle required destruction."
            )


if __name__ == "__main__":
    raise SystemExit(main())
