# Continuous-game Jev experiments

All executed actions were selected by live Jev numerical choices. These are guided state-control demonstrations, not pixel-input play or evidence of general numerical accuracy. No policy training was performed.

| Game | Attempt | Seed | Reward | Outcome | Steps | API calls | Mean action latency |
|---|---|---:|---:|---|---:|---:|---:|
| Bipedal Walker | v1 | 19 | -117.58 | fall | 99 | 40 | 0.572s |
| Bipedal Walker | v1 | 7 | -115.31 | fall | 75 | 30 | 0.688s |
| Lunar Lander | v1 | 19 | -508.56 | crash | 71 | 30 | 0.480s |
| Lunar Lander | v2 | 19 | -128.30 | crash | 73 | 30 | 0.513s |
| Lunar Lander | v3 | 19 | -256.98 | out_of_bounds | 125 | 50 | 0.509s |
| Lunar Lander | v4 | 19 | -114.64 | crash | 77 | 32 | 0.510s |
| Lunar Lander | v1 | 7 | -458.25 | crash | 62 | 26 | 0.642s |
| Lunar Lander | v2 | 7 | -100.64 | crash | 66 | 28 | 0.511s |
| Lunar Lander | v3 | 7 | -36.42 | crash | 92 | 38 | 0.534s |
| Lunar Lander | v4 | 7 | -105.97 | crash | 66 | 28 | 0.488s |
| Continuous Mountain Car | v1 | 19 | 91.92 | goal_reached | 82 | 42 | 0.569s |
| Continuous Mountain Car | v1 | 7 | 91.72 | goal_reached | 84 | 42 | 0.526s |

## Setup and limitations

- Gymnasium 1.3.0. LunarLander-v3 continuous=True, MountainCarContinuous-v0, BipedalWalker-v3 hardcore=False.
- Model: typesafe/jev-1.13-20260917 through OpenRouter/systemone. Structured observations and recent action/state history only; no images sent. Walker also sees privileged torso position.
- K=20, resolution 0.005: 400 exact Decimal grid points in [-1,1), two levels, all action dimensions batched at each level. Candidate count is min(K, remaining points). Final interval lower endpoints are the only commands executed.
- Action hold: Lunar Lander and Walker 5 physics frames (0.10 seconds); Mountain Car 4 discrete transitions. Box2D physics runs at 50 Hz. Mountain Car seconds use the environment rendering rate of 30 fps, not a separately defined physical timestep.
- Videos omit API waiting and play at natural simulation speed. GIFs are natural-speed excerpts of at most 12 seconds and width320. Short crashes naturally have shorter GIFs.
- Lunar Lander v1 included the public heuristic in nested arithmetic form; v2 expanded its expressions and clarified signs; v3 replaced formulas with verbal control guidance and effect labels; v4 corrects v3 coarse labels at exactly main=0 and lateral=+0.5. Every failed attempt is retained.
- Mountain Car received an explicit energy-pumping heuristic and the transition equation. Both observed episodes reach the goal; this does not isolate unguided reasoning.
- Walker received an explicit alternating gait description and balance/joint guidance; both observed attempts fell. Python did not supply a computed gait phase or action target.
- The representative GIF uses seed7 of the latest prompt attempt for each game, selected before comparing rewards. Every individual run includes its own MP4, GIF, poster, exact rules, script snapshot, action log and complete API records without authorization headers.
- No retry/fallback controller. API errors would stop an episode and be recorded. All current completed episodes terminate through actual environment conditions.

## Source semantics

Local installed official source was inspected and hashed in smoke-semantics.json. Physics probes use fresh environments and are diagnostics, not Jev evaluation episodes.

- Lunar Lander source: main fires only for main>0; lateral fires only for abs(lateral)>0.5. Positive lateral decreases angle. Safe sleeping without body crash is reported as success; score>=200 is separately recorded.
- Walker source: sign(action) sets target motor direction and abs(action) sets torque cap. Its docstring says motor speed, but this experiment follows implementation. Knee observations are joint.angle+1.
- Mountain Car: success requires position>=0.45 and velocity>=0. The per-step action cost is 0.1*action^2 and terminal goal bonus is100.

## Verification

verification.json reconstructs every executed action component from the two recorded Jev choices; checks frame/step and reward totals; decodes each video; and checks every GIF is width320 and under2MB. This checks provenance, not action optimality.
