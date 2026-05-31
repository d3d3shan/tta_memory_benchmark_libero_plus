# TTA Memory Benchmark for LIBERO-plus

Lightweight reproduction package for running pi0.5/OpenTau evaluations on LIBERO-plus perturbation benchmarks.

This repository is intentionally small. It does not vendor OpenTau, LIBERO-plus, model weights, virtual environments, raw outputs, or MP4 result videos. It stores the evaluation overlay: patches, configs, queue scripts, failure-grid tools, result summaries, and links to Hugging Face artifacts.

## What Is Included

- `patches/opentau_libero_plus_eval.patch`: local OpenTau changes used for memory-safe LIBERO-plus evaluation.
- `scripts/`: evaluation, queue, config-generation, aggregation, and failure-grid scripts.
- `configs/local/`: smoke tests and 50x5 perturbation configs used in the local runs.
- `results_summaries/`: JSON/MD summaries for completed camera view, robot initial state, and light conditions runs.
- `docs/`: notes on reward/success definitions, failure modes, and evaluation strategy.
- `hf_datasets.md`: public Hugging Face datasets containing failure-grid MP4s and metadata.
- `bootstrap_server.sh`: clone/install/apply-patch helper for a fresh Linux GPU server.

## Completed Results

Official one-pass evaluation rates, using 5 episodes per task:

| Perturbation | Tasks | Episodes | Success |
|---|---:|---:|---:|
| Camera Viewpoints | 419 | 2095 | 1197/2095 = 57.14% |
| Robot Initial States | 393 | 1965 | 1430/1965 = 72.77% |
| Light Conditions | 274 | 1370 | 1209/1370 = 88.25% |
| Combined | 1086 | 5430 | 3836/5430 = 70.64% |

## Fresh Server Setup

Prerequisites:

- Linux with an NVIDIA GPU and working `nvidia-smi`
- Git
- Python 3.10 or 3.11
- Hugging Face access to `TensorAuto/tPi0.5-libero`

Recommended first run:

```bash
git clone https://github.com/d3d3shan/tta_memory_benchmark_libero_plus.git
cd tta_memory_benchmark_libero_plus
bash bootstrap_server.sh
source .venv-opentau/bin/activate
hf auth login
cd OpenTau
bash ../scripts/run_libero_plus_smoke.sh
```

The bootstrap script creates sibling `OpenTau/` and `LIBERO-plus/` directories inside this repository checkout, installs OpenTau in editable mode, installs LIBERO-plus in editable mode, and applies the patch.

## Running More Evaluations

Use `run_examples.md` for concrete commands. The default configs are conservative for a 12GB GPU:

- `batch_size=1`
- `max_parallel_tasks=1`
- `bf16`
- lazy one-task-at-a-time environment creation
- episode length 520
- deterministic episode seeds from `1000`

For larger GPUs, adjust config values cautiously after a smoke test passes.

## Large Artifacts

Failure-grid videos are not committed here. Use the Hugging Face links in `hf_datasets.md`.
