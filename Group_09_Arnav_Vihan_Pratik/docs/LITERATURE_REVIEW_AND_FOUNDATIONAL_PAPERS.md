# Verified literature and scope

DOI titles/authors were checked against publisher-deposited Crossref metadata. The raw responses and metadata receipt are in bibliography/. Some existing source records were reused from the earlier citation audit; new quadruped sources were fetched for this correction. The DOI resolver and author pages were also checked for the three legged-robot papers. This is bibliographic verification, not a claim to have reproduced those systems.

| DOI | Actual title | Relevance / boundary |
|---|---|---|
| [10.1109/LRA.2018.2849506](https://doi.org/10.1109/LRA.2018.2849506) | Probabilistic Terrain Mapping for Mobile Robots With Uncertain Localization | Elevation mapping with uncertain localization. Our mapper uses exact pose and is simpler/nonprobabilistic. |
| [10.1109/IROS.2009.5354535](https://doi.org/10.1109/IROS.2009.5354535) | Stereo camera based navigation of mobile robots on rough terrain | Background only; not an implementation claim. |
| [10.1177/0278364906065543](https://doi.org/10.1177/0278364906065543) | Toward Reliable Off Road Autonomous Vehicles Operating in Challenging Environments | Background only; not an implementation claim. |
| [10.1109/TSMCC.2007.905819](https://doi.org/10.1109/TSMCC.2007.905819) | Human Performance Issues and User Interface Design for Teleoperated Robots | Teleoperation interface/workload motivation; no participants measured here. |
| [10.1109/TSMCB.2003.811794](https://doi.org/10.1109/TSMCB.2003.811794) | Human-robot interactions during the robot-assisted urban search and rescue response at the World Trade Center | Background only; not an implementation claim. |
| [10.1002/rob.21856](https://doi.org/10.1002/rob.21856) | Algorithms and experiments on routing of unmanned aerial vehicles with mobile recharging stations | Original source title was incorrect. This DOI is UAV routing with mobile recharging stations, not emergency ground reconnaissance; excluded from core paper. |
| [10.1109/IROS.2018.8594448](https://doi.org/10.1109/IROS.2018.8594448) | Dynamic Locomotion in the MIT Cheetah 3 Through Convex Model-Predictive Control | Quadruped force-control background. Our instantaneous least-squares allocation is not this paper’s MPC. |
| [10.1126/scirobotics.abk2822](https://doi.org/10.1126/scirobotics.abk2822) | Learning robust perceptive locomotion for quadrupedal robots in the wild | Perceptive locomotion and perception failure motivation. No learned attention encoder or real-world reproduction here. |
| [10.1126/scirobotics.adi9641](https://doi.org/10.1126/scirobotics.adi9641) | Learning robust autonomous navigation and locomotion for wheeled-legged robots | Direct wheeled-legged navigation context. Our hand-designed FSM is not the paper’s learned hierarchical policy. |
| [10.1109/IROS.2012.6386109](https://doi.org/10.1109/IROS.2012.6386109) | MuJoCo: A physics engine for model-based control | Background only; not an implementation claim. |

Research gap addressed locally: reproducible M20 mesh-preserving ray-map-to-paired-climb integration, explicit physical acceptance and retained failures. This is an educational integration study, not a state-of-the-art locomotion contribution.
