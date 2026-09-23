# BipedalWalker prompt recovery report

Live NumericJev terrain completions: **0 / 16 completed episodes**. Pending episodes: bipedalwalker-seed7-v16_fixed0_direct-hold1. These results do not establish general impossibility; they describe only the tested prompts and disclosed protocols.

Best verified forward reach: `bipedalwalker-seed7-v9_sequential-hold1`, maximum torso x=18.4117 from initial x=4.6638; the normal-terrain finish is x>88.6667. This run ended `fall` after336frames (6.72s), reward-55.258339. Its full video is `bipedalwalker-seed7-v9_sequential-hold1/replay.mp4` and GIF is `bipedalwalker-seed7-v9_sequential-hold1/preview.gif`. A failed rollout is not a successful walking demonstration.

| Prompt/protocol | Seed | Hold | Frames | Reward | Max x | End | Success |
|---|---:|---:|---:|---:|---:|---|---|
| v2_literal | 7 | 5 | 55 | -108.53 | 4.66 | fall | False |
| v3_verbal | 7 | 5 | 54 | -108.02 | 4.66 | fall | False |
| v4_tuned | 7 | 5 | 70 | -114.32 | 4.66 | fall | False |
| v5_tuned_verbal | 7 | 5 | 59 | -111.88 | 4.66 | fall | False |
| v6_reference-hold1 | 7 | 1 | 89 | -96.42 | 7.12 | fall | False |
| v7_reference_cases-hold1 | 19 | 1 | 81 | -96.47 | 7.08 | fall | False |
| v8_focused_reference-hold1 | 7 | 1 | 303 | -130.66 | 4.71 | left_boundary | False |
| v9_sequential-hold1 | 7 | 1 | 336 | -55.26 | 18.41 | fall | False |
| v9_sequential-hold1 | 19 | 1 | 162 | -78.77 | 11.71 | fall | False |
| v10_rounded-hold1 | 7 | 1 | 100 | -120.46 | 4.73 | fall | False |
| v12_fall_extension-hold1 | 7 | 1 | 224 | -118.25 | 6.27 | fall | False |
| v13_phase_predicates-hold1 | 7 | 1 | 128 | -82.67 | 10.64 | fall | False |
| v14_inequality-hold1 | 7 | 1 | 296 | -113.85 | 6.46 | fall | False |
| v15_fixed0_inequality-hold1 | 7 | 1 | 359 | -112.75 | 6.81 | fall | False |
| v15_fixed0_inequality-hold1 | 19 | 1 | 246 | -109.39 | 6.92 | fall | False |
| v17_simple_coefficients-hold1 | 7 | 1 | 158 | -90.97 | 8.72 | fall | False |

Independent replay/provenance audit: 15/15 audited episodes passed. Every motor is reconstructed from real Jev API interval choices and exactly matched to the executed action. Same-seed replay verifies raw observations, rewards, frame counts, termination and terrain-completion labels. `audit.json` includes hashes of actions, API logs, videos and runner snapshots; `manifest.json` lists all attempts.

The environment, initial state, normal terrain and success definition were never weakened. Physical action grid stayed[-1,1) with0.005 resolution and K20 two-stage refinement. v2–v5 usedhold5; later variants usedhold1 and disclosed additional model-selected gait planning. v9–v14 used5API calls per one physics frame; fixed-support v15–v17 used3. API waits pause simulation and are omitted from videos. The control-frequency and planning changes preclude describing later runs as a prompt-only controlled comparison with the original setup.

The main diagnosed failures were: (1) original qualitative prompts copied angle goals as torque; (2) simplified single-transition gait discarded the public heuristic's chained transitions; (3) parallel plan outputs could disagree; (4) model-decoded knee memory drifted, which fixed-angle templates removed; (5) despite focused raw-value expressions, Jev still selected incorrect torque magnitudes/signs and sometimes premature transitions. On v9, post-hoc arithmetic audit measured256/1344 motor values with absolute error>0.2 forseed7 and101/648 forseed19. These computed diagnostic values were never fed into the API or substituted as actions.

All offline Python controller analyses are separately prefixed`diagnostic` and must never be presented as Jev results. They establish that normal-terrain completion is physically possible: the fixed0.0 support-knee-angle policy with the disclosed original PD coefficients completed both7/19 offline (1585/1554frames, rewards315.35/315.49). The corresponding live models did not inherit those numeric outputs. Archived-state prompt probes test model arithmetic only and are not episodes.

`README.md` details variant semantics; every run contains full API requests/responses, action logs, source snapshots, summaries, full MP4, GIF, poster and final frame. `first-decision-prompts.json` offers a compact exact prompt sample. No successful Walker result is claimed unless a run's independent audit has`replay_terrain_finished: true`.
