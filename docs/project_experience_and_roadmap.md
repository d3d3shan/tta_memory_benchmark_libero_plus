# Project Experience and Roadmap

This note summarizes what has been completed, what was learned, and how to continue the LIBERO-plus benchmark work on a future server.

## Current Objective

The project is a lightweight reproduction package for evaluating pi0.5-style policies on LIBERO-plus perturbation benchmarks through OpenTau. The immediate goal was not full training. It was to make inference/evaluation reliable, collect useful failure videos, and preserve enough scripts/configs to continue on another machine.

The repository intentionally keeps only code, configs, notes, and lightweight summaries. Large videos and detailed failure-grid artifacts are stored in Hugging Face datasets linked from `hf_datasets.md`.

## Completed Work

- Fixed the local GPU evaluation path for `TensorAuto/tPi0.5-libero` on LIBERO-plus via OpenTau.
- Added an OpenTau patch for memory-safe LIBERO evaluation: per-task lazy environment creation, explicit episode length propagation, stable render FPS metadata, deterministic seed-to-init-state behavior, and cleaner grid summary videos.
- Ran smoke tests for pi0.5 on LIBERO-plus.
- Completed three perturbation categories with 5 episodes per task:
  - `Camera Viewpoints`: 419 tasks, 2095 episodes, 1197 successes, 57.14%.
  - `Robot Initial States`: 393 tasks, 1965 episodes, 1430 successes, 72.77%.
  - `Light Conditions`: 274 tasks, 1370 episodes, 1209 successes, 88.25%.
- Uploaded failure-grid videos and metadata to public Hugging Face datasets.
- Created this lightweight GitHub repository for future clone-and-continue workflows.

## Evaluation Lessons

- Official success rate should be computed from the original evaluation pass: `5 episodes/task`.
- Low-difficulty failed-task reruns are only for video collection and should not be counted again in benchmark success rates.
- LIBERO success/reward is a task completion predicate. It does not fully capture whether the robot used the exact human-preferred strategy.
- Some videos stop soon after success because the environment marks success immediately; this is useful for benchmark scoring but less ideal for post-success stability analysis.
- Failure grids are best treated as visual diagnostics. Detailed mapping from grid tile to task/episode/seed/perturbation is stored in JSON/MD metadata.

## Hardware and Runtime Lessons

The local machine used for the first run had a 12GB RTX 5070 Ti Laptop GPU, so the committed configs are conservative. Do not assume the next server has the same limits.

For a new server, first estimate hardware capacity, then select evaluation parameters:

| Hardware class | Suggested starting point |
|---|---|
| `<16GB VRAM` | Use `batch_size=1`, `max_parallel_tasks=1`, metrics-only for easy subsets, rerun failures for videos. |
| `16-24GB VRAM` | Try `batch_size=2` after smoke passes; keep lazy per-task envs until memory is verified. |
| `>=24GB VRAM` | Consider recording more videos directly and increasing batch size gradually. |
| `>=40GB VRAM` | Consider multi-policy queues or more direct-video evaluation, but keep configs versioned per run. |

Always run smoke tests before full queues. Track `nvidia-smi`, wall time, and output size for the first few tasks before launching large runs.

## Strategy That Worked

- Use conservative configs to prove correctness first.
- Keep `max_parallel_tasks=1` with lazy environment construction to avoid memory spikes.
- Use `bf16` inference for pi0.5.
- Use fixed episode seeds starting at `1000` so repeated runs are comparable.
- For low-difficulty subsets, run metrics first and rerun only failed tasks with video.
- For harder subsets, record videos in the first pass because the failure rate is high enough that rerun may not save time.
- Keep GitHub lightweight; store videos and heavy artifacts on Hugging Face.

## Remaining Work

- Complete the remaining LIBERO-plus perturbation categories:
  - `Background Textures`
  - `Language Instructions`
  - `Objects Layout`
  - `Sensor Noise`
- Add more policies for comparison, using the same task IDs, episode seeds, and result schema.
- Add TTA/memory-based policy variants and compare against pi0.5 baseline.
- Standardize a single result schema for all policies and perturbations.
- Automate Hugging Face dataset upload for each completed category.
- Build a failure taxonomy: perception error, grasp failure, wrong target, collision, planning dead-end, premature success, and post-success instability.
- Add optional post-success hold steps when the research question is stability, not just official benchmark success.

## Recommended Next Run Order

1. Run `bash scripts/run_libero_plus_smoke.sh` on the new server.
2. Run `bash scripts/run_libero_plus_7perturb_smoke.sh`.
3. Estimate hardware using `docs/server_hardware_check.md`.
4. Generate or copy configs for one remaining category.
5. Run a small subset first, then scale to full category.
6. Store videos in HF datasets and keep GitHub limited to scripts, configs, and summaries.
