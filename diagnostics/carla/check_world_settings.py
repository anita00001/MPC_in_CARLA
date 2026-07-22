import carla

client = carla.Client("localhost", 2000)
client.set_timeout(10.0)

world = client.get_world()
settings = world.get_settings()

print("Map:", world.get_map().name)
print("Synchronous mode:", settings.synchronous_mode)
print("Fixed delta seconds:", settings.fixed_delta_seconds)
print("No-rendering mode:", settings.no_rendering_mode)
print("Physics substepping:", settings.substepping)
print("Maximum substeps:", settings.max_substeps)
print(
    "Maximum substep delta:",
    settings.max_substep_delta_time,
)
