# M20 extended technical report


This report supports the required four-page faculty dossier. The final implementation preserves the supplied M20 quadruped morphology and adds a reproducible industrial obstacle-and-climb evaluation, actual 500 Hz telemetry and a dimensionless business model. The robot completes the tested course under ideal simulated sensing; deployment, human workload and field savings remain unvalidated.

The final experiment contains 60 independent runs, 30 per policy. Proposed map-and-transfer control accepts 30/30, each with both terrace ascents and no harmful contact steps. The reactive baseline accepts 0/30; all runs time out with harmful contacts. All outcomes are retained. No baseline or historical UGV scaffold numbers are relabeled as M20 results.

The raw audit checked 4,495,972 actual samples across 254 CSV parts. Primary final goal error differs by -12.203960 m (proposed minus baseline), Welch t=-715.183168, df=29.445694, p=5.5115214e-64, 95% CI [-12.238837, -12.169083]. The pooled Cohen d of -184.659500 is very large because the weak baseline fails near the first obstacle with low variability. This is integration evidence, not proof of state-of-the-art superiority.

Canonical source is inside Group_09_Arnav_Vihan_Pratik/M20. The frozen simulation digest is 52e6297c4a62995dfe65bcc65186b0ee7b7dcc0c1eb07e0c13672799031332d8. The evaluation folder includes the predeclared design, source snapshot, mesh hashes, per-run configurations, measured samples, summary records and independently recomputed statistics.

AI assistance was substantial in implementation, experiments, analysis and drafting. The original mechanical model and mesh assets were reused. Team identities are confirmed, but individual authorship, hours, learning, peer scores and signatures must be personally attested. This report does not create contribution evidence.

IMAGE:docs/figures/course_climbing_frame.png

Historical rendered physical state showing paired-leg transfer. The final study’s measured records are identified by their separate source digest and trial IDs.


# Mechanical model and control architecture


The M20 MJCF has a floating base, twelve articulated leg joints and four actuated foot wheels: nq=23, nv=22, nu=16. The supplied total mass is 34.525856 kg and seventeen STL meshes retain the robot’s appearance. Collision primitives and inertias are supplied/simplified model quantities, not identified hardware parameters.

MuJoCo integrates at 0.002 s with implicitfast. The robot uses friction coefficients 1/0.01/0.001; floor sliding friction is seeded U(0.75,1.15), with torsional 0.005 and rolling 0.0001. Robot solref is 0.005/1; floor solref is 0.02/1. These settings provide numerical contact compliance and are not calibrated material measurements.

Multibody dynamics obey M(q)q̈+C(q,q̇)q̇+g(q)=τ+Jᵀf. Joint commands combine PD tracking, bias compensation and stance-wrench allocation before saturation. Leg Kp is [500,800,800] N m/rad and Kd is [25,40,40] N m s/rad. Leg torque caps are 76.4 N m; hub caps are 21.6 N m. The instantaneous regularized wrench solution is not model-predictive control.

Analytic two-link inverse kinematics uses two 0.25 m sagittal links and the supplied lateral geometry. Wheel target conversion retains a 0.09 m servo radius versus 0.093 m collision radius. Effective steering width is 0.55 m. This mismatch and skid-steer approximation limit interpretation of the kinematic slip proxy; it is not a measured tire-slip estimator.

The FSM starts in WAKEUP, cruises through mapped detours, aligns for a terrace, shifts support, transfers the front pair, raises/advances the body, shifts support to the front and transfers the rear pair. A clearance phase moves the hind feet beyond the lip before the next navigation/transfer phase. A second measured terrace invokes the sequence again.

Strict climb acceptance requires front and rear pair airborne events and re-support events plus geometric progression. Mission acceptance additionally requires goal arrival, no rollover, no tilt-stop violation and zero harmful contact steps. Expected support on traversable terrain is distinguished from contacts with harmful obstacle geometry. This prevents torso rise, foot sliding or reaching a goal through collisions from being counted as successful climbing.

Worked static check: mg=34.525856×9.81=338.698647 N. Equal four-foot loading would be 84.674662 N per foot; a 0.25 m lever gives 21.168666 N m. These are illustrative equilibrium calculations. The actual seed-42 support normals near 2.302 s sum to about 338.739 N; individual normals are read from the measured diagnostic CSV and need not be equal.


