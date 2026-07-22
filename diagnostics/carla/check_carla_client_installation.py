#!/usr/bin/env python3
"""Check whether the CARLA Python client can be imported."""

from __future__ import annotations

import importlib.metadata
import sys


def main() -> int:
    print("=" * 70)
    print("CARLA PYTHON CLIENT INSTALLATION")
    print("=" * 70)

    print(f"Python executable: {sys.executable}")

    try:
        import carla
    except ModuleNotFoundError as error:
        print("FAIL: The CARLA Python module is not installed.")
        print(f"Details: {error}")
        return 1
    except Exception as error:
        print("FAIL: CARLA was found but could not be imported.")
        print(f"Error type: {type(error).__name__}")
        print(f"Details: {error}")
        return 2

    module_path = getattr(carla, "__file__", "not exposed")
    module_version = getattr(carla, "__version__", None)

    if module_version is None:
        try:
            module_version = importlib.metadata.version("carla")
        except importlib.metadata.PackageNotFoundError:
            module_version = "not exposed"

    print("PASS: CARLA Python module imported successfully.")
    print(f"Module path    : {module_path}")
    print(f"Package version: {module_version}")

    required_attributes = [
        "Client",
        "VehicleControl",
        "Transform",
        "Location",
        "Rotation",
    ]

    print("\nCARLA API objects:")

    missing_attributes: list[str] = []

    for attribute in required_attributes:
        available = hasattr(carla, attribute)
        status = "PASS" if available else "FAIL"
        print(f"  {status}: carla.{attribute}")

        if not available:
            missing_attributes.append(attribute)

    if missing_attributes:
        print("\nFAIL: Required CARLA API objects are missing.")
        return 3

    print("\nPASS: The CARLA Python client appears usable.")
    print("Note: This test does not require the CARLA server to be running.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
