#!/usr/bin/env python3
"""Manage a deterministic CARLA simulation session."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import carla
import yaml


@dataclass(frozen=True)
class TrafficManagerConfig:
    enabled: bool
    port: int
    synchronous_mode: bool
    random_seed: int


@dataclass(frozen=True)
class SimulationConfig:
    host: str
    port: int
    timeout_seconds: float
    synchronous_mode: bool
    fixed_delta_seconds: float
    no_rendering_mode: bool
    traffic_manager: TrafficManagerConfig


def load_simulation_config(
    config_path: str | Path,
) -> SimulationConfig:
    """Load simulation settings from project_config.yaml."""
    path = Path(config_path)

    if not path.is_file():
        raise FileNotFoundError(
            f"Configuration file was not found: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        raw_config: dict[str, Any] = yaml.safe_load(file) or {}

    simulation = raw_config.get("simulation")

    if simulation is None:
        raise ValueError(
            "The configuration file has no 'simulation' section."
        )

    traffic_manager = simulation.get(
        "traffic_manager",
        {},
    )

    fixed_delta_seconds = float(
        simulation.get("fixed_delta_seconds", 0.05)
    )

    if fixed_delta_seconds <= 0.0:
        raise ValueError(
            "fixed_delta_seconds must be greater than zero."
        )

    return SimulationConfig(
        host=str(simulation.get("host", "localhost")),
        port=int(simulation.get("port", 2000)),
        timeout_seconds=float(
            simulation.get("timeout_seconds", 10.0)
        ),
        synchronous_mode=bool(
            simulation.get("synchronous_mode", True)
        ),
        fixed_delta_seconds=fixed_delta_seconds,
        no_rendering_mode=bool(
            simulation.get("no_rendering_mode", False)
        ),
        traffic_manager=TrafficManagerConfig(
            enabled=bool(
                traffic_manager.get("enabled", False)
            ),
            port=int(
                traffic_manager.get("port", 8000)
            ),
            synchronous_mode=bool(
                traffic_manager.get(
                    "synchronous_mode",
                    True,
                )
            ),
            random_seed=int(
                traffic_manager.get(
                    "random_seed",
                    42,
                )
            ),
        ),
    )


class CarlaSession:
    """Configure, advance, and restore a CARLA simulation."""

    def __init__(
        self,
        config: SimulationConfig,
    ) -> None:
        self.config = config

        self.client: carla.Client | None = None
        self.world: carla.World | None = None
        self.traffic_manager: carla.TrafficManager | None = None

        self.original_settings: carla.WorldSettings | None = None
        self.active = False

    def connect(self) -> carla.World:
        """Connect to the CARLA server and obtain the current world."""
        if self.client is not None:
            raise RuntimeError(
                "The CARLA session is already connected."
            )

        client = carla.Client(
            self.config.host,
            self.config.port,
        )
        client.set_timeout(
            self.config.timeout_seconds
        )

        # Confirm that the server is reachable.
        client_version = client.get_client_version()
        server_version = client.get_server_version()

        if client_version != server_version:
            raise RuntimeError(
                "CARLA client and server versions do not match: "
                f"client={client_version}, "
                f"server={server_version}"
            )

        world = client.get_world()

        self.client = client
        self.world = world

        return world

    def enable(self) -> None:
        """Apply deterministic world settings."""
        if self.world is None:
            raise RuntimeError(
                "Call connect() before enable()."
            )

        if self.active:
            raise RuntimeError(
                "The CARLA session is already active."
            )

        self.original_settings = self.world.get_settings()

        settings = self.world.get_settings()
        settings.synchronous_mode = (
            self.config.synchronous_mode
        )
        settings.fixed_delta_seconds = (
            self.config.fixed_delta_seconds
        )
        settings.no_rendering_mode = (
            self.config.no_rendering_mode
        )

        self.world.apply_settings(settings)

        if self.config.traffic_manager.enabled:
            if self.client is None:
                raise RuntimeError(
                    "CARLA client is unavailable."
                )

            traffic_manager = self.client.get_trafficmanager(
                self.config.traffic_manager.port
            )

            traffic_manager.set_synchronous_mode(
                self.config.traffic_manager.synchronous_mode
            )

            traffic_manager.set_random_device_seed(
                self.config.traffic_manager.random_seed
            )

            self.traffic_manager = traffic_manager

        self.active = True

    def tick(self, timeout: float | None = None) -> int:
        """Advance the simulation by one frame."""
        if self.world is None:
            raise RuntimeError(
                "The CARLA session is not connected."
            )

        if not self.active:
            raise RuntimeError(
                "The CARLA session is not enabled."
            )

        if not self.config.synchronous_mode:
            raise RuntimeError(
                "tick() requires synchronous mode."
            )

        if timeout is None:
            return self.world.tick()

        return self.world.tick(timeout)

    def snapshot(self) -> carla.WorldSnapshot:
        """Return the latest CARLA world snapshot."""
        if self.world is None:
            raise RuntimeError(
                "The CARLA session is not connected."
            )

        return self.world.get_snapshot()

    def restore(self) -> None:
        """Restore Traffic Manager and world settings."""
        if self.world is None:
            return

        if self.traffic_manager is not None:
            try:
                self.traffic_manager.set_synchronous_mode(
                    False
                )
            finally:
                self.traffic_manager = None

        if self.original_settings is not None:
            self.world.apply_settings(
                self.original_settings
            )

        self.original_settings = None
        self.active = False

    def close(self) -> None:
        """Restore settings and release client references."""
        self.restore()

        self.world = None
        self.client = None

    def __enter__(self) -> CarlaSession:
        self.connect()
        self.enable()
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object | None,
    ) -> None:
        self.close()
