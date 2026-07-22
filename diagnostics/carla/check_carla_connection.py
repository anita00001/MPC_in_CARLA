import carla

try:
    client = carla.Client("localhost", 2000)
    client.set_timeout(10.0)

    world = client.get_world()

    print("PASS: Connected to CARLA.")
    print("Map:", world.get_map().name)
except RuntimeError as error:
    print("FAIL: Could not connect to CARLA.")
    print(error)
