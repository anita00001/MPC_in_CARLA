import carla

client = carla.Client("localhost", 2000)
client.set_timeout(10.0)

world = client.get_world()
snapshot = world.get_snapshot()

timestamp = snapshot.timestamp

print("Frame:", snapshot.frame)
print("Elapsed simulation time:", timestamp.elapsed_seconds)
print("Current delta seconds:", timestamp.delta_seconds)

if timestamp.delta_seconds > 0:
    print(
        "Equivalent simulation frequency:",
        1.0 / timestamp.delta_seconds,
        "Hz",
    )
