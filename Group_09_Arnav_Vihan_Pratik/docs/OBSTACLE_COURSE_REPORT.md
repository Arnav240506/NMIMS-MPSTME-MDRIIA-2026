> Historical implementation/evidence note. For the current independent 500 Hz study and final package, use CAPSTONE_VERIFICATION_REPORT.md and the current run guide. Do not pool these protocols.

# Expanded M20 obstacle and climbing course verification

Verified on 26 October 2026. This extension uses the supplied M20 hybrid quadruped, preserving all 17 meshes, 12 articulated leg motors and four wheeled-foot motors. The new default demonstration is `course_climb`. It uses wheeled-foot cruise between articulated paired-leg transfers; it is not sustained braked-foot walking along the entire course.

## Scene and behavior

The industrial training yard contains three alternating 60 cm-high barricades, drums, crates, tanks, pipe racks and two physical boundary rails: **20 hazard/boundary geometries** in the combined course. Two additional rigid support terraces each add **8 cm** of height, reaching **16 cm total elevation**. Decorative warehouse panels, stripes, bands, beacons and windows are visual scenery. The controller is given a goal, not the designed slalom waypoints or terrain lip coordinates.

Actual ideal ray intersections build a 5 cm grid. Unknown cells remain blocked. Tall hazards receive 0.70 m inflation; A* requests are made at 5 Hz and the robot follows and replans the measured route. The larger course map covers x=-1.2 to 15.4 m and y=-3.4 to 3.4 m. The three barricades force alternating detours. Docking and paired transfers assume broad terraces aligned with world x.

Climbing uses a measured edge and surface level. Height-banded measured x coordinates address cell-boundary bias; the static sensor fixtures resolve the two course edges within 15 mm. This is a fixture-specific sampling bound, not a universal sensing guarantee. Each ascent requires simultaneous front-pair and rear-pair airborne states above the support level, re-contact, all four feet beyond the lip and on the raised surface, and the expected torso-height gain. A contact-free near-goal timeout is still rejected if either climb lacks this evidence.

## Actual experiment results

| Experiment | Policy | Accepted | Harmful-contact trials | Interpretation |
|---|---|---:|---:|---|
| Dense avoidance, 12 matched seeds | Measured-map controller | 12/12 | 0/12 | Three alternating detours |
| Same 12 dense scenes | Delayed reactive software baseline | 0/12 | 12/12 | Software comparison, no human participants |
| Closed-gate fixtures | Measured-map controller | 0/2 | 0/2 | No mission completion; final motion stopped |
| Combined detours and two climbs | Measured-map controller | 6/6 | 0/6 | Six descriptive seeded checks |
| Combined course seed 42 | Illustrative reactive baseline | 0/1 | 1/1 | Not a fully matched inferential comparison |

The avoidance extension's two-sided exact paired McNemar p-value is **0.00048828125**, based on 12 shared-only accepted pairs and zero baseline-only accepted pairs. These are selected static fixture seeds and a deliberately simple software baseline. The seven combined-course runs are descriptive; no paired p-value is claimed for them. The original 100-run/50-pair study remains a separate dataset and is not pooled with either extension.

### Combined course seed checks

| Seed | Accepted | Simulated seconds | Goal error m | Verified climbs | Harmful contact steps | Peak absolute roll deg | Peak absolute pitch deg |
|---:|---|---:|---:|---:|---:|---:|---:|
| 42 | True | 121.394 | 0.108 | 2 | 0 | 1.48 | 12.21 |
| 2026 | True | 120.288 | 0.108 | 2 | 0 | 1.33 | 12.24 |
| 2027 | True | 120.324 | 0.083 | 2 | 0 | 1.34 | 12.21 |
| 2028 | True | 118.964 | 0.109 | 2 | 0 | 1.39 | 12.25 |
| 2029 | True | 120.242 | 0.107 | 2 | 0 | 1.37 | 12.24 |
| 2030 | True | 120.040 | 0.109 | 2 | 0 | 1.34 | 12.23 |

Seed 42 completes in **121.394 simulated seconds**, with **0.108 m** goal error and **zero harmful contact steps**. Its independently verified ascent times are 87.078 s and 117.420 s. The driven path length is 21.271 m and it records 350 planner calls. All other final seeded trials and the failed baseline remain in the dataset.

![Actual trajectories from all combined-course checks](../analytics/climbing_course/course_paths.png)

![Actual torso and foot heights and contact states](../analytics/climbing_course/course_climbing_telemetry.png)

## Verification performed

- **44 automated tests pass**, covering M20 anatomy, kinematics, motor limits, rays, map statistics, unknown blocking, no diagonal corner cutting, latency, stop behavior, acceptance, portable XMLs, course geometry and measured step-edge regression fixtures.
- The **100 original trial logs** were re-audited against their frozen source, raw states and measured maps.
- All **26 avoidance-extension runs** and **7 combined-course runs** pass CSV/state identity, 20 ms sample timing, torque-limit, acceptance, map hit-count and ordered planner-history audits. Each accepted combined trial contains two distinct independently validated ascent records.
- Contact safety is evaluated from actual MuJoCo solver contacts **every 2 ms**, not only from the 50 Hz CSV samples. Step and floor supports are treated separately from harmful contacts.
- The three new seed 42 clips fully decode: **1,214 frames each at 10 fps**, 121.4 s duration. PNG-to-video representative frame comparisons pass; the video is explicitly a native rendering of recorded physical states, not a fresh live run. Source-state and plan hashes are retained in the media receipt.
- The original M20 still compiles with nq=23, nv=22, nu=16 and 17 meshes. New standalone course XMLs are supplied under `M20/M20_obstacle_course.xml` and `models/m20_obstacle_course.xml`.

