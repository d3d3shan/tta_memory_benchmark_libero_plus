#!/usr/bin/env python3
"""Prepare HF upload folders for the three remainder LIBERO-plus perturbations.

Input is the payload copied from wzxuan:
  - reports/failure_grids/{background_textures,language_instructions,objects_layout}
  - eval_outputs/**/eval_info.json
  - configs/** and logs/**

Success rates are computed only from metric sources:
  - eval_outputs/metrics
  - eval_outputs/low_l1_l3_metrics
  - eval_outputs/high_l4_l5_videos

Failed-task reruns are copied as metadata but are not counted in benchmark rates.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any


SLUG_TO_TITLE = {
    "background_textures": "Background Textures",
    "language_instructions": "Language Instructions",
    "objects_layout": "Objects Layout",
}

SLUG_TO_REPO = {
    "background_textures": "pi05-libero-plus-background-textures-failures",
    "language_instructions": "pi05-libero-plus-language-instructions-failures",
    "objects_layout": "pi05-libero-plus-objects-layout-failures",
}

SLUG_TO_TAG = {
    "background_textures": "background-textures",
    "language_instructions": "language-instructions",
    "objects_layout": "objects-layout",
}

LOCAL_PREVIOUS = [
    {
        "title": "Camera Viewpoints",
        "repo": "pi05-libero-plus-camera-view-failures",
        "tasks": 419,
        "episodes": 2095,
        "successes": 1197,
        "failures": 898,
        "success_rate": 1197 / 2095,
        "grid_videos": 55,
        "note": "Most brittle among the completed local categories; camera pose changes strongly affect visual grounding.",
    },
    {
        "title": "Robot Initial States",
        "repo": "pi05-libero-plus-robot-initial-failures",
        "tasks": 393,
        "episodes": 1965,
        "successes": 1430,
        "failures": 535,
        "success_rate": 1430 / 1965,
        "grid_videos": 32,
        "note": "Moderate robustness; failures often come from approach pose and grasp recovery sensitivity.",
    },
    {
        "title": "Light Conditions",
        "repo": "pi05-libero-plus-light-conditions-failures",
        "tasks": 274,
        "episodes": 1370,
        "successes": 1209,
        "failures": 161,
        "success_rate": 1209 / 1370,
        "grid_videos": 10,
        "note": "Highest success among completed local categories; illumination shifts are less damaging than geometry/language changes.",
    },
]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def task_meta(classification_json: Path) -> dict[int, dict[str, Any]]:
    data = load_json(classification_json)
    return {int(item["id"]) - 1: item for item in data["libero_10"]}


def metric_eval_infos(payload_root: Path, slug: str) -> list[Path]:
    roots = [
        payload_root / "eval_outputs" / "metrics" / slug,
        payload_root / "eval_outputs" / "low_l1_l3_metrics" / slug,
        payload_root / "eval_outputs" / "high_l4_l5_videos" / slug,
    ]
    out: list[Path] = []
    for root in roots:
        if root.exists():
            out.extend(sorted(root.rglob("eval_info.json")))
    return out


def all_eval_infos(payload_root: Path, slug: str) -> list[Path]:
    out = []
    for path in sorted((payload_root / "eval_outputs").rglob("eval_info.json")):
        if f"/{slug}/" in path.as_posix():
            out.append(path)
    return out


def collect_metric_records(payload_root: Path, slug: str, meta: dict[int, dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[tuple[int, int, str]] = set()
    for eval_info in metric_eval_infos(payload_root, slug):
        info = load_json(eval_info)
        source = str(eval_info.relative_to(payload_root))
        for item in info.get("per_task", []):
            task_id = int(item["task_id"])
            task = meta.get(task_id, {})
            metrics = item["metrics"]
            successes = metrics.get("successes", [])
            sum_rewards = metrics.get("sum_rewards", [])
            max_rewards = metrics.get("max_rewards", [])
            video_paths = metrics.get("video_paths", [])
            for episode, success in enumerate(successes):
                key = (task_id, episode, source)
                if key in seen:
                    continue
                seen.add(key)
                records.append(
                    {
                        "task_id": task_id,
                        "episode": episode,
                        "seed": 1000 + episode,
                        "success": bool(success),
                        "sum_reward": sum_rewards[episode] if episode < len(sum_rewards) else None,
                        "max_reward": max_rewards[episode] if episode < len(max_rewards) else None,
                        "difficulty_level": task.get("difficulty_level"),
                        "task_name": task.get("name", f"task_{task_id}"),
                        "category": task.get("category", SLUG_TO_TITLE[slug]),
                        "video_path": video_paths[episode] if episode < len(video_paths) else None,
                        "eval_info": source,
                    }
                )
    return sorted(records, key=lambda x: (int(x["task_id"]), int(x["episode"]), x["eval_info"]))


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    successes = sum(1 for item in records if item["success"])
    episodes = len(records)
    tasks = len({int(item["task_id"]) for item in records})
    by_level: dict[str, dict[str, int]] = {}
    for item in records:
        level = str(item.get("difficulty_level") or "unknown")
        slot = by_level.setdefault(level, {"episodes": 0, "successes": 0})
        slot["episodes"] += 1
        slot["successes"] += int(bool(item["success"]))
    for slot in by_level.values():
        slot["failures"] = slot["episodes"] - slot["successes"]
        slot["success_rate"] = slot["successes"] / slot["episodes"] if slot["episodes"] else 0.0
    return {
        "tasks": tasks,
        "episodes": episodes,
        "successes": successes,
        "failures": episodes - successes,
        "success_rate": successes / episodes if episodes else 0.0,
        "by_difficulty_level": dict(sorted(by_level.items())),
    }


def copy_tree_contents(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for item in sorted(src.iterdir()):
        target = dst / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)


def dataset_readme(slug: str, summary: dict[str, Any], grid_count: int, missing_video_count: int) -> str:
    title = SLUG_TO_TITLE[slug]
    tag = SLUG_TO_TAG[slug]
    return f"""---
