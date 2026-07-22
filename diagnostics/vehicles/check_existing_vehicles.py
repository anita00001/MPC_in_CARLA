import carla

client = carla.Client("localhost", 2000)
client.set_timeout(10.0)

world = client.get_world()
vehicles = world.get_actors().filter("vehicle.*")

print("Existing vehicles:", len(vehicles))

for vehicle in vehicles:
    print(
        "Actor ID:",
        vehicle.id,
        "| Type:",
        vehicle.type_id,
        "| Role:",
        vehicle.attributes.get("role_name", ""),
    )