## Run and reproduce

From the repository root in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Setup -Mode course_climb
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Mode course_climb -Live
powershell -ExecutionPolicy Bypass -File .\run_demo.ps1 -Mode course_climb -Record
```

If Python 3.12 is installed but absent from the Windows launcher, add `-Python "C:\path\to\python.exe"` to `-Setup`. This option validates the interpreter version before creating the environment.

`-Live` executes native interactive physics. A normal run creates the authoritative logged trial. `-Record` runs physics and renders its saved states. The combined deadline is 180 simulated seconds; wall-clock time depends on the computer. The supplied video is `docs/showcase/M20_Obstacle_Course.mp4`. Pages 19–22 of the Word guide explain the new workflow.

```powershell
$Py = ".\.venv\Scripts\python.exe"
$Analytics = "Group_09_Arnav_Vihan_Pratik\analytics"
& $Py -m pytest -q
& $Py "$Analytics\verify_evidence.py"
& $Py "$Analytics\analyze_course.py" --folder "$Analytics\obstacle_course"
& $Py "$Analytics\analyze_course.py" --folder "$Analytics\climbing_course"
$Stamp = Get-Date -Format yyyyMMdd_HHmmss
$Fresh = "$Analytics\local_runs\combined_$Stamp"
& $Py "$Analytics\run_course_benchmark.py" --combined --pairs 6 --out $Fresh
& $Py "$Analytics\analyze_course.py" --folder $Fresh
```

Existing experimental destinations are refused by the course batch runner. Source hashes are checked before and after execution. In combined mode, `--pairs` selects the number of shared-controller seeds and the runner adds one illustrative baseline; this mode does not create fully matched pairs.

## Fresh installation and source extraction

A clean extracted source copy created a separate virtual environment and independently installed all 31 locked dependencies. The Windows launcher did not register the available CPython 3.12 runtime; the new explicit `-Python` setup option was tested successfully. All 44 tests passed with no broken package requirements. The normal PowerShell helper completed the full default course with exit 0, two verified climbs and zero harmful contacts. The qpos, qvel, ctrl, targets and time arrays match the supplied seed 42 run bit for bit. The detailed receipt is `analytics/course_fresh_extraction_verification.json`. The final archive is refreshed with that receipt and the tested launcher.

## Sources and retained failures

| Dataset | Physical source SHA256 |
|---|---|
| Original 100-run study | `24a1c256abcc9a5bc3d0b38ecae3354d8a9f313ff8daf0e2b9c18daa8f7b2f96` |
| Dense avoidance extension | `f6667155f6c018f1b0f2b70341b93c9e2ddf067a0976a078f42d32168b3a8210` |
| Combined obstacle and climbing extension | `e492a29fd3f4c1029773d51940e3aaeedfe68e761b94a6bb9f7542e0cf26f1b9` |

Each dataset's `source_snapshot/M20` contains its exact Python and mechanical XML source. Meshes remain the unchanged supplied root assets. To re-execute a historical version, use a separate extracted project copy and copy that snapshot's Python files and M20.xml into its M20 folder while preserving the meshes. Do not replace old trial hashes with current hashes. Current-source extension runs use the normal commands above.

Development failures are retained under `analytics/development_evidence/course_tuning`. Some attempts reached the upper goal with no harmful contact but failed rear-pair liftoff; another incurred upper rear-leg contact. Parameter and edge-detection changes were evaluated in real transfer simulations. Intermediate full source snapshots were not retained for each tuning variant, so these development logs are not claimed as fully reproducible final experiments. The final experiments have exact source snapshots.

## Limits and pending human actions

Sensing and pose are ideal. The course has rigid static obstacles, no moving pedestrians, dust, loose rubble, hardware actuation or human workload study. The result does not establish industrial safety certification, arbitrary stair traversal, sustained gait or field reliability. The maps use exact simulated pose and are not SLAM. Camera panels do not drive navigation.

An additional sampled native geometry-distance diagnostic found inconsistent distance/witness outputs in some box queries. Those trial minimum-clearance values are withheld, rather than advertised as verified margins. This does not replace or alter the solver's 2 ms contact audit. The ray cutoff correction follows the [MuJoCo API distinction between geometry culling and ray intersection range](https://mujoco.readthedocs.io/en/stable/APIreference/APIfunctions.html#mj-multiray); its distant-plane regression is tested locally.

No student Git contributions, human survey scores, approvals or public posts have been invented. Student review, genuine commits, rehearsal and individual viva remain human actions. The updated four-page paper presents the extension separately from the original study. The updated Word guide, raw logs, videos, source snapshots and detailed receipts accompany the submission.
