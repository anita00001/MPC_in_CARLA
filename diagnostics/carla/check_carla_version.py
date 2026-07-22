import carla

client = carla.Client("localhost", 2000)
client.set_timeout(10.0)

client_version = client.get_client_version()
server_version = client.get_server_version()

print(f"CARLA client version: {client_version}")
print(f"CARLA server version: {server_version}")

if client_version == server_version:
    print("PASS: Client and server versions match.")
else:
    print("FAIL: Client and server versions do not match.")
