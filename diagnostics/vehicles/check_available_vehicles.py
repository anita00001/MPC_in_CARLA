import carla

client = carla.Client("localhost", 2000)
client.set_timeout(10.0)

world = client.get_world()
blueprints = world.get_blueprint_library().filter("vehicle.*")

print(f"Available vehicle blueprints: {len(blueprints)}")

for blueprint in sorted(blueprints, key=lambda item: item.id):
    print(blueprint.id)
