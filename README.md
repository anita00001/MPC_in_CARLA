# Hierarchical Dual-MPC Autonomous Driving in CARLA

## Project Overview

This project develops a constraint-aware autonomous driving controller in the CARLA simulator using a hierarchical dual Model Predictive Control architecture.

The system is divided into two coordinated controllers:

- **Lateral MPC** for steering and path tracking
- **Longitudinal MPC** for speed tracking, acceleration, throttle, and braking

A supervisory layer manages speed planning, solver failures, emergency braking, and safety overrides.

The initial implementation uses CARLA ground-truth vehicle state data so that controller design can be validated independently from perception. Sensor-based localization, object detection, and advanced estimation are planned as later extensions.

## Project Title

**Design and Comparative Evaluation of a Hierarchical Dual-MPC Autonomous Vehicle Controller for Constrained Path Tracking, Adaptive Speed Control, and Lead-Vehicle Following in CARLA**

## Main Objectives

The completed system should be able to:

1. Spawn and control an ego vehicle in CARLA.
2. Follow a predefined route.
3. Track a changing target speed.
4. Reduce speed before entering curves.
5. Respect steering, acceleration, braking, and steering-rate constraints.
6. Perform smooth lane-change maneuvers.
7. Follow a lead vehicle while maintaining a safe gap.
8. Stop safely when a solver fails or a collision risk is detected.
9. Log and evaluate tracking, comfort, safety, and computation metrics.
10. Compare MPC performance against a PID baseline under identical conditions.

## System Architecture

```text
CARLA map
    |
    v
Global route planner
    |
    v
Reference generator
    |-- Local path
    |-- Reference heading
    |-- Reference curvature
    |-- Reference speed
    |
    v
State estimator
    |-- Position
    |-- Yaw
    |-- Speed
    |-- Yaw rate
    |
    v
Supervisory controller
    |-- Curve-speed planning
    |-- Lead-vehicle handling
    |-- Emergency braking
    |-- Solver-failure fallback
    |
    +---------------------------+
    |                           |
    v                           v
Lateral MPC               Longitudinal MPC
Steering command          Acceleration command
    |                           |
    +-------------+-------------+
                  |
                  v
            Actuator mapper
      steering / throttle / brake
                  |
                  v
          CARLA VehicleControl
```

## Initial Technical Scope

This implementation will include:

- One ego vehicle
- CARLA synchronous simulation
- Fixed simulation time step
- Ground-truth state access
- Waypoint-based route generation
- Lateral MPC
- Longitudinal MPC
- Curvature-based speed planning
- Lead-vehicle following
- Emergency braking
- Solver-failure fallback
- CSV logging
- Automated metrics
- PID baseline comparison

This implementation will not require:

- Camera-based lane detection
- Object detection
- SLAM
- Neural-network perception
- ROS integration
- Nonlinear MPC
- Multi-agent cooperation

These can be added after the control system is reliable.

##   Project Structure

```text
MPC_in_CARLA/
├── config/
│   ├── project_config.yaml
│   ├── controller.yaml
│   ├── vehicle.yaml
│   └── scenarios.yaml
│
├── diagnostics/
│   ├── carla/
│   ├── environment/
│   ├── solvers/
│   └── vehicles/
│
├── controllers/
│   ├── lateral_mpc.py
│   ├── longitudinal_mpc.py
│   ├── actuator_mapper.py
│   └── safety_supervisor.py
│
├── models/
│   ├── lateral_model.py
│   ├── longitudinal_model.py
│   └── dynamic_bicycle.py
│
├── planning/
│   ├── route_planner.py
│   ├── reference_generator.py
│   ├── speed_planner.py
│   └── obstacle_tracker.py
│
├── estimation/
│   ├── ground_truth.py
│   └── ekf.py
│
├── scenarios/
│   ├── straight_speed_test.py
│   ├── curved_route_test.py
│   ├── lane_change_test.py
│   └── following_test.py
│
├── evaluation/
│   ├── logger.py
│   ├── metrics.py
│   └── plots.py
│
├── tests/
│   ├── test_models.py
│   ├── test_reference.py
│   └── test_actuator_mapper.py
│
├── run_diagnostics.py
├── run_experiment.py
└── README.md
```

