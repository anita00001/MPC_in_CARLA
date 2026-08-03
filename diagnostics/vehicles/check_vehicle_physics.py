#!/usr/bin/env python3
"""Inspect the physics properties of a spawned CARLA vehicle."""

from __future__ import annotations

import sys

import carla


CARLA_HOST = "localhost"
CARLA_PORT = 2000
CARLA_TIMEOUT_SECONDS = 10.0


def main() -> int:
    try:
        client = carla.Client(CARLA_HOST, CARLA_PORT)
        client.set_timeout(CARLA_TIMEOUT_SECONDS)

        world = client.get_world()
        vehicles = list(world.get_actors().filter("vehicle.*"))

        if not vehicles:
            print("FAIL: No vehicle is currently spawned.")
            return 1

        ego_vehicles = [
            vehicle
            for vehicle in vehicles
            if vehicle.attributes.get("role_name") == "ego"
        ]

        vehicle = ego_vehicles[0] if ego_vehicles else vehicles[0]
        physics = vehicle.get_physics_control()

        print(f"Vehicle: {vehicle.type_id}")
        print(f"Actor ID: {vehicle.id}")
        print(f"Role name: {vehicle.attributes.get('role_name', '')}")
        print(f"Mass: {physics.mass} kg")
        print(f"Drag coefficient: {physics.drag_coefficient}")
        print(f"Center of mass: {physics.center_of_mass}")
        print(f"Number of wheels: {len(physics.wheels)}")

        for index, wheel in enumerate(physics.wheels):
            print(f"\nWheel {index}")
            print(f"  Location: {wheel.location}")
            print(f"  Radius: {wheel.wheel_radius}")
            print(
                f"  Maximum steer angle: "
                f"{wheel.max_steer_angle} degrees"
            )

            if hasattr(wheel, "tire_friction"):
                print(f"  Tire friction: {wheel.tire_friction}")

            if hasattr(wheel, "damping_rate"):
                print(f"  Damping rate: {wheel.damping_rate}")

            if hasattr(wheel, "max_brake_torque"):
                print(
                    f"  Maximum brake torque: "
                    f"{wheel.max_brake_torque}"
                )

            if hasattr(wheel, "max_handbrake_torque"):
                print(
                    f"  Maximum handbrake torque: "
                    f"{wheel.max_handbrake_torque}"
                )

        print("\nPASS: Vehicle physics data is accessible.")
        return 0

    except RuntimeError as error:
        print("FAIL: CARLA runtime error.")
        print(error)
        return 2

    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
