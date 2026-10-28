# LinkedIn video: script and cues (Group 08 SkyHydro, 3:45)

Recorded with every member's webcam on over a silent Full HD background video of our MuJoCo simulation and graphs (links in the [README](../README.md#videos)). Each member speaks once, in order. Numbers come from `analytics/trial_stats.json` and `analytics/business_results.json`.

| Video time | Speaker | On screen |
|---|---|---|
| 0:00–1:08 | Manikya Rathore | Flood valley, survey scan with the blue camera beam, trained RL pilot delivering to roofs |
| 1:08–1:45 | Shourya Garg | Vision-guided drop controller (10 m/s crosswind), FSM state at the top |
| 1:45–2:40 | Keswani Laksh | Baseline GPS drop misses at 15 m/s, battery-reserve ABORT (`--battery-soc 0.27`), box plot, trajectory plot |
| 2:40–3:35 | Vora Jash | Business sensitivity graph, M/M/c queue graph |
| 3:35–3:45 | none | Team names and repository link |

## 1. Manikya Rathore (E056), 0:00–1:08

"Hello, we are Group 08, and our project is SkyHydro. On average, floods affect about 3.2 crore people in India every year. When a village is cut off, medicine can take hours to arrive by boat. So we asked two questions. Can a drone drop medicine accurately in strong wind? And can a small drone fleet pay for itself compared to boats?

This is our flood valley, built in the MuJoCo physics simulator. First, the drone flies over every house. The blue beam is its camera, checking each roof for survivors. Then our reinforcement learning pilot takes over. It picks up medicine from the warehouse on the hill and drops it on each roof. It completed 30 out of 30 missions, about twice as fast as the pilot we programmed by hand.

I built the simulation, the valley and the RL pilot. One thing AI got wrong: it said GPU training would be much faster, but the physics runs on the CPU, so the GPU stayed at about 20 percent."

## 2. Shourya Garg (E020), 1:08–1:45

"Now let's look at the drop itself. The text at the top shows each step: take off, fly, hover, lower the cable, and release. The wind makes the canister swing, so the camera tracks the canister, not the drone. The drone moves until the canister is above the roof, and lets go only when the swinging has settled.

I worked on this flight logic and the camera-guided release. AI's first design made the drone wobble in strong wind. We saw it in the simulation and replaced it with a slower, steadier correction."

## 3. Keswani Laksh (E032), 1:45–2:40

"For comparison, this drop uses GPS only. In strong wind, the canister swings away and falls into the water. This next clip shows a safety feature: when the battery gets too low, the drone cancels the delivery and flies back.

To test this properly, we ran 240 simulations, with wind up to 15 metres per second and canisters from 1 to 3 kilograms. With our controller, the average miss distance fell from 2.82 metres to just 0.31 metres. A Welch's t-test shows this is not chance, with p below 0.001. Unsafe drops fell from 34 percent to under 1 percent.

I ran the trials and the statistics. AI's setup script started 23 processes at once, and the lab PC ran out of memory. We limited it to 8."

## 4. Vora Jash (E067), 2:40–3:35

"Now the business side. Instead of rupees, we compare every cost with running one rescue boat for one hour. One urgent drone delivery costs under 4 percent of a boat trip. A drone earns back its cost in about three months. Our inputs are assumptions, so this graph tests them, and the drone stays cheaper unless it costs over 3,600 boat-hours. In waiting time, two drones answer a request in about 34 minutes, while four boats take about 222 minutes.

I built the business model. AI claimed drones are 85 percent faster, but gave no source. So we calculated it from our own model. It also came out at 85 percent, but now it's backed by our own numbers. Thank you."

## Where each number comes from

| Spoken | Source |
|---|---|
| 3.2 crore people affected per year | CWC state-wise flood damage statistics 1953–2016: 31.88 million/yr (dossier §1.1) |
| 30/30 missions, about 2× faster (150 s vs 309 s) | `analytics/rl_pilot_real_trials.csv` |
| 2.82 m → 0.31 m, p < 0.001 (t = 7.35, d = 0.98) | `analytics/trial_stats.json`, `tests.radial_error_m` |
| Unsafe drops 34 % → under 1 % | `trial_stats.json`, `baseline_unsafe_drop_rate` / `proposed_unsafe_drop_rate` |
| Under 4 % of a boat trip | κ = 0.036, `business_results.json` |
| Pays back in about three months | T_payback = 3.0 months, P_payback = 0.08 |
| Break-even over 3,600 boat-hours per drone | `break_even` = 3,644 |
| 34 min vs 222 min to answer a request | `latency_uav_min` / `latency_boat_min` (M/M/c wait + outbound leg) |
| 85 % faster | `latency_reduction` = 0.848 |
