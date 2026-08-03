#!/usr/bin/env python3
"""Spawn an ego vehicle and keep it alive for manual diagnostics."""

from __future__ import annotations

from pathlib import Path
import sys
import threading
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
    manager = EgoVehicleManager(world, config.vehicle)

    stop_event = threading.Event()

    try:
        vehicle = manager.spawn()

        print("=" * 70)
        print("EGO VEHICLE IS ACTIVE")
        print("=" * 70)
        print(f"Actor ID  : {vehicle.id}")
        print(f"Blueprint : {vehicle.type_id}")
        print(
            f"Spawn     : {manager.spawn_point_index}"
        )
        print()
        print(
            "Keep this terminal open. Press Enter to destroy "
            "the vehicle and exit."
        )

        input_thread = threading.Thread(
            target=lambda: (
                input(),
                stop_event.set(),
            ),
            daemon=True,
        )
        input_thread.start()

        settings = world.get_settings()

        while not stop_event.is_set():
            if settings.synchronous_mode:
                world.tick()
            else:
                time.sleep(0.05)

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
        if manager.destroy():
            print("PASS: Ego vehicle destroyed.")
        else:
            print("Cleanup complete.")


if __name__ == "__main__":
    raise SystemExit(main())
