# Focused racing prompts: follow-up

All five new runs finished every tile. The four seed7 settings and the additional seed19 run use the same prompt, unchanged physics, original action grid, hold10 frames, and 180-second horizon.

| Seed | K | Grid spacing | Coverage | Reward | Sim seconds | API calls |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 10 | 0.005 | 100.00% | 579.70 | 84.06 | 1263 |
| 7 | 20 | 0.005 | 100.00% | 579.40 | 84.12 | 842 |
| 7 | 10 | 0.02 | 100.00% | 577.30 | 84.54 | 846 |
| 7 | 20 | 0.02 | 100.00% | 572.80 | 85.44 | 856 |
| 19 | 20 | 0.005 | 100.00% | 531.10 | 93.78 | 938 |

## What changed

The per-steering question now states an explicit numerical guide: use the4-tile waypoint bearing divided by75, clipped to+/-0.6. The pedal question gives an ordered speed table with gentle throttle/brake, slowing for sharp bends/offroad states. Current simulator telemetry is preserved, while previous commands and action history are removed from model input. Each question receives its own full control instructions. Jev calculates and selects the command through the same multiway decoder; Python performs no action correction.

The earlier prompt showed wrong-sign steering copied from its history in archived states. The focused prompt repaired several such fixed-state decisions. However both control guidance and input presentation changed together; this is not a causal isolation of history removal or a guarantee of general driving reliability.

## Verification

verification.json reconstructs every choice/window/control and independently replays all5 episodes in fresh environments. Current telemetry, all intermediate tile counts, cumulative rewards, termination, and source hashes match. All5 runs have0% fully-offroad frames. No live calls or original records were modified during replay.

The videos show simulation time and omit API waiting. These are selected guided demonstrations, not autonomous pixel-input play or real-time driving.