license: mit
task_categories:
- robotics
- video-classification
language:
- en
tags:
- libero-plus
- opentau
- pi0.5
- robotics
- failure-analysis
- {tag}
pretty_name: pi0.5 LIBERO-plus {title} Failures
---

# pi0.5 LIBERO-plus {title} Failures

Failure summary artifacts for evaluating `TensorAuto/tPi0.5-libero` on the LIBERO-plus `{title}` perturbation subset through OpenTau.

## Evaluation Setup

- Benchmark: LIBERO-plus
- Suite: `libero_10`
- Perturbation category: `{title}`
- Policy: `TensorAuto/tPi0.5-libero`
- Tasks: {summary["tasks"]}
- Episodes per task: 5
- Metric episodes: {summary["episodes"]}
- Seed schedule: episode seeds `1000` to `1004`
- Episode length: 520 steps
- Source machine: `wzxuan` under `/data/wangjinqiu/tta-memory/libero_plus_eval`

## Summary

- Successes: {summary["successes"]} / {summary["episodes"]}
- Success rate: {summary["success_rate"]:.2%}
- Failures: {summary["failures"]}
- Failure grid videos: {grid_count}
- Failures missing videos in the grid report: {missing_video_count}

## Files

- `videos/`: 16-panel failure grid videos.
- `metadata/summary.json`: benchmark counts, success rate, and difficulty-level breakdown.
- `metadata/metric_records.json`: per-episode metric records used for the success rate.
- `metadata/eval_info_paths.json`: eval files included in the payload.
- `metadata/source_configs/`: configs/logs copied from the wzxuan run payload when available.

