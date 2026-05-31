#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OPENTAU_DIR="${OPENTAU_DIR:-$ROOT/OpenTau}"
export OPENTAU_DIR
cd "$OPENTAU_DIR"

PRESET="${1:-standard}"

case "$PRESET" in
  quick)
    TASKS_PER_CATEGORY=2
    EPISODES_PER_TASK=1
    MAX_EPISODES_RENDERED=1
    ;;
  standard)
    TASKS_PER_CATEGORY=8
    EPISODES_PER_TASK=2
    MAX_EPISODES_RENDERED=2
    ;;
  strong)
    TASKS_PER_CATEGORY=20
    EPISODES_PER_TASK=3
    MAX_EPISODES_RENDERED=3
    ;;
  full)
    TASKS_PER_CATEGORY=0
    EPISODES_PER_TASK=3
    MAX_EPISODES_RENDERED=3
    ;;
  *)
    echo "Usage: $0 [quick|standard|strong|full]" >&2
    exit 2
    ;;
esac

"$SCRIPT_DIR/make_libero_plus_perturb_eval_configs.py" \
  --suite libero_10 \
  --tasks-per-category "$TASKS_PER_CATEGORY" \
  --episodes-per-task "$EPISODES_PER_TASK" \
  --seed 1000 \
  --sample-mode stride \
  --episode-length 520 \
  --batch-size 1 \
  --max-episodes-rendered "$MAX_EPISODES_RENDERED" \
  --grid-cols 2

cat <<'EOF'

Generated configs only. Nothing has been evaluated.

Run one category manually, for example:

  ../scripts/run_libero_plus_eval_config.sh \
    configs/local/libero_plus_perturb_eval/pi05_libero_10_background_textures.json

Recommended order:

  1. background_textures
  2. camera_viewpoints
  3. language_instructions
  4. light_conditions
  5. objects_layout
  6. robot_initial_states
  7. sensor_noise

EOF
