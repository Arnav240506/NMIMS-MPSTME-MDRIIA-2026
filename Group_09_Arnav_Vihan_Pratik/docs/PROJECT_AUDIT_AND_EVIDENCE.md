> Historical implementation/evidence note. For the current independent 500 Hz study and final package, use CAPSTONE_VERIFICATION_REPORT.md and the current run guide. Do not pool these protocols.

# Project audit and evidence

**26 October 2026 course extension:** The new default is `course_climb`, with a denser industrial yard and two physical terrace transfers. See [OBSTACLE_COURSE_REPORT.md](OBSTACLE_COURSE_REPORT.md) and Word guide pages 19–22 for the current commands and verification. The original yard evidence documented below is preserved as its own experiment.

## Input and preservation

The corrected source archive NMIMS-MPSTME-MDRIIA-2026.zip is 280,034,525 bytes and has local ZIP records but no central directory/end record. A raw-DEFLATE recovery script verified CRC32 and sizes for 59 selected source/course entries, including all 17 original M20 STL meshes. The final hand-in includes the small recovery manifest and recovery script; original supplied data and recovered_originals remain outside the clean ZIP. The truncated final screen recording is not presented as evidence.

The master prompt specified Group 09 and a UGV scaffold; the later direct user correction selects the M20 robot dog, and the root README supplies the hybrid locomotion context. Prior box-vehicle data/figures/paper were excluded. No input-document success/performance claim is treated as a new result.

## Corrections to inherited claims

| Inherited claim/behavior | Verified correction |
|---|---|
| Box car used as project robot | Full M20 hierarchy, four articulated legs, 16 motors and 17 STL assets |
| M20 mass 23.3 kg | Summed original XML body mass is 34.525856 kg |
| Movement/climb prints unconditional success | Measured task predicates and nonzero failure exit |
| 9.9 cm climb measured from crouch | Settled standing reference, actual step contact/liftoff and all four feet above lip |
| Synthetic random CSV and sinusoidal telemetry | Every final row comes from actual mj_step execution |
| Full SLAM / ROSbot XL equivalence | Exact MuJoCo pose and ideal ray intersections; no pose estimation/ROS nodes |
| Complete map refresh at >50 Hz | Interleaved ray integration 50 Hz, full lattice 0.32 s, cost 10 Hz, planning 5 Hz |
| Nine-axis fused IMU | Exact simulation attitude/angular velocity feedback; no magnetometer fusion |
| Fixed 64% workload reduction | No participants, NASA-TLX, SUS or field workload result |
| Friction/braking assumed 600 N m | Actual motor saturation visible, leg 76.4 N m / hub 21.6 N m |
| Unknown terrain treated safe / forced forward fallback | Unknown blocked, no-route stop |
| Never tips / guaranteed roll under 3 deg | Actual maxima and all failures reported; short walking roll is above 3 deg |

## Executed evidence

Showcase seed 42: 59.368 simulated s, goal error 0.107750 m, true 0.08 m step verified, harmful contact steps 0, peak roll 1.376875 deg, peak pitch 11.647652 deg. Short leg walk: 12.0 s and 0.981384 m actual base path; each foot has measured lift and support.

Benchmark: 100 simulations, 50 pairs. Baseline 10/50 accepted; shared 47/50. Source fingerprints and full states are in every trial. Protocol was fixed before batch execution; development/probe runs are excluded from the benchmark and labeled separately. Selected development failures remain as evidence rather than being recoded as successes.

Each telemetry file contains simulated timestamps, x/y/z, roll/pitch/yaw, velocities, commands, ideal clearance, map coverage, a kinematic slip proxy, torque, decision reason, phase, four foot coordinates/contact flags/normal forces and contact counts. states.npz includes actual full qpos/qvel and 16 motor commands/targets at 50 Hz. Contacts are inspected every 2 ms; CSV is sampled every 20 ms. Ground/step/rubble wheel support is expected; any other robot-world contact is harmful. Self contacts are separately counted. Exact geometry under support contacts is used in evaluation only.

## Honest failures and boundaries

See analytics/benchmark/failure_cases.csv and docs/FAILURE_CASES.md. A safe stop at a blocked route is not mission completion. A wheel-only driver reaching an 8 cm curb without verified paired ascent is not accepted. Development rear-leg step contact was detected and corrected with a 3 cm higher rear transfer posture. A longer diagonal-pair gait prototype became unstable around 24 s; final walking evidence is a 12 s bounded demonstration, not sustained qualification. The final baseline is intentionally simple and cannot support conclusions about human performance.

No physical M20 was tested. STL supplier identity, hardware calibration and distribution rights require team verification before public redistribution. The supplied assets are retained locally for this authorized course package; no external publishing was performed. Axes are x-forward/y-left/z-up SI, matching the chosen ROS coordinate convention in intent only; no ROS transform tree is running. ISO 3691-4 is contextual course reading, not certification. Dynamic collapse, toxic gas, communication loss, sensor noise, battery and hardware actuator dynamics are outside this model.

A supplementary closest-hazard audit uses native mj_geomDistance on all robot collision primitives at recorded 10 Hz poses. Results are in analytics/benchmark/geometry_clearance.csv. These are sampled geometric minima against barrier/tank hazards, not continuous swept-volume guarantees; the original 2 ms harmful-contact audit remains authoritative.
