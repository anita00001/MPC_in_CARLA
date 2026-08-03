#!/usr/bin/env python3
"""Reusable ego-vehicle spawning and cleanup utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import random
from typing import Any

import carla
import yaml


@dataclass(frozen=True)
class CarlaConnectionConfig:
    host: str
    port: int
    timeout_seconds: float


@dataclass(frozen=True)
class EgoVehicleConfig:
    blueprint: str
    role_name: str
    spawn_point_index: int | None
    autopilot: bool
    spawn_z_offset: float
    randomize_spawn_points: bool
    random_seed: int
    follow_with_spectator: bool
    spectator_height: float
    spectator_distance: float


@dataclass(frozen=True)
class ProjectConfig:
    connection: CarlaConnectionConfig
    vehicle: EgoVehicleConfig


def load_project_config(path: str | Path) -> ProjectConfig:
    """Load CARLA and ego-vehicle settings from YAML."""
    config_path = Path(path)

    if not config_path.is_file():
        raise FileNotFoundError(
            f"Configuration file was not found: {config_path}"
        )

    with config_path.open("r", encoding="utf-8") as file:
        raw_config: dict[str, Any] = yaml.safe_load(file) or {}

    simulation = raw_config.get("simulation", {})
    vehicle = raw_config.get("vehicle", {})

    required_simulation_fields = {
        "host",
        "port",
        "timeout_seconds",
    }

    required_vehicle_fields = {
        "blueprint",
        "role_name",
    }

    missing_simulation = required_simulation_fields - simulation.keys()
    missing_vehicle = required_vehicle_fields - vehicle.keys()

    if missing_simulation:
        raise ValueError(
            "Missing simulation configuration fields: "
            + ", ".join(sorted(missing_simulation))
        )

    if missing_vehicle:
        raise ValueError(
            "Missing vehicle configuration fields: "
            + ", ".join(sorted(missing_vehicle))
        )

    spawn_point_index = vehicle.get("spawn_point_index")

    if spawn_point_index is not None:
        spawn_point_index = int(spawn_point_index)

    connection_config = CarlaConnectionConfig(
        host=str(simulation["host"]),
        port=int(simulation["port"]),
        timeout_seconds=float(simulation["timeout_seconds"]),
    )

    vehicle_config = EgoVehicleConfig(
        blueprint=str(vehicle["blueprint"]),
        role_name=str(vehicle["role_name"]),
        spawn_point_index=spawn_point_index,
        autopilot=bool(vehicle.get("autopilot", False)),
        spawn_z_offset=float(vehicle.get("spawn_z_offset", 0.25)),
        randomize_spawn_points=bool(
            vehicle.get("randomize_spawn_points", False)
        ),
        random_seed=int(vehicle.get("random_seed", 42)),
        follow_with_spectator=bool(
            vehicle.get("follow_with_spectator", True)
        ),
        spectator_height=float(
            vehicle.get("spectator_height", 8.0)
        ),
        spectator_distance=float(
            vehicle.get("spectator_distance", 12.0)
        ),
    )

    return ProjectConfig(
        connection=connection_config,
        vehicle=vehicle_config,
    )


class EgoVehicleManager:
    """Spawn, configure, access, and destroy one CARLA ego vehicle."""

    def __init__(
        self,
        world: carla.World,
        config: EgoVehicleConfig,
    ) -> None:
        self.world = world
        self.config = config
        self.vehicle: carla.Vehicle | None = None
        self.spawn_point_index: int | None = None

    def _get_blueprint(self) -> carla.ActorBlueprint:
        blueprint_library = self.world.get_blueprint_library()

        try:
            blueprint = blueprint_library.find(
                self.config.blueprint
            )
        except RuntimeError as error:
            available = sorted(
                blueprint.id
                for blueprint
                in blueprint_library.filter("vehicle.*")
            )

            raise RuntimeError(
                f"Vehicle blueprint '{self.config.blueprint}' "
                f"was not found.\nAvailable vehicle blueprints:\n"
                + "\n".join(available)
            ) from error

        if blueprint.has_attribute("role_name"):
            blueprint.set_attribute(
                "role_name",
                self.config.role_name,
            )

        return blueprint

    def _get_spawn_candidates(
        self,
    ) -> list[tuple[int, carla.Transform]]:
        spawn_points = self.world.get_map().get_spawn_points()

        if not spawn_points:
            raise RuntimeError(
                "The current CARLA map has no vehicle spawn points."
            )

        indexed_spawn_points = list(enumerate(spawn_points))

        selected_index = self.config.spawn_point_index

        if selected_index is not None:
            if selected_index < 0 or selected_index >= len(spawn_points):
                raise IndexError(
                    f"spawn_point_index={selected_index} is outside "
                    f"the valid range 0..{len(spawn_points) - 1}."
                )

            indexed_spawn_points = [
                indexed_spawn_points[selected_index]
            ]

        elif self.config.randomize_spawn_points:
            random_generator = random.Random(
                self.config.random_seed
            )
            random_generator.shuffle(indexed_spawn_points)

        return indexed_spawn_points

    def _apply_z_offset(
        self,
        transform: carla.Transform,
    ) -> carla.Transform:
        location = carla.Location(
            x=transform.location.x,
            y=transform.location.y,
            z=(
                transform.location.z
                + self.config.spawn_z_offset
            ),
        )

        rotation = carla.Rotation(
            pitch=transform.rotation.pitch,
            yaw=transform.rotation.yaw,
            roll=transform.rotation.roll,
        )

        return carla.Transform(location, rotation)

    def spawn(self) -> carla.Vehicle:
        """Spawn the configured ego vehicle.

        Returns:
            The spawned CARLA vehicle actor.

        Raises:
            RuntimeError: If the actor is already spawned or no spawn
                attempt succeeds.
        """
        if self.vehicle is not None and self.vehicle.is_alive:
            raise RuntimeError(
                "An ego vehicle is already managed by this instance."
            )

        blueprint = self._get_blueprint()
        candidates = self._get_spawn_candidates()

        attempted_indexes: list[int] = []

        for spawn_index, original_transform in candidates:
            attempted_indexes.append(spawn_index)

            spawn_transform = self._apply_z_offset(
                original_transform
            )

            actor = self.world.try_spawn_actor(
                blueprint,
                spawn_transform,
            )

            if actor is None:
                continue

            self.vehicle = actor
            self.spawn_point_index = spawn_index

            try:
                self.vehicle.set_autopilot(
                    self.config.autopilot
                )
            except Exception:
                self.destroy()
                raise

            if self.config.follow_with_spectator:
                self.position_spectator()

            return self.vehicle

        attempted_text = ", ".join(
            str(index) for index in attempted_indexes
        )

        raise RuntimeError(
            "Could not spawn the ego vehicle. "
            f"Blueprint: {self.config.blueprint}. "
            f"Attempted spawn-point indexes: {attempted_text}. "
            "A spawn point may be occupied or obstructed."
        )

    def position_spectator(self) -> None:
        """Place the spectator above and behind the ego vehicle."""
        if self.vehicle is None or not self.vehicle.is_alive:
            raise RuntimeError(
                "Cannot position the spectator before spawning "
                "the ego vehicle."
            )

        vehicle_transform = self.vehicle.get_transform()
        forward_vector = vehicle_transform.get_forward_vector()

        spectator_location = carla.Location(
            x=(
                vehicle_transform.location.x
                - forward_vector.x
                * self.config.spectator_distance
            ),
            y=(
                vehicle_transform.location.y
                - forward_vector.y
                * self.config.spectator_distance
            ),
            z=(
                vehicle_transform.location.z
                + self.config.spectator_height
            ),
        )

        spectator_rotation = carla.Rotation(
            pitch=-25.0,
            yaw=vehicle_transform.rotation.yaw,
            roll=0.0,
        )

        spectator = self.world.get_spectator()
        spectator.set_transform(
            carla.Transform(
                spectator_location,
                spectator_rotation,
            )
        )

    def destroy(self) -> bool:
        """Destroy the managed ego vehicle if it exists."""
        if self.vehicle is None:
            return False

        destroyed = False

        try:
            if self.vehicle.is_alive:
                destroyed = bool(self.vehicle.destroy())
        finally:
            self.vehicle = None
            self.spawn_point_index = None

        return destroyed

    def __enter__(self) -> EgoVehicleManager:
        self.spawn()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object | None,
    ) -> None:
        self.destroy()
