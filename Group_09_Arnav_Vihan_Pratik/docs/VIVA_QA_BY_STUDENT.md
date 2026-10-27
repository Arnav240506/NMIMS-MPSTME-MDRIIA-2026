# Individual viva preparation

Answers describe verified implementation, not evidence of who authored it. Each student should explain the equation, show the code and state its limitation.

## Arnav Saurabh Surve (E064)

### 1. Why is this an M20 dog rather than a car?
It has four multi-joint legs from the supplied M20 chain, 12 leg motors and four wheeled feet. We demonstrate actual foot lift and paired transfers. Wheels are part of this hybrid model.
Code/evidence: `scene.build_scene`. Follow-up: show its inputs, one logged output and one failure boundary.

### 2. How many degrees of freedom are present?
There are 16 actuated joints plus a free floating base: nq=23 because the base quaternion uses four numbers; nv=22 because base rotation has three velocities.
Code/evidence: `tests.test_authentic_anatomy`. Follow-up: show its inputs, one logged output and one failure boundary.

### 3. What is the actual mass?
Summing the supplied XML inertias gives 34.525856 kg. We preserved those inertias and corrected the old 23.3 kg text.
Code/evidence: `scene.build_scene`. Follow-up: show its inputs, one logged output and one failure boundary.

### 4. How does inverse kinematics work?
The two 0.25 m links use cos(knee)=(x²+z_leg²-l1²-l2²)/(2*l1*l2). The lateral offset first determines hip roll; front and rear use different knee branches. FK is checked against MuJoCo.
Code/evidence: `legged_control.inverse_leg`. Follow-up: show its inputs, one logged output and one failure boundary.

### 5. What torques are applied?
PD joint error, bias compensation and stance-Jacobian terms are combined, then leg torques are clipped to ±76.4 N m and hubs to ±21.6 N m. Torque is sent through motors, not the floating base.
Code/evidence: `hybrid_control.M20Actuation.apply`. Follow-up: show its inputs, one logged output and one failure boundary.

### 6. Is the balance controller MPC?
No. It allocates an instantaneous desired body wrench using regularized least squares and clips contact forces. It has no prediction horizon or constrained MPC solve.
Code/evidence: `hybrid_control.M20Actuation.apply`. Follow-up: show its inputs, one logged output and one failure boundary.

### 7. Why climb with front and rear pairs?
This follows the README strategy: lower and shift the CoM over the support pair, lift the other pair with floating wheels, plant it, move the torso and then lift the rear pair. Two-foot support remains a demanding balance condition.
Code/evidence: `hybrid_control.PairClimbController`. Follow-up: show its inputs, one logged output and one failure boundary.

### 8. How do you prove an actual climb?
Measure from settled standing, require actual front/rear liftoff and re-support, then all four feet beyond the true lip, at plateau height, with support contacts. Merely standing from crouch cannot pass.
Code/evidence: `simulation.run_trial`. Follow-up: show its inputs, one logged output and one failure boundary.

### 9. What was the contact bug?
A rear upper-leg collision touched the step during rear transfer. The evaluator rejected it; raising the rear transfer body reference by 3 cm removed it in the verified showcase.
Code/evidence: `simulation.contact_audit`. Follow-up: show its inputs, one logged output and one failure boundary.

### 10. How is slip measured?
The logged proxy compares hub speed times wheel radius against body longitudinal speed, normalized by at least 0.10 m/s. It is a kinematic discrepancy, especially imperfect during swings and turns, not calibrated physical slip.
Code/evidence: `simulation.run_trial`. Follow-up: show its inputs, one logged output and one failure boundary.

### 11. How does skid steering turn?
uL=v-w*b/2, uR=v+w*b/2, with effective track 0.55 m. M20 wheel axes are -y, so forward target joint rates are negative. Feedback compensates measured yaw-rate error and pivot drift.
Code/evidence: `recon_controller.ReconExecutive.physics_tick`. Follow-up: show its inputs, one logged output and one failure boundary.

### 12. Can the dog walk indefinitely?
The supplied evidence verifies a 12-second diagonal-pair demonstration. A longer development run destabilized around 24 seconds. More robust gait optimization and hardware tests remain open.
Code/evidence: `legged_control.CrawlController`. Follow-up: show its inputs, one logged output and one failure boundary.

## Vihan Shripad Joshi (E070)

### 1. Where do map heights come from?
From native MuJoCo multi-ray intersections with actual environment geometry. The controller does not read terrain heights directly from the scene metadata.
Code/evidence: `m20_rosbot_mapping.raycast`. Follow-up: show its inputs, one logged output and one failure boundary.

### 2. What is 2.5D mapping?
Each x-y cell stores measured elevation statistics rather than a full volume. Overhangs and multi-level terrain are poorly represented, so it is not full 3D reconstruction.
Code/evidence: `m20_rosbot_mapping.M20Map`. Follow-up: show its inputs, one logged output and one failure boundary.

