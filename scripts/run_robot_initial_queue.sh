#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$ROOT/.venv-opentau"
OPENTAU_DIR="${OPENTAU_DIR:-$ROOT/OpenTau}"
export OPENTAU_DIR
cd "$OPENTAU_DIR"

LOG="note3/robot_initial_queue.log"
mkdir -p note3

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG"
}

run_config() {
  local cfg="$1"
  log "Running $cfg"
  "$SCRIPT_DIR/run_libero_plus_eval_config.sh" "$cfg" 2>&1 | tee -a "$LOG"
  log "Finished $cfg"
}

generate_low_failure_rerun_config() {
  "$VENV/bin/python" "$SCRIPT_DIR/make_robot_initial_rerun_config.py"
}

make_final_grids() {
  log "Rendering final available failure grids"
  mapfile -t eval_infos < <(
    {
      find outputs/pi05_libero_plus_robot_initial_50x5/low_l1_l3_metrics -name eval_info.json 2>/dev/null || true
      find outputs/pi05_libero_plus_robot_initial_50x5/low_l1_l3_failed_rerun -name eval_info.json 2>/dev/null || true
      find outputs/pi05_libero_plus_robot_initial_50x5/high_l4_l5_part_01 -name eval_info.json 2>/dev/null || true
      find outputs/pi05_libero_plus_robot_initial_50x5/high_l4_l5_part_02 -name eval_info.json 2>/dev/null || true
      find outputs/pi05_libero_plus_robot_initial_50x5/high_l4_l5_part_03 -name eval_info.json 2>/dev/null || true
      find outputs/pi05_libero_plus_robot_initial_50x5/high_l4_l5_part_04 -name eval_info.json 2>/dev/null || true
    } | sort
  )
  args=()
  for eval_info in "${eval_infos[@]}"; do
    args+=(--eval-info "$eval_info")
  done
  "$VENV/bin/python" "$SCRIPT_DIR/make_robot_initial_failure_grids.py" \
    "${args[@]}" \
    --output-dir note3 \
    --grid-prefix robot_initial_full_failure_grid \
    --grid-size 16 \
    --cols 4 \
    --fps 20 \
    --hold-last-frames 40 2>&1 | tee -a "$LOG"
}

log "Queue started"
"$VENV/bin/python" "$SCRIPT_DIR/make_robot_initial_eval_configs.py" 2>&1 | tee -a "$LOG"

run_config "configs/local/robot_initial_50x5/robot_initial_low_l1_l3_metrics.json"
low_cfg="$(generate_low_failure_rerun_config)"
if [[ "$low_cfg" != "NO_LOW_FAILURES" ]]; then
  run_config "$low_cfg"
else
  log "No L1-L3 failures to rerun"
fi

run_config "configs/local/robot_initial_50x5/robot_initial_high_l4_l5_part_01.json"
run_config "configs/local/robot_initial_50x5/robot_initial_high_l4_l5_part_02.json"
run_config "configs/local/robot_initial_50x5/robot_initial_high_l4_l5_part_03.json"
run_config "configs/local/robot_initial_50x5/robot_initial_high_l4_l5_part_04.json"

make_final_grids
log "Queue complete"