# Project Roadmap

## Phase 1 — Environment and Toolchain Preparation

### Purpose

Establish a reliable development environment before writing controller code.

### Tasks

- Confirm the Python interpreter used by the project.
- Verify that the CARLA Python client can be imported.
- Confirm that the CARLA client and server versions match.
- Verify access to the CARLA map and world.
- Check that CVXPY and OSQP are installed.
- Solve a small test optimization problem with OSQP.
- Verify supporting packages such as NumPy, SciPy, pandas, Matplotlib, and PyYAML.
- Benchmark the CARLA simulation step time.
- Confirm that the intended ego-vehicle blueprint exists.

### Deliverables

- Working CARLA client connection
- Working OSQP solver
- Project configuration file
- Diagnostic scripts
- Reproducible environment checks

### Completion Criteria

This phase is complete when:

- CARLA is reachable from Python.
- The client and server versions match.
- A valid vehicle blueprint is available.
- CVXPY can solve a quadratic program with OSQP.
- The simulation can run at the proposed control interval.

---

## Phase 2 — Ego-Vehicle Spawning and Cleanup

### Purpose

Create a reusable and safe mechanism for spawning the ego vehicle.

### Tasks

- Read the vehicle blueprint from configuration.
- Select a valid CARLA spawn point.
- Assign the role name `ego`.
- Disable autopilot.
- Spawn the vehicle using `try_spawn_actor`.
- Confirm actor creation.
- Store the actor reference.
- Destroy the actor during cleanup.
- Restore CARLA world settings on exit.
- Handle failed spawn attempts gracefully.

###   Files

```text
carla_session.py
vehicles/spawn_ego.py
config/vehicle.yaml
```

### Deliverables

- Ego-vehicle spawning utility
- Safe cleanup logic
- Configurable vehicle selection
- Spawn-point selection logic

### Completion Criteria

This phase is complete when:

- One ego vehicle can be spawned consistently.
- The vehicle can be identified by role name.
- The actor is destroyed when the script exits.
- Repeated runs do not leave abandoned actors.

---

## Phase 3 — Deterministic CARLA Session

### Purpose

Make simulation execution repeatable and suitable for closed-loop control.

### Tasks

- Preserve the original CARLA world settings.
- Enable synchronous mode.
- Set a fixed simulation time step.
- Advance the world using `world.tick()`.
- Read frame numbers and timestamps.
- Restore the original settings when the program exits.
- Configure Traffic Manager for synchronous mode when traffic is used.
- Add exception handling for interrupted runs.

###   Initial Setting

```text
Fixed simulation step: 0.05 s
Controller frequency: 20 Hz
```

### Deliverables

- `CarlaSession` wrapper
- Deterministic simulation loop
- Automatic settings restoration

### Completion Criteria

This phase is complete when:

- Every `world.tick()` advances exactly one frame.
- Simulation timestamps increase by the configured fixed interval.
- World settings are restored after normal exit and exceptions.

---

## Phase 4 — Vehicle State Access and Representation

### Purpose

Create a consistent state representation for controller input.

### Initial State Source

Use CARLA ground-truth actor information.

### State Variables

```text
x position
y position
z position
yaw angle
longitudinal speed
velocity components
yaw rate
acceleration
simulation timestamp
frame number
```

### Tasks

- Read vehicle transform.
- Convert CARLA yaw from degrees to radians.
- Read linear velocity.
- Calculate speed magnitude.
- Read angular velocity.
- Read acceleration.
- Define a `VehicleState` dataclass.
- Normalize all angles consistently.
- Validate units.

