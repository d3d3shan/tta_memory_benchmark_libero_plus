#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV="$ROOT/.venv-opentau"
OPENTAU_DIR="${OPENTAU_DIR:-$ROOT/OpenTau}"
export OPENTAU_DIR
cd "$OPENTAU_DIR"

LOG="note2/camera_view_remaining_queue.log"
mkdir -p note2

log() {
  printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "$LOG"
}

wait_for_eval_info() {
  local dir="$1"
  log "Waiting for eval_info under $dir"
  until find "$dir" -name eval_info.json -print -quit | grep -q .; do
    sleep 60
  done
}

run_config() {
  local cfg="$1"
  log "Running $cfg"
  "$SCRIPT_DIR/run_libero_plus_eval_config.sh" "$cfg" 2>&1 | tee -a "$LOG"
  log "Finished $cfg"
}

generate_low_failure_rerun_config() {
  "$VENV/bin/python" - <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["OPENTAU_DIR"])
base = json.loads((root / "configs/local/libero_plus_camera_view_50x5_metrics_050_149.json").read_text())
low_root = root / "outputs/pi05_libero_plus_camera_view_50x5/remaining_150_418_low_l1_l3_metrics"
eval_infos = list(low_root.rglob("eval_info.json"))
if not eval_infos:
    raise SystemExit("low metrics eval_info not found")
info = json.loads(eval_infos[-1].read_text())
failed_task_ids = []
for item in info["per_task"]:
    if any(not success for success in item["metrics"]["successes"]):
        failed_task_ids.append(int(item["task_id"]))
failed_task_ids = sorted(set(failed_task_ids))
manifest = {
    "source_eval_info": str(eval_infos[-1].relative_to(root)),
    "failed_task_ids": failed_task_ids,
}
(root / "note2/camera_view_low_l1_l3_failed_rerun_manifest.json").write_text(
    json.dumps(manifest, indent=2) + "\n",
    encoding="utf-8",
)
if not failed_task_ids:
    print("NO_LOW_FAILURES")
    raise SystemExit(0)
cfg = json.loads(json.dumps(base))
cfg["output_dir"] = "outputs/pi05_libero_plus_camera_view_50x5/remaining_150_418_low_l1_l3_failed_rerun"
cfg["env"]["task_ids"] = failed_task_ids
cfg["eval"]["max_episodes_rendered"] = 5
cfg["eval"]["grid_size"] = [1, 5]
path = root / "configs/local/camera_view_50x5_remaining/remaining_150_418_low_l1_l3_failed_rerun.json"
path.write_text(json.dumps(cfg, indent=4) + "\n", encoding="utf-8")
print(path.relative_to(root))
PY
}

make_final_grids() {
  log "Rendering final available failure grids"
  mapfile -t eval_infos < <(
    {
      find outputs/pi05_libero_plus_camera_view_50x5/part_000_049 -name eval_info.json
      find outputs/pi05_libero_plus_camera_view_50x5/failed_050_149_rerun_part_01 -name eval_info.json
      find outputs/pi05_libero_plus_camera_view_50x5/failed_050_149_rerun_part_02 -name eval_info.json
      find outputs/pi05_libero_plus_camera_view_50x5/remaining_150_418_high_l4_l5_part_01 -name eval_info.json
      find outputs/pi05_libero_plus_camera_view_50x5/remaining_150_418_high_l4_l5_part_02 -name eval_info.json
      find outputs/pi05_libero_plus_camera_view_50x5/remaining_150_418_high_l4_l5_part_03 -name eval_info.json
      find outputs/pi05_libero_plus_camera_view_50x5/remaining_150_418_high_l4_l5_part_04 -name eval_info.json
      find outputs/pi05_libero_plus_camera_view_50x5/remaining_150_418_high_l4_l5_part_05 -name eval_info.json
      find outputs/pi05_libero_plus_camera_view_50x5/remaining_150_418_low_l1_l3_failed_rerun -name eval_info.json 2>/dev/null || true
    } | sort
  )
  args=()
  for eval_info in "${eval_infos[@]}"; do
    args+=(--eval-info "$eval_info")
  done
  "$VENV/bin/python" "$SCRIPT_DIR/make_camera_view_full_failure_grids.py" \
    "${args[@]}" \
    --output-dir note2 \
    --grid-prefix camera_view_full_failure_grid \
    --grid-size 16 \
    --cols 4 \
    --fps 20 \
    --hold-last-frames 40 2>&1 | tee -a "$LOG"
}

log "Queue started"
wait_for_eval_info "outputs/pi05_libero_plus_camera_view_50x5/remaining_150_418_high_l4_l5_part_02"

run_config "configs/local/camera_view_50x5_failed_050_149_rerun/failed_050_149_rerun_part_01.json"
run_config "configs/local/camera_view_50x5_failed_050_149_rerun/failed_050_149_rerun_part_02.json"
run_config "configs/local/camera_view_50x5_remaining/remaining_150_418_high_l4_l5_part_03.json"
run_config "configs/local/camera_view_50x5_remaining/remaining_150_418_high_l4_l5_part_04.json"
run_config "configs/local/camera_view_50x5_remaining/remaining_150_418_high_l4_l5_part_05.json"
run_config "configs/local/camera_view_50x5_remaining/remaining_150_418_low_l1_l3_metrics.json"

low_cfg="$(generate_low_failure_rerun_config)"
if [[ "$low_cfg" != "NO_LOW_FAILURES" ]]; then
  run_config "$low_cfg"
else
  log "No L1-L3 low-chunk failures to rerun"
fi

make_final_grids
log "Queue complete"
