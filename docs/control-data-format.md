# JevNext control experiment data

The static page loads `results.json` relative to `index.html`. It contains actual measured outcomes and the complete development history, including unsuccessful attempts.

## Top-level fields

| Field | Type | Meaning |
|---|---|---|
| `updated_at` | ISO date string or null | Date of the experiment manifest, displayed in UTC. |
| `model` | string or null | Exact model identifier used in the listed experiments. Explain mixed models in protocol notes and per-run config. |
| `method` | string | Concise method label. |
| `protocol_notes` | string[] | Input access, prompts, control frequency, timing definitions, success criteria, and limitations. |
| `games` | game[] | Displayed in supplied order. Four intended games: CarRacing-v3, LunarLander-v3 with continuous=true, MountainCarContinuous-v0, BipedalWalker-v3. |
| `racing_ablation` | run[] | Flat array of comparison runs, shown separately from the four-game summaries. Same row schema as other runs. |
| `historical_racing_ablation` | run[], optional | Earlier comparisons using a different prompt. Preserved separately; also retained in the racing ledger. |
| `config` | object, optional | Experiment configuration; shown as expandable formatted JSON. |
| `source_url` | string, optional | Repository or experiment code link. Defaults to Bring-AI/jev-numeric. |
| `measurement_url` | string, optional | Human-inspectable measurements link. Defaults to results.json. |
| `configuration_url` | string, optional | Experiment source/configuration link. Defaults to this document. |

## Game fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string | Stable game identifier. |
| `title` | string | Display name such as CarRacing. |
| `description` | string | Brief description of the control problem. |
| `environment` | string | Gymnasium environment name; note continuous configuration for LunarLander. |
| `action_dimensions` | number | Number of real-valued control outputs. |
| `runs` | run[] | Every recorded attempt, successful or unsuccessful, in source order. |
| `media` | media object, optional | Fallback featured media; per-run media takes precedence. |
| `notes` | string[] | Observations and caveats grounded in the recorded data. |
| `success_criterion` | string, optional | Explicit criterion used to compute success booleans. Do not imply universal benchmark thresholds. |
| `featured_run_id` | string, optional | Run to show in the large player. Without this, runs[0] is used. No automatic best-run selection. |
| `config` | object, optional | Environment and controller configuration, shown in the run ledger. |

## Run fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string, optional | Stable descriptive run identifier. Displayed in the ledger. |
| `seed` | number | Environment seed. |
| `reverse_options` | boolean | True = reverse order; false = forward order; missing = unknown. |
| `branching` | number | K, choices per interval refinement step. |
| `resolution` | number, decimal string, or object | Grid spacing, optionally by control dimension. This is not a confidence interval. |
| `coverage_percent` | number, optional | Track coverage as a percent; adds a column to racing/ablation ledgers. Coverage does not determine success in the UI; use the recorded success boolean and explicit completion criterion. |
| `reward` | number or null | Recorded episode or partial-episode reward. Explain partial episodes in stop_reason/notes. |
| `success` | boolean or null | Strict true/false assessment; null/missing stays unassessed and is excluded from the assessed success denominator. |
| `stop_reason` | string | Environment termination/truncation, action budget, API error, or other actual stop reason. |
| `steps` | number | Environment simulation steps, not automatically action count. Document control/action repeats separately. |
| `sim_seconds` | number | Simulated duration, excluding network waiting. |
| `api_calls` | number | Recorded API request count. |
| `mean_action_latency_s` | number or null | Mean wall-clock time to obtain a control action. Define included requests and excluded time in protocol notes. |
| `media` | media object, optional | Per-run recording links. Required for recorded unsuccessful attempts that have media. |
| `trace` | string, optional | Relative or HTTPS link to a complete raw trace. JSON, JSONL, and compressed .gz files all work. Labeled “Recorded trace.” |
| `config` | object, optional | Prompt version, max steps, action repeats, range, rates, source revision, actions/control count, overrides, privileged input access, and other settings. |
| `experiment_stage` | string, optional | Marks the prompt-development round; does not alter the recorded outcome. |

Media objects contain optional relative or HTTPS paths: `gif`, `video`, and `poster`. MP4/H.264 is the intended full-video format. Use relative paths such as `media/car-racing-seed19.mp4` to keep GitHub Pages project URLs and future root-domain hosting working. A poster is strongly recommended so reduced-motion mode can display a still image. GIFs animate by default unless the operating system requests reduced motion; visitors can pause previews with the page-level checkbox. Videos never autoplay and use native accessible controls.

## Display rules

- Every supplied run appears in the game ledger. Ablation runs appear in their own full table and are not silently added to game totals.
- The main result belongs to the explicitly featured recording: completion status, coverage (racing), or episode reward (other games). Unknown results remain unassessed.
- The expandable ledger retains every attempt and counts successful recordings across development. This count is not presented as an estimated success rate.
- The shown run's branching, resolution, and mean action latency are labeled as belonging to that recording. They are not presented as averages over different settings.
- Featured run selection never changes all-run statistics. Mark illustrative or diagnostic prompts in the run config; retain earlier unsuccessful variants.
- Walker configurations disclose intermediate gait decisions, target-angle templates, and the number of planning calls in addition to motor-refinement calls. Angle goals are distinct from the executed motor commands.
- Walker `composed-v1` and `comparison-v2` configurations explicitly distinguish term-grid spacing from physical motor spacing. Signed interval centers are added as integer units and clipped. `comparison-v2` compiles fixed affine rules into input-interval criteria; each bin remains a recorded Jev choice. This differs from directly choosing a whole-motor interval.
- All rows expose available video, GIF, and trace links. Direct video links use the browser's native player; visitors can inspect unsuccessful attempts as well as the featured one.
- Empty games or missing featured videos leave a visible development/missing-recording notice. Do not deploy an empty scaffold.
- Text is inserted as DOM text, not HTML. Links accept HTTP and HTTPS URLs only, including relative URLs resolved under the current page.

## Publishing

No compilation is needed. Copy `index.html`, `app.js`, `style.css`, `assets/mark.svg`, a completed `results.json`, media, and linked evidence to the hosting root (for example GitHub Pages `docs/`). Keep `docs/data-contract.md` if retaining the default configuration link; otherwise set `configuration_url` to the actual experiment source.

Preserve all existing repository documentation when integrating. This source directory's internal `docs/` is a data format document, not a request to overwrite the public repository's entire `docs/` tree.