### Files

```text
estimation/ground_truth.py
models/state.py
```

### Deliverables

- Ground-truth state estimator
- Standard vehicle-state structure
- Unit and angle conventions

### Completion Criteria

This phase is complete when:

- Position, yaw, speed, and yaw rate update consistently.
- All controller inputs use SI units.
- Angles are represented consistently in radians.

---

## Phase 5 — Data Logging and Experiment Recording

### Purpose

Make controller behavior measurable and reproducible.

### Data to Record

```text
simulation time
frame number
vehicle position
yaw
speed
acceleration
yaw rate
reference position
reference heading
reference speed
lateral error
heading error
steering command
acceleration command
throttle
brake
solver status
solver time
safety override state
```

### Tasks

- Create an experiment logger.
- Store data in memory during a run.
- Save results to CSV.
- Save the configuration used for each experiment.
- Create unique output directories.
- Add plotting utilities.
- Record failure conditions.

###   Output Structure

```text
results/
└── experiment_name/
    ├── data.csv
    ├── config.yaml
    ├── metrics.json
    └── plots/
```

### Deliverables

- CSV logger
- Experiment metadata
- Plotting utilities
- Result-directory convention

### Completion Criteria

This phase is complete when:

- Every control step is recorded.
- Results can be loaded with pandas.
- A run can be reproduced from its saved configuration.

---

## Phase 6 — Actuator Characterization

### Purpose

Measure how the selected CARLA vehicle responds to throttle and brake commands.

### Tasks

- Run constant-throttle tests.
- Run constant-brake tests.
- Record speed and acceleration.
- Estimate acceleration using finite differences.
- Apply low-pass filtering to acceleration estimates.
- Identify throttle dead zones.
- Identify brake dead zones.
- Estimate maximum useful acceleration.
- Estimate maximum normal deceleration.
- Build an initial acceleration-to-actuator mapping.

### Test Inputs

Example throttle values:

```text
0.1
0.2
0.3
0.5
0.7
```

Example brake values:

```text
0.1
0.3
0.5
0.7
1.0
```

### Deliverables

- Vehicle-response dataset
- Throttle-response plots
- Brake-response plots
- Initial actuator mapper

### Completion Criteria

This phase is complete when:

- Positive acceleration commands can be mapped to throttle.
- Negative acceleration commands can be mapped to brake.
- Dead zones are handled.
- The mapping produces stable speed-control behavior.

---

## Phase 7 — Longitudinal Vehicle Model

### Purpose

Create the prediction model used by longitudinal MPC.

### Initial Model

```text
v(k+1) = v(k) + Ts * a(k)
```

Optional expanded model:

```text
s(k+1) = s(k) + Ts * v(k)
v(k+1) = v(k) + Ts * a(k)
```

### Tasks

- Define the discrete model.
- Define state and input matrices.
- Validate predictions against CARLA data.
- Add drag or acceleration bias later if needed.
- Add speed-dependent parameters only after the basic model works.

### Deliverables

- `longitudinal_model.py`
- Model tests
- Prediction-validation plots

### Completion Criteria

This phase is complete when:

- The model predicts short-horizon speed changes reasonably.
- Matrix dimensions and units are verified.
- Automated tests cover the state update.

---

## Phase 8 — Longitudinal MPC

### Purpose

Track a speed reference while respecting acceleration and comfort constraints.

### Optimization Objective

The longitudinal MPC should penalize:

- Speed tracking error
- Acceleration magnitude
- Acceleration change
- Jerk

### Constraints

Typical initial constraints:

```text
Minimum acceleration
Maximum acceleration
Minimum speed
Optional maximum speed
Optional jerk limit
```

### Tasks

- Define optimization variables.
- Add discrete dynamics.
- Add input and state constraints.
- Build the objective function.
- Solve with OSQP.
- Apply only the first optimized input.
- Warm-start the next solve.
- Handle infeasible or failed solutions.
- Record solver status and execution time.

