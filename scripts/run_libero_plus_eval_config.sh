#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <config_path>" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$ROOT/.venv-opentau"
OPENTAU_DIR="${OPENTAU_DIR:-$ROOT/OpenTau}"
CONFIG_PATH="$1"

export LIBERO_CONFIG_PATH="${LIBERO_CONFIG_PATH:-$HOME/.libero}"
export MUJOCO_GL="${MUJOCO_GL:-egl}"
export TOKENIZERS_PARALLELISM=false
export HF_HUB_OFFLINE="${HF_HUB_OFFLINE:-1}"
export TRANSFORMERS_OFFLINE="${TRANSFORMERS_OFFLINE:-1}"
export OPENTAU_DISABLE_TQDM="${OPENTAU_DISABLE_TQDM:-1}"

cd "$OPENTAU_DIR"

exec "$VENV/bin/accelerate" launch --num_processes 1 \
  src/opentau/scripts/eval.py \
  --config_path="$CONFIG_PATH"