# Perception terrain and experimental design


The industrial yard includes three alternating tall barriers, cylinders, crates, pipe/boundary geometry and two 8 cm terrace rises (16 cm cumulative elevation). Terrain roughness adds physical low rubble boxes rather than changing labels alone. The tested environment is static, rigid and deliberately structured; it is not a loose-debris disaster simulator.

Ideal ray intersections and exact MuJoCo pose update a 2.5D elevation/traversability grid. The dense course uses 5 cm cells. Unknown cells are blocked for path search; local sensing/frontier behavior reveals reachable space. A* routing uses obstacle inflation and height/roughness/slope costs. Height bands identify the low step edge and docking point. The broad terraces are approximately aligned with world x, which is a task assumption rather than general stair detection.

The evaluator separately builds a fixed reference polyline from the known fixture geometry. Both policies are scored by the same method. This reference is never sent to control. It avoids the optimistic error obtained when an online replan begins at the current robot position, but it measures nearest-segment cross-track distance rather than time-indexed tracking performance.

Thirty independent seeds per policy were predeclared. Baseline 31000–31029 and proposed 32000–32029 do not overlap. Each arm has ten trials with roughness bound 0, ten at 3 mm and ten at 6 mm. For nonzero bounds, rubble heights are U(bound/2,bound). Floor friction is U(0.75,1.15), barriers shift within ±0.08 m, initial lateral displacement within ±0.02 m and yaw within ±0.02 rad. Delay is fixed at the assumed 0.35 s. The per-trial time budget is 180 simulated seconds.

The baseline uses the same M20 and standing/rolling actuation but a delayed reactive driver without mapping or paired climb logic. The proposed policy bundles multiple improvements. This comparison tests system integration; it cannot isolate the contribution of mapping, climb transfer or delay handling. A stronger baseline and controlled ablations are important future work.

Historical evidence remains separate: 100 original paired runs, 26 avoidance/blocked runs and seven earlier combined-course checks. Their source hashes and protocols differ. They are not pooled with the final sixty independent runs or used to inflate sample size. Earlier 50 Hz diagnostics are explicitly distinguished from the final actual 500 Hz scientific logger.


# Telemetry statistics and failure interpretation


TrialLogger streams actual post-step pose and velocity with the actuator force applied over the preceding 2 ms interval. Unit actuator gear is asserted, so the sixteen force channels represent motor torque. The logger writes bounded plain CSV parts, not interpolated 500 Hz rows generated from 50 Hz data. Numeric serialization preserves timestamps at six decimals and measured channels at nine significant digits.

Tracking RMSE is sqrt(mean(error_x²+error_y²)) after the 2.4 s startup interval. Effort is the complete time integral of the sum of sixteen squared torques. Each includes failed trials and their actual durations. Separate 50 Hz state arrays support playback and diagnostic foot-force inspection.

The verifier checks all CSV hashes and continuous timestamps, run IDs/seeds, torque finiteness, position-reference arithmetic, RMSE, integrated effort, harmful contact counts, final distance to goal and both airborne/re-support gate pairs for accepted runs. The default seed-42 migration was bitwise identical in saved qpos/qvel/ctrl/targets/time to the previous controller version: adding full-rate logging did not change its dynamics.

Primary goal-error means are 12.310317 m baseline and 0.106357 m proposed. Cross-track RMSE means are 0.581105 and 0.194681 m. Squared-torque effort means are 1,128,398.226 and 555,625.351 N²m²s. Standard deviations, inference and secondary metrics are in statistics.json; all failures are in failure_cases.csv.

Welch inference was chosen for independent groups with unequal variances. The pooled-SD standardized mean difference is reported separately from the Welch standard error. A Mann–Whitney sensitivity test gives p≈3.0199×10⁻¹¹. The extreme separation is expected when one policy cannot progress through the fixture; a small p-value does not cure weak-baseline design or prove hardware safety.

IMAGE:docs/figures/capstone_results.png

The first plot uses measured seed 32000 and its fixed evaluator path. The second includes all sixty runs. Every proposed roughness stratum has 10/10 acceptance; baseline strata have 0/10. No trial was removed to improve results. These sample counts do not establish a population success probability of one.


# Business assumptions and empirical telemetry bridge


