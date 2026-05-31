# LIBERO-plus adaptive video recording strategy

## Current rule

Use task difficulty level and observed failure density, not only perturbation category.

- L1-L2: run metrics-only first, then rerun failures with video. Observed camera-view success is about 98%, so full video recording is mostly waste.
- L3: run metrics-only first by default. If a chunk falls below about 85% success, rerun failed-task groups with video.
- L4-L5: prefer direct video recording for small chunks or rerun whole failed-task groups. These levels produce dense failures, so recording only after the fact can require many reruns.
- Always keep `batch_size=1`, `max_parallel_tasks=1`, `seed=1000`, and `n_episodes=5` for comparability and 12GB VRAM safety.

## Evidence from current camera-view runs

Completed camera-view coverage so far:

- Index `0-49`: 50 tasks, 250 episodes, 247 successes, 3 failures.
- Index `50-149`: 100 tasks, 500 episodes, 349 successes, 151 failures.
- Combined index `0-149`: 150 tasks, 750 episodes, 596 successes, 154 failures, success `79.47%`.

Observed success by difficulty on camera-view index `0-149`:

| Level | Success | Failure | Success rate |
| ---: | ---: | ---: | ---: |
| L1 | 54 | 1 | 98.18% |
| L2 | 163 | 2 | 98.79% |
| L3 | 135 | 30 | 81.82% |
| L4 | 69 | 26 | 72.63% |
| L5 | 175 | 95 | 64.81% |

This is why low-level tasks should not be fully recorded, while high-level chunks can justify direct video if we need visual failure analysis.

## Remaining category sizes

| Category | Total tasks | L1 | L2 | L3 | L4 | L5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Camera Viewpoints | 419 | 16 | 47 | 55 | 58 | 243 |
| Robot Initial States | 393 | 64 | 77 | 100 | 83 | 69 |
| Sensor Noise | 449 | 27 | 97 | 81 | 124 | 120 |

## Practical continuation

For full-score evaluation, keep metrics collection separate from failure videos:

- Metrics pass: evaluate every task with 5 episodes and write `eval_info.json`.
- Failure video pass: only render the failed task episodes needed for 16-cell grids.
- For L4/L5-heavy chunks, direct video can be cheaper than a second full model load, but should be chunked to avoid writing hundreds of videos unnecessarily.

Current next camera-view continuation index is `150`.