### Test Scenarios

- Constant speed
- Step changes in speed
- Ramp speed reference
- Full stop
- Repeated acceleration and braking

### Deliverables

- `longitudinal_mpc.py`
- Speed-tracking experiment
- Longitudinal tuning configuration
- Solver timing measurements

### Completion Criteria

This phase is complete when:

- The vehicle tracks a changing speed reference.
- Overshoot is acceptable.
- Throttle and brake do not oscillate excessively.
- Solver execution stays inside the control period.

---

## Phase 9 — Route Generation

### Purpose

Create a reference route for autonomous path tracking.

### Tasks

- Obtain CARLA map waypoints.
- Generate a forward route from a spawn point.
- Handle intersections.
- Store route position, heading, and road information.
- Resample the route at a consistent spacing.
- Plot the route for inspection.
- Later replace simple branch selection with a global route planner.

### Route Data

```text
x
y
z
yaw
road ID
lane ID
lane width
curvature
cumulative distance
```

### Deliverables

- `route_planner.py`
- Route export
- Route visualization
- Route validation tests

### Completion Criteria

This phase is complete when:

- The route follows the intended lane center.
- Route points are ordered correctly.
- The route does not jump unexpectedly between nearby lanes.

---

## Phase 10 — Reference Generation and Path Errors

### Purpose

Generate the local path information needed by lateral MPC.

### Tasks

- Find the nearest route point.
- Limit the nearest-point search to a forward window.
- Calculate signed lateral error.
- Calculate heading error.
- Normalize heading error to `[-pi, pi]`.
- Build a look-ahead reference horizon.
- Estimate path curvature.
- Smooth noisy curvature estimates.
- Verify coordinate and sign conventions.

### Path Errors

```text
Lateral error:
signed distance from the vehicle to the reference path

Heading error:
vehicle yaw minus reference yaw
```

### Deliverables

- `reference_generator.py`
- Nearest-point search
- Error-calculation functions
- Curvature horizon
- Unit tests for error signs

### Completion Criteria

This phase is complete when:

- Left and right path offsets have consistent signs.
- Steering direction is consistent with the calculated errors.
- Heading wraparound does not cause discontinuities.

---

## Phase 11 — Lateral Vehicle Model

### Purpose

Create the prediction model used by lateral MPC.

### Initial Error-State Model

```text
State:
e_y      lateral error
e_psi    heading error

Input:
delta    steering angle
```

Example discrete dynamics:

```text
e_y(k+1) =
    e_y(k) + Ts * v * e_psi(k)

e_psi(k+1) =
    e_psi(k)
    + Ts * ((v / L) * delta(k) - v * curvature(k))
```

### Tasks

- Determine or estimate wheelbase.
- Define steering-angle units.
- Define a low-speed safeguard.
- Include curvature feedforward.
- Validate model predictions.
- Add speed scheduling later if required.

### Deliverables

- `lateral_model.py`
- Wheelbase configuration
- Model validation
- Automated tests

### Completion Criteria

This phase is complete when:

- Steering signs match CARLA behavior.
- The model predicts the direction of path-error change.
- The model is stable over the prediction horizon.

---

## Phase 12 — Lateral MPC

### Purpose

Track the lane center while respecting steering constraints.

### Optimization Objective

The lateral MPC should penalize:

- Lateral error
- Heading error
- Steering magnitude
- Steering-rate change

### Constraints

```text
Maximum steering angle
Maximum steering rate
Optional lateral-error bounds
```

### Tasks

- Define state and steering variables.
- Add the lateral error dynamics.
- Add steering-angle constraints.
- Add steering-rate constraints.
- Add curvature reference.
- Solve with OSQP.
- Normalize steering to CARLA input.
- Warm-start the solver.
- Handle solver failures.

### Test Progression

