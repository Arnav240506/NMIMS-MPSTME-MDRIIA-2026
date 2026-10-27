> Historical implementation/evidence note. For the current independent 500 Hz study and final package, use CAPSTONE_VERIFICATION_REPORT.md and the current run guide. Do not pool these protocols.

# Retained failures and their meaning

The final matched benchmark has 40 baseline failures and three shared failures. None were removed or recoded as successes. Full outcomes are in analytics/benchmark/failure_cases.csv.

- Baseline: 15 low-step cases did not satisfy verified paired ascent; all 15 barrier-detour cases failed strict safety acceptance, including four that reached the goal only after harmful contact; eight combined missions timed out; both blocked fixtures failed completion.
- Shared seed 1043, combined mission: final goal error 0.053372 m, no harmful contacts, but rear_pair_air=false. The low step was 0.0580619 m. The robot reached the goal area without establishing the required simultaneous rear-pair liftoff; climb_verified remained false and the 80 s deadline expired. Physical arrival is therefore not accepted as a verified paired-climb mission. A better contact-transfer trajectory and per-foot timing diagnosis are future improvements. Do not loosen the predicate after viewing the result.
- Shared seeds 1048 and 1049: map/planner stopped at a barrier spanning the mapped domain. This is protective behavior, but neither mission reached its goal.
- Development-only: rear upper-leg contact against the 8 cm step was detected (20 harmful timesteps in the climb fixture; 72 in the combined fixture). Raising the rear transfer body reference by 3 cm removed those contacts in the frozen showcase and batch. Those earlier files remain labeled development runs, outside comparative statistics.
- Development-only: a longer diagonal-pair walk destabilized near 24 s. The delivered walking claim is limited to the measured 12 s demonstration, with peak roll about 3.67 degrees. No indefinite walking guarantee is claimed.

failure_baseline_contact.png and failure_shared_pair_liftoff.png show actual recorded physics states, with selected sample/time receipts in analytics/failure_frame_receipts.json. A still image alone cannot prove the full event; use states.npz, telemetry.csv and summary.json for verification.

Independent smoke execution also completed six actual simulations on three paired cases. Baseline accepted 1/3 and shared 2/3; the shared low-step seed 1001 failed the strict ascent predicate and timed out. These extra cases are excluded from primary benchmark statistics and reinforce the stated limits of the contact-transfer trajectory.
