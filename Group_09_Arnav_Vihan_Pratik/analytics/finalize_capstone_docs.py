"""Write the current release index, verification report and honest human handoff."""
from pathlib import Path
import json,shutil,hashlib
G=Path(__file__).resolve().parents[1];A=G/'analytics';D=G/'docs';R=G.parent
def write(p,t):p.write_text(t.strip()+'\n',encoding='utf-8')
def main():
    s=json.loads((A/'capstone_500hz/statistics.json').read_text());v=json.loads((A/'capstone_500hz/verification.json').read_text());fresh=json.loads((A/'capstone_group_only_verification.json').read_text());form=json.loads((D/'provenance/capstone_form_controls.json').read_text())
    readme=r'''# Group 09 M20 quadruped capstone

This is the self-contained assigned group folder. Run commands **from this folder**. The supplied M20 has four articulated legs, twelve leg motors, four foot-wheel motors and seventeen original meshes. It rolls through an industrial yard, avoids three alternating barriers and performs paired-leg transfers over two 8 cm terraces.

| Member | Roll | Confirmed SAP |
|---|---|---|
| Arnav Saurabh Surve | E064 | 70362400067 |
| Vihan Shripad Joshi | E070 | 70362400086 |
| Pratik Mangesh Gaikwad | E073 | 70362300032 |

## Run

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_demo.ps1 -Setup
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_demo.ps1 -Live
```

Open a second PowerShell in this folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_demo.ps1 -Business
```

Python 3.12 is required; use `-Setup -Python C:\path\to\python.exe` if the py launcher is unavailable. The launcher verifies the supplied version. The live viewport shows actual FSM, decisions, contacts and climb counters. The business dashboard is interactive and explicitly labels assumed inputs.

## Verified final study

60 independent simulations, 30 per policy, ten at each of three roughness bounds. Proposed: 30/30 accepted, two climbs and zero harmful contacts each. Reactive baseline: 0/30 accepted; all timeouts with contacts. Raw scientific telemetry is **actual 500 Hz**, 4,495,972 samples in 254 CSV parts. 54 tests passed in a separate group-only copy, and full seed-42 qpos/qvel/ctrl/targets/time replay arrays matched bitwise.

The baseline lacks mapping and paired climbing. These results demonstrate tested integration, not superiority over a strong planner or expert operator. Ideal sensing/exact pose, rigid low terraces and uncalibrated business assumptions remain explicit limits.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe analytics\analyze_capstone.py
.\.venv\Scripts\python.exe analytics\plot_capstone.py
.\.venv\Scripts\python.exe analytics\telemetry_business_bridge.py
```

To execute fresh physics: `python analytics/run_capstone_benchmark.py --workers 3 --out analytics/capstone_rerun` using the local environment. Never overwrite evidence to replace a failure.

## Documents

- [Required four-page dossier](docs/MDRIIA_Group_09_Technical_Dossier.pdf) and [editable original-field Word form](docs/MDRIIA_Group_09_Technical_Dossier.docx).
- [Detailed ten-page run guide](docs/M20_Complete_Step_by_Step_Run_Guide.pdf), also supplied in DOCX and Markdown.
- [Extended technical report](docs/M20_Extended_Technical_Report.pdf).
- [Four-page IEEE research manuscript](docs/paper/Group09_HazardousTerrain_IEEE.pdf) with editable TeX.
- [Verification and discrepancy resolution](docs/CAPSTONE_VERIFICATION_REPORT.md).
- [Showcase recording plan](docs/SHOWCASE_RECORDING_GUIDE.md).

All 212 faculty Word controls remain; 146 technical fields are completed and 66 personal fields are preserved for students. Recordings/webcams, genuine commits, peer review, personal declarations/signatures, public LinkedIn URL and each student's Teams Turn in remain human actions. No contribution history or public posting is fabricated.

## Evidence layout

`M20/` contains the canonical runtime and assets; `src/` entry points; `models/` portable MJCF aliases; `analytics/capstone_500hz/` the final design, raw CSVs, source snapshot and inference; `analytics/capstone_checks/pilot_42/` the default full-course check. The separate `telemetry.csv`/`states.npz` visualization channel is 50 Hz and is not the scientific logger.

Historical `benchmark/`, `obstacle_course/`, `climbing_course/` and documents explicitly marked historical concern different protocols/source versions. Do not pool them with the final independent study. The GitHub subset omits historical evidence and replay videos/binaries; the full offline archive retains them. Source provenance and original templates remain identifiable.

AI assistance was substantial. Every member must review, understand, contribute and personally attest their own work.
'''
    write(G/'README.md',readme)
    write(R/'README.md','# M20 capstone release\n\nThe current project is entirely inside [Group_09_Arnav_Vihan_Pratik](Group_09_Arnav_Vihan_Pratik/README.md). Use that folder for GitHub and all current commands. The root M20 folder is a retained historical runtime; the root launcher forwards to the current group version.\n\nFinal archives are under submission/. The four-page faculty dossier, guide, extended report and research paper are inside the group docs folder.')
    write(R/'run_demo.ps1',"& (Join-Path $PSScriptRoot 'Group_09_Arnav_Vihan_Pratik\\run_demo.ps1') @args\nexit $LASTEXITCODE")
    write(G/'.gitignore',r'''.venv/
__pycache__/
.pytest_cache/
*.pyc
*.mp4
*.avi
*.npz
*.aux
*.log
*.out
analytics/local_runs/
analytics/capstone_rerun/
analytics/development_runs/
''')
    recording=r'''# Group 09 showcase recording guide

Target 3:45 within the required 3–4 minutes. This is a plan for the team’s later recording, not a claim that footage or posting exists. No slides and no currency amounts. Capture genuine live MuJoCo FSM behavior, a business sensitivity graph and each member’s webcam/speech.

| Planned interval | Speaker and action | Evidence to show |
|---|---|---|
| 0:00–0:25 | Arnav: identify the M20 and inspection problem | Four legs, 16 actuators, industrial yard |
| 0:25–1:15 | Vihan: explain ideal rays, exact pose, unknown cells and A* | Live DETOUR_NAV, changing decision, barriers |
| 1:15–2:15 | Arnav: explain support shifts and both climbs | Front/rear pair phases, contacts, climb counter |
| 2:15–3:10 | Pratik: change capital/operating parity and queue arrival rate | P, NCRI and unstable-queue boundary |
| 3:10–3:45 | All: measured result, AI correction, limitation and contribution | 60 real trials, 500 Hz, honest baseline limits |

Open `run_demo.ps1 -Live` and `run_demo.ps1 -Business` in separate terminals in the group folder. Rehearse on the actual laptop; live simulated time can advance slower than wall time. If needed, record longer and use explicitly edited live excerpts. Do not label an edited or accelerated segment uninterrupted real time. Saved MP4s are replay evidence and do not replace the live/webcam requirement.

Speak in your own words after reviewing the code. Suggested numerical explanation: 30/30 integrated-policy acceptances versus 0/30 simple reactive-driver acceptances; the baseline lacks map and climb capability, so the comparison is limited. Business base P=0.076923, NCRI=0.78 and Wq=6.667 working hours are assumed scenarios. The separate telemetry bridge uses actual attempt duration plus assumed operational overhead.

Record at a readable resolution, check microphone levels and prevent other windows covering the viewport. Watch the exported video completely before posting. Publish the real video natively to LinkedIn, verify playback and enter the actual URL/duration in Section 5. Change its No fields to Yes only after the final video actually contains each element.

Each member reviews Group 10 (surgical assistant) and Group 03 (AED delivery) from actual posts, then fills the assigned 0–2 scores, real timestamp and viva question. Personal hours, contribution shares, signatures and optional consent are not supplied by this package.

After adding personal fields and URL, export one clean four-page PDF, have all members use that exact same signed file and each personally click Turn in on Teams. Commit DOCX/PDF to the assigned group docs folder from genuine accounts. Do not fabricate accounts, commit shares or contribution history.
'''
    for name in ['SHOWCASE_RECORDING_GUIDE.md','LINKEDIN_SHOWCASE_PLAN.md','DEMO_SCRIPT_AND_CHECKLIST.md']:write(D/name,recording)
    write(D/'SETUP_AND_RUN.md','# Current setup and run instructions\n\nUse the [complete current guide](M20_Complete_Step_by_Step_Run_Guide.md). All commands run from the assigned group folder. Setup, live viewer and interactive business dashboard are available through its run_demo.ps1. The historical root M20 runtime is not the current entry point.')
    c=s['comparisons']['goal_error_m']
    report=f'''# Capstone verification and discrepancy resolution

## Verified technical outcome

The current Group 09 folder is self-contained and uses the supplied M20 hybrid quadruped. All 60 predeclared independent final-course trials are retained, including every failure. Proposed acceptance is 30/30, baseline 0/30; both climbs and zero harmful contacts are verified for each accepted trial. There are {v['total_actual_samples']:,} actual physics samples in {v['CSV_parts']} plain CSV parts at 500 Hz. This is measured simulation evidence, not generated target data.

Primary terminal goal-error difference (proposed minus baseline): {c['difference_proposed_minus_baseline']:.9f} m; Welch t={c['t']:.9f}, df={c['df']:.9f}, p={c['p_two_sided']:.9g}; pooled Cohen d={c['cohen_d_pooled']:.9f}; 95% CI [{c['CI95'][0]:.9f}, {c['CI95'][1]:.9f}] m. The extreme standardized effect reflects a weak baseline that fails near the first barrier with low variability. It is not general or hardware superiority.

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
| Four-page PDF versus 18-page form | Canonical faculty form now four pages; all {form['controls']} tags/properties retained, {form['technical_fields']} technical fields completed, {form['personal_controls_preserved']} personal controls preserved. Extended detail is a separate six-page report. |
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

The simulator source digest was frozen at `{v['source_sha256']}` throughout the 60-run experiment. Per-run JSON/CSV evidence was complete before aggregate export hit a NumPy Boolean serialization error. The worker now returns the normalized saved JSON; resuming re-aggregated all existing completed trials. No physics data was replaced. Independent raw verification passed afterward. Analytics/document fixes are outside the frozen physical-source digest.

The new default logger was also checked against the earlier seed-42 saved state arrays bitwise. Historical 100-run, 26-run and seven-run studies have distinct source hashes and are not pooled with the current experiment. The original faculty template and supplied sources are preserved. No Git contribution was invented.

## Equations and primary sources

Welch statistic, variance-based degrees of freedom and pooled sample variance were checked against [NIST Two-Sample t-Test](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm). The code computes a two-sided t interval for the mean difference and separately divides by pooled SD for Cohen d. A known-shift analytic oracle tests sign, df, CI and scale.

The M/M/1 waiting formula and Little-law identities were checked against [MIT OpenCourseWare 2.854 M/M/1 Queue](https://live.ocw.mit.edu/courses/2-854-introduction-to-manufacturing-systems-fall-2016/927056a1af54772a587fd84ad4951e71_MIT2_854F16_Mm1Queue.pdf). Tests cover M/M/1, a known M/M/2 case, zero arrivals and unstable utilization. Rates are per week; the conversion to working hours assumes 40 h/week. No arrival/service data was measured in a plant.

P=K/[L(V−O)] and T_months=12K/(V−O) use K in annual-baseline cost units, V and O as annual values and L in years. Common cost scaling preserves the result. Base P=0.076923, T=4.615385 months, NCRI=0.78 and 0.15 FTE are assumption-driven. The FMEA scores are engineering judgments; code evidence does not validate their probabilities.

The attached showcase PDF is byte-identical to the capstone-pack guide (SHA256 d0d1a62aea862162bf0036eef90edb1c7ad1ead1aa6c6d53325b9faad68317c3). Faculty form source SHA256 is {form['original_sha256']}. Robotics reference metadata checks are retained in docs/bibliography/verification.json; sources are not used to invent this project's human/field outcomes.

## Material limits and personal actions

Ideal rays and exact pose, rigid static low terraces, mild roughness and a weak reactive baseline limit generalization. There is no hardware validation, sustained braked-wheel walking proof, human workload study, observed bandwidth reduction, measured plant labor saving or safety certification. Current comparisons are integration-level, not causal ablations. Total effort depends on duration and is not electrical energy.

Students still need their own genuine contributions/commits, review and understanding, webcam/speech recordings, LinkedIn publication and real URL, actual peer reviews of Groups 10 and 03, personal learning fields, signatures/consent and individual Teams Turn in. These are intentionally not fabricated. Re-export the exact same signed four-page PDF after personal edits and verify its pagination. Maximum marks cannot be guaranteed.
'''
    for name in ['CAPSTONE_VERIFICATION_REPORT.md','FINAL_DELIVERY_REPORT.md','DOSSIER_VERIFICATION_REPORT.md']:write(D/name,report)
    write(D/'RUBRIC_COMPLIANCE_MATRIX.md','# Current 20-mark assessment map\n\n| Component | Evidence | Remaining personal action |\n|---|---|---|\n| Robotics 10 | Dossier 1–2/4, M20 model/controller, 60 actual trials, 500 Hz audit, tests | Review code and defend physics |\n| Business 5 | Dossier 3–4, normalized payback/NCRI/labor, M/M/c, sensitivity and telemetry bridge | Explain assumptions and calculations |\n| Showcase/viva 5 | Dossier 5, live FSM, business GUI, recording plan | Record/post genuine 3–4 min video, peer review, viva |\n\nThe source course also contains an older 100-mark rubric. The final capstone-specific 20-mark instructions govern this handoff. No grade is claimed. Every member must individually turn in the same signed four-page PDF.')
    for name in ['PROJECT_AUDIT_AND_EVIDENCE.md','OBSTACLE_COURSE_REPORT.md','FAILURE_CASES.md','M20_RECTIFICATION_AUDIT.md']:
        p=D/name;old=p.read_text(encoding='utf-8')
        if not old.startswith('> Historical'):write(p,'> Historical implementation/evidence note. For the current independent 500 Hz study and final package, use CAPSTONE_VERIFICATION_REPORT.md and the current run guide. Do not pool these protocols.\n\n'+old)
    # Correct active textual identifiers; retain untouched archived originals and source snapshots.
    for base in [D,G/'analytics']:
        for p in base.rglob('*'):
            if not p.is_file() or p.suffix not in {'.md','.html','.tex','.py'} or 'source_snapshot' in p.parts:continue
            if p.name in {'finalize_capstone_docs.py','build_capstone_paper.py'}:continue
            old=p.read_text(encoding='utf-8');new=old
            for x,y in [('70362400017','70362400067'),('70362400063','70362400086'),('70362400033','70362300032')]:new=new.replace(x,y)
            if new!=old:p.write_text(new,encoding='utf-8')
    roster=json.loads((D/'TEAM_ROSTER.json').read_text());roster['project_showcase']['submission_status']='RECORDING_AND_POSTING_PENDING';roster['members'][2]['viva_focus']='Independent Welch inference, pooled effect size, dimensionless economics, queue stability and explicit assumptions';write(D/'TEAM_ROSTER.json',json.dumps(roster,indent=2))
    ui=D/'provenance/ui';ui.mkdir(parents=True,exist_ok=True)
    for name in ['live_viewport.png','business_live.png','business_unstable.png']:
        p=R/'recovery/capstone_instruction_audit'/name
        if p.exists():shutil.copy2(p,ui/name)
    write(ui/'README.md','Genuine native UI captures from this verification session. The live viewport image shows actual stepped physics, not state replay. Business screenshots show the base scenario and the unstable-queue message after interacting with the slider. These are technical QA evidence, not student webcam/showcase completion.')
    print('Current release documentation synchronized.')
if __name__=='__main__':main()