1. Straight road at low speed
2. Gentle curve at low speed
3. Curved route at medium speed
4. Different initial lateral offsets
5. Different heading errors

### Deliverables

- `lateral_mpc.py`
- Low-speed lane-following scenario
- Lateral tuning configuration
- Tracking plots

### Completion Criteria

This phase is complete when:

- The vehicle follows a route without sustained oscillation.
- Lateral error remains within a declared limit.
- Steering-rate limits are respected.
- Solver execution remains inside the control period.

---

## Phase 13 — Dual-MPC Integration

### Purpose

Run lateral and longitudinal control together.

### Tasks

- Read one synchronized state per frame.
- Generate lateral and longitudinal references.
- Solve both controllers.
- Map acceleration to throttle and brake.
- Normalize steering.
- Apply one CARLA control command.
- Record total loop execution time.
- Define the order of safety overrides.
- Add fallback commands.

### Control Loop

```text
Tick CARLA
Read state
Update nearest route point
Generate path reference
Generate speed reference
Solve lateral MPC
Solve longitudinal MPC
Run safety supervisor
Map commands
Apply CARLA control
Log results
```

### Deliverables

- Integrated control loop
- `run_experiment.py`
- Shared configuration
- Combined-control scenario

### Completion Criteria

This phase is complete when:

- Both controllers run in the same frame loop.
- Commands remain stable.
- Total computation remains within the control period.
- The vehicle completes a basic route.

---

## Phase 14 — Curvature-Based Speed Planning

### Purpose

Reduce speed before curves to improve safety and path tracking.

### Planned Relationship

```text
v_curve =
sqrt(a_y_max / (abs(curvature) + epsilon))
```

### Tasks

- Read future curvature along the route.
- Calculate a curve-limited speed.
- Apply a maximum cruise speed.
- Add minimum curve speed.
- Smooth the speed profile.
- Limit acceleration and deceleration between reference points.
- Provide a speed horizon to longitudinal MPC.

### Deliverables

- `speed_planner.py`
- Curve-speed reference
- Constant-speed versus adaptive-speed comparison

### Completion Criteria

This phase is complete when:

- The vehicle slows before entering curves.
- Lateral error decreases on tighter bends.
- Speed references do not change abruptly.

---

## Phase 15 — Safety Supervisor

### Purpose

Provide an independent protection layer outside the MPC optimization.

### Safety Conditions

- Repeated solver failure
- Invalid vehicle state
- Excessive lateral error
- Missed control deadline
- Unsafe lead-vehicle gap
- Low time to collision
- Collision detection
- Route loss

### Possible Responses

```text
Hold previous control briefly
Reduce target speed
Apply controlled braking
Apply emergency braking
Stop the experiment
```

### Tasks

- Define safety states.
- Define escalation rules.
- Track consecutive solver failures.
- Add time-to-collision calculation.
- Add independent emergency braking.
- Record every safety intervention.
- Ensure the safety supervisor overrides controller outputs.

### Deliverables

- `safety_supervisor.py`
- Safety event logging
- Failure-injection tests

### Completion Criteria

This phase is complete when:

- Solver failure does not produce uncontrolled commands.
- The vehicle can stop safely.
- Emergency braking overrides MPC.
- Safety events are traceable in logs.

---

## Phase 16 — Lead-Vehicle Following

### Purpose

Extend longitudinal MPC to maintain a safe following distance.

### Desired Gap Model

```text
desired_gap =
minimum_gap + time_headway * ego_speed
```

### Tasks

- Spawn a lead vehicle.
- Confirm that ego and lead vehicles are in the same lane.
- Estimate relative longitudinal distance.
- Estimate relative speed.
- Predict lead-vehicle motion.
- Create a following-speed reference.
- Add a distance constraint to longitudinal MPC.
- Introduce slack variables to reduce infeasibility.
- Add emergency braking for low TTC.

### Deliverables

