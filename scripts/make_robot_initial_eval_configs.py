#!/usr/bin/env python
"""Generate pi0.5 LIBERO-plus Robot Initial States 50x5 eval configs."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path


ROOT = Path(os.environ.get("OPENTAU_DIR", Path.cwd())).resolve()
BASE_CONFIG = ROOT / "configs/local/pi05_libero_plus_7perturb_smoke.json"
CLASSIFICATION = ROOT.parent / "LIBERO-plus/libero/libero/benchmark/task_classification.json"
OUT_DIR = ROOT / "configs/local/robot_initial_50x5"
OUTPUT_ROOT = "outputs/pi05_libero_plus_robot_initial_50x5"


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def chunked(items: list[int], size: int) -> list[list[int]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def make_config(base: dict, output_dir: str, task_ids: list[int], render: bool, notes: str) -> dict:
    cfg = deepcopy(base)
    cfg["output_dir"] = output_dir
    cfg["seed"] = 1000
    cfg["action_chunk"] = 10
    cfg["policy"]["chunk_size"] = 10
    cfg["policy"]["n_action_steps"] = 10
    cfg["policy"]["num_steps"] = 10
    cfg["env"]["task"] = "libero_10"
    cfg["env"]["task_ids"] = task_ids
    cfg["env"]["episode_length"] = 520
    cfg["env"]["init_states"] = True
    cfg["env"]["max_parallel_tasks"] = 1
    cfg["eval"]["n_episodes"] = 5
    cfg["eval"]["batch_size"] = 1
    cfg["eval"]["use_async_envs"] = False
    cfg["eval"]["max_episodes_rendered"] = 5 if render else 0
    cfg["eval"]["grid_size"] = [1, 5] if render else [1, 1]
    cfg["eval"]["recording_root"] = None
    cfg["wandb"]["notes"] = notes
    return cfg


def write_config(path: Path, cfg: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=4) + "\n", encoding="utf-8")


def main() -> None:
    base = load_json(BASE_CONFIG)
    tasks = [
        item
        for item in load_json(CLASSIFICATION)["libero_10"]
        if item["category"] == "Robot Initial States"
    ]
    low = [int(item["id"]) - 1 for item in tasks if int(item["difficulty_level"]) <= 3]
    high = [int(item["id"]) - 1 for item in tasks if int(item["difficulty_level"]) >= 4]

    manifest = {
        "category": "Robot Initial States",
        "suite": "libero_10",
        "episodes_per_task": 5,
        "seed": 1000,
        "episode_length": 520,
        "policy": "TensorAuto/tPi0.5-libero",
        "strategy": {
            "low_l1_l3": "metrics-only first; rerun failed tasks with video",
            "high_l4_l5": "direct video recording in chunks",
        },
        "configs": [],
    }

    low_path = OUT_DIR / "robot_initial_low_l1_l3_metrics.json"
    write_config(
        low_path,
        make_config(
            base,
            f"{OUTPUT_ROOT}/low_l1_l3_metrics",
            low,
            render=False,
            notes="Robot Initial States L1-L3 metrics-only, 5 episodes per task; failed tasks will be rerun with video.",
        ),
    )
    manifest["configs"].append(
        {
            "name": "low_l1_l3_metrics",
            "config": str(low_path.relative_to(ROOT)),
            "render": False,
            "task_count": len(low),
            "task_ids": low,
        }
    )

    for idx, task_ids in enumerate(chunked(high, 50), start=1):
        path = OUT_DIR / f"robot_initial_high_l4_l5_part_{idx:02d}.json"
        write_config(
            path,
            make_config(
                base,
                f"{OUTPUT_ROOT}/high_l4_l5_part_{idx:02d}",
                task_ids,
                render=True,
                notes=f"Robot Initial States L4-L5 direct-video part {idx}, 5 episodes per task.",
            ),
        )
        manifest["configs"].append(
            {
                "name": f"high_l4_l5_part_{idx:02d}",
                "config": str(path.relative_to(ROOT)),
                "render": True,
                "task_count": len(task_ids),
                "task_ids": task_ids,
            }
        )

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(manifest_path.relative_to(ROOT))
    for item in manifest["configs"]:
        print(f"{item['name']}: {item['task_count']} tasks")


if __name__ == "__main__":
    main()