The base economic model uses normalized annual baseline value V=1, annual operating cost O=0.22, capital K=0.30 in annual-baseline cost units and life L=5 years. κ=O/V; NCRI=1−κ; payback months=12K/(V−O); lifetime-normalized P=K/[L(V−O)]. These yield κ=0.22, NCRI=0.78, T=4.615385 months and P=0.076923. Scaling K,V,O by the same factor leaves the result unchanged.

Assumed reclaimed annual hours H=312 and full-time capacity 2080 give ΔFTE=0.15. A ±30% hours scenario gives 0.105–0.195 FTE. At κ≥1 there is no positive savings payback; with K=0.30 and L=5 the within-life boundary is κ=0.94. These are explicit assumptions, not measured employment changes.

M/M/1 uses λ=8/week and μ=12/week, with 40 working hours/week. ρ=2/3, Wq=λ/[μ(μ−λ)]=1/6 week=6.666667 working hours, W=0.25 week, Lq=1.333333 and L=2. M/M/c uses Erlang C; zero arrivals and unstable ρ≥1 are tested. Poisson arrivals, exponential independent service, FCFS and steady state are unverified modeling assumptions.

The separate telemetry bridge reads real final-study acceptance and attempt duration. Proposed mean attempt duration is 119.731467 simulated seconds and empirical accepted fraction is 1.000. With an explicitly assumed 3-hour inspection/reset overhead per attempt and 40 working hours/week, μ_eff=40p/(3+t/3600)=13.187137 successful jobs/week. At λ=8 this scenario gives Wq=4.678124 working hours. This is a sensitivity scenario, not a measured service rate; baseline zero accepted service is reported as zero capacity, not divided by zero.

IMAGE:docs/figures/capstone_economics_small.png

FMEA ratings are subjective 1–10 planning scores. Severity remains fixed after mitigation; assumed occurrence/detection reductions produce the displayed post RPNs. Simulation/code supports tilt latches, local stopping, blocked-path handling, contact gates and witness validation. It does not statistically validate the numerical risk scores or establish regulatory conformity.


# Reproduction audit and remaining human work


Run the group-only commands in the complete guide. The simulation module and assets are now under the assigned group folder, and models use relative ../M20/meshes references. A clean group-only staging check runs tests and a full seed-42 course without a sibling M20 dependency. The final verification report records the resulting receipt rather than assuming portability from a successful local run.

The original final batch completed all sixty simulations before an aggregate JSON serialization bug surfaced on a NumPy Boolean. The batch worker now returns the normalized per-run JSON; the complete evidence was re-aggregated and independently audited. No raw sample or outcome was regenerated to hide a failure. This is separate from the physical source digest, which remained frozen throughout the experiment.

Live UI evidence confirms the native viewport displays FSM/decision/contact/climb telemetry. The business dashboard was opened and its sliders changed: capital altered payback, and requests above capacity produced the unstable-queue message. Genuine UI screenshots are distinguished from renderer-generated physics replays. A short window-closure diagnostic records user_closed and is not claimed as a complete course.

The four-page faculty form retains 212 tagged controls and all original dropdown properties. Its 146 technical fields are completed; 66 personal controls remain unchanged for students. Word-to-PDF output is rendered and visually inspected. The extended report supplies detail without making the required dossier eighteen pages long. The existing unverified dossier target is updated after final QA, while its original backup is retained.

Sources for statistical formulas: NIST/SEMATECH e-Handbook, Two-Sample t-Test for Equal Means, https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm. Queue formulas: MIT OpenCourseWare, 2.854 Introduction to Manufacturing Systems, M/M/1 Queue (2016), linked in CAPSTONE_VERIFICATION_REPORT.md. Robotics literature metadata and DOI checks are retained in docs/bibliography/verification.json. No field or human outcome is attributed to those sources as a result of this project.

Remaining human actions are deliberate: genuine personal-account contributions, student review/understanding, webcam/speech recording, native LinkedIn posting and real URL, assigned peer reviews, personal learning fields and signatures, optional consent choices, and each member’s individual Teams Turn in. These cannot be completed by manufacturing records. The code, mathematical scenarios and measured evidence are prepared for those actions.

Future evaluation should use held-out geometry, stronger comparable-capability baselines, perception noise and drift, dynamic hazards, more severe roughness, hardware identification, energy measurement and actual operational workload/time studies. The current evidence establishes the tested simulated integration and nothing beyond it.
