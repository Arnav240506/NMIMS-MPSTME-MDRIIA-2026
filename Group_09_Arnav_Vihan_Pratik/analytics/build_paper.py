"""Populate the four-page IEEE manuscript from measured statistics and telemetry."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent;PAPER=HERE.parent/'docs/paper'
TEMPLATE=r'''\documentclass[conference]{IEEEtran}
\usepackage{amsmath,amssymb,graphicx,booktabs,url}
\usepackage[hidelinks]{hyperref}
\graphicspath{{../figures/}}
\begin{document}
\title{M20 Quadruped Reconnaissance Using Terrain Mapping and Paired-Leg Step Transfer}
\author{\IEEEauthorblockN{Arnav Saurabh Surve\quad Vihan Shripad Joshi\quad Pratik Mangesh Gaikwad}
\IEEEauthorblockA{E064 / SAP 70362400067\quad E070 / SAP 70362400086\quad E073 / SAP 70362300032\\
B.Tech Computer Science and Business Systems, SVKM's NMIMS MPSTME, Mumbai\\
MDRIIA 702CO0E012, Group 09, Academic Year 2026--2027}}
\maketitle
\begin{abstract}
Hazardous-terrain reconnaissance requires mobility and sensing to work together. We implement a reproducible MuJoCo study using the supplied M20 hybrid canine quadruped, preserving its four articulated legs, sixteen motors and seventeen visual meshes. Ideal range intersections build a true-pose-referenced elevation grid; local A* planning, heading alignment and front/rear paired-leg transfers negotiate a low platform. Physical acceptance distinguishes standing up, foot placement, goal arrival and harmful contacts. Across fifty matched seeded environments (one hundred simulations), a delayed reactive software driver completes @@BASE@@/50 accepted missions and the integrated controller completes @@SHARED@@/50. The two-sided exact paired test gives $p=@@P@@$. A representative 8 cm climb-and-detour mission takes @@TIME@@ simulated seconds with zero harmful contacts. A separate twelve-second leg-walking demonstration verifies foot lift. Results support this tested integration under ideal sensing, not field safety or measured human workload reduction. Raw failed trials, editable analysis and simulation states accompany the submission.
\end{abstract}
\begin{IEEEkeywords}
quadruped, wheeled-legged robot, terrain mapping, MuJoCo, shared autonomy, reproducibility
\end{IEEEkeywords}

\section{Problem and Contribution}
The course asks how LiDAR traversability mapping can improve unknown-terrain reconnaissance while reducing teleoperation burden and latency. The supplied README identifies M20, a hybrid robot dog, as the intended platform. We preserve its articulated legs, inertias and STL assets; wheeled travel and paired leg transfer use the same complete robot.

The industrial-yard fixture includes a low concrete platform, 25 cm barrier, low rubble and storage tank with collisions. Warehouse walls and markings are decorative. Toxic gas, structural collapse and disaster-field mechanics are not simulated.

Our educational contribution is auditable map-to-transfer integration: actual rays build a measured grid; local planning docks the robot before a contact-gated paired climb; evaluation rejects false success. The comparison tests the complete policy bundle against a delayed software driver. It does not establish locomotion novelty or human workload reduction.

\begin{figure}[t]
\centering\includegraphics[width=\columnwidth]{figure1_system_architecture.pdf}
\caption{Implemented simulation pipeline. The diagram describes module flow; empirical figures below use actual MuJoCo logs. Local control can override the delayed remote-intent channel.}
\label{fig:architecture}
\end{figure}

\section{Related Work and Scope}
Fankhauser \emph{et al.} study terrain mapping with uncertain localization~\cite{fankhauser}; our simpler mapper assumes exact pose and does not propagate localization uncertainty. Di Carlo \emph{et al.} use convex model-predictive force control for quadrupeds~\cite{dicarlo}. We use an instantaneous regularized wrench allocation with clipping, without a predictive horizon or constrained MPC optimization.

Miki \emph{et al.} combine exteroception and proprioception for robust perceptive locomotion~\cite{miki}. Lee \emph{et al.} integrate learned navigation and locomotion for wheeled-legged robots~\cite{lee}. Those systems motivate platform choice and integrated control, but their learned policies and field performance are not reproduced here. Teleoperation interface and performance issues discussed by Chen \emph{et al.}~\cite{chen} motivate the delayed-driver comparison; software intervention events cannot substitute for participant workload scores. MuJoCo supplies articulated-body dynamics and contact integration~\cite{mujoco}.

\clearpage
\section{Robot and Closed-Loop Method}
\subsection{Preserved M20 Physical Model}
The model has $q\in\mathbb{R}^{23}$ generalized positions and 22 velocities: sixteen joint coordinates plus a free base represented by translation and a quaternion. Summed supplied body mass is 34.525856 kg, correcting the inherited textual value. Visual STL meshes are separate from primitive collision geometry; their collision approximation is a limitation, not a hardware-identification result. Table~\ref{tab:model} summarizes the implemented numerical model.

\begin{table}[t]
\caption{M20 model and control parameters (SI units)}\label{tab:model}
\centering\begin{tabular}{ll}\toprule
Quantity & Implemented value\\\midrule
Leg / hub actuators & 12 / 4\\
Visual meshes / mass & 17 / 34.525856 kg\\
Thigh / shank length & 0.25 / 0.25 m\\
Wheel collision / servo radius & 0.093 / 0.090 m\\
Leg / hub torque limits & 76.4 / 21.6 N m\\
Physics / torque servo & 500 / 500 Hz\\
IK and wrench allocation & 100 Hz\\
Map integration / cost update & 50 / 10 Hz\\
Grid / obstacle inflation & 0.03 / 0.70 m\\\bottomrule
\end{tabular}
\end{table}

For the sagittal two-link component, inverse kinematics uses
\begin{equation}
\cos q_k=\frac{x^2+z_{\ell}^2-l_1^2-l_2^2}{2l_1l_2},\quad l_1=l_2=0.25\ \mathrm{m}.
\end{equation}
The 0.158076 m lateral offset determines hip roll before this solve. Front and rear legs use opposite knee branches. Forward/inverse kinematics is checked against MuJoCo wheel-body positions on all four limbs.

Joint torque combines target tracking, bias compensation and stance-force terms:
\begin{equation}
\tau=\operatorname{sat}\!\left[K_p(q_d-q)-K_d\dot q+\tau_{bias}-J^Tf\right].
\end{equation}
An instantaneous allocation $f=A^T(AA^T+\lambda I)^{-1}w_d$ approximates the desired body wrench, with normal-force and friction-box clipping. It is neither a constrained contact optimum nor proof of two-foot balance. Pitch/roll state feedback and braked support hubs assist transfers. Motor commands respect supplied limits; no artificial 600 N m wheel locking is used. The floating-base state is set only for initial grounding, never rewritten to advance the robot.

\subsection{Measured Mapping and Planning}
Native multi-ray intersections exclude robot/decorative geometry by group identity, retaining genuinely tall hazards. Cells store count, mean, peak and local height variation. The true MuJoCo pose transforms the scan; this is not SLAM, ROSbot localization or a fused nine-axis inertial estimator. An interleaved scan integrates at 50 Hz simulated time, with sixteen groups requiring 0.32 s for one full lattice. Cost updates run at 10 Hz; A* requests run at 5 Hz. These are scheduling rates, not claimed wall-clock throughput.

The normalized terrain term is
\begin{equation}
c=0.4\bar{s}+0.3\bar{r}+0.3\bar{h},\quad 0\leq c\leq1,
\end{equation}
with slope, roughness and local step clipped relative to $30^\circ$, 0.04 m and 0.14 m. A separate obstacle-proximity penalty influences A*. Unknown/inflated cells are blocked, diagonal corner cuts are forbidden, and a reachable measured frontier is attempted before a no-route stop. Inflation approximates footprint plus tracking margin; it does not certify swept-volume clearance.

\begin{figure}[t]
\centering\includegraphics[width=\columnwidth]{figure2_kinematic_telemetry.pdf}
\caption{Actual MuJoCo mission telemetry, seed 42. Foot bottom height subtracts the 0.093 m wheel radius. Startup rise, front/rear foot transfer and plateau arrival are distinct events; torque stays bounded. Source: \texttt{demo\_runs/m20\_mission/telemetry.csv}.}
\label{fig:telemetry}
\end{figure}

\subsection{Paired Climb and Safety Acceptance}
A broad connected low terrace supplies a measured lip and height. The robot aligns its yaw, packs the rear stance, lowers/shifts its center of mass, swings the front pair with floating hubs, raises/pulls the torso, shifts over the front pair and swings the rear pair. Each swing transitions only after actual pair re-contact. A plateau-clearance phase precedes restoring the nominal rolling posture, avoiding premature rear-foot drop at the edge.

A verified climb requires both pair liftoffs and re-support, all four foot centers beyond the true lip, plateau-height support and base rise relative to settled standing. Terrain truth is used only by this evaluator. Goal acceptance additionally requires a 0.22 m goal region for 0.4 s, no harmful robot--world contacts, no rollover and no latched tilt stop. Wheel contacts with designated supports are expected; other world contacts are harmful and self-contact is logged separately. Contact auditing runs every 2 ms; telemetry samples every 20 ms.

\clearpage
\section{Experimental Design and Results}
\subsection{Matched Protocol}
Fifty environments each receive two policies on the same complete M20: (i) a delayed reactive goal-seeking software driver with the same standing servo, and (ii) the local mapping/planning/paired-climb executive. The baseline is not participant teleoperation. The shared arm retains local authority despite delayed remote intent, so policy differences include planning and climbing as well as delay handling. No factorial causal separation is claimed.

The locally fixed batch design file fixes ten flat, fifteen climb, fifteen barrier-detour, eight combined-mission and two blocked fixtures. Seeds 1000--1049 vary floor friction (0.75--1.15), step height (0.055--0.085 m), barrier position/width and low rubble. Delays cycle through 0.05, 0.35, 0.8 and 1.2 s. Scenario-specific deadlines are 20--80 simulated seconds. Failed, collided and timed-out trials remain in the dataset; a protected stop is not completed reconnaissance. These seeded fixtures are not samples from an identified industrial terrain distribution.

Each trial saves configuration, source SHA-256, software versions, start/end times, actual pose/velocities, joint states, torques, foot contacts, range/map coverage and decisions. A hub-speed discrepancy is logged as a kinematic slip proxy, not calibrated tire slip. Mechanical work is an absolute torque--velocity integral and does not include electronics or battery efficiency. Development probes and showcase seed 42 are excluded from comparative inference.

\begin{table}[t]
\caption{Measured outcomes: 50 simulations per policy}\label{tab:results}
\centering\begin{tabular}{lrr}\toprule
Metric & Baseline & Shared\\\midrule
Accepted missions & @@BASE@@/50 & @@SHARED@@/50\\
Harmful-contact trials & @@BHC@@ & @@SHC@@\\
Rollover trials & @@BRO@@ & @@SRO@@\\
Goal error, mean (m) & @@BERR@@ & @@SERR@@\\
Goal error, SD (m) & @@BSD@@ & @@SSD@@\\
Duration, mean (s) & @@BTIME@@ & @@STIME@@\\\bottomrule
\end{tabular}
\end{table}

\subsection{Primary Paired Inference}
The primary null is equal paired acceptance probability. There are @@DISB@@ shared-only and @@DISC@@ baseline-only accepted pairs. A two-sided exact McNemar test, evaluated through the discordant-pair binomial distribution, gives $p=@@P@@$. The shared-minus-baseline acceptance difference is @@DIFF@@ percentage points, with paired bootstrap 95\% interval [@@CIL@@, @@CIU@@] percentage points (20,000 resamples; analysis seed 2026). Figure~\ref{fig:comparison} shows actual outcomes and goal-error distributions. The large observed difference applies to this deliberately simpler baseline and selected fixtures.

For continuous final goal error, the paired mean difference is @@ERRDIFF@@ m (difference SD @@ERRSD@@ m), with bootstrap 95\% interval [@@ECIL@@, @@ECIU@@] m. An exploratory paired sensitivity test gives $t(49)=@@T@@$, $p=@@TP@@$, Cohen's $d_z=@@DZ@@$. Shapiro--Wilk $p=@@SHAP@@$ indicates that a normal-difference assumption should be treated cautiously; the Wilcoxon sensitivity result is $p=@@WP@@$. Binary exact inference is primary. Effect size and significance targets were not used to generate outcomes.

\begin{figure}[t]
\centering\includegraphics[width=\columnwidth]{figure3_comparative_performance.pdf}
\caption{Actual MuJoCo benchmark: 50 matched environments, 100 simulations. Bars count strict accepted missions; boxplots include failures. Source: \texttt{benchmark/results.csv}. Error intervals and exact paired inference are reported in text and machine-readable statistics.}
\label{fig:comparison}
\end{figure}

\subsection{Representative Success and Retained Failures}
The combined showcase (seed 42) finishes in @@TIME@@ simulated seconds with @@GOALERR@@ m goal error, an actual 8 cm four-foot ascent, zero harmful contacts, peak absolute roll @@ROLL@@$^\circ$ and pitch @@PITCH@@$^\circ$. A separate twelve-second diagonal-pair walking run advances approximately 0.81 m in x with measurable foot lift; its peak roll is 3.67$^\circ$, so a universal ``below 3$^\circ$'' claim would be false.

Combined-mission seed 1043 reached the goal area but did not verify simultaneous rear-pair liftoff, so it remained a failed mission. All final failed cases are listed in \texttt{failure\_cases.csv}. Development auditing also found an upper rear-leg step contact during transfer; raising the rear-transfer reference by 3 cm corrected the showcased fixture. A longer gait prototype destabilized around 24 s, so the walking claim is deliberately bounded. The baseline may approach or collide with a barrier or stall at a step; arriving near a goal does not erase earlier harmful contacts. Blocked-world stops remain unsuccessful missions even when the protective decision is appropriate.

\clearpage
\section{Operational Interpretation and Limitations}
\subsection{Dimensionless Economics and Human Factors}
The operational model uses illustrative normalized assumptions, independent of simulation acceptance:
\begin{equation}
\kappa=\frac{C_{op}}{V_{reclaimed}},\qquad
T_{payback}=\frac{12C_{capital}}{1-\kappa},\quad\kappa<1.
\end{equation}
For $C_{op}=0.22$, $V_{reclaimed}=1$ and $C_{capital}=0.30$, the illustrative payback is 4.615 months. An assumed 312 reclaimed annual hours corresponds to $312/2080=0.15$ FTE. These inputs were not measured at a plant, and a successful robot simulation does not establish reclaimed labor. At $\kappa\geq1$ there is no finite positive payback under this model; invalid/nonfinite denominators are rejected. Sensitivity outputs accompany the code.

Software interventions are controller events, not NASA-TLX or human risk measurements. A workload study needs a participant protocol, valid scales and counterbalancing. We make no measured human-workload claim.

\subsection{Threats to Validity}
First, sensing and pose are ideal. Range noise, dropout, motion distortion, dust, reflective surfaces, pose drift and map uncertainty are absent. Front RGB/depth panels visualize a simulated camera but do not contribute to control; there is no camera--LiDAR fusion. Geometry-group self exclusion is an oracle property of this simulation. A hardware system would require calibrated sensing and self-filtering under uncertainty.

Second, original mesh appearance and XML inertias do not identify physical hardware. Primitive collisions, a rigid low platform and seeded rubble do not model compliant tires, actuator electrical dynamics, backlash, battery depletion or loose debris. The force allocator clips an approximate friction box without solving a constrained contact optimization. Its successful finite tests are not a proof of global stability. The slope fixture is exploratory and excluded from the primary batch.

Third, the simple baseline and bundled autonomous features favor an integration-level comparison. The study does not establish that an expert human, a tuned wheel-only controller or modern learned locomotion would perform similarly. Future ablations should independently remove planning, paired transfers and delay protection, and evaluate held-out terrain distributions and sustained gait. A 50-pair interval concerns the chosen mixture, not arbitrary industrial missions.

Fourth, ``unknown terrain'' means the local controller receives no preloaded map, while the simulator and evaluator necessarily know geometry. Step detection assumes a broad low terrace roughly aligned with the world x direction. Post-detour heading alignment and a larger barrier-to-step gap make that fixture feasible for the M20 body shift. These design constraints must accompany any replication; the algorithm is not a general stair or rubble-climbing solution.

\section{Reproducibility and Conclusion}
CPython 3.12.14, MuJoCo 3.11.0 and pinned numerical/plotting dependencies were used. The submission contains original M20 assets, tests, source hashes, every benchmark trace, failure records, analysis scripts and this editable manuscript. Running \texttt{analytics/run\_benchmark.py} executes physics; \texttt{analyze\_benchmark.py} and \texttt{generate\_paper\_figures.py} derive the statistics and plots from those logs. CSV timestamps represent simulated time, independent of wall-clock rendering speed.

@@COURSE_EXTENSION@@

The verified result is a mesh-preserving M20 quadruped pipeline that can map, detour, align and execute paired low-step transfer in the tested simulation. Its observed comparative improvement is conditional on ideal sensing, a simple software-driver baseline and small fixed scenario families. Physical deployment, robust perception, sustained locomotion, human workload and independent validation remain future work. SI x-forward/y-left/z-up conventions are used; no ISO certification or running ROS transform system is claimed.

\paragraph{Provenance and review} The supplied mechanical model is not claimed as original CAD work. Substantial AI assistance was used for implementation, experiments and drafting. Names identify the course team, not verified individual authorship of generated code. Genuine student review, commits, expert demonstration and individual viva are pending human actions. No contributions, publication acceptance or public posting have been fabricated.

\begin{thebibliography}{6}
\bibitem{fankhauser} P. Fankhauser, M. Bloesch, and M. Hutter, ``Probabilistic terrain mapping for mobile robots with uncertain localization,'' \emph{IEEE Robot. Autom. Lett.}, 2018, doi: \url{10.1109/LRA.2018.2849506}.
\bibitem{dicarlo} J. Di Carlo, P. M. Wensing, B. Katz, G. Bledt, and S. Kim, ``Dynamic locomotion in the MIT Cheetah 3 through convex model-predictive control,'' in \emph{IROS}, 2018, doi: \url{10.1109/IROS.2018.8594448}.
\bibitem{miki} T. Miki \emph{et al.}, ``Learning robust perceptive locomotion for quadrupedal robots in the wild,'' \emph{Science Robotics}, vol. 7, eabk2822, 2022, doi: \url{10.1126/scirobotics.abk2822}.
\bibitem{lee} J. Lee \emph{et al.}, ``Learning robust autonomous navigation and locomotion for wheeled-legged robots,'' \emph{Science Robotics}, vol. 9, eadi9641, 2024, doi: \url{10.1126/scirobotics.adi9641}.
\bibitem{chen} J. Y. C. Chen, E. C. Haas, and M. J. Barnes, ``Human performance issues and user interface design for teleoperated robots,'' \emph{IEEE Trans. Syst. Man Cybern. C}, 2007, doi: \url{10.1109/TSMCC.2007.905819}.
\bibitem{mujoco} E. Todorov, T. Erez, and Y. Tassa, ``MuJoCo: A physics engine for model-based control,'' in \emph{IROS}, 2012, doi: \url{10.1109/IROS.2012.6386109}.
\end{thebibliography}
\end{document}
'''

def main():
    st=json.loads((HERE/'benchmark/statistics.json').read_text());d=json.loads((HERE/'demo_runs/m20_mission/summary.json').read_text())
    b=st['policies']['baseline'];s=st['policies']['shared'];t=st['exploratory_paired_t']
    vals={'BASE':b['accepted'],'SHARED':s['accepted'],'P':f'{st["exact_McNemar_p"]:.6g}',
      'TIME':f'{d["simulated_s"]:.2f}','GOALERR':f'{d["goal_error_m"]:.3f}','ROLL':f'{d["max_abs_roll_deg"]:.2f}','PITCH':f'{d["max_abs_pitch_deg"]:.2f}',
      'BHC':b['harmful_contact_trials'],'SHC':s['harmful_contact_trials'],'BRO':b['rollovers'],'SRO':s['rollovers'],
      'BERR':f'{b["goal_error_m"]["mean"]:.3f}','SERR':f'{s["goal_error_m"]["mean"]:.3f}',
      'BSD':f'{b["goal_error_m"]["sd"]:.3f}','SSD':f'{s["goal_error_m"]["sd"]:.3f}',
      'BTIME':f'{b["simulated_s"]["mean"]:.2f}','STIME':f'{s["simulated_s"]["mean"]:.2f}',
      'DISB':st['shared_only_accepted'],'DISC':st['baseline_only_accepted'],
      'DIFF':f'{st["acceptance_difference_shared_minus_baseline"]*100:.1f}',
      'CIL':f'{st["acceptance_difference_bootstrap_CI95"][0]*100:.1f}','CIU':f'{st["acceptance_difference_bootstrap_CI95"][1]*100:.1f}',
      'ERRDIFF':f'{st["goal_error_difference_m"]:.3f}','ERRSD':f'{st["goal_error_difference_sd_m"]:.3f}',
      'ECIL':f'{st["goal_error_difference_bootstrap_CI95_m"][0]:.3f}','ECIU':f'{st["goal_error_difference_bootstrap_CI95_m"][1]:.3f}',
      'T':f'{t["statistic"]:.3f}','TP':f'{t["p_value"]:.6g}','DZ':f'{t["cohen_dz"]:.3f}',
      'SHAP':f'{t["shapiro_p"]:.6g}','WP':f'{st["exploratory_Wilcoxon"]["p_value"]:.6g}'}
    for k in ('P','TP','SHAP','WP'):
        value=vals[k]
        if 'e' in value:
            mantissa,exponent=value.split('e');vals[k]=mantissa+r'\times10^{'+str(int(exponent))+'}'
    course=json.loads((HERE/'obstacle_course/statistics.json').read_text())
    combined=json.loads((HERE/'climbing_course/statistics.json').read_text())
    checks=[r for r in combined['combined_climbing'] if r['policy']=='shared']
    passed=sum(r['accepted'] for r in checks)
    vals['COURSE_EXTENSION']=(r'\paragraph{Expanded course check} A separate extension uses a 5 cm grid, twenty physical hazard/boundary geometries and two successive 8 cm terrace rises. Twelve matched avoidance seeds give '
        +str(course['policies']['shared']['accepted'])+r'/12 accepted for map-based control versus '+str(course['policies']['baseline']['accepted'])
        +r'/12 for the delayed software baseline. The combined detour-and-two-climb course accepts '+str(passed)+'/'+str(len(checks))
        +r' shared-controller seed checks. These selected extension trials are not pooled with the original fifty pairs; raw failures and version-specific source snapshots are retained.')
    text=TEMPLATE
    for k,v in vals.items():text=text.replace('@@'+k+'@@',str(v))
    if '@@' in text:raise ValueError('Unfilled paper variable')
    (PAPER/'Group09_HazardousTerrain_IEEE.tex').write_text(text,encoding='utf-8')
    (PAPER/'main.tex').write_text('\\input{Group09_HazardousTerrain_IEEE.tex}\n',encoding='utf-8')
    print('Paper populated from actual benchmark statistics.')

if __name__=='__main__':
    from build_capstone_paper import main as current_main
    current_main()
