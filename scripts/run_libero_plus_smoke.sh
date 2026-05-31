#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$ROOT/.venv-opentau"
OPENTAU_DIR="${OPENTAU_DIR:-$ROOT/OpenTau}"

export LIBERO_CONFIG_PATH="${LIBERO_CONFIG_PATH:-$HOME/.libero}"
export MUJOCO_GL="${MUJOCO_GL:-egl}"
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"

cd "$OPENTAU_DIR"

if [[ "${1:-}" == "inference" ]]; then
  exec "$VENV/bin/python" "$SCRIPT_DIR/pi05_smoke_inference.py" \
    --config_path configs/local/pi05_inference_smoke.json
fi

exec "$VENV/bin/accelerate" launch --num_processes 1 \
  src/opentau/scripts/eval.py \
  --config_path=configs/local/pi05_libero_plus_smoke.json
