> Historical implementation/evidence note. For the current independent 500 Hz study and final package, use CAPSTONE_VERIFICATION_REPORT.md and the current run guide. Do not pool these protocols.

# M20 rectification audit

The user's corrected requirement is the M20 quadruped, with the repository README
as design context. The previous box-UGV submission is superseded for this task;
its experiments, images and numbers are not evidence for M20.

The newly supplied 280,034,525-byte archive has local ZIP records but no central
directory/end record. Recovery verified the stored CRC and compressed/uncompressed
sizes of all 59 selected entries, including both M20 XML models and all 17 STL
assets. Full recovery receipts are in `provenance/recovered_manifest.json`.
Original recovered sources are preserved separately under `recovered_originals/`
and will not be mixed with new executable submission evidence.

The root README has been read in full. Its intended primary system is M20:
16 actuators (12 leg, 4 hub), ground wake-up, continuous occupancy/elevation
mapping, terrain classification, forelimb-pair step / torso advance /
hindlimb-pair step, active attitude feedback, A* detour, post-detour alignment,
and a four-panel RGB/depth/map/cost dashboard. The underlying 17 mesh assets
and leg hierarchy will be retained.

| Intake observation | Issue / verification action |
|---|---|
| Original pure-walk test advanced about -0.08 m in 12 s but printed unconditional success | Replace printed assertions with measured gait/goal/stability checks. |
| XML has 23 positions, 22 velocities, 16 actuators; summed mass 34.525856 kg | Correct README's 23.3 kg claim. Retain supplied inertias rather than silently changing mass. |
| Root README claims fixed balance/workload/performance numbers | Re-execute and report measured outcomes; no universal no-roll or human-workload claim. |
| Mapping hard-filters every z>0.35 m sample | Replace self filtering by geometry identity, preserving genuinely tall hazards. |
| Original planner permits unknown cells and forces forward on no route | Explicit unknown policy and safe no-route behavior. |
| Original navigation success depends on elevation and can stop partway through waypoints | Separate all-goal completion, detour clearance, climb contact/height and no-roll acceptance. |
| 600 N m assumed parking friction bypasses hub motor limits | Explicitly document/calibrate braking assumptions; keep motor saturation visible. |
| Detour returns to cruise without an alignment stage | Add a real docking/heading stage sized from the actual M20 footprint and sensed step. |
| README calls true-pose referenced mapping full SLAM | Label actual localization method; no loop closure or ROS runtime claim without implementation. |

Development-only gait experiments are separate from the final benchmark. A
support-shift single-foot prototype and a diagonal-pair prototype were tested
to diagnose locomotion. The README's fore/hind paired climb remains the intended
primary obstacle strategy. No untested "guaranteed" balance assertion is adopted.