### 3. Is this SLAM?
No. Pose is exactly known from MuJoCo. We accumulate a global grid using that pose; we do not estimate pose, optimize a pose graph or close loops.
Code/evidence: `m20_rosbot_mapping.M20Map.scan`. Follow-up: show its inputs, one logged output and one failure boundary.

### 4. What is the real map update rate?
Rays are integrated at 50 Hz in 16 interleaved groups. A full lattice takes 0.32 s of simulated time. Cost updates are 10 Hz and planning requests are 5 Hz; no wall-clock throughput claim is made.
Code/evidence: `m20_rosbot_mapping.M20Map.scan`. Follow-up: show its inputs, one logged output and one failure boundary.

### 5. How do cells aggregate samples?
The mapper stores count, sum, squared sum, mean and peak. Empty cells remain unknown. Peaks help detect hazards; mean and local variation support traversability costs.
Code/evidence: `m20_rosbot_mapping.M20Map.integrate`. Follow-up: show its inputs, one logged output and one failure boundary.

### 6. How is cost calculated?
c=0.4 clip(slope/30deg)+0.3 clip(roughness/0.04m)+0.3 clip(step/0.14m). The later obstacle proximity penalty is separate and can make the A* planning cost exceed one.
Code/evidence: `m20_rosbot_mapping.normalized_cost`. Follow-up: show its inputs, one logged output and one failure boundary.

### 7. How is the robot removed from its own scan?
Geometry groups exclude robot collisions/visual meshes while retaining environmental obstacles. We no longer discard every height above 0.35 m, which would erase genuine tall hazards.
Code/evidence: `m20_rosbot_mapping.ENVIRONMENT_GROUPS`. Follow-up: show its inputs, one logged output and one failure boundary.

### 8. How does A* choose a route?
Eight-neighbor edges cost distance times a risk weight. The Euclidean heuristic is a lower bound because all edge weights are at least distance. Unknown/inflated cells and diagonal corner cuts are blocked.
Code/evidence: `m20_rosbot_mapping.astar`. Follow-up: show its inputs, one logged output and one failure boundary.

### 9. Why inflate obstacles by 0.70 m?
The planned center must leave room for the robot footprint and extra tracking/slip margin. This conservative circular approximation does not prove exact swept-body clearance for every posture.
Code/evidence: `m20_rosbot_mapping.M20Map.update_cost`. Follow-up: show its inputs, one logged output and one failure boundary.

### 10. What happens if no route exists?
Try reachable measured frontiers; otherwise command zero rather than guessing forward through unknown terrain. The blocked fixture is intentionally not counted as mission completion.
Code/evidence: `m20_rosbot_mapping.plan_route`. Follow-up: show its inputs, one logged output and one failure boundary.

### 11. How is the curb located?
Broad connected measured cells above 3.5 cm and below 14 cm indicate a low terrace. Its leading cell supplies lip position and median measured peak supplies height; this is a fixture-specific detector.
Code/evidence: `m20_rosbot_mapping.M20Map.detect_step`. Follow-up: show its inputs, one logged output and one failure boundary.

### 12. Do RGB/depth cameras control the robot?
Their rendered panels are for observation. Mapping uses ideal LiDAR rays; cameras are not fused into control. Real perception would need noise, calibration, motion compensation and localization tests.
Code/evidence: `replay.replay`. Follow-up: show its inputs, one logged output and one failure boundary.

## Pratik Mangesh Gaikwad (E073)

### 1. What is the actual baseline?
A deterministic delayed reactive software driver on the same M20 standing servo. It steers toward the goal and reacts to forward range; it has no A* map or paired climb. It is not a human operator.
Code/evidence: `recon_controller.reactive_driver`. Follow-up: show its inputs, one logged output and one failure boundary.

### 2. How is latency simulated?
Commands are timestamped with release time t+delay and queued FIFO. All commands due by the current simulation time are released in order. Delays are 0.05, 0.35, 0.8 or 1.2 s in the benchmark.
Code/evidence: `recon_controller.LatencyQueue`. Follow-up: show its inputs, one logged output and one failure boundary.

### 3. Does shared autonomy experience the same delay?
The remote intent channel is delayed, but the local shared planner retains control authority. That is the intended architectural advantage. The study bundles planning and climbing, so it cannot isolate latency alone.
Code/evidence: `recon_controller.ReconExecutive.navigation_tick`. Follow-up: show its inputs, one logged output and one failure boundary.

### 4. How many final experiments were actually run?
Sixty independent physics trials: 30 per policy, ten per policy at each roughness bound 0, 3 and 6 mm. Proposed acceptance is 30/30; baseline acceptance is 0/30. All failures remain. Raw logs contain 4,495,972 actual 500 Hz samples, not interpolated 50 Hz data.
Code/evidence: `analytics/run_capstone_benchmark.py` and `analytics/capstone_500hz/verification.json`.