- Lead-vehicle scenario
- Relative-state estimator
- Safe-distance constraint
- Following-performance metrics

### Completion Criteria

This phase is complete when:

- The ego vehicle follows a slower vehicle smoothly.
- The desired time headway is maintained.
- Sudden lead-vehicle deceleration triggers a safe response.

---

## Phase 17 — Lane-Change Planning and Control

### Purpose

Demonstrate smooth lateral maneuvering beyond lane-center tracking.

### Tasks

- Select start and target lanes.
- Generate a smooth lane-change path.
- Use a quintic polynomial or spline.
- Ensure zero lateral velocity and acceleration at the start and end.
- Build path and curvature references.
- Test different speeds and maneuver lengths.
- Enforce steering and comfort constraints.

### Deliverables

- Lane-change reference generator
- Lane-change scenario
- Maneuver metrics

### Completion Criteria

This phase is complete when:

- The lane change ends near the target lane center.
- Lateral overshoot is limited.
- Steering and lateral acceleration remain within limits.

---

## Phase 18 — PID Baseline

### Purpose

Create a fair comparison between MPC and conventional control.

### Tasks

- Implement or reuse a longitudinal PID.
- Implement or reuse a lateral PID.
- Use the same route and speed reference.
- Use the same vehicle and spawn point.
- Use the same simulation settings.
- Run identical scenarios.
- Record the same metrics.

### Deliverables

- PID controller implementation
- Shared experiment configuration
- MPC-versus-PID result tables

### Completion Criteria

This phase is complete when:

- PID and MPC are evaluated under identical conditions.
- Results are reported without assuming MPC is always superior.

---

## Phase 19 — Evaluation Framework

### Purpose

Measure the controller objectively.

### Tracking Metrics

- Speed RMSE
- Lateral RMSE
- Heading RMSE
- Maximum lateral error
- Maximum speed error
- Stopping-distance error
- Route completion percentage

### Comfort Metrics

- RMS acceleration
- Maximum acceleration
- Maximum deceleration
- RMS jerk
- Maximum jerk
- RMS steering rate
- Maximum steering rate
- Lateral acceleration

### Safety Metrics

- Minimum lead-vehicle gap
- Minimum TTC
- Lane invasions
- Collisions
- Constraint violations
- Emergency-braking events

### Computation Metrics

- Mean solver time
- 95th-percentile solver time
- Maximum solver time
- Solver failure count
- Missed deadlines
- Total control-loop time

### Deliverables

- `metrics.py`
- Automated summary reports
- Comparison plots
- Experiment tables

### Completion Criteria

This phase is complete when:

- Every scenario produces a repeatable metric report.
- Results can be compared across configurations.
- Timing and solver failures are included.

---

## Phase 20 — Robustness and Disturbance Testing

### Purpose

Evaluate how the controller behaves outside ideal conditions.

### Disturbances

- Initial lateral offset
- Initial heading error
- Noisy state measurements
- Delayed measurements
- Vehicle mass variation
- Different road friction
- Sudden reference changes
- Lead-vehicle emergency braking
- Partial solver failure

### Tasks

- Define controlled disturbance scenarios.
- Run repeated trials.
- Measure recovery time.
- Measure peak error.
- Compare MPC and PID robustness.
- Identify failure boundaries.

### Deliverables

- Disturbance scenarios
- Robustness plots
- Failure-case documentation

### Completion Criteria

This phase is complete when:

- Recovery behavior is quantified.
- Failure cases are documented rather than hidden.
- Safety behavior is verified under disturbances.

---

## Phase 21 — Sensor-Based State Estimation

### Purpose

Reduce dependence on simulator ground truth.

### Possible Sensors

- GNSS
- IMU
- Wheel-speed estimate
- Lane-detection output
- Radar or lidar for lead-vehicle tracking

### Tasks

