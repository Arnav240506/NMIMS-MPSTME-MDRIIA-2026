# HISTORICAL REVISION SHEET: numerical study summaries below describe earlier experiments. For the final 60 independent runs, 500 Hz telemetry, Welch inference and business model, use VIVA_QA_BY_STUDENT.md and M20_Complete_Step_by_Step_Run_Guide.pdf. Do not quote earlier paired statistics as final capstone results.

# Vihan Shripad Joshi (E070) — quick revision

Explain in your own words; do not claim unverified authorship.

- **Where do map heights come from?** From native MuJoCo multi-ray intersections with actual environment geometry.
- **What is 2.5D mapping?** Each x-y cell stores measured elevation statistics rather than a full volume.
- **Is this SLAM?** No.
- **What is the real map update rate?** Rays are integrated at 50 Hz in 16 interleaved groups.
- **How do cells aggregate samples?** The mapper stores count, sum, squared sum, mean and peak.
- **How is cost calculated?** c=0.4 clip(slope/30deg)+0.3 clip(roughness/0.04m)+0.3 clip(step/0.14m).
- **How is the robot removed from its own scan?** Geometry groups exclude robot collisions/visual meshes while retaining environmental obstacles.
- **How does A* choose a route?** Eight-neighbor edges cost distance times a risk weight.
- **Why inflate obstacles by 0.70 m?** The planned center must leave room for the robot footprint and extra tracking/slip margin.
- **What happens if no route exists?** Try reachable measured frontiers; otherwise command zero rather than guessing forward through unknown terrain.
- **How is the curb located?** Broad connected measured cells above 3.5 cm and below 14 cm indicate a low terrace.
- **Do RGB/depth cameras control the robot?** Their rendered panels are for observation.
