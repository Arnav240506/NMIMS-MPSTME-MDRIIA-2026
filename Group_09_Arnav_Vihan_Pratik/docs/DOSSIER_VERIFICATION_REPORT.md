# Capstone verification and discrepancy resolution

## Verified technical outcome

The current Group 09 folder is self-contained and uses the supplied M20 hybrid quadruped. All 60 predeclared independent final-course trials are retained, including every failure. Proposed acceptance is 30/30, baseline 0/30; both climbs and zero harmful contacts are verified for each accepted trial. There are 4,495,972 actual physics samples in 254 plain CSV parts at 500 Hz. This is measured simulation evidence, not generated target data.

Primary terminal goal-error difference (proposed minus baseline): -12.203959831 m; Welch t=-715.183167762, df=29.445693976, p=5.5115214e-64; pooled Cohen d=-184.659499882; 95% CI [-12.238836911, -12.169082751] m. The extreme standardized effect reflects a weak baseline that fails near the first barrier with low variability. It is not general or hardware superiority.

## Resolution against the supplied capstone guide

| Requirement or discrepancy | Resolution and evidence |
|---|---|
| Car versus requested M20 | Original quadruped anatomy, 17 STL meshes, 12 leg + 4 hub motors; tests load nq=23/nv=22/nu=16. |
| Obstacle scene and climbing | Dense industrial yard, three alternating barriers, two 8 cm terraces; contact-gated pair lifts/support. |
| Work outside assigned group folder | Canonical runtime/assets moved into Group_09_Arnav_Vihan_Pratik/M20; portable relative models; own launcher/requirements/tests. |
| Actual 500 Hz scientific logging | Every actual 2 ms step saved; all 16 torque channels, pose/velocity, reference/error, FSM/events. 50 Hz replay files are separately identified. |
| N≥30, three roughness courses | 30 independent runs per policy; ten per bound 0/3/6 mm; disjoint seed sets, stated friction/barrier/start perturbations. |
| Comparable tracking metric | Same fixed evaluator-only path method for both policies; geometric nearest-segment error after startup, not timed tracking. |
| Required Welch, pooled d, CI | Independent design and predeclared primary terminal error; secondary nonparametric sensitivity. |
| Lifetime payback and queue missing | Tested general normalization, lifetime fraction P, NCRI, Erlang C M/M/c and overload handling; interactive graph. |
| Business and real telemetry | Separate telemetry_business_bridge.py reads real attempt duration/acceptance and adds explicitly assumed overhead; base planning model remains labeled. |
| Four-page PDF versus 18-page form | Canonical faculty form now four pages; all 212 tags/properties retained, 146 technical fields completed, 66 personal controls preserved. Extended detail is a separate six-page report. |
| Conflicting SAP IDs | Faculty pack IDs confirmed directly by user: E064 70362400067, E070 70362400086, E073 70362300032. |
| FSM absent from live viewport | Native live overlay shows phase/decision/time/contact/climb counters; genuine UI capture retained. |
| Old documentation and paper | Current ten-page detailed guide, four-page IEEE paper and six-page technical report; historical documents labeled separately. |
| GitHub binaries | Separate GitHub-ready package excludes videos, NPZ, caches and virtual environments; includes models and final plain raw CSVs. |
| Personal recording and posting | Deliberately pending as requested; detailed 3:45 plan, all-member webcam/speech and live/business requirements supplied. |

## Executed checks

- 54 tests passed in a fresh group-only staging folder using a separately installed locked environment. The staging parent has no sibling M20. See analytics/capstone_group_only_tests.xml.
- Full seed-42 group-only run accepted, 121.394 simulated seconds, two climbs, zero harmful contact steps, goal error 0.107743895 m. qpos, qvel, ctrl, targets and time arrays are bitwise equal to the canonical pilot. See analytics/capstone_group_only_verification.json.
- All 60 raw final-study trials pass SHA256, 2 ms continuity, run/seed, torque, effort, RMSE, contact, goal and two-ascent gates. See analytics/capstone_500hz/verification.json.
- Native live viewport was visually inspected. Interactive business capital input changed payback; arrival rate above capacity produced the no-finite-delay message. Genuine screenshots live in docs/provenance/ui/.
- Word form fields were compared to the original source. The four-page PDF was exported with Microsoft Word and every page rendered/inspected. The guide/report and IEEE paper also undergo page-by-page visual QA.
- Final ZIP CRC, entry hashes, source/doc consistency and exclusion checks are recorded in submission/package_receipt.json and the package manifest. Use those receipts, not a historical package hash.

## Data provenance and the aggregation repair

The simulator source digest was frozen at `52e6297c4a62995dfe65bcc65186b0ee7b7dcc0c1eb07e0c13672799031332d8` throughout the 60-run experiment. Per-run JSON/CSV evidence was complete before aggregate export hit a NumPy Boolean serialization error. The worker now returns the normalized saved JSON; resuming re-aggregated all existing completed trials. No physics data was replaced. Independent raw verification passed afterward. Analytics/document fixes are outside the frozen physical-source digest.

The new default logger was also checked against the earlier seed-42 saved state arrays bitwise. Historical 100-run, 26-run and seven-run studies have distinct source hashes and are not pooled with the current experiment. The original faculty template and supplied sources are preserved. No Git contribution was invented.

## Equations and primary sources

Welch statistic, variance-based degrees of freedom and pooled sample variance were checked against [NIST Two-Sample t-Test](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm). The code computes a two-sided t interval for the mean difference and separately divides by pooled SD for Cohen d. A known-shift analytic oracle tests sign, df, CI and scale.

The M/M/1 waiting formula and Little-law identities were checked against [MIT OpenCourseWare 2.854 M/M/1 Queue](https://live.ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016/927056a1af54772a587fd84ad4951e71_MIT2_854F16_Mm1Queue.pdf). Tests cover M/M/1, a known M/M/2 case, zero arrivals and unstable utilization. Rates are per week; the conversion to working hours assumes 40 h/week. No arrival/service data was measured in a plant.

P=K/[L(V−O)] and T_months=12K/(V−O) use K in annual-baseline cost units, V and O as annual values and L in years. Common cost scaling preserves the result. Base P=0.076923, T=4.615385 months, NCRI=0.78 and 0.15 FTE are assumption-driven. The FMEA scores are engineering judgments; code evidence does not validate their probabilities.

The attached showcase PDF is byte-identical to the capstone-pack guide (SHA256 d0d1a62aea862162bf0036eef90edb1c7ad1ead1aa6c6d53325b9faad68317c3). Faculty form source SHA256 is a920ee6d76a9981ca40a2d326e88923ba34cceefd2b25a201753d9ed96a2de53. Robotics reference metadata checks are retained in docs/bibliography/verification.json; sources are not used to invent this project's human/field outcomes.

## Material limits and personal actions

Ideal rays and exact pose, rigid static low terraces, mild roughness and a weak reactive baseline limit generalization. There is no hardware validation, sustained braked-wheel walking proof, human workload study, observed bandwidth reduction, measured plant labor saving or safety certification. Current comparisons are integration-level, not causal ablations. Total effort depends on duration and is not electrical energy.

Students still need their own genuine contributions/commits, review and understanding, webcam/speech recordings, LinkedIn publication and real URL, actual peer reviews of Groups 10 and 03, personal learning fields, signatures/consent and individual Teams Turn in. These are intentionally not fabricated. Re-export the exact same signed four-page PDF after personal edits and verify its pagination. Maximum marks cannot be guaranteed.
