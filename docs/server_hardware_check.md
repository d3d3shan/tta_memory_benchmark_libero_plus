# Server Hardware Check

Run these checks before choosing evaluation parameters on a new server.

## Basic Commands

```bash
nvidia-smi
nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv
nproc
free -h
df -h .
python --version
```

If using the project virtual environment:

```bash
source .venv-opentau/bin/activate
python - <<'PY'
import torch
print("torch", torch.__version__)
print("cuda available", torch.cuda.is_available())
if torch.cuda.is_available():
    print("gpu", torch.cuda.get_device_name(0))
    print("total GB", torch.cuda.get_device_properties(0).total_memory / 1024**3)
PY
```

## Parameter Selection

Start from the smoke configs, then scale only after observing real memory usage.

| VRAM | First full-eval settings to try |
|---:|---|
| `<16GB` | `batch_size=1`, `max_parallel_tasks=1`, minimal direct video. |
| `16-24GB` | Try `batch_size=2`; keep `max_parallel_tasks=1`. |
| `24-40GB` | Try higher direct-video coverage or `batch_size=2-4`; monitor memory. |
| `>=40GB` | Consider larger queues, more policies, or more video recording; still keep one config per run. |

Do not decide solely from VRAM. CPU count, disk throughput, available RAM, and MuJoCo rendering stability also matter.

## Smoke Acceptance

A server is ready for large queues only if:

- `nvidia-smi` shows the expected GPU and stable driver.
- pi0.5 model loads without CPU fallback.
- one LIBERO-plus smoke task runs to completion.
- GPU memory has at least 15-20% headroom after the smoke run.
- output videos, if enabled, are playable.

## Scaling Rule

Increase only one parameter at a time:

1. `batch_size`
2. direct video count
3. number of tasks per queue
4. number of policies

If a run crashes or stalls, revert the last change and keep the previous stable config.
