# NumericJev racing recovery: direct controls

The goal is lap completion using Jev-produced numeric steering and signed throttle/brake. There is no geometric-controller fallback and no programmatic replacement of the selected action.

## What changed

- Conservative speed guidance: 12–16 on straight road and 6–10 in tight turns/recovery.
- Explain brake strength: brake 0.10 removed about 6 speed units in 0.2 seconds in the observed simulator. Ask for gentler braking and release before zero speed.
- Explicit low-speed recovery: positive throttle and steering toward the road; steering alone cannot turn a stationary car. State that historical controls are observations, not commands to repeat.
- Include the previous six real control observations/actions and a consecutive stationary-observation duration signal. The signal increments by 0.2 seconds at observations below speed 0.2, so it has one control-step quantization.
- Put these rules directly in both choice questions, as well as the state. Retain exact action descriptions at the final numeric-tree level.
- Increase the simulation horizon from 60 to 180 seconds to allow slower completion. The 10-second no-new-tile guard and 900-second wall limit remain unchanged.

All changes form one policy revision; this experiment does not isolate which of them contributes how much.

## Results: all four conditions

| Seed | Order | Track coverage | Lap finished | Sim seconds | Fully-offroad frames | API calls |
|---|---|---:|---|---:|---:|---:|
| 19 | forward | 100.00% | True | 79.74 | 0.00% | 798 |
| 7 | forward | 99.69% | False | 85.20 | 0.31% | 852 |
| 7 | reverse | 84.95% | False | 85.92 | 11.73% | 860 |
| 19 | reverse | 99.43% | False | 92.16 | 1.80% | 922 |

## Verification and limits

Audited every final selected option against the executed steering/pedal value, numeric leaf index, action bounds, raw current telemetry, and actual preceding six controls. Counts agree at two API requests per control. Same-seed track hashes match the original reference episodes. All four runs used identical recovery source. Independently replaying only the decoded actions reproduces every visited-tile count, final reward, offroad fraction, and termination. This is four exploratory runs on two tracks, not a general driving benchmark.

The controller receives privileged simulator state and future centerline points, not camera images. Simulation pauses during API calls, and videos omit those waits. Numeric actions are finite-grid values at resolution 0.02, decoded through two ten-way tree levels; no continuous head is trained.

At the archived final stopped state from the previous seed-19 run, the revised policy chose steering -0.50 and throttle 0.08 in both option orders. Original and revised raw responses are in fixed-state-*.json. Previous failing episodes are preserved outside this directory.

## Run another episode

```bash
/tmp/numericjev-racing-env/bin/python /data/yww/notebook/numericjev-game-experiments/car-racing-20260923/recovery/run_recovery.py --seed 19
```

Append --reverse to reverse option insertion order. Each invocation defaults to a fresh timestamped directory. The runner uses the existing local Jev client and credentials configuration. Every episode saves full API requests/responses, actions, a summary, track geometry, source snapshots, and a video. No GPU is used.
