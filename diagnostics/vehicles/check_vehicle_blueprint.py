#!/usr/bin/env python3
"""Check whether the configured CARLA vehicle blueprint exists."""

from __future__ import annotations

import sys

import carla


CARLA_HOST = "localhost"
CARLA_PORT = 2000
CARLA_TIMEOUT_SECONDS = 10.0
VEHICLE_BLUEPRINT_ID = "vehicle.lincoln.mkz"


def read_attribute(
    blueprint: carla.ActorBlueprint,
    attribute_name: str,
) -> str | None:
    """Return an actor attribute as text when it exists."""
    if not blueprint.has_attribute(attribute_name):
        return None

    attribute = blueprint.get_attribute(attribute_name)
    return str(attribute)


def main() -> int:
    try:
        client = carla.Client(CARLA_HOST, CARLA_PORT)
        client.set_timeout(CARLA_TIMEOUT_SECONDS)

        world = client.get_world()
        blueprint_library = world.get_blueprint_library()

        matches = blueprint_library.filter(VEHICLE_BLUEPRINT_ID)

        print(f"Requested blueprint: {VEHICLE_BLUEPRINT_ID}")

        if not matches:
            print("FAIL: Vehicle blueprint was not found.")
            return 1

        print("PASS: Vehicle blueprint is available.")

        for blueprint in matches:
            print(f"Blueprint ID: {blueprint.id}")

            number_of_wheels = read_attribute(
                blueprint,
                "number_of_wheels",
            )

            if number_of_wheels is not None:
                print(f"Number of wheels: {number_of_wheels}")

            role_name = read_attribute(
                blueprint,
                "role_name",
            )

            if role_name is not None:
                print(f"Default role name: {role_name}")

        return 0

    except RuntimeError as error:
        print("FAIL: Could not connect to the CARLA server.")
        print(error)
        return 2

    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
