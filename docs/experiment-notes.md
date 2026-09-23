# NumericJev continuous-control experiments

[Interactive recordings](./) · [All measurements](results.json) · [Data format](control-data-format.md) · [Runner source snapshots](evidence/control/runner-sources.tar.gz)

These are 26 exploratory Jev rollouts across four environments, including prompt-development failures. No policy was trained. The model receives structured state and explicit control guidance. It does not receive gameplay images. Counts across different prompts, seeds, and stopping rules are descriptive, not estimated success rates.

## Where NumericJev is used

Every action component is decoded by asking Jev which numeric interval to retain, then repeating until one grid point remains. Python executes the selected lower endpoint. All components are batched into one request at each tree level. There is no fallback controller or programmatic replacement of selected actions.

CarRacing decodes steering and a signed pedal value. The latter maps to throttle if positive and brake if negative. LunarLander decodes two engine commands; MountainCar decodes motor force; BipedalWalker decodes four joint commands. The shared numeric range is `[-1,1)`, so the upper bound itself is not available.

## K and resolution: fixed-track comparison

All four conditions used seed 7, forward option order, the same recovery-policy instructions, and a 180-second simulation horizon. The former 10-second no-new-tile guard was disabled in **all four** conditions. Thus this comparison does not confound K with that guard, but earlier runs used a different stopping rule.

| K | Grid spacing | Requests/action | Track covered | End | Sim. seconds | API calls | Mean action latency |
|---:|---:|---:|---:|---|---:|---:|---:|
| 10 | 0.020 | 2 | 99.69% | Time limit | 180.00 | 1,800 | 0.507 s |
| 20 | 0.020 | 2 | 97.18% | Time limit | 180.00 | 1,800 | 0.510 s |
| 10 | 0.005 | 3 | **100%** | **Lap finished** | **127.32** | 1,911 | 0.756 s |
| 20 | 0.005 | 2 | 94.36% | Time limit | 180.00 | 1,800 | 0.543 s |

The finer K=10 rollout completed this track; increasing K did not improve these individual runs. One rollout per setting cannot establish a general causal effect or reliability estimate. The 0.005 spacing gives 400 values per component, compared with 100 at 0.02. Representational precision does not guarantee a good control decision.

At 99.69% the coarser K=10 car had missed one track tile, rather than merely lacking decimal precision in a completion counter. Completion still required the environment's actual `lap_finished` signal. Neither the environment nor the success criterion was changed to label that run successful.

## All environments

| Environment | Recorded outcomes | Featured recording |
|---|---|---|
| CarRacing-v3 | 2 completed, 12 incomplete across four experiment stages | Seed 7, K=10, spacing 0.005; 100% coverage |
| LunarLander-v3, continuous | 8 unsuccessful: four prompt versions × two seeds | Latest prompt, seed 7; crash |
| MountainCarContinuous-v0 | Both seeds reached the goal | Seed 7; reward 91.72 |
| BipedalWalker-v3, normal terrain | Both seeds fell | Seed 7; reward −115.31 |

The CarRacing player deliberately features a completed run. For the three additional games the player uses seed 7 of the latest attempted prompt. The expandable ledger retains every episode and its full video, including unsuccessful attempts. The complete three-game prompt history is in the [experiment report](evidence/control/games-REPORT.md).

## Inputs and timing

- Model: `typesafe/jev-1.13-20260917`, accessed through OpenRouter/systemone. Gymnasium 1.3.0. No GPU training.
- CarRacing: privileged speed, slip, yaw, road contact and future centerline waypoints. Recovery instructions include conservative speeds, gentle braking, positive throttle at low speed, and six recent controls.
- LunarLander: normalized observation vector and history. The first two prompts supplied heuristic arithmetic; later prompts used verbal guidance and interval-effect labels. Version 4 corrected labels at engine deadzone boundaries. All eight attempts failed.
- MountainCar: position, velocity, history, the transition equation, and explicit energy-pumping guidance. Both successful episodes are guided control demonstrations, not an isolated test of unguided planning.
- Walker: joint observations, contacts, lidar and privileged torso position; explicit gait/balance guidance. Python supplied no gait phase or computed action target. Both episodes fell.
- Box2D physics runs at 50 Hz. Car actions are held for 10 frames; Lander and Walker for 5. MountainCar actions are held for 4 discrete transitions. Its displayed seconds use a 30-fps rendering convention, not a separately defined physical timestep.
- Simulation pauses during API inference. Videos omit network waits and show simulation-speed frames; short crashes therefore produce short clips. GIFs are excerpts of at most 10–12 seconds. Mean action latency includes the sequential tree requests, excluding simulation and rendering. These are not real-time-control demonstrations.

## Audit artifacts

Each ledger row links a compressed archive with the complete API requests/responses, executed actions, original summary, and available rules/source snapshots. Request archives contain no authorization headers. Media are provided separately for direct playback. Runner snapshots retain original experiment paths for provenance; their local imports and credential-loading paths require adaptation outside the original workspace. They are not a packaged portable benchmark.

- [Additional games: action provenance and recording checks](evidence/control/games-verification.json)
- [Additional games: source semantics and diagnostic probes](evidence/control/games-smoke-semantics.json)
- [Four K/precision runs: action reconstruction and independent replay](evidence/control/racing-verification.json)
- [Earlier racing recovery: report](evidence/control/racing-recovery-report.md) and [all four summaries](evidence/control/racing-recovery-results.json)

Offline reconstruction checks whether Jev's selected options produced the saved actions. Replay checks whether those actions reproduce the recorded environment outcome. Neither establishes that an action was optimal.
