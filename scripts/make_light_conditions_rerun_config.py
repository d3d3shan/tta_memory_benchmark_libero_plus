#!/usr/bin/env python
"""Create a video rerun config for low-difficulty Light Conditions failures."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path


ROOT = Path(os.environ.get("OPENTAU_DIR", Path.cwd())).resolve()
METRICS_CONFIG = ROOT / "configs/local/light_conditions_50x5/light_conditions_low_l1_l3_metrics.json"
METRICS_ROOT = ROOT / "outputs/pi05_libero_plus_light_conditions_50x5/low_l1_l3_metrics"
OUT_CONFIG = ROOT / "configs/local/light_conditions_50x5/light_conditions_low_l1_l3_failed_rerun.json"
MANIFEST = ROOT / "note4/light_conditions_low_l1_l3_failed_rerun_manifest.json"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    eval_infos = sorted(METRICS_ROOT.rglob("eval_info.json"))
    if not eval_infos:
        raise SystemExit(f"metrics eval_info not found under {METRICS_ROOT}")
    info = load_json(eval_infos[-1])
    failed_task_ids = sorted(
        {
            int(item["task_id"])
            for item in info["per_task"]
            if any(not success for success in item["metrics"].get("successes", []))
        }
    )
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(
        json.dumps(
            {
                "source_eval_info": str(eval_infos[-1].relative_to(ROOT)),
                "failed_task_ids": failed_task_ids,
                "failed_task_count": len(failed_task_ids),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if not failed_task_ids:
        print("NO_LOW_FAILURES")
        return

    cfg = deepcopy(load_json(METRICS_CONFIG))
    cfg["output_dir"] = "outputs/pi05_libero_plus_light_conditions_50x5/low_l1_l3_failed_rerun"
    cfg["env"]["task_ids"] = failed_task_ids
    cfg["eval"]["max_episodes_rendered"] = 5
    cfg["eval"]["grid_size"] = [1, 5]
    cfg["wandb"]["notes"] = "Light Conditions L1-L3 failed-task rerun with video."
    OUT_CONFIG.write_text(json.dumps(cfg, indent=4) + "\n", encoding="utf-8")
    print(OUT_CONFIG.relative_to(ROOT))


if __name__ == "__main__":
    main()
