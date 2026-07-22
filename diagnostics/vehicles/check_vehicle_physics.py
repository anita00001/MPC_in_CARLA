import carla

client = carla.Client("localhost", 2000)
client.set_timeout(10.0)

world = client.get_world()
vehicles = list(world.get_actors().filter("vehicle.*"))

if not vehicles:
    raise RuntimeError("No vehicle is currently spawned.")

vehicle = vehicles[0]
physics = vehicle.get_physics_control()

print("Vehicle:", vehicle.type_id)
print("Mass:", physics.mass, "kg")
print("Drag coefficient:", physics.drag_coefficient)
print("Center of mass:", physics.center_of_mass)
print("Number of wheels:", len(physics.wheels))

for index, wheel in enumerate(physics.wheels):
    print(f"\nWheel {index}")
    print("  Position:", wheel.position)
    print("  Radius:", wheel.wheel_radius)
    print("  Maximum steer angle:", wheel.max_steer_angle, "degrees")
