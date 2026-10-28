# HISTORICAL REVISION SHEET: numerical study summaries below describe earlier experiments. For the final 60 independent runs, 500 Hz telemetry, Welch inference and business model, use VIVA_QA_BY_STUDENT.md and M20_Complete_Step_by_Step_Run_Guide.pdf. Do not quote earlier paired statistics as final capstone results.

# Arnav Saurabh Surve (E064) — quick revision

Explain in your own words; do not claim unverified authorship.

- **Why is this an M20 dog rather than a car?** It has four multi-joint legs from the supplied M20 chain, 12 leg motors and four wheeled feet.
- **How many degrees of freedom are present?** There are 16 actuated joints plus a free floating base: nq=23 because the base quaternion uses four numbers; nv=22 because base rotation has three velocities..
- **What is the actual mass?** Summing the supplied XML inertias gives 34.525856 kg.
- **How does inverse kinematics work?** The two 0.25 m links use cos(knee)=(x²+z_leg²-l1²-l2²)/(2*l1*l2).
- **What torques are applied?** PD joint error, bias compensation and stance-Jacobian terms are combined, then leg torques are clipped to ±76.4 N m and hubs to ±21.6 N m.
- **Is the balance controller MPC?** No.
- **Why climb with front and rear pairs?** This follows the README strategy: lower and shift the CoM over the support pair, lift the other pair with floating wheels, plant it, move the torso and then lift the rear pair.
- **How do you prove an actual climb?** Measure from settled standing, require actual front/rear liftoff and re-support, then all four feet beyond the true lip, at plateau height, with support contacts.
- **What was the contact bug?** A rear upper-leg collision touched the step during rear transfer.
- **How is slip measured?** The logged proxy compares hub speed times wheel radius against body longitudinal speed, normalized by at least 0.10 m/s.
- **How does skid steering turn?** uL=v-w*b/2, uR=v+w*b/2, with effective track 0.55 m.
- **Can the dog walk indefinitely?** The supplied evidence verifies a 12-second diagonal-pair demonstration.
