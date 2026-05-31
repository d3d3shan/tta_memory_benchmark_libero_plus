#!/usr/bin/env python
"""Render all available Camera Viewpoints failure videos into 16-way grids."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Any

from make_camera_view_eval_report import collect_records, render_grid


def choose_failure_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deduplicate failures, preferring records that already have videos."""
    by_key: dict[tuple[int, int], dict[str, Any]] = {}
    for record in records:
        if record["success"]:
            continue
        key = (int(record["task_id"]), int(record["episode"]))
        previous = by_key.get(key)
        if previous is None:
            by_key[key] = record
            continue
        if not previous.get("video_path") and record.get("video_path"):
            by_key[key] = record

    failures = []
    missing_video = []
    for idx, key in enumerate(sorted(by_key), start=1):
        item = dict(by_key[key])
        item["failure_index"] = idx
        if item.get("video_path"):
            failures.append(item)
        else:
            missing_video.append(item)
    return failures, missing_video


def write_report(
    output_dir: Path,
    selected_failures: list[dict[str, Any]],
    missing_video: list[dict[str, Any]],
    grid_paths: list[Path],
    eval_infos: list[str],
    grid_size: int,
) -> None:
    payload = {
        "eval_infos": eval_infos,
        "failure_videos": selected_failures,
        "failure_video_count": len(selected_failures),
        "missing_video_failures": missing_video,
        "missing_video_count": len(missing_video),
        "grid_videos": [path.name for path in grid_paths],
        "grid_size": grid_size,
    }
    (output_dir / "camera_view_full_failure_grids.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Camera View full failure grids",
        "",
        f"- Failure videos rendered: `{len(selected_failures)}`",
        f"- Failures missing videos: `{len(missing_video)}`",
        f"- Grid size: `{grid_size}`",
        "",
        "## Grid Videos",
        "",
    ]
    for path in grid_paths:
        lines.append(f"- `{path.name}`")

    lines.extend(
        [
            "",
            "## Failure Video Legend",
            "",
            "| # | phase | task | ep | seed | level | view tuple | reward | video |",
            "|---:|---|---:|---:|---:|---:|---|---:|---|",
        ]
    )
    for item in selected_failures:
        lines.append(
            f"| {item['failure_index']} | {item['phase']} | {item['task_id']} | {item['episode']} | "
            f"{item['seed']} | {item.get('difficulty_level')} | `{item['camera_view_tuple']}` | "
            f"{item['max_reward']} | `{item['video_path']}` |"
        )

    if missing_video:
        lines.extend(
            [
                "",
                "## Missing Video Failures",
                "",
                "These failures are present in metrics-only evals but do not yet have a corresponding failure video.",
                "",
                "| task | ep | seed | level | view tuple | eval info |",
                "|---:|---:|---:|---:|---|---|",
            ]
        )
        for item in missing_video:
            lines.append(
                f"| {item['task_id']} | {item['episode']} | {item['seed']} | {item.get('difficulty_level')} | "
                f"`{item['camera_view_tuple']}` | `{item['eval_info']}` |"
            )

    (output_dir / "camera_view_full_failure_grids.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-info", action="append", required=True)
    parser.add_argument("--output-dir", default="note2")
    parser.add_argument("--grid-prefix", default="camera_view_full_failure_grid")
    parser.add_argument("--grid-size", type=int, default=16)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--fps", type=float, default=20.0)
    parser.add_argument("--hold-last-frames", type=int, default=40)
    args = parser.parse_args()

    repo_root = Path(os.environ.get("OPENTAU_DIR", Path.cwd())).resolve()
    output_dir = repo_root / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    records = []
    for eval_info in args.eval_info:
        phase = Path(eval_info).parts[1] if "/" in eval_info else "eval"
        records.extend(collect_records(repo_root, [eval_info], phase))

    selected_failures, missing_video = choose_failure_records(records)
    grid_paths = []
    for grid_idx, start in enumerate(range(0, len(selected_failures), args.grid_size), start=1):
        chunk = selected_failures[start : start + args.grid_size]
        if not chunk:
            continue
        grid_path = output_dir / f"{args.grid_prefix}_{grid_idx:03d}.mp4"
        render_grid(repo_root, chunk, grid_path, args.cols, args.fps, args.hold_last_frames)
        grid_paths.append(grid_path)

    write_report(output_dir, selected_failures, missing_video, grid_paths, args.eval_info, args.grid_size)
    print(output_dir / "camera_view_full_failure_grids.md")
    for path in grid_paths:
        print(path)
    if missing_video:
        print(f"missing_video_failures={len(missing_video)}")


if __name__ == "__main__":
    main()