### 5. Why are these groups independent?
Baseline seeds 31000–31029 and proposed seeds 32000–32029 are disjoint. Both sample the same declared scenario design. Do not apply the earlier paired-study method to these runs.

### 6. What is the primary hypothesis test?
Predeclared Welch two-sample inference tests equality of mean terminal XY goal error. Means are 12.310317 m baseline and 0.106357 m proposed. The proposed-minus-baseline difference is -12.203960 m, t=-715.183, df=29.446, p=5.51e-64.
Code/evidence: `analytics/analyze_capstone.py` and `analytics/capstone_500hz/statistics.json`.

### 7. What does pooled Cohen d mean here?
It is the mean difference divided by pooled within-group standard deviation: -184.6595. It is not paired d_z. Its extreme magnitude follows a weak baseline failing at the first barrier with little variability. This is not evidence of general superiority over capable planners or human experts.

### 8. What does the 95% interval describe?
The Welch interval [-12.23884,-12.16908] m describes uncertainty in the mean difference under this trial design and its assumptions. It does not establish hardware safety, all-environment reliability or human benefit. Mann–Whitney sensitivity also separates these groups, but does not repair the weak comparator.

### 9. Did operator workload decrease by 64%?
No human workload was measured. Intervention counts are software events, not NASA-TLX. A participant study would need a protocol, consent, task counterbalancing and valid scales.
Code/evidence: `docs/PROJECT_AUDIT_AND_EVIDENCE.md`. Follow-up: show its inputs, one logged output and one failure boundary.

### 10. What is dimensionless cost parity?
kappa=robot operating parity/reclaimed-value parity. Inputs are illustrative normalized assumptions; no real operational savings are inferred from these simulations.
Code/evidence: `analytics.hazardous_recon_economics.economics`. Follow-up: show its inputs, one logged output and one failure boundary.

### 11. How are payback and FTE calculated?
For annual value V, annual operating cost O, capital K and life L: kappa=O/V, payback months=12K/(V-O), P=K/[L(V-O)], NCRI=1-kappa. No positive savings means no finite savings payback. With assumed V=1, O=.22, K=.30, L=5, payback is 4.6154 months and P=.076923. Assumed 312 hours/2080 gives .15 FTE; it is not measured labor reduction.
Code/evidence: `analytics.hazardous_recon_economics.economics`. Follow-up: show its inputs, one logged output and one failure boundary.

### 12. What still requires genuine team action?
Each student must review, rerun, understand and personally commit their own changes, demonstrate to the panel and defend the viva. Posting and human/hardware validation are pending; generated documents cannot substitute for them.
Code/evidence: `docs/RUBRIC_COMPLIANCE_MATRIX.md`. Follow-up: show its inputs, one logged output and one failure boundary.


## Expanded course viva questions

**Arnav — What makes the new course a climbing demonstration?** Two separate 8 cm rises require front and rear pair liftoff and re-contact, all feet beyond each measured lip, and the expected torso and foot height gain. The dog uses its supplied wheeled feet between transfers. A near-goal state alone is rejected. Rear landing placement was tuned using actual physics; failed development runs are retained.

**Arnav — Is the second obstacle a single 16 cm step?** No. The first surface is 8 cm above the floor; the second is another 8 cm higher. Its absolute height is 16 cm. The second transfer uses the first measured support level.

**Vihan — Why keep exact return coordinates as well as a grid?** A vertical face can land in the cell immediately before the physical edge. Using a cell boundary can bias a 5 cm grid lip estimate. Height-banded measured x coordinates reduce that bias for the course fixtures. Finite ray sampling still creates error; this is not an exact-edge guarantee under arbitrary sensing.

**Vihan — Does the dog follow a prewritten slalom?** The controller is given a final goal and constructs its route from measured rays, blocked unknown cells, inflated hazards and A*. The arena is designed to require alternating detours. Docking assumes broad x-aligned terraces, which is a stated limitation.

**Pratik — Can earlier experiments be pooled with the final 60 runs?** No. The original 50-pair study, new 12-pair avoidance extension and descriptive multi-seed climbing check use different course designs and source versions. Their raw data and hashes remain separate. The final capstone has its own 60 independent trials and source digest; earlier studies are not added to its sample size.

**Pratik — Why not advertise the geometry clearance number?** Some native distance queries returned inconsistent distance and witness segments. Those values are withheld. The primary harmful-contact audit uses actual solver contacts at every 2 ms step, and the limitation is documented.

**Pratik — How does real telemetry enter the business model?** `telemetry_business_bridge.py` reads actual accepted fraction and attempt duration. Effective weekly capacity is 40*p/(assumed overhead hours + measured seconds/3600). The overhead, 40-hour week and arrival demand remain explicit assumptions. This is a sensitivity scenario, not observed field capacity.

**Pratik — What happens when demand reaches capacity?** The M/M/c model has no finite steady-state wait when utilization is at least one. The dashboard displays instability instead of a misleading negative delay. Poisson arrivals, exponential service and independence remain unvalidated assumptions.
