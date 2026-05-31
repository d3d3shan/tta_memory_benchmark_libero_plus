#!/usr/bin/env python
"""Aggregate LIBERO-plus perturbation eval outputs.

The script expects the directory layout produced by
scripts/run_libero_plus_eval_config.sh and the manifest produced by
scripts/make_libero_plus_perturb_eval_configs.py.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path


ORIGINAL_COUNTS = {
    "Background Textures": 289,
    "Camera Viewpoints": 419,
    "Language Instructions": 383,
    "Light Conditions": 274,
    "Objects Layout": 312,
    "Robot Initial States": 393,
    "Sensor Noise": 449,
}


def slugify(value: str) -> str:
    return value.lower().replace(" ", "_")


def latest_eval_info(output_root: Path, category: str) -> Path:
    candidates = sorted(
        (output_root / f"libero_10_{slugify(category)}").glob("post-training-eval/*/eval_info.json"),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        raise FileNotFoundError(f"No eval_info.json found for {category} under {output_root}")
    return candidates[-1]


def load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def task_successes(info: dict) -> dict[int, list[bool]]:
    result = {}
    for item in info["per_task"]:
        result[int(item["task_id"])] = [bool(v) for v in item["metrics"]["successes"]]
    return result


def representative_videos(info: dict) -> list[str]:
    success_video = None
    failure_video = None
    for item in info["per_task"]:
        for ok, path in zip(item["metrics"]["successes"], item["metrics"]["video_paths"], strict=True):
            if ok and success_video is None:
                success_video = path
            if not ok and failure_video is None:
                failure_video = path
    videos = []
    if success_video is not None:
        videos.append(success_video)
    if failure_video is not None:
        videos.append(failure_video)
    return videos


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="configs/local/libero_plus_perturb_eval/manifest_libero_10.json")
    parser.add_argument("--output-root", default="outputs/pi05_libero_plus_perturb_eval")
    parser.add_argument("--note-dir", default="note")
    parser.add_argument("--tag", default="pi05_libero_plus_standard")
    args = parser.parse_args()

    repo_root = Path(os.environ.get("OPENTAU_DIR", Path.cwd())).resolve()
    manifest = load_json(repo_root / args.manifest)
    output_root = repo_root / args.output_root
    note_dir = repo_root / args.note_dir
    note_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    all_videos = []
    total_success = 0
    total_episodes = 0
    total_eval_s = 0.0
    category_scores = []

    for entry in manifest["configs"]:
        category = entry["category"]
        eval_path = latest_eval_info(output_root, category)
        info = load_json(eval_path)
        overall = info["overall"]
        n_episodes = int(overall["n_episodes"])
        success_rate = float(overall["pc_success"])
        successes = round(success_rate * n_episodes / 100)
        eval_s = float(overall.get("eval_per_gpu_s", 0.0))
        rows.append(
            {
                "category": category,
                "original_count": ORIGINAL_COUNTS.get(category, ""),
                "sampled_tasks": entry["n_tasks"],
                "episodes": n_episodes,
                "successes": successes,
                "success_rate": success_rate,
                "eval_s": eval_s,
                "eval_ep_s": float(overall.get("eval_ep_s", 0.0)),
                "eval_info": str(eval_path.relative_to(repo_root)),
                "task_ids": ",".join(str(v) for v in entry["task_ids"]),
                "task_successes": json.dumps(task_successes(info), ensure_ascii=False),
            }
        )
        total_success += successes
        total_episodes += n_episodes
        total_eval_s += eval_s
        category_scores.append(success_rate)
        all_videos.extend(representative_videos(info))

    macro_success = sum(category_scores) / len(category_scores)
    micro_success = total_success / total_episodes * 100

    csv_path = note_dir / f"{args.tag}.csv"
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    json_path = note_dir / f"{args.tag}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "suite": manifest["suite"],
                "seed": manifest["seed"],
                "sample_mode": manifest["sample_mode"],
                "tasks_per_category": manifest["tasks_per_category"],
                "episodes_per_task": manifest["episodes_per_task"],
                "macro_success": macro_success,
                "micro_success": micro_success,
                "total_success": total_success,
                "total_episodes": total_episodes,
                "total_eval_s": total_eval_s,
                "rows": rows,
                "representative_videos": all_videos,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    video_list_path = note_dir / f"{args.tag}_representative_videos.txt"
    with open(video_list_path, "w", encoding="utf-8") as f:
        for path in all_videos:
            f.write(path + "\n")

    md_path = note_dir / f"{args.tag}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# pi0.5 LIBERO-plus standard eval\n\n")
        f.write("## Scope\n\n")
        f.write(
            "This is a cost-effective standard run on `libero_10`: 7 perturbation categories, "
            "8 stride-sampled tasks per category, 2 fixed-seed episodes per task, 112 episodes total.\n\n"
        )
        f.write(
            "Important: LIBERO-plus original category counts are not equal. This run intentionally uses "
            "equal samples per category for macro comparison across perturbation types; it is not the "
            "full original-distribution weighted benchmark.\n\n"
        )
        f.write("## Overall\n\n")
        f.write(f"- Macro success across 7 categories: `{macro_success:.2f}%`\n")
        f.write(f"- Micro success across sampled episodes: `{micro_success:.2f}%` ({total_success}/{total_episodes})\n")
        f.write(f"- Total eval wall time recorded by eval loop: `{total_eval_s:.1f}s`\n\n")
        f.write("## Per Category\n\n")
        f.write("| Category | Original count | Sampled tasks | Episodes | Success | Eval s | Eval s/ep |\n")
        f.write("| --- | ---: | ---: | ---: | ---: | ---: | ---: |\n")
        for row in rows:
            f.write(
                f"| {row['category']} | {row['original_count']} | {row['sampled_tasks']} | "
                f"{row['episodes']} | {row['success_rate']:.2f}% ({row['successes']}/{row['episodes']}) | "
                f"{row['eval_s']:.1f} | {row['eval_ep_s']:.2f} |\n"
            )
        f.write("\n## Config\n\n")
        f.write("- Policy: `TensorAuto/tPi0.5-libero`\n")
        f.write("- Suite: `libero_10`\n")
        f.write("- Sampling: `stride`, `tasks_per_category=8`, `episodes_per_task=2`, seed `1000`\n")
        f.write("- Runtime: `batch_size=1`, `action_chunk=10`, `MUJOCO_GL=egl`, Hugging Face offline mode\n")
        f.write("- Memory control: policy is loaded once; LIBERO envs are created lazily one task at a time\n")
        f.write("- Video: per-task grids and all episode videos are under each category output directory\n\n")
        f.write("## Output Files\n\n")
        f.write(f"- CSV summary: `{csv_path.relative_to(repo_root)}`\n")
        f.write(f"- JSON summary: `{json_path.relative_to(repo_root)}`\n")
        f.write(f"- Representative video list: `{video_list_path.relative_to(repo_root)}`\n")
        f.write("- Manifest: `configs/local/libero_plus_perturb_eval/manifest_libero_10.json`\n\n")
        f.write("## Task-Level Successes\n\n")
        for row in rows:
            f.write(f"- {row['category']}: `{row['task_successes']}`\n")

    print(md_path)
    print(csv_path)
    print(json_path)
    print(video_list_path)


if __name__ == "__main__":
    main()
