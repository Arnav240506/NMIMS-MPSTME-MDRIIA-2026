"""Regenerate evidence-linked teaching and submission documentation."""
from pathlib import Path
import json,shutil,html
HERE=Path(__file__).resolve().parent;GROUP=HERE.parent;ROOT=GROUP.parent;DOC=GROUP/'docs'

def write(path,text):path.write_text(text.strip()+'\n',encoding='utf-8')

def main():
    stats=json.loads((HERE/'benchmark/statistics.json').read_text())
    demo=json.loads((HERE/'demo_runs/m20_mission/summary.json').read_text())
    walk=json.loads((HERE/'demo_runs/m20_walk/summary.json').read_text())
    b=stats['policies']['baseline'];s=stats['policies']['shared'];t=stats['exploratory_paired_t']
    roster=json.loads((DOC/'TEAM_ROSTER.json').read_text())
    roster['platform']='Recovered M20 hybrid canine quadruped, 12 leg + 4 wheel motors, 17 original STL meshes'
    roster['implementation_assistance']='Substantial AI-assisted implementation, experiments, analysis and drafting. Students must review and personally defend their specialties.'
    roster['verified_student_commits']='PENDING: no student contribution history is available in the recovered source.'
    for member in roster['members']:
        member['github_handle']='[TO VERIFY]';member['verified_commit_hashes']=[];member['review_status']='PENDING_STUDENT_REVIEW'
    roster['members'][0]['role']='M20 quadruped dynamics, torque/contact validation and terrain review'
    roster['members'][0]['viva_focus']='Analytic leg IK, paired support, skid steering, torque limits and contact acceptance'
    roster['members'][1]['role']='Ideal LiDAR ray mapping, measured elevation/cost grid and A* review'
    roster['members'][1]['viva_focus']='True-pose referenced 2.5D mapping, unknown cells, inflation, A* and sensing limitations'
    roster['members'][2]['viva_focus']='Delayed software-driver baseline, paired inference, intervention proxies and dimensionless economics; no measured human workload'
    refs=json.loads((DOC/'bibliography/verification.json').read_text());roster['foundational_papers']=refs
    roster['project_showcase'].update(submission_status='VIDEO_BUILT_POSTING_PENDING',linkedin_url='PENDING_SUBMISSION')
    write(DOC/'TEAM_ROSTER.json',json.dumps(roster,indent=2))
    readme=fr'''# MDRIIA Group 09 — M20 robot dog

This corrected project uses the supplied **M20 hybrid legged-wheeled canine quadruped**. It retains all 17 STL meshes and the original mass/inertia hierarchy: four articulated legs, 12 leg motors and four foot-wheel motors. The earlier box vehicle is superseded and its results are not used here.

**Course:** MDRIIA 702CO0E012, NMIMS MPSTME, B.Tech CSBS, AY 2026–2027.

| Member | Roll | SAP | Specialty to review and defend |
|---|---|---|---|
| Arnav Saurabh Surve | E064 | 70362400067 | M20 dynamics, paired-leg control, contact safety |
| Vihan Shripad Joshi | E070 | 70362400086 | LiDAR grid, traversability and A* |
| Pratik Mangesh Gaikwad | E073 | 70362300032 | Latency, paired analysis and dimensionless economics |

The authorized research question remains: How can an autonomous ground vehicle utilizing simulated LiDAR rangefinders and traversability cost-mapping in MuJoCo navigate unknown unstructured hazardous terrain while reducing teleoperation cognitive workload and communication latency? The experiment addresses a software-driver comparison; the human workload part remains unmeasured.

## Run from this repository root

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Setup -Mode mission
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Mode walk
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Mode mission -Live
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe Group_09_Arnav_Vihan_Pratik\analytics\run_benchmark.py --smoke
```

`-Live` executes the actual physics in the native MuJoCo window. `-Record` runs physics, saves telemetry and renders recorded states into MP4; `-Viewer` displays that recorded-state replay. GPU speed changes wall-clock playback/compute time, not the 2 ms physical timestep. Escape closes replay windows. Close the native viewer to finish.

## Implemented behavior

Grounded crouch-to-stand; wheel cruise; continuous ideal LiDAR intersections; 3 cm elevation/cost mapping; A* detour around a 25 cm barrier; latched post-detour yaw alignment; front-pair swing, torso advance and rear-pair swing over a measured low step; pitch/roll feedback and bounded joint torques; plateau clearance and final goal acceptance. A separate short diagonal-pair gait demonstrates leg walking with braked feet. No floating-base position is overwritten after initialization.

The scenery is an industrial inspection yard: warehouse walls, a storage tank, a concrete platform, a barrier and seeded low rubble. The platform is 8 cm for showcase seed 42 and 5.5–8.5 cm in randomized cases. The barrier/step gap is increased from the supplied layout to accommodate the actual M20 support shift. Decorative cracks/warehouse walls are visual only; tank, barrier, step and rubble have collisions.

## Actual measurements

- Showcase mission seed 42: **{demo['simulated_s']:.3f} simulated seconds**, goal error {demo['goal_error_m']:.3f} m, all four feet verified on the 8 cm step, **zero harmful contact steps**, peak absolute roll {demo['max_abs_roll_deg']:.2f} deg and pitch {demo['max_abs_pitch_deg']:.2f} deg.
- Short walking demo: {walk['simulated_s']:.1f} s, final x {walk['terrain']['goal'][0]-walk['goal_error_m']:.2f} m approximately; each foot lifts and returns to contact, no harmful contacts. This is not evidence of indefinite gait stability.
- Benchmark: **{stats['N_simulations']} actual simulations / {stats['N_pairs']} matched environments**. Accepted: baseline {b['accepted']}/50, shared {s['accepted']}/50. Exact paired McNemar p={stats['exact_McNemar_p']:.8g}. All failures remain in `analytics/benchmark/failure_cases.csv`.

## Evidence and limits

See `Group_09_Arnav_Vihan_Pratik/docs/SETUP_AND_RUN.md`, `PROJECT_AUDIT_AND_EVIDENCE.md`, `FINAL_DELIVERY_REPORT.md`, `VIVA_QA_BY_STUDENT.md`, `paper/Group09_HazardousTerrain_IEEE.pdf`, and `analytics/benchmark/RESULTS.md`. Each trial includes configuration, source hash, actual 50 Hz telemetry, qpos/qvel/motor states, actual ray map and contact categories.

The mapping uses exact simulated pose and ideal rays. It does not estimate pose, close SLAM loops, run ROSbot/ROS nodes, or fuse a real 9-axis IMU. RGB/depth panels visualize simulated cameras and do not drive mapping. A 50 Hz interleaved ray stream takes 0.32 s for one full lattice pass; cost updates are 10 Hz and A* requests 5 Hz. Body attitudes/velocities are exact MuJoCo state feedback. This is simulation-only and provides no ISO certification, deployment safety, field reliability or human workload result.

Substantial AI assistance is disclosed. No student commits, approvals or posting have been fabricated. Git histories, personal reviews, panel demonstration and viva remain genuine student actions.
'''
    write(ROOT/'README.md',readme)
    write(GROUP/'README.md',readme.replace('from this repository root','from the parent repository root (one level above this Group folder)'))
    write(DOC/'SETUP_AND_RUN.md',r'''# Setup and reproduction

Use 64-bit CPython 3.12 on Windows. The tested environment and exact dependency versions are pinned in the root requirements.txt. Install from the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pytest -q
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Mode walk
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Mode mission -Record
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Mode mission -Live
.\.venv\Scripts\python.exe Group_09_Arnav_Vihan_Pratik\analytics\run_benchmark.py --smoke
.\.venv\Scripts\python.exe Group_09_Arnav_Vihan_Pratik\analytics\run_benchmark.py --workers 4
.\.venv\Scripts\python.exe Group_09_Arnav_Vihan_Pratik\analytics\analyze_benchmark.py
.\.venv\Scripts\python.exe Group_09_Arnav_Vihan_Pratik\analytics\hazardous_recon_economics.py
.\.venv\Scripts\python.exe Group_09_Arnav_Vihan_Pratik\analytics\generate_paper_figures.py
.\.venv\Scripts\python.exe Group_09_Arnav_Vihan_Pratik\analytics\verify_evidence.py
```

Do not overwrite supplied evidence when experimenting: use simulation.py --out with a new folder. The benchmark script intentionally recreates its named trials; use --out for an independent rerun. Four workers need several GB of RAM; use --workers 1 on smaller computers. A full run can take tens of minutes depending on CPU and rendering competition. Rendering is separate from physics and may take longer.

Individual commands:

```powershell
.\.venv\Scripts\python.exe M20\simulation.py --mode climb --duration 45 --out Group_09_Arnav_Vihan_Pratik\analytics\local_runs\curb
.\.venv\Scripts\python.exe M20\simulation.py --mode blocked --duration 22 --out Group_09_Arnav_Vihan_Pratik\analytics\local_runs\blocked
.\.venv\Scripts\python.exe M20\replay.py Group_09_Arnav_Vihan_Pratik\analytics\demo_runs\m20_mission --show --no-record
```

Exit 0 means the declared task passed. Exit 2 means actual acceptance failed, including blocked/tilted fixtures. A protected stop is a successful safety response but does not count as a completed reconnaissance mission. The walking entry defaults to 12 s; do not interpret this as sustained gait qualification. The slope fixture is exploratory and outside the main benchmark.

MuJoCo front RGB/depth and a 4-panel dashboard are supported with OpenGL. The native viewer shows live integration; replay is explicitly labeled captured physics. Close native windows normally. In headless environments, run --headless and inspect logged state; graphical output is not required to compute the benchmark.

The generated course model models/hazardous_terrain_ugv.xml is a legacy filename that now contains the full M20. Its meshdir is relative to ../../M20/meshes. Do not move the Group folder away from its M20 sibling. Regenerate both scenes with python M20/scene.py.

Compile paper source with Tectonic or a TeX distribution supporting IEEEtran. From docs/paper: tectonic Group09_HazardousTerrain_IEEE.tex. The supplied PDF has already been compiled and visually checked. Citation verification receipts are saved; re-querying Crossref requires networking and may be rate-limited.
''')
    write(GROUP/'RESEARCH_AND_IMPLEMENTATION_GUIDE.md',r'''# Implementation and review guide

Read the root README first. The source of truth is the full recovered M20, not the superseded box vehicle. Original code is preserved outside the clean hand-in under recovered_originals, with CRC-verified archive recovery receipts.

| Module | Implemented mechanism | Student review specialty |
|---|---|---|
| M20/scene.py | 17 meshes, 34.525856 kg, 16 motors, seeded industrial yard | Arnav |
| M20/legged_control.py | Analytic IK/FK and short diagonal-pair foot walking | Arnav |
| M20/hybrid_control.py | Joint PD, wrench distribution, torque limits, fore/rear paired climb | Arnav |
| M20/m20_rosbot_mapping.py | Ideal environment-only rays, 3 cm measured grid, A*, strict unknown blocking | Vihan |
| M20/recon_controller.py | FIFO delay, local planner, alignment latch, safety stops | Vihan + Pratik |
| M20/simulation.py | Actual integration, per-contact audit, physical acceptance, CSV/NPZ evidence | All |
| analytics/analyze_benchmark.py | Exact paired binary test, bootstrap and exploratory continuous analysis | Pratik |
| analytics/hazardous_recon_economics.py | Dimensionless illustrative sensitivity, invalid input checks | Pratik |

These are proposed review responsibilities; they do not claim who authored generated work.

The leg chain has 0.25 m thigh and shank links, lateral hip offset 0.158076 m, and wheel collision radius 0.093 m. FK/IK is checked against MuJoCo body positions on all four legs. Wheel velocity targets use the -y joint axis, with uL=v-w*b/2 and uR=v+w*b/2. A calibrated velocity servo commands bounded torques. The wheel-speed radius in the servo is 0.09 m; the slip proxy uses the collision radius 0.093 m, so the approximation is explicit.

For stance contacts, wrench allocation solves f=A^T(AA^T+lambda I)^(-1)w with positive normal force clipping and an approximate friction box. This is a regularized instantaneous least-squares allocation, not MPC and not a contact-constrained optimum. Desired joint torque combines PD, bias compensation and stance Jacobian terms, clipped to 76.4 N m for leg joints and 21.6 N m for hubs. No 600 N m parking friction is used.

The climb receives a lip and height detected from measured cells. It does not read geometry truth. The evaluator may use true step dimensions and actual contacts to reject false success. Ground-to-standing height gain is explicitly excluded from climb gain. Contact gates require each swinging pair to land; all four feet must finally be above the true lip, supported on the plateau and at the expected height. Startup, contact transfer and completion are separate phases.

Terrain cost uses clipped slope/roughness/step terms weighted 0.4/0.3/0.3. A separate obstacle proximity penalty can raise planning cost above 1. Traversability normalization itself remains bounded. Tall hazards are retained by geometry-based robot self-filtering. Unknown cells are blocked; reachable measured frontiers are considered if no measured route to goal exists. Inflation is a 0.70 m circumscribed footprint/margin. It does not prove swept-volume clearance under arbitrary slip.

The baseline uses the same articulated robot and standing servo with delayed reactive software steering. The shared arm can substitute local mapping/planning/climbing for low-level remote velocity. This compares full autonomy bundles; it does not isolate latency, A*, gait or human skill causally. Human workload remains an open study.

Before making real student commits, review your files, rerun tests, explain the equations and limitations, then commit under your own configured identity on your assigned feature branch. Keep the original main untouched. Do not manufacture four commits to satisfy a numerical checklist without real review/change history.
''')
    write(DOC/'PROJECT_AUDIT_AND_EVIDENCE.md',f'''# Project audit and evidence

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

Showcase seed 42: {demo['simulated_s']:.3f} simulated s, goal error {demo['goal_error_m']:.6f} m, true 0.08 m step verified, harmful contact steps {demo['harmful_contact_steps']}, peak roll {demo['max_abs_roll_deg']:.6f} deg, peak pitch {demo['max_abs_pitch_deg']:.6f} deg. Short leg walk: {walk['simulated_s']:.1f} s and {walk['path_length_m']:.6f} m actual base path; each foot has measured lift and support.

Benchmark: {stats['N_simulations']} simulations, {stats['N_pairs']} pairs. Baseline {b['accepted']}/50 accepted; shared {s['accepted']}/50. Source fingerprints and full states are in every trial. Protocol was fixed before batch execution; development/probe runs are excluded from the benchmark and labeled separately. Selected development failures remain as evidence rather than being recoded as successes.

Each telemetry file contains simulated timestamps, x/y/z, roll/pitch/yaw, velocities, commands, ideal clearance, map coverage, a kinematic slip proxy, torque, decision reason, phase, four foot coordinates/contact flags/normal forces and contact counts. states.npz includes actual full qpos/qvel and 16 motor commands/targets at 50 Hz. Contacts are inspected every 2 ms; CSV is sampled every 20 ms. Ground/step/rubble wheel support is expected; any other robot-world contact is harmful. Self contacts are separately counted. Exact geometry under support contacts is used in evaluation only.

## Honest failures and boundaries

See analytics/benchmark/failure_cases.csv and docs/FAILURE_CASES.md. A safe stop at a blocked route is not mission completion. A wheel-only driver reaching an 8 cm curb without verified paired ascent is not accepted. Development rear-leg step contact was detected and corrected with a 3 cm higher rear transfer posture. A longer diagonal-pair gait prototype became unstable around 24 s; final walking evidence is a 12 s bounded demonstration, not sustained qualification. The final baseline is intentionally simple and cannot support conclusions about human performance.

No physical M20 was tested. STL supplier identity, hardware calibration and distribution rights require team verification before public redistribution. The supplied assets are retained locally for this authorized course package; no external publishing was performed. Axes are x-forward/y-left/z-up SI, matching the chosen ROS coordinate convention in intent only; no ROS transform tree is running. ISO 3691-4 is contextual course reading, not certification. Dynamic collapse, toxic gas, communication loss, sensor noise, battery and hardware actuator dynamics are outside this model.
''')
    write(DOC/'DEMO_SCRIPT_AND_CHECKLIST.md',r'''# Five-minute demonstration

Run from the repository root. Install and test before the panel. Keep the supplied MP4 and PDF available if graphics fails. Each member must explain their own reviewed contribution; this script is preparation, not proof of participation.

| Time | Speaker | Rehearsable action |
|---|---|---|
| 0:00–0:35 | Arnav | Show the M20 image: four articulated legs, 12 leg plus 4 wheel motors, 34.525856 kg from XML. State simulation-only scope. |
| 0:35–1:10 | Arnav | Run the 12 s walking command below; show actual foot-height/contact traces and torque limits. Explain bounded demonstration. |
| 1:10–2:30 | Vihan | Start native live mission. Explain actual ray intersections, true-pose 3 cm grid, 0.70 m inflation, blocked unknown cells and A*. Watch the barrier detour and docking. |
| 2:30–3:20 | Arnav + Vihan | Show fore-pair step, torso transfer and rear-pair step. Explain why standing up alone is not a climb. Show 4-panel RGB/depth/map/cost recording. |
| 3:20–4:20 | Pratik | Open benchmark/RESULTS.md. Describe 50 paired seeds, software baseline, exact McNemar and exploratory d_z. Run economics script. Say the assumptions are illustrative and no humans were measured. |
| 4:20–5:00 | All | Open the four-page paper, show one retained failure, list student review/Git/hardware/human-study work still pending. |

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Mode walk
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Mode mission -Live
.\.venv\Scripts\python.exe M20\replay.py Group_09_Arnav_Vihan_Pratik\analytics\demo_runs\m20_mission --show --no-record
.\.venv\Scripts\python.exe Group_09_Arnav_Vihan_Pratik\analytics\hazardous_recon_economics.py
```

The live window executes actual mj_step physics. Tab and Shift+Tab hide the native left/right panels; use mouse zoom/rotate as needed. Closing the window stops it. The recorded replay is explicitly labeled and separate from live evidence. The headless mission command saves objective acceptance and can be run in a second terminal. Rendering can slow wall time; do not claim 50 Hz wall-clock sensor throughput on an overloaded laptop.

Before demo: check dependencies, run pytest, verify ZIP manifest, confirm seed 42 mission summary accepted=true and harmful_contact_steps=0, test native OpenGL, open MP4 and four-page PDF, and rehearse the division of speaking. If native graphics fails, show logged headless execution and label the saved video as a replay. Do not replace a failed live execution with a claim that it passed.
''')
    write(DOC/'LINKEDIN_SHOWCASE_PLAN.md',r'''# Authentic showcase and publication plan

The delivered M20_showcase.mp4 combines actual recorded MuJoCo walking and mission frames with a short result card, lasting 60–90 s. No image generation is used for evidence. robot_3d.mp4 and hud.mp4 preserve native-rendered views of recorded physical qpos/qvel. The HUD map is deterministically recomputed from the recorded poses; its yellow path is the final planned-path overlay, not a claim that each historical path was identical.

Storyboard: 0–12 s short diagonal-pair walking; next ~59 s mission wakeup, barrier detour, docking, front-pair step, torso advance, rear-pair step and plateau arrival; final card states actual seed-42 result and simulation-only limitations. The continuous videos retain natural simulated timing at 10 frames/s; showcase clips/cuts are documented by create_showcase.py. Captions should identify the original supplied M20 model and AI-assisted implementation.

Poster: docs/figures/video_poster.png, derived from a real MuJoCo frame. Four-panel evidence: analytics/demo_runs/m20_mission/hud.mp4. Review for correct robot geometry, visible moving legs, no invented graph lines, accurate labels and readable captions before presenting.

Draft caption (review before posting):

“Our MDRIIA Group 09 simulation studies M20, a hybrid quadruped with articulated legs and wheeled feet, in an industrial inspection yard. The pipeline combines measured ray-grid mapping, A* detours, paired-leg step transfer and torque-limited control. We compare 50 matched seeded environments against a delayed software-driver baseline and retain failed trials. This is simulation evidence, not a field safety or human workload claim. Substantial AI assistance was used; each member is reviewing and defending their specialty.”

No post was published. linkedin_url remains PENDING_SUBMISSION. Team members must verify model redistribution permissions, review the actual results, provide their own contribution statements and publish through their own accounts if required. Do not invent a link, credentials, endorsements or student Git activity.
''')
    write(DOC/'RUBRIC_COMPLIANCE_MATRIX.md',r'''# Rubric evidence matrix — 100 marks

Statuses describe evidence readiness, not awarded marks. The faculty alone awards marks. A panel demonstration or oral answer cannot be completed by generated documentation.

| Milestone item | Marks | Evidence | Status / remaining action |
|---|---:|---|---|
| M1 Git setup/feature branches/PR | 3 | Proposed branches in TEAM_ROSTER; isolated codex feature branch | PENDING genuine student clones, branches and PRs |
| M1 roster/toolchain | 3 | TEAM_ROSTER.json, requirements.txt, tests/environment | PARTIAL; identities preserved, GitHub handles/student review pending |
| M1 interrogative/hypothesis | 4 | README, paper methods, benchmark design/statistics | IMPLEMENTED; human workload question remains open |
| M2 physical architecture | 8 | M20.xml + 17 STL; generated full M20 yard; anatomy tests | IMPLEMENTED |
| M2 core control | 7 | Physical walking and paired-climb logged runs; torque-limited executive | IMPLEMENTED within documented tested limits |
| M2 telemetry | 5 | Every benchmark telemetry.csv and states.npz | IMPLEMENTED, actual physics |
| M3 experimental execution | 8 | 100 simulations / 50 matched pairs; design and all failures retained | IMPLEMENTED |
| M3 statistics | 6 | analyze_benchmark.py, statistics.json, RESULTS.md | IMPLEMENTED; exact primary paired test and exploratory t/d_z, no forced target |
| M3 dimensionless economics / psychometrics | 6 | economics script, validation tests, sensitivity JSON | PARTIAL: economics implemented; human scales not measured |
| M4 four-page IEEE paper | 15 | Editable TeX, compiled PDF, 3 figures, 2 tables, DOI receipts | IMPLEMENTED subject to team/faculty review |
| M4 live panel demonstration | 15 | Native viewer, recorded MP4, 5-minute script and headless objective result | PREPARED and locally exercised; actual expert-panel demonstration PENDING |
| M4 individual viva | 15 | 12 Q&As per student + quick sheets | PREPARED; actual individual defense PENDING |
| M4 real commit trajectory | 5 | No spoofed or fabricated history | PENDING genuine student review/commits; four real commits per member as course requires |
| TOTAL | 100 | Technical package complete with explicit boundaries | No promised grade |

Model meshes and code supplied by the user have been preserved with provenance. There is no claim of original mechanical CAD authorship. Personal GitHub handles, post URLs, expert endorsements, approvals and human-study data remain blank/pending until supplied by the responsible people. The zero-currency rule is respected in generated economics and teaching materials. SI coordinate conventions are implemented; ISO/ROS certification/runtime is not claimed.
''')
    # Compact 36-answer defense set, each tied to executable modules.
    qa={
    'Arnav Saurabh Surve (E064)':[
      ('Why is this an M20 dog rather than a car?','It has four multi-joint legs from the supplied M20 chain, 12 leg motors and four wheeled feet. We demonstrate actual foot lift and paired transfers. Wheels are part of this hybrid model.','scene.build_scene'),
      ('How many degrees of freedom are present?','There are 16 actuated joints plus a free floating base: nq=23 because the base quaternion uses four numbers; nv=22 because base rotation has three velocities.','tests.test_authentic_anatomy'),
      ('What is the actual mass?','Summing the supplied XML inertias gives 34.525856 kg. We preserved those inertias and corrected the old 23.3 kg text.','scene.build_scene'),
      ('How does inverse kinematics work?','The two 0.25 m links use cos(knee)=(x²+z_leg²-l1²-l2²)/(2*l1*l2). The lateral offset first determines hip roll; front and rear use different knee branches. FK is checked against MuJoCo.','legged_control.inverse_leg'),
      ('What torques are applied?','PD joint error, bias compensation and stance-Jacobian terms are combined, then leg torques are clipped to ±76.4 N m and hubs to ±21.6 N m. Torque is sent through motors, not the floating base.','hybrid_control.M20Actuation.apply'),
      ('Is the balance controller MPC?','No. It allocates an instantaneous desired body wrench using regularized least squares and clips contact forces. It has no prediction horizon or constrained MPC solve.','hybrid_control.M20Actuation.apply'),
      ('Why climb with front and rear pairs?','This follows the README strategy: lower and shift the CoM over the support pair, lift the other pair with floating wheels, plant it, move the torso and then lift the rear pair. Two-foot support remains a demanding balance condition.','hybrid_control.PairClimbController'),
      ('How do you prove an actual climb?','Measure from settled standing, require actual front/rear liftoff and re-support, then all four feet beyond the true lip, at plateau height, with support contacts. Merely standing from crouch cannot pass.','simulation.run_trial'),
      ('What was the contact bug?','A rear upper-leg collision touched the step during rear transfer. The evaluator rejected it; raising the rear transfer body reference by 3 cm removed it in the verified showcase.','simulation.contact_audit'),
      ('How is slip measured?','The logged proxy compares hub speed times wheel radius against body longitudinal speed, normalized by at least 0.10 m/s. It is a kinematic discrepancy, especially imperfect during swings and turns, not calibrated physical slip.','simulation.run_trial'),
      ('How does skid steering turn?','uL=v-w*b/2, uR=v+w*b/2, with effective track 0.55 m. M20 wheel axes are -y, so forward target joint rates are negative. Feedback compensates measured yaw-rate error and pivot drift.','recon_controller.ReconExecutive.physics_tick'),
      ('Can the dog walk indefinitely?','The supplied evidence verifies a 12-second diagonal-pair demonstration. A longer development run destabilized around 24 seconds. More robust gait optimization and hardware tests remain open.','legged_control.CrawlController')],
    'Vihan Shripad Joshi (E070)':[
      ('Where do map heights come from?','From native MuJoCo multi-ray intersections with actual environment geometry. The controller does not read terrain heights directly from the scene metadata.','m20_rosbot_mapping.raycast'),
      ('What is 2.5D mapping?','Each x-y cell stores measured elevation statistics rather than a full volume. Overhangs and multi-level terrain are poorly represented, so it is not full 3D reconstruction.','m20_rosbot_mapping.M20Map'),
      ('Is this SLAM?','No. Pose is exactly known from MuJoCo. We accumulate a global grid using that pose; we do not estimate pose, optimize a pose graph or close loops.','m20_rosbot_mapping.M20Map.scan'),
      ('What is the real map update rate?','Rays are integrated at 50 Hz in 16 interleaved groups. A full lattice takes 0.32 s of simulated time. Cost updates are 10 Hz and planning requests are 5 Hz; no wall-clock throughput claim is made.','m20_rosbot_mapping.M20Map.scan'),
      ('How do cells aggregate samples?','The mapper stores count, sum, squared sum, mean and peak. Empty cells remain unknown. Peaks help detect hazards; mean and local variation support traversability costs.','m20_rosbot_mapping.M20Map.integrate'),
      ('How is cost calculated?','c=0.4 clip(slope/30deg)+0.3 clip(roughness/0.04m)+0.3 clip(step/0.14m). The later obstacle proximity penalty is separate and can make the A* planning cost exceed one.','m20_rosbot_mapping.normalized_cost'),
      ('How is the robot removed from its own scan?','Geometry groups exclude robot collisions/visual meshes while retaining environmental obstacles. We no longer discard every height above 0.35 m, which would erase genuine tall hazards.','m20_rosbot_mapping.ENVIRONMENT_GROUPS'),
      ('How does A* choose a route?','Eight-neighbor edges cost distance times a risk weight. The Euclidean heuristic is a lower bound because all edge weights are at least distance. Unknown/inflated cells and diagonal corner cuts are blocked.','m20_rosbot_mapping.astar'),
      ('Why inflate obstacles by 0.70 m?','The planned center must leave room for the robot footprint and extra tracking/slip margin. This conservative circular approximation does not prove exact swept-body clearance for every posture.','m20_rosbot_mapping.M20Map.update_cost'),
      ('What happens if no route exists?','Try reachable measured frontiers; otherwise command zero rather than guessing forward through unknown terrain. The blocked fixture is intentionally not counted as mission completion.','m20_rosbot_mapping.plan_route'),
      ('How is the curb located?','Broad connected measured cells above 3.5 cm and below 14 cm indicate a low terrace. Its leading cell supplies lip position and median measured peak supplies height; this is a fixture-specific detector.','m20_rosbot_mapping.M20Map.detect_step'),
      ('Do RGB/depth cameras control the robot?','Their rendered panels are for observation. Mapping uses ideal LiDAR rays; cameras are not fused into control. Real perception would need noise, calibration, motion compensation and localization tests.','replay.replay')],
    'Pratik Mangesh Gaikwad (E073)':[
      ('What is the actual baseline?','A deterministic delayed reactive software driver on the same M20 standing servo. It steers toward the goal and reacts to forward range; it has no A* map or paired climb. It is not a human operator.','recon_controller.reactive_driver'),
      ('How is latency simulated?','Commands are timestamped with release time t+delay and queued FIFO. All commands due by the current simulation time are released in order. Delays are 0.05, 0.35, 0.8 or 1.2 s in the benchmark.','recon_controller.LatencyQueue'),
      ('Does shared autonomy experience the same delay?','The remote intent channel is delayed, but the local shared planner retains control authority. That is the intended architectural advantage. The study bundles planning and climbing, so it cannot isolate latency alone.','recon_controller.ReconExecutive.navigation_tick'),
      ('How many experiments were actually run?','There are 50 matched environments and two policies, totaling 100 actual physics simulations. Terrain, friction, height and delay are seeded; failed trials remain in the CSV.','analytics.run_benchmark.design'),
      ('Why use matched pairs?','Both policies receive the same seed and scenario, reducing environmental variation in policy differences. The two rows in a pair are dependent and should not be treated as unrelated samples.','analytics.analyze_benchmark.analyze'),
      ('What is the primary hypothesis test?','Acceptance is binary. Exact McNemar uses only discordant pairs, with the shared-only and baseline-only counts tested against equal probability. Its p-value is computed from a two-sided binomial test.','analytics.analyze_benchmark.analyze'),
      ('What does d_z mean?','For continuous paired goal-error differences, d_z=mean(difference)/SD(difference). It is not pooled Cohen d. The t-test is exploratory when paired differences are non-normal.','analytics.analyze_benchmark.analyze'),
      ('What does the 95% interval describe?','The bootstrap resamples matched differences, not individual unpaired rows. It estimates sampling variation under this chosen scenario mixture; it does not certify all hazardous environments.','analytics.analyze_benchmark.bootstrap_mean_ci'),
      ('Did operator workload decrease by 64%?','No human workload was measured. Intervention counts are software events, not NASA-TLX. A participant study would need a protocol, consent, task counterbalancing and valid scales.','docs/PROJECT_AUDIT_AND_EVIDENCE.md'),
      ('What is dimensionless cost parity?','kappa=robot operating parity/reclaimed-value parity. Inputs are illustrative normalized assumptions; no real operational savings are inferred from these simulations.','analytics.hazardous_recon_economics.economics'),
      ('How are payback and FTE calculated?','Payback months=12*capital parity/(1-kappa) only when kappa<1. Reclaimed FTE=illustrative reclaimed annual hours/2080. Nonpositive denominators and nonfinite inputs are rejected.','analytics.hazardous_recon_economics.economics'),
      ('What still requires genuine team action?','Each student must review, rerun, understand and personally commit their own changes, demonstrate to the panel and defend the viva. Posting and human/hardware validation are pending; generated documents cannot substitute for them.','docs/RUBRIC_COMPLIANCE_MATRIX.md')]}
    lines=['# Individual viva preparation','', 'Answers describe verified implementation, not evidence of who authored it. Each student should explain the equation, show the code and state its limitation.','']
    for person,questions in qa.items():
        lines+=['## '+person,'']
        for i,(question,answer,code) in enumerate(questions,1):lines +=[f'### {i}. {question}',answer,f'Code/evidence: `{code}`. Follow-up: show its inputs, one logged output and one failure boundary.','']
    write(DOC/'VIVA_QA_BY_STUDENT.md','\n'.join(lines))
    for person,questions in qa.items():
        roll=person.split('(')[1].strip(')')
        sheet=['# '+person+' — quick revision','', 'Explain in your own words; do not claim unverified authorship.','']
        for q,a,c in questions:sheet+=['- **'+q+'** '+a.split('. ')[0]+'.']
        write(DOC/f'QUICK_REVISION_{roll}.md','\n'.join(sheet))
        items=''.join('<li><strong>'+html.escape(q)+'</strong> '+html.escape(a.split('. ')[0])+'.</li>' for q,a,c in questions)
        card='<!doctype html><html><head><meta charset="utf-8"><title>'+person+' quick revision</title><style>@page{size:A4;margin:14mm}body{font:10.5pt/1.25 Arial;color:#152c39;max-width:180mm;margin:auto}h1{font-size:18pt}li{margin:0 0 7pt}footer{font-size:9pt;border-top:1px solid #597786;padding-top:7pt}</style></head><body><h1>'+person+'</h1><p>M20 quadruped | one-page review card | simulation evidence only</p><ol>'+items+'</ol><footer>Explain the code, one measured result and its limitation. Substantial AI assistance; personal review and individual defense are required.</footer></body></html>'
        write(DOC/f'QUICK_REVISION_{roll}.html',card)
    write(DOC/'DEMO_AND_VIVA_CRIB_SHEET.md',r'''# Current demo and viva entry points

Use DEMO_SCRIPT_AND_CHECKLIST.md for the five-minute faculty flow, VIVA_QA_BY_STUDENT.md for 36 questions, and QUICK_REVISION_E064/E070/E073.md for specialty sheets. The platform is the recovered articulated M20 quadruped. The older car and workload assertions are superseded. Authoritative measurements are in analytics/benchmark/statistics.json and demo_runs/m20_mission/summary.json.
''')
    lit=['# Verified literature and scope','', 'DOI titles/authors were checked against publisher-deposited Crossref metadata. The raw responses and metadata receipt are in bibliography/. Some existing source records were reused from the earlier citation audit; new quadruped sources were fetched for this correction. The DOI resolver and author pages were also checked for the three legged-robot papers. This is bibliographic verification, not a claim to have reproduced those systems.','', '| DOI | Actual title | Relevance / boundary |','|---|---|---|']
    for r in refs:
        doi=r['doi'];rel='Background only; not an implementation claim.'
        if '8594448' in doi:rel='Quadruped force-control background. Our instantaneous least-squares allocation is not this paper’s MPC.'
        if 'abk2822' in doi:rel='Perceptive locomotion and perception failure motivation. No learned attention encoder or real-world reproduction here.'
        if 'adi9641' in doi:rel='Direct wheeled-legged navigation context. Our hand-designed FSM is not the paper’s learned hierarchical policy.'
        if '2849506' in doi:rel='Elevation mapping with uncertain localization. Our mapper uses exact pose and is simpler/nonprobabilistic.'
        if '905819' in doi:rel='Teleoperation interface/workload motivation; no participants measured here.'
        if 'rob.21856' in doi:rel='Original source title was incorrect. This DOI is UAV routing with mobile recharging stations, not emergency ground reconnaissance; excluded from core paper.'
        lit.append(f'| [{doi}](https://doi.org/{doi}) | {r["title"]} | {rel} |')
    lit+=['','Research gap addressed locally: reproducible M20 mesh-preserving ray-map-to-paired-climb integration, explicit physical acceptance and retained failures. This is an educational integration study, not a state-of-the-art locomotion contribution.']
    write(DOC/'LITERATURE_REVIEW_AND_FOUNDATIONAL_PAPERS.md','\n'.join(lit))
    write(DOC/'RESEARCH_PAPER_MANUSCRIPT_BLUEPRINT.md',r'''# Final manuscript map

The completed editable manuscript is paper/Group09_HazardousTerrain_IEEE.tex; its compiled PDF is the final paper. It contains the preserved Group 09 identities, M20 anatomy/IK/torque control, true-pose ideal-ray mapping, paired study, computed inference, illustrative dimensionless economics, explicit failed trials and limitations. Figures are generated from actual M20 telemetry/results by analytics/generate_paper_figures.py; bibliography verification is in bibliography/verification.json.

Unsupported inherited workload percentages, synthetic random benchmark distributions, box-vehicle results, guaranteed balance and claims of full ROS/SLAM deployment have been removed. The final paper is four pages, two columns, with at least three figures, two tables and at least five genuine DOI references. The report records compilation and visual QA separately from scientific validation.
''')
    print('Documentation and 36 viva answers generated from current results.')

if __name__=='__main__':
    from build_capstone_support import main as current_main
    current_main()