- Spawn sensors.
- Synchronize sensor frames.
- Add measurement-noise models.
- Implement an Extended Kalman Filter.
- Estimate position, yaw, speed, and yaw rate.
- Compare estimated state against CARLA ground truth.
- Run the controller using estimated state.

### Deliverables

- Sensor manager
- EKF implementation
- State-estimation evaluation
- Estimated-state controller mode

### Completion Criteria

This phase is complete when:

- State estimates remain sufficiently accurate for control.
- Controller performance remains acceptable without direct ground truth.

---

## Phase 22 — Advanced MPC Extensions

### Purpose

Improve model accuracy and performance after the linear controllers are stable.

### Possible Extensions

- Gain-scheduled MPC
- Adaptive MPC
- Nonlinear MPC
- Integrated steering and acceleration MPC
- Dynamic bicycle model
- Tire-force constraints
- Road-friction estimation
- Online model adaptation

### Tasks

- Identify limitations of the linear controllers.
- Add only one extension at a time.
- Reuse the same scenarios and metrics.
- Compare complexity, performance, and solve time.

### Deliverables

- Advanced controller variant
- Comparative analysis
- Computational-cost evaluation

### Completion Criteria

This phase is complete when:

- The advanced method demonstrates a measurable benefit.
- Real-time feasibility is evaluated.
- Improvements are not claimed without evidence.

---

## Phase 23 — Final Documentation and Reproducibility

### Purpose

Make the project understandable, repeatable, and suitable for assessment or publication.

### Tasks

- Document installation.
- Document CARLA startup.
- Document configuration files.
- Document every experiment.
- Save random seeds.
- Save software versions.
- Add diagrams.
- Add result tables and plots.
- Explain limitations.
- Include failure cases.
- Add a final demonstration script.

### Deliverables

- Final README
- Installation guide
- Experiment guide
- Configuration reference
- Final report
- Demonstration video
- Reproducible result archive

# Implementation Order

1. Environment validation
2. Ego-vehicle spawning
3. Deterministic CARLA session
4. Ground-truth state access
5. Logging
6. Actuator characterization
7. Longitudinal model
8. Longitudinal MPC
9. Route generation
10. Path-error calculation
11. Lateral model
12. Lateral MPC
13. Dual-MPC integration
14. Curvature-based speed planning
15. Safety supervisor
16. Lead-vehicle following
17. Lane-change control
18. PID baseline
19. Evaluation framework
20. Robustness testing
21. Sensor-based estimation
22. Advanced MPC
23. Final documentation


# Milestones

## Milestone 1 — Controlled CARLA Vehicle

The ego vehicle can be spawned, controlled, and cleaned up safely.

## Milestone 2 — Working Longitudinal Control

The vehicle follows changing speed references.

## Milestone 3 — Working Lateral Control

The vehicle follows a CARLA route at low speed.

## Milestone 4 — Integrated Dual MPC

Both controllers operate together in a synchronized loop.

## Milestone 5 — Constraint-Aware Driving

The vehicle slows for curves and respects actuator limits.

## Milestone 6 — Safety and Following

The ego vehicle follows a lead vehicle and performs emergency braking.

## Milestone 7 — Comparative Evaluation

MPC and PID are evaluated under repeatable scenarios.

## Milestone 8 — Final Demonstration

The vehicle completes a route containing curves, speed changes, lane changes, and traffic interaction.

# Definition of Project Completion

The project is complete when:

1. The ego vehicle completes a predefined route.
2. Speed follows a changing reference.
3. Lateral error remains within a declared limit.
4. The vehicle slows before major curves.
5. Steering and acceleration constraints are respected.
6. The control loop meets its timing requirement.
7. Solver failures result in safe fallback behavior.
8. The vehicle maintains a safe lead-vehicle gap.
9. Lane-change behavior is smooth and repeatable.
10. MPC and PID are compared under identical conditions.
11. Results are reproducible from saved configurations.
12. Limitations and failure cases are documented.