The grid videos are for qualitative failure-mode inspection. The official success rate above is computed only from metric eval outputs and excludes failed-task video reruns.
"""


def prepare_dataset(payload_root: Path, output_root: Path, slug: str, meta: dict[int, dict[str, Any]]) -> dict[str, Any]:
    repo = SLUG_TO_REPO[slug]
    dataset_dir = output_root / repo
    if dataset_dir.exists():
        shutil.rmtree(dataset_dir)
    videos_dir = dataset_dir / "videos"
    metadata_dir = dataset_dir / "metadata"
    videos_dir.mkdir(parents=True)
    metadata_dir.mkdir(parents=True)

    grid_src = payload_root / "reports" / "failure_grids" / slug
    grid_count = 0
    for mp4 in sorted(grid_src.glob("*.mp4")):
        shutil.copy2(mp4, videos_dir / mp4.name)
        grid_count += 1

    records = collect_metric_records(payload_root, slug, meta)
    summary = summarize(records)
    eval_infos = [str(path.relative_to(payload_root)) for path in all_eval_infos(payload_root, slug)]

    copy_tree_contents(payload_root / "configs", metadata_dir / "source_configs")
    copy_tree_contents(payload_root / "logs", metadata_dir / "source_logs")
    write_json(metadata_dir / "summary.json", summary)
    write_json(metadata_dir / "metric_records.json", records)
    write_json(metadata_dir / "eval_info_paths.json", eval_infos)
    write_json(metadata_dir / "grid_videos.json", sorted(f"videos/{p.name}" for p in videos_dir.glob("*.mp4")))

    missing_video_count = max(0, int(summary["failures"]) - grid_count * 16)
    (dataset_dir / "README.md").write_text(
        dataset_readme(slug, summary, grid_count, missing_video_count), encoding="utf-8"
    )

    return {
        "title": SLUG_TO_TITLE[slug],
        "repo": repo,
        "tasks": summary["tasks"],
        "episodes": summary["episodes"],
        "successes": summary["successes"],
        "failures": summary["failures"],
        "success_rate": summary["success_rate"],
        "grid_videos": grid_count,
        "note": analysis_note(slug, summary["success_rate"]),
    }


def analysis_note(slug: str, success_rate: float) -> str:
    if slug == "background_textures":
        return "Texture/domain shift stresses visual appearance; failures are useful for checking whether policy overfits tabletop/background cues."
    if slug == "language_instructions":
        return "Language paraphrase/instruction shift directly tests semantic grounding; low score usually indicates instruction following and target disambiguation errors."
    if slug == "objects_layout":
        return "Object layout changes stress spatial search, grasp approach, and collision recovery; failures often expose planning rather than pure perception issues."
    return f"Observed success rate {success_rate:.2%}."


def write_overall_report(output_root: Path, rows: list[dict[str, Any]]) -> None:
    all_rows = LOCAL_PREVIOUS + rows
    total_success = sum(int(row["successes"]) for row in all_rows)
    total_episodes = sum(int(row["episodes"]) for row in all_rows)
    macro = sum(float(row["success_rate"]) for row in all_rows) / len(all_rows)
    micro = total_success / total_episodes if total_episodes else 0.0

    report = output_root / "pi05_libero_plus_six_perturb_hf_report.md"
    lines = [
        "# pi0.5 LIBERO-plus Perturbation Result Summary",
        "",
        "This report combines the three earlier local perturbation uploads with the three `wzxuan` perturbation uploads prepared from `/data/wangjinqiu/tta-memory/libero_plus_eval`.",
        "",
        "## Overall",
        "",
        f"- Categories summarized: `{len(all_rows)}`",
        f"- Micro success: `{total_success}/{total_episodes}` = `{micro:.2%}`",
        f"- Macro success across categories: `{macro:.2%}`",
        "- Policy: `TensorAuto/tPi0.5-libero`",
        "- Benchmark: LIBERO-plus `libero_10`, 5 episodes per task, seeds `1000..1004`",
        "",
        "## Hugging Face Datasets",
        "",
        "| Perturbation | HF dataset | Tasks | Episodes | Success | Failure grids | Short analysis |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in all_rows:
        url = f"https://huggingface.co/datasets/d3d3shan/{row['repo']}"
        lines.append(
            f"| {row['title']} | [{row['repo']}]({url}) | {row['tasks']} | {row['episodes']} | "
            f"{row['successes']}/{row['episodes']} ({row['success_rate']:.2%}) | {row['grid_videos']} | {row['note']} |"
        )
    lines.extend(
        [
            "",
            "## Caveats",
            "",
            "- Success is the LIBERO/OpenTau task-completion predicate from `eval_info.json`; videos are qualitative diagnostics.",
            "- Failed-task reruns are excluded from success-rate computation.",
            "- The three earlier local datasets and the three `wzxuan` datasets were prepared on different machines, but use the same policy, task suite, 5-episode protocol, and seed schedule.",
            "- `Sensor Noise` is not included here because the downloaded `wzxuan` payload did not contain a failure-grid report for that category.",
            "",
        ]
    )
    report.write_text("\n".join(lines), encoding="utf-8")

    write_json(
        output_root / "pi05_libero_plus_six_perturb_hf_report.json",
        {
            "micro_success": micro,
            "macro_success": macro,
            "total_successes": total_success,
            "total_episodes": total_episodes,
            "rows": all_rows,
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-root", required=True)
    parser.add_argument("--classification-json", required=True)
    parser.add_argument("--output-root", default="OpenTau/note5_hf_upload")
    args = parser.parse_args()

    payload_root = Path(args.payload_root).resolve()
    output_root = Path(args.output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    meta = task_meta(Path(args.classification_json).resolve())

    rows = []
    for slug in SLUG_TO_TITLE:
        rows.append(prepare_dataset(payload_root, output_root, slug, meta))
    write_overall_report(output_root, rows)

    for row in rows:
        print(output_root / row["repo"])
    print(output_root / "pi05_libero_plus_six_perturb_hf_report.md")


if __name__ == "__main__":
    main()
