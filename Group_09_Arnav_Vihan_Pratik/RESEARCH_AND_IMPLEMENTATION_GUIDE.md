# Implementation and review guide

Read the root README first. The source of truth is the full recovered M20, not the superseded box vehicle. Original code is preserved outside the clean hand-in under recovered_originals, with CRC-verified archive recovery receipts.

| Module | Implemented mechanism | Student review specialty |
|---|---|---|
| M20/scene.py | 17 meshes, 34.525856 kg, 16 motors, seeded industrial yard | Arnav |
| M20/legged_control.py | Analytic IK/FK and short diagonal-pair foot walking | Arnav |
| M20/hybrid_control.py | Joint PD, wrench distribution, torque limits, fore/rear paired climb | Arnav |
| M20/m20_rosbot_mapping.py | Ideal environment-only rays, 5 cm dense-course measured grid, A*, strict unknown blocking | Vihan |
| M20/recon_controller.py | FIFO delay, local planner, alignment latch, safety stops | Vihan + Pratik |
| M20/simulation.py | Actual integration, per-contact audit, physical acceptance, CSV/NPZ evidence | All |
| analytics/analyze_capstone.py | Independent Welch inference, pooled Cohen d, CI and raw-log audit | Pratik |
| analytics/hazardous_recon_economics.py | Dimensionless illustrative sensitivity, invalid input checks | Pratik |

These are proposed review responsibilities; they do not claim who authored generated work.

The leg chain has 0.25 m thigh and shank links, lateral hip offset 0.158076 m, and wheel collision radius 0.093 m. FK/IK is checked against MuJoCo body positions on all four legs. Wheel velocity targets use the -y joint axis, with uL=v-w*b/2 and uR=v+w*b/2. A calibrated velocity servo commands bounded torques. The wheel-speed radius in the servo is 0.09 m; the slip proxy uses the collision radius 0.093 m, so the approximation is explicit.

For stance contacts, wrench allocation solves f=A^T(AA^T+lambda I)^(-1)w with positive normal force clipping and an approximate friction box. This is a regularized instantaneous least-squares allocation, not MPC and not a contact-constrained optimum. Desired joint torque combines PD, bias compensation and stance Jacobian terms, clipped to 76.4 N m for leg joints and 21.6 N m for hubs. No 600 N m parking friction is used.

The climb receives a lip and height detected from measured cells. It does not read geometry truth. The evaluator may use true step dimensions and actual contacts to reject false success. Ground-to-standing height gain is explicitly excluded from climb gain. Contact gates require each swinging pair to land; all four feet must finally be above the true lip, supported on the plateau and at the expected height. Startup, contact transfer and completion are separate phases.

Terrain cost uses clipped slope/roughness/step terms weighted 0.4/0.3/0.3. A separate obstacle proximity penalty can raise planning cost above 1. Traversability normalization itself remains bounded. Tall hazards are retained by geometry-based robot self-filtering. Unknown cells are blocked; reachable measured frontiers are considered if no measured route to goal exists. Inflation is a 0.70 m circumscribed footprint/margin. It does not prove swept-volume clearance under arbitrary slip.

The baseline uses the same articulated robot and standing servo with delayed reactive software steering. The shared arm can substitute local mapping/planning/climbing for low-level remote velocity. This compares full autonomy bundles; it does not isolate latency, A*, gait or human skill causally. Human workload remains an open study.

Before making real student commits, review your files, rerun tests, explain the equations and limitations, then commit under your own configured identity on your assigned feature branch. Keep the original main untouched. Do not manufacture four commits to satisfy a numerical checklist without real review/change history.
