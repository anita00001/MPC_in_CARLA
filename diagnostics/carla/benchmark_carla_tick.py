from __future__ import annotations

import statistics
import time

import carla

HOST = "localhost"
PORT = 2000
FIXED_DELTA_SECONDS = 0.05
NUMBER_OF_TICKS = 200

client = carla.Client(HOST, PORT)
client.set_timeout(10.0)

world = client.get_world()
original_settings = world.get_settings()

tick_times: list[float] = []

try:
    settings = world.get_settings()
    settings.synchronous_mode = True
    settings.fixed_delta_seconds = FIXED_DELTA_SECONDS
    world.apply_settings(settings)

    # Warm-up ticks
    for _ in range(20):
        world.tick()

    for _ in range(NUMBER_OF_TICKS):
        start = time.perf_counter()
        world.tick()
        elapsed = time.perf_counter() - start
        tick_times.append(elapsed)

    sorted_times = sorted(tick_times)
    p95_index = int(0.95 * (len(sorted_times) - 1))

    mean_time = statistics.mean(tick_times)
    maximum_time = max(tick_times)
    p95_time = sorted_times[p95_index]

    print(f"Configured simulation step: {FIXED_DELTA_SECONDS:.4f} s")
    print(f"Target controller frequency: {1 / FIXED_DELTA_SECONDS:.1f} Hz")
    print(f"Mean wall-clock tick time: {mean_time * 1000:.2f} ms")
    print(f"95th percentile tick time: {p95_time * 1000:.2f} ms")
    print(f"Maximum tick time: {maximum_time * 1000:.2f} ms")

    slower_ticks = sum(
        tick_time > FIXED_DELTA_SECONDS
        for tick_time in tick_times
    )

    print(
        "Ticks slower than the 50 ms real-time budget:",
        f"{slower_ticks}/{NUMBER_OF_TICKS}",
    )

finally:
    world.apply_settings(original_settings)
