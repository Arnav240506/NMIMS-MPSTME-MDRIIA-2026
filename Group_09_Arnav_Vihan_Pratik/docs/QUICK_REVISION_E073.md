# HISTORICAL REVISION SHEET: numerical study summaries below describe earlier experiments. For the final 60 independent runs, 500 Hz telemetry, Welch inference and business model, use VIVA_QA_BY_STUDENT.md and M20_Complete_Step_by_Step_Run_Guide.pdf. Do not quote earlier paired statistics as final capstone results.

# Pratik Mangesh Gaikwad (E073) — quick revision

Explain in your own words; do not claim unverified authorship.

- **What is the actual baseline?** A deterministic delayed reactive software driver on the same M20 standing servo.
- **How is latency simulated?** Commands are timestamped with release time t+delay and queued FIFO.
- **Does shared autonomy experience the same delay?** The remote intent channel is delayed, but the local shared planner retains control authority.
- **How many experiments were actually run?** There are 50 matched environments and two policies, totaling 100 actual physics simulations.
- **Why use matched pairs?** Both policies receive the same seed and scenario, reducing environmental variation in policy differences.
- **What is the primary hypothesis test?** Acceptance is binary.
- **What does d_z mean?** For continuous paired goal-error differences, d_z=mean(difference)/SD(difference).
- **What does the 95% interval describe?** The bootstrap resamples matched differences, not individual unpaired rows.
- **Did operator workload decrease by 64%?** No human workload was measured.
- **What is dimensionless cost parity?** kappa=robot operating parity/reclaimed-value parity.
- **How are payback and FTE calculated?** Payback months=12*capital parity/(1-kappa) only when kappa<1.
- **What still requires genuine team action?** Each student must review, rerun, understand and personally commit their own changes, demonstrate to the panel and defend the viva.
