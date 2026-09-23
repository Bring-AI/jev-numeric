# NumericJev continuous-control experiments

[Interactive recordings](./) · [All measurements](results.json) · [Data format](control-data-format.md)

This snapshot features selected recordings after prompt refinement, with 63 development episodes retained in the run ledgers. Each recorded motor command comes from Jev's interval selections. No policy was trained and no fallback controller replaced model outputs. The model receives structured observations and explicit control guidance, not gameplay images. The manifest records the snapshot time; ongoing experiments are added after completion and audit.

## Featured recordings

| Game | Recorded run | Outcome | Reward | Simulation seconds | API calls |
|---|---|---|---:|---:|---:|
| CarRacing | racing-focused-v2-K20-resolution0.005-seed7 | 100% track coverage | 579.40 | 84.12 | 842 |
| LunarLander | lunarlander-seed7-v14 | safe landing | 243.91 | 6.24 | 126 |
| MountainCar | mountaincar-seed7-v1 | goal reached | 91.72 | 2.80 | 42 |
| BipedalWalker | bipedalwalker-seed7-v9_sequential-hold1 | fall | -55.26 | 6.72 | 1680 |

These are guided demonstrations selected on development seeds. They do not estimate performance on unseen seeds or establish a general success rate. The simulator, terrain, and completion definitions were not changed to make a run successful.

## What changed in the prompts

- **CarRacing:** put full steering and pedal instructions in their respective questions. Use the current four-tile waypoint bearing divided by 75 (clipped to ±0.6), plus an ordered conservative speed table. Remove previous commands from model input. Jev evaluates these guides and selects the actual actions. Several archived-state probes corrected wrong-sign steering, but guidance and input presentation changed together, so this does not isolate one causal fix.
- **LunarLander:** put focused instructions and the current raw observation in each engine question. Main thrust follows an altitude/descent-speed table; lateral thrust uses an arithmetic stabilization guide. The selected v14 seed-7 run landed upright on the central pad. v14 produced four safe terminations scoring above 200 across seeds 7 and 19 plus repeats; one repeat settled at the pad edge. Earlier off-pad safe terminations and crashes are retained with their own outcomes.
- **MountainCar:** retain the original successful runs. Their prompt includes the dynamics equation and energy-pumping guidance.
- **BipedalWalker:** test gait instructions, numerical motor equations, and sequential model-chosen gait decisions. Later variants pass disclosed phase-to-angle-goal templates into the motor questions; these angle goals are not motor commands. Every executed torque still comes from NumericJev. Per-run configurations disclose the additional planning calls and action frequency; follow-up results and failures are in the full ledger.

## K and precision: revised racing prompt

All four seed-7 settings use the same revised prompt, forward option order, unchanged physics, actions held for 10 frames, and a 180-second simulation horizon. The additional seed-19 run uses that same prompt.

| Seed | K | Grid spacing | Coverage | Simulation seconds | API calls |
|---:|---:|---:|---:|---:|---:|
| 7 | 10 | 0.020 | 100% | 84.54 | 846 |
| 7 | 20 | 0.020 | 100% | 85.44 | 856 |
| 7 | 10 | 0.005 | 100% | 84.06 | 1263 |
| 7 | 20 | 0.005 | 100% | 84.12 | 842 |
| 19 | 20 | 0.005 | 100% | 93.78 | 938 |

The earlier prompt completed only the K=10 / 0.005 condition: coverage was 99.69%, 97.18%, 100%, and 94.36% in the corresponding four seed-7 settings. Those records remain in the racing ledger and `historical_racing_ablation` in the JSON manifest. The new results do not establish that a larger K or finer precision caused the improvement: the prompt changed between rounds.

## Numerical actions, observations, and timing

- Model: `typesafe/jev-1.13-20260917`, through OpenRouter/systemone. Gymnasium 1.3.0. No GPU training.
- Each action is a finite-grid number on `[-1,1)`. Python partitions the range and executes the selected cell's lower endpoint. The excluded upper bound is not an available action.
- CarRacing uses steering plus a signed pedal, mapped mechanically to throttle if positive and brake if negative. It receives privileged speed, slip, yaw, road contact, and future track-centerline waypoints.
- Lander uses main and lateral engine commands; MountainCar uses one motor force; Walker uses four hip/knee commands. Earlier Walker prompts receive extended observations including lidar and torso position. The focused sequential variants receive only the joint/body measurements printed in their questions; lidar and torso position remain in the diagnostic logs but are not given to Jev. Exact input access, prompt variants, and histories are archived.
- All motor components share one request per tree level. K=10 / 0.005 uses three motor-refinement calls; the other tested grids use two. Later Walker protocols add model-chosen gait and numerical target-memory calls; the exact count is in each run's configuration.
- Box2D integrates at 50 Hz. CarRacing holds actions for 10 frames; Lander for 5. Walker initially used 5-frame holds, while later attempts update every frame. MountainCar holds 4 discrete steps; displayed seconds follow its 30-fps rendering convention.
- Simulation pauses during API inference. Full videos omit network waiting and show simulation-speed frames. GIFs are short excerpts. Mean action latency includes all planning and refinement requests, excluding physics/rendering. These are not real-time-control demonstrations.
- Racing completion requires every track tile and the environment's lap-finished flag. Lander success uses the original asleep/no-body-crash termination; pad position and the score-200 threshold are reported separately. MountainCar requires the goal position and nonnegative velocity. Walker requires the normal terrain's right finish without a torso fall.

## Evidence and independent replay

Every ledger row links the recorded requests/responses, executed actions, original summary, and source snapshots. Media are separate for direct playback. Authentication headers are excluded. Source snapshots retain original local import paths and require adaptation outside the original workspace; they are evidence, not a packaged portable benchmark.

- Revised racing: [report](evidence/control/prompt-racing-REPORT.md), [all five reconstruction/replay audits](evidence/control/prompt-racing-verification.json).
- Revised Lander: [report with all 16 attempts](evidence/control/prompt-lunarlander-REPORT.md), [audit manifest](evidence/control/prompt-lunarlander-verification-manifest.json).
- Walker follow-ups: [development report](evidence/control/prompt-bipedalwalker-README.md), [action reconstruction and replay](evidence/control/prompt-bipedalwalker-audit.json).
- Earlier additional games: [action/recording checks](evidence/control/games-verification.json), [source semantics](evidence/control/games-smoke-semantics.json).
- Earlier racing comparison: [independent replay](evidence/control/racing-verification.json).
- All exact prompts and controls, including Walker follow-ups: each row's **Recorded trace** link. Offline arithmetic/reference-controller probes are diagnostics, never counted as model episodes.

Reconstruction checks that recorded Jev choices produced the executed actions. Fresh deterministic replay checks that those actions reproduce the reported observations, reward, and termination. Neither establishes that a selected action was optimal.
