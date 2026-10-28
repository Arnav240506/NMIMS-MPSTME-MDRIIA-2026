"""Update the existing IEEE manuscript with the final independent experiment."""
from pathlib import Path
import json,re
from build_paper import TEMPLATE
HERE=Path(__file__).resolve().parent;OUT=HERE.parent/'docs/paper'
def main():
    s=json.loads((HERE/'capstone_500hz/statistics.json').read_text());c=s['comparisons'];v=json.loads((HERE/'capstone_500hz/verification.json').read_text());hero=json.loads((HERE/'capstone_checks/pilot_42/summary.json').read_text())
    text=TEMPLATE
    for old,new in [('70362400017','70362400067'),('70362400063','70362400086'),('70362400033','70362300032')]:text=text.replace(old,new)
    abstract=r'''Hazardous-terrain reconnaissance requires mobility and sensing to work together. We preserve the supplied M20 hybrid canine quadruped with four articulated legs, sixteen motors and seventeen meshes. Ideal rays build a true-pose-referenced terrain grid; A* navigation and contact-gated paired-leg transfer negotiate three alternating barriers and two 8 cm terrace rises. A predeclared independent experiment uses thirty trials per policy across three low-roughness strata. The integrated policy accepts 30/30 missions with both climbs and zero harmful contacts; a delayed reactive software driver accepts 0/30. Terminal goal error is 0.1064 versus 12.3103 m, with proposed-minus-baseline Welch 95% interval $[-12.2388,-12.1691]$ m. Actual 500 Hz logs contain 4,495,972 samples, independently checked against summaries. Dimensionless payback and queue models use explicitly assumed business inputs, with a separate measured-duration capacity scenario. The large comparative separation reflects a weak baseline on this fixture; it does not establish field safety, expert-operator superiority or human workload reduction.'''
    abstract=abstract.replace('%',chr(92)+'%')
    text=re.sub(r'\\begin\{abstract\}.*?\\end\{abstract\}',lambda m:'\\begin{abstract}\n'+abstract+'\n\\end{abstract}',text,flags=re.S)
    text=text.replace('figure1_system_architecture.pdf','capstone_system_architecture.pdf')
    text=text.replace('The industrial-yard fixture includes a low concrete platform, 25 cm barrier, low rubble and storage tank with collisions. Warehouse walls and markings are decorative. Toxic gas, structural collapse and disaster-field mechanics are not simulated.','The industrial-yard fixture includes three alternating tall barriers, cylinders, crates, boundary geometry, low rubble and two successive 8 cm concrete terrace rises. Toxic gas, structural collapse, moving hazards and loose-debris mechanics are not simulated.')
    text=text.replace('Grid / obstacle inflation & 0.03 / 0.70 m','Dense-course grid / inflation & 0.05 / 0.70 m')
    text=text.replace('Contact auditing runs every 2 ms; telemetry samples every 20 ms.','Contact auditing and scientific CSV logging run every 2 ms. Separate 20 ms state snapshots support replay and foot-force diagnostics.')
    text=text.replace('figure2_kinematic_telemetry.pdf','capstone_climb_telemetry.pdf')
    text=text.replace('Actual MuJoCo mission telemetry, seed 42. Foot bottom height subtracts the 0.093 m wheel radius. Startup rise, front/rear foot transfer and plateau arrival are distinct events; torque stays bounded. Source: \\texttt{demo\\_runs/m20\\_mission/telemetry.csv}.','Actual two-climb seed-42 telemetry. Foot-bottom height subtracts the 0.093 m wheel radius; startup and two transfers are distinct. This diagnostic figure uses the 50 Hz replay channel; scientific effort uses actual 500 Hz torques.')
    results=r'''\section{Experimental Design and Results}
\subsection{Independent Predeclared Protocol}
Thirty independent trials per policy compare a delayed reactive software driver with the integrated map-and-transfer executive on the same M20. The baseline has the same standing/rolling actuation but no mapper or paired climb logic. It is neither participant teleoperation nor a comparable modern planner. Policy differences bundle mapping, navigation and transfer; this is an integration comparison, not a causal single-feature ablation.

Seeds 31000--31029 and 32000--32029 are disjoint. Each arm has ten runs at each roughness bound 0, 3 and 6 mm. Nonzero rubble heights follow $U(b/2,b)$; floor friction is $U(0.75,1.15)$, barrier displacement is within $\pm0.08$ m, initial lateral position within $\pm0.02$ m and yaw within $\pm0.02$ rad. Assumed delay is 0.35 s; timeout is 180 simulated seconds. Design and source hashes were saved before execution. No outcome was sampled from a target distribution or discarded.

Every 2 ms, actual pose, velocity, sixteen torques, reference/error, FSM and contact events are saved to bounded CSV parts. A fixed evaluator-only A* polyline, computed identically for either policy from the fixture geometry, is never fed to the controller. After 2.4 s startup, nearest-segment XY error defines cross-track RMSE. This differs from timed trajectory tracking. Effort is $E=\sum_t\sum_j\tau_j^2\Delta t$; it is not energy. Unequal durations and failures affect both metrics.

\begin{table}[t]
\caption{Actual final-course outcomes, 30 runs per policy}
\centering\begin{tabular}{lrr}\toprule
Metric & Baseline & Proposed\\\midrule
Accepted / harmful-contact trials & 0 / 30 & 30 / 0\\
Rollovers & 0 & 0\\
Goal error mean (m) & 12.3103 & 0.1064\\
Goal error SD (m) & 0.0931 & 0.0082\\
Cross-track RMSE mean (m) & 0.5811 & 0.1947\\
Effort mean ($10^6$ N$^2$m$^2$s) & 1.1284 & 0.5556\\
Duration mean (s) & 180.000 & @@DURATION@@\\\bottomrule
\end{tabular}\end{table}

\subsection{Primary Inference and Interpretation}
The predeclared null is equality of mean terminal XY goal error. Independent Welch inference gives $t=-715.183$, $\nu=29.446$, $p=5.5115\times10^{-64}$. The mean difference (proposed minus baseline) is $-12.20396$ m, with 95\% interval $[-12.23884,-12.16908]$ m. Pooled-SD Cohen $d=-184.659$ is reported separately from the Welch standard error. Mann--Whitney sensitivity gives $p=3.0199\times10^{-11}$.

The enormous standardized difference arises because every baseline run stalls near the first barrier with little variability. It supports successful integration on these tasks, not general superiority or population reliability of one. Each roughness stratum has 10/10 proposed acceptance and 0/10 baseline acceptance. All baseline contacts/timeouts remain in the dataset. No normality or hardware claim follows from a small p-value.

\begin{figure}[t]\centering
\includegraphics[width=\columnwidth]{capstone_results_paper.pdf}
\caption{Measured seed-32000 route against its fixed evaluator reference, and terminal errors for all sixty runs. Both failures and successes are retained.}\label{fig:comparison}
\end{figure}

\subsection{Reproduction and Failure Evidence}
The independent audit checks 4,495,972 samples in 254 CSV parts: SHA256, continuous 2 ms timing, run IDs/seeds, effort, RMSE, contacts, terminal distance and both pair-lift/re-support gates. Seed 42 completes both rises in 121.394 simulated seconds, with 0.107744 m goal error and no harmful contacts. Default physical states remain bitwise identical after the logger migration. Earlier 100-run, 26-run and seven-run studies remain separate, with their own protocols and source hashes.
'''
    results=results.replace('@@DURATION@@',f'{c["simulated_s"]["proposed_mean"]:.3f}')
    start=text.index('\\section{Experimental Design and Results}');end=text.index('\\clearpage',start)
    text=text[:start]+results+'\n'+text[end:]
    econ=r'''\subsection{Dimensionless Economics and Human Factors}
All economic inputs are uncalibrated planning assumptions. With annual baseline $V=1$, operating parity $O=0.22$, capital $K=0.30$ in annual-baseline units and life $L=5$ years,
\begin{equation}
\begin{gathered}
\kappa=O/V,\qquad\mathrm{NCRI}=1-\kappa,\\
P=\frac{K}{L(V-O)},\qquad T=\frac{12K}{V-O}.
\end{gathered}
\end{equation}
Thus NCRI is 0.78, lifetime payback fraction is 0.076923 and payback is 4.615 months. Assumed 312 reclaimed hours/year gives 0.15 FTE at 2080 h/year. Scaling all cost terms equally preserves these ratios. At $V\le O$, no positive savings payback is reported; within-life break-even is $\kappa=0.94$ for the stated capital/life.

An assumed M/M/1 queue with $\lambda=8$/week, $\mu=12$/week and 40 working hours/week has $\rho=2/3$ and $W_q=\lambda/[\mu(\mu-\lambda)]=6.667$ working hours. Erlang C supports M/M/c; $\rho\ge1$ returns no finite steady-state delay. Poisson arrivals, exponential service and independence are assumptions, not observed plant processes.

A separate bridge uses actual simulation attempt duration and acceptance fraction $p$ with assumed inspection/reset overhead $h$: $\mu_{eff}=40p/(h+t/3600)$. Varying $h=1.5,3,4.5$ hours exposes the dominance of unmeasured operational work. Baseline zero accepted service yields zero scenario capacity. No NASA-TLX, bandwidth saving or observed labor benefit is inferred from motion.

'''
    start=text.index('\\subsection{Dimensionless Economics');end=text.index('\\subsection{Threats to Validity}',start);text=text[:start]+econ+text[end:]
    start=text.index('\\subsection{Threats to Validity}');end=text.index('\\section{Reproducibility',start)
    limits=r'''\subsection{Threats to Validity}
Sensing and pose are ideal: range noise, dropout, reflective surfaces and localization drift are absent. Simulated RGB/depth panels are observational, not camera--LiDAR fusion. Robot self-exclusion uses known geometry groups. Hardware would require calibrated sensing and uncertainty-aware filtering.

Supplied meshes/inertias do not identify real hardware. Primitive collisions and rigid terraces omit tire compliance, electrical actuator dynamics, backlash, batteries and loose debris. The clipped instantaneous force allocator is not a constrained optimum. A short earlier walking check does not prove sustained braked-foot gait.

The weak reactive baseline lacks mapping and climbing. Stronger baselines and factorial ablations are required to attribute causal benefit. Thirty runs per arm in three mild roughness strata do not sample arbitrary industrial environments. Unknown terrain means no preloaded controller map; the evaluator knows fixture geometry. Terrace detection assumes broad, low steps aligned roughly with world x. No human-workload or standards-conformity claim is made.

'''
    text=text[:start]+limits+text[end:]
    text=text.replace('A 50-pair interval concerns the chosen mixture, not arbitrary industrial missions.','The independent interval concerns this fixture distribution, not arbitrary industrial missions.')
    text=text.replace('\\texttt{analytics/run\\_benchmark.py}','\\texttt{analytics/run\\_capstone\\_benchmark.py}').replace('\\texttt{analyze\\_benchmark.py}','\\texttt{analyze\\_capstone.py}').replace('\\texttt{generate\\_paper\\_figures.py}','\\texttt{plot\\_capstone.py}')
    text=text.replace('@@COURSE_EXTENSION@@','')
    text=text.replace('A low platform.','Two low terraces.')
    assert '@@' not in text
    (OUT/'Group09_HazardousTerrain_IEEE.tex').write_text(text,encoding='utf-8')
    (OUT/'main.tex').write_text('\\input{Group09_HazardousTerrain_IEEE.tex}\n',encoding='utf-8')
    print('Final independent-study manuscript generated.')
if __name__=='__main__':main()
