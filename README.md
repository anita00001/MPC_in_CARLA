# MPC in CARLA

A CARLA-based autonomous vehicle control project using a dual Model Predictive Control architecture:

- **Longitudinal MPC** for speed, acceleration, throttle, and braking
- **Lateral MPC** for steering and path tracking

The project is currently in the environment-validation and simulator-diagnostics stage.

## Project status

Validated successfully:

- Python 3.10.12
- CARLA Python client 0.10.0
- CARLA server 0.10.0
- CARLA map access
- CVXPY 1.7.5
- OSQP 1.1.3
- OSQP quadratic-program solve test
- CARLA synchronous-step benchmark at 20 Hz
- Ego vehicle blueprint availability

Current diagnostic result:

```text
Passed : 14
Failed : 0
Skipped: 2
Total  : 16
```

The two skipped checks require a spawned vehicle:

- Ground-truth state access
- Vehicle physics inspection

## Tested environment

```text
Operating system : Linux x86_64
Python           : 3.10.12
CARLA client     : 0.10.0
CARLA server     : 0.10.0
CVXPY            : 1.7.5
OSQP             : 1.1.3
Map              : Carla/Maps/Town10HD_Opt
```

The current ego-vehicle blueprint is:

```text
vehicle.lincoln.mkz
```

## Project structure

```text
MPC_in_CARLA/
├── config/
│   └── project_config.yaml
├── diagnostics/
│   ├── carla/
│   │   ├── benchmark_carla_tick.py
│   │   ├── check_carla_client_installation.py
│   │   ├── check_carla_connection.py
│   │   ├── check_carla_version.py
│   │   ├── check_simulation_delta.py
│   │   └── check_world_settings.py
│   ├── environment/
│   │   ├── check_project_environment.py
│   │   ├── check_python_system.py
│   │   └── check_supporting_packages.py
│   ├── solvers/
│   │   ├── check_cvxpy.py
│   │   └── check_osqp.py
│   └── vehicles/
│       ├── check_available_vehicles.py
│       ├── check_existing_vehicles.py
│       ├── check_ground_truth_state.py
│       ├── check_vehicle_blueprint.py
│       └── check_vehicle_physics.py
├── run_diagnostics.py
├── diagnostics_report.txt
└── README.md
```

Future implementation folders will include:

```text
controllers/
models/
planning/
estimation/
scenarios/
evaluation/
tests/
```

## Requirements

The following Python packages are currently used:

```text
numpy
scipy
pandas
matplotlib
PyYAML
cvxpy
osqp
carla
```

Check package availability with:

```bash
python3 diagnostics/environment/check_supporting_packages.py
```

## CARLA server

Start the CARLA simulator before running CARLA-dependent diagnostics.

Verify that the server is listening on the default port:

```bash
ss -ltnp | grep ':2000'
```

Expected form:

```text
LISTEN ... 0.0.0.0:2000 ...
```

The diagnostics currently connect to:

```text
Host: localhost
Port: 2000
```

## Run all diagnostics

From the project root:

```bash
python3 run_diagnostics.py
```

The runner:

- executes all diagnostic scripts
- continues after individual failures
- skips checks that require unavailable prerequisites
- detects whether the CARLA server is running
- detects whether a vehicle actor is spawned
- prints a pass, fail, and skip summary
- writes the complete output to `diagnostics_report.txt`

## Run individual diagnostics

### Environment

```bash
python3 diagnostics/environment/check_python_system.py
python3 diagnostics/environment/check_supporting_packages.py
python3 diagnostics/environment/check_project_environment.py
```

### CARLA client and server

```bash
python3 diagnostics/carla/check_carla_client_installation.py
python3 diagnostics/carla/check_carla_connection.py
python3 diagnostics/carla/check_carla_version.py
python3 diagnostics/carla/check_world_settings.py
python3 diagnostics/carla/check_simulation_delta.py
```

### Optimization solvers

```bash
python3 diagnostics/solvers/check_cvxpy.py
python3 diagnostics/solvers/check_osqp.py
```

### Vehicle checks

```bash
python3 diagnostics/vehicles/check_available_vehicles.py
python3 diagnostics/vehicles/check_existing_vehicles.py
python3 diagnostics/vehicles/check_vehicle_blueprint.py
python3 diagnostics/vehicles/check_ground_truth_state.py
python3 diagnostics/vehicles/check_vehicle_physics.py
```

The ground-truth and vehicle-physics checks require at least one spawned vehicle actor.

### Performance benchmark

```bash
python3 diagnostics/carla/benchmark_carla_tick.py
```

The validated benchmark result at a 0.05-second simulation step was:

```text
Target controller frequency              : 20.0 Hz
Mean wall-clock tick time                 : 16.66 ms
95th-percentile wall-clock tick time      : 19.23 ms
Maximum wall-clock tick time              : 21.75 ms
Ticks slower than the 50 ms time budget   : 0/200
```

This indicates that the simulator can currently sustain the proposed 20 Hz simulation step under the tested conditions. MPC solve time must still be included when evaluating the complete control loop.

## Configuration

The project configuration is stored in:

```text
config/project_config.yaml
```

Current core settings:

```yaml
project:
  ego_vehicle_count: 1
  initial_state_source: ground_truth
  controller_architecture: dual_mpc

vehicle:
  blueprint: vehicle.lincoln.mkz

controllers:
  lateral:
    enabled: true
    type: linear_mpc

  longitudinal:
    enabled: true
    type: linear_mpc

simulation:
  host: localhost
  port: 2000
  proposed_fixed_delta_seconds: 0.05
```

These values define the initial project scope. They are not all simulator-discovered properties.

## Planned control architecture

```text
CARLA map and route
        |
        v
Reference generator
        |
        v
Ground-truth state estimator
        |
        +----------------------+
        |                      |
        v                      v
Lateral MPC             Longitudinal MPC
Steering angle          Acceleration command
        |                      |
        +----------+-----------+
                   |
                   v
          Actuator mapping
     steer / throttle / brake
                   |
                   v
          CARLA VehicleControl
```

## Development roadmap

### Phase 1 — Vehicle spawning and state access

- Add a controlled ego-vehicle spawning script
- Spawn `vehicle.lincoln.mkz`
- Verify transform, velocity, acceleration, and yaw-rate access
- Inspect actual vehicle physics and wheel data
- Add reliable cleanup after each run

### Phase 2 — Deterministic simulation session

- Enable synchronous mode
- Set `fixed_delta_seconds` to 0.05
- Preserve and restore the original world settings
- Verify frame-by-frame stepping

### Phase 3 — Logging

- Record simulation time
- Record position, yaw, velocity, and acceleration
- Record control commands
- Save results to CSV
- Add plotting utilities

### Phase 4 — Longitudinal MPC

- Build a discrete longitudinal vehicle model
- Track constant and changing speed references
- Map acceleration commands to throttle and brake
- Measure speed RMSE, overshoot, acceleration, and jerk

### Phase 5 — Route generation

- Extract CARLA lane waypoints
- Build a local reference path
- Calculate nearest path point
- Calculate lateral and heading errors
- Estimate path curvature

### Phase 6 — Lateral MPC

- Build a path-error model
- Optimize steering commands
- Enforce steering-angle and steering-rate constraints
- Validate low-speed path tracking
- Add curvature feedforward

### Phase 7 — Dual-MPC operation

- Run lateral and longitudinal MPC together
- Add curvature-based speed planning
- Add solver-failure fallback behavior
- Measure total control-loop execution time

### Phase 8 — Safety and traffic interaction

- Spawn a lead vehicle
- Calculate distance and time to collision
- Add safe-following logic
- Add emergency braking
- Add longitudinal safety constraints

### Phase 9 — Evaluation

- Implement repeatable scenarios
- Compare MPC against a PID baseline
- Measure tracking, comfort, safety, and computation metrics
- Save configuration and results for every experiment

## Intended evaluation scenarios

1. Straight-road speed tracking
2. Curved-road lane following
3. Combined path and speed tracking
4. Curvature-aware speed reduction
5. Smooth lane-change maneuver
6. Lead-vehicle following
7. Disturbance rejection
8. Solver-failure fallback
9. PID versus MPC comparison

## Important notes

- The CARLA client and server versions should match.
- CARLA-dependent diagnostics require the simulator to be running.
- Vehicle-state and vehicle-physics diagnostics require a spawned vehicle.
- The blueprint metadata reports `number_of_wheels = 3` for `vehicle.lincoln.mkz`; this should not be treated as authoritative until verified through `vehicle.get_physics_control().wheels`.
- The project currently uses simulator ground truth. Sensor-based state estimation will be added only after the controller works reliably.
- Nonlinear MPC is outside the initial implementation scope.

## Next implementation task

Create a safe ego-vehicle spawning utility that:

- reads the blueprint from `config/project_config.yaml`
- selects a valid CARLA spawn point
- assigns the role name `ego`
- disables autopilot
- verifies actor creation
- destroys the vehicle during cleanup

After spawning the vehicle, rerun:

```bash
python3 run_diagnostics.py
```

The two previously skipped diagnostics should then execute.
