#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required" >&2
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

if [ ! -d OpenTau ]; then
  git clone https://github.com/TensorAuto/OpenTau.git OpenTau
fi

if [ ! -d LIBERO-plus ]; then
  git clone https://github.com/Lifelong-Robot-Learning/LIBERO-plus.git LIBERO-plus
fi

python3 -m venv .venv-opentau
source .venv-opentau/bin/activate
python -m pip install --upgrade pip wheel setuptools

python -m pip install -e ./LIBERO-plus
python -m pip install -e ./OpenTau

cd OpenTau
if git apply --check "$ROOT/patches/opentau_libero_plus_eval.patch"; then
  git apply "$ROOT/patches/opentau_libero_plus_eval.patch"
else
  echo "Patch already applied or does not match current OpenTau. Inspect with:" >&2
  echo "  cd OpenTau && git diff -- src/opentau/envs/configs.py src/opentau/envs/libero.py src/opentau/scripts/eval.py" >&2
fi

mkdir -p configs/local
rsync -a "$ROOT/configs/local/" configs/local/

echo "Bootstrap complete."
echo "Next:"
echo "  source .venv-opentau/bin/activate"
echo "  hf auth login"
echo "  cd OpenTau"
echo "  bash ../scripts/run_libero_plus_smoke.sh"
