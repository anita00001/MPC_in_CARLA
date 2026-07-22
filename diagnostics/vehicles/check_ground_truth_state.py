from __future__ import annotations

import math

import carla

client = carla.Client("localhost", 2000)
client.set_timeout(10.0)

world = client.get_world()
vehicles = list(world.get_actors().filter("vehicle.*"))

if not vehicles:
    raise RuntimeError(
        "No vehicle is currently spawned. "
        "Spawn one before running this check."
    )

vehicle = vehicles[0]

transform = vehicle.get_transform()
velocity = vehicle.get_velocity()
angular_velocity = vehicle.get_angular_velocity()
acceleration = vehicle.get_acceleration()

speed = math.sqrt(
    velocity.x**2
    + velocity.y**2
    + velocity.z**2
)

print("Vehicle:", vehicle.type_id)
print("Actor ID:", vehicle.id)
print("Position:", transform.location)
print("Rotation:", transform.rotation)
print("Velocity:", velocity)
print("Speed:", speed, "m/s")
print("Angular velocity:", angular_velocity)
print("Acceleration:", acceleration)

print("PASS: Ground-truth actor state is accessible.")
