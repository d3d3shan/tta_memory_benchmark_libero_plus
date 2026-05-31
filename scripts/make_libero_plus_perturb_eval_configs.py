#!/usr/bin/env python
"""Generate per-perturbation LIBERO-plus eval configs.

This script only writes config files. It does not run evaluation.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
from copy import deepcopy
from pathlib import Path


CATEGORIES = [
    "Background Textures",
    "Camera Viewpoints",
    "Language Instructions",
    "Light Conditions",
    "Objects Layout",
    "Robot Initial States",
    "Sensor Noise",
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def select_items(items: list[dict], limit: int, mode: str, seed: int) -> list[dict]:
    items = sorted(items, key=lambda x: int(x["id"]))
    if limit <= 0 or limit >= len(items):
        return items
    if mode == "first":
        return items[:limit]
    if mode == "random":
        rng = random.Random(seed)
        return sorted(rng.sample(items, limit), key=lambda x: int(x["id"]))
    if mode == "stride":
        if limit == 1:
            return [items[0]]
        idxs = [round(i * (len(items) - 1) / (limit - 1)) for i in range(limit)]
        return [items[i] for i in idxs]
    raise ValueError(f"Unknown sample mode: {mode}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="libero_10")
    parser.add_argument("--base-config", default="configs/local/pi05_libero_plus_7perturb_smoke.json")
    parser.add_argument("--classification-json", default="../LIBERO-plus/libero/libero/benchmark/task_classification.json")
    parser.add_argument("--out-dir", default="configs/local/libero_plus_perturb_eval")
    parser.add_argument("--output-root", default="outputs/pi05_libero_plus_perturb_eval")
    parser.add_argument("--tasks-per-category", type=int, default=5, help="0 means all tasks in each category.")
    parser.add_argument("--episodes-per-task", type=int, default=3)
    parser.add_argument("--seed", type=int, default=1000)
    parser.add_argument("--sample-mode", choices=["first", "random", "stride"], default="first")
    parser.add_argument("--episode-length", type=int, default=520)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--action-chunk", type=int, default=10)
    parser.add_argument("--max-episodes-rendered", type=int, default=3)
    parser.add_argument("--grid-cols", type=int, default=3)
    args = parser.parse_args()

    repo_root = Path(os.environ.get("OPENTAU_DIR", Path.cwd())).resolve()
    base_path = repo_root / args.base_config
    classification_path = (repo_root / args.classification_json).resolve()
    out_dir = repo_root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(base_path, encoding="utf-8") as f:
        base_cfg = json.load(f)
    with open(classification_path, encoding="utf-8") as f:
        classification = json.load(f)

    suite_items = classification[args.suite]
    manifest = {
        "suite": args.suite,
        "seed": args.seed,
        "sample_mode": args.sample_mode,
        "tasks_per_category": args.tasks_per_category,
        "episodes_per_task": args.episodes_per_task,
        "configs": [],
    }

    for category in CATEGORIES:
        category_items = [x for x in suite_items if x["category"] == category]
        selected = select_items(category_items, args.tasks_per_category, args.sample_mode, args.seed)
        task_ids = [int(x["id"]) - 1 for x in selected]

        cfg = deepcopy(base_cfg)
        slug = slugify(category)
        cfg["output_dir"] = f"{args.output_root}/{args.suite}_{slug}"
        cfg["seed"] = args.seed
        cfg["env"]["task"] = args.suite
        cfg["env"]["task_ids"] = task_ids
        cfg["env"]["episode_length"] = args.episode_length
        cfg["env"]["init_states"] = True
        cfg["env"]["max_parallel_tasks"] = 1
        cfg["policy"]["chunk_size"] = args.action_chunk
        cfg["policy"]["n_action_steps"] = args.action_chunk
        cfg["policy"]["num_steps"] = args.action_chunk
        cfg["action_chunk"] = args.action_chunk
        cfg["eval"]["n_episodes"] = args.episodes_per_task
        cfg["eval"]["batch_size"] = args.batch_size
        cfg["eval"]["use_async_envs"] = False
        cfg["eval"]["max_episodes_rendered"] = args.max_episodes_rendered
        rows = max(1, math.ceil(args.max_episodes_rendered / max(1, args.grid_cols)))
        cfg["eval"]["grid_size"] = [rows, args.grid_cols]
        cfg["eval"]["recording_root"] = None
        cfg["wandb"]["notes"] = (
            f"Evaluating pi0.5 on LIBERO-plus {args.suite}, category={category}, "
            f"tasks={len(task_ids)}, episodes_per_task={args.episodes_per_task}"
        )

        cfg_path = out_dir / f"pi05_{args.suite}_{slug}.json"
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
            f.write("\n")

        manifest["configs"].append(
            {
                "category": category,
                "config": str(cfg_path.relative_to(repo_root)),
                "n_tasks": len(task_ids),
                "task_ids": task_ids,
                "task_names": [x["name"] for x in selected],
            }
        )

    manifest_path = out_dir / f"manifest_{args.suite}.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"Wrote manifest: {manifest_path.relative_to(repo_root)}")
    for item in manifest["configs"]:
        print(f"{item['category']}: {item['config']} ({item['n_tasks']} tasks)")


if __name__ == "__main__":
    main()
