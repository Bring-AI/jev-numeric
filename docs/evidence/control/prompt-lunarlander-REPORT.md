# LunarLander prompt recovery results

All 16 new live episodes are retained. The featured v14 prompt safely lands on the central pad for seeds7 and19 with rewards243.9075 and224.7228. Independent fresh live repeats and deterministic logged-action replays are listed below.

## What changed

The successful v14 prompt puts complete instructions in each action question, uses only the current raw observation, and repeats that observation in the question. Main thrust uses an explicit ordered altitude/descent-speed decision table. Lateral thrust uses the disclosed Gymnasium-style arithmetic stabilization guide. Jev chooses every coarse interval and every final 0.005 interval; Python executes the selected lower endpoints without replacement, fallback, or computed action targets. No environment/dynamics/success rule was changed.

First five fixed-state prompt variants (v5-v9;15probes,30requests) tested full per-axis instructions, repeated observation, arithmetic framing, concise formulas, and unevaluated numeric substitution. Full episodes v5/v7 still anchored on past actions. Removing history in v10 extended survival and eventually produced asleep-without-crash termination, but away from the pad. v11 remained too fast on descent. The main-engine decision table in v14 made both seeds reach central-pad, upright, score>=200 landings. v12 and v15 isolate alternative side-control instructions; every failure remains included.

## All new live episodes

| Run | Reward | Steps | Safe termination | Score>=200 | Final x | Result |
|---|---:|---:|:---:|:---:|---:|---|
| lunarlander-seed19-v10 | 121.3722 | 491 | True | False | -0.4358 | Safe environment termination away from the central pad; do not present as center-pad success. |
| lunarlander-seed19-v11 | 21.2812 | 102 | False | False | -0.0667 | Failed attempt preserved. |
| lunarlander-seed19-v12 | -650.0911 | 84 | False | False | +0.8424 | Failed attempt preserved. |
| lunarlander-seed19-v14 | 224.7228 | 287 | True | True | +0.1030 | Safe environment termination on the central pad, reward>=200. |
| lunarlander-seed19-v14-replicate | 211.9723 | 328 | True | True | +0.2138 | Safe environment termination away from the central pad; do not present as center-pad success. |
| lunarlander-seed19-v15 | 178.8793 | 282 | True | False | -0.4222 | Safe environment termination away from the central pad; do not present as center-pad success. |
| lunarlander-seed19-v5 | -134.7320 | 73 | False | False | -0.0923 | Failed attempt preserved. |
| lunarlander-seed19-v7 | -146.7799 | 73 | False | False | -0.0911 | Failed attempt preserved. |
| lunarlander-seed7-v10 | 144.8993 | 647 | True | False | +0.2450 | Safe environment termination away from the central pad; do not present as center-pad success. |
| lunarlander-seed7-v11 | 41.7953 | 105 | False | False | -0.1643 | Failed attempt preserved. |
| lunarlander-seed7-v12 | -736.2778 | 99 | False | False | +1.0363 | Failed attempt preserved. |
| lunarlander-seed7-v14 | 243.9075 | 312 | True | True | +0.1099 | Safe environment termination on the central pad, reward>=200. |
| lunarlander-seed7-v14-replicate | 254.8375 | 261 | True | True | +0.0716 | Safe environment termination on the central pad, reward>=200. |
| lunarlander-seed7-v15 | 241.5861 | 303 | True | True | -0.0835 | Safe environment termination on the central pad, reward>=200. |
| lunarlander-seed7-v5 | -147.2982 | 66 | False | False | -0.2326 | Failed attempt preserved. |
| lunarlander-seed7-v7 | -116.6770 | 68 | False | False | -0.1959 | Failed attempt preserved. |

## Verification and provenance

verify.py independently parses each selected coarse and leaf interval from api-records.jsonl, checks nesting and0.005width, reconstructs every action from the selected lower endpoint, and replays LunarLander from the recorded seed. It compares every observation (to the original six-decimal telemetry precision), step count, intermediate and total reward, final sleeping/crash flags, and success classification. Each episode verification.json records SHA-256 hashes for the action/API/media/source artifacts. verification-manifest.json collects these audits.

The stock Gymnasium heuristic was run only in offline-heuristic-diagnostic.json to check whether hold5 and this grid can land. Those controls were never supplied in a Jev request or used in a model episode. This diagnostic is excluded from all live-result counts.

Exact live prompts are in request.questions of api-records.jsonl; actual-question-prompts.txt extracts the first decision. rules.txt is inherited runner text and is not the focused question prompt. runner-snapshot.py is the imported original dynamics/media runner; recovery-snapshot.py is the wrapper captured at episode completion and may contain subsequently added inactive variants. The active prompts and executable actions are fully independently audited.

## Media and interpretation

replay.mp4 plays sampled simulation frames at natural simulation speed (10fps for frames spaced5steps at50Hz), omitting API waits. preview.gif is8fps at the same nominal speed. final.png shows the terminal scene. Featured v14 seed7 and seed19 frames show upright landing between the two pad flags. v10 qualifies only under the unchanged simulator asleep/no-crash success definition and is explicitly labelled off-pad.

Prompt selection used these seeds during development. The fresh live repeats assess reproducibility on those same seeds; this is not evidence of broad unseen-seed generalization.
