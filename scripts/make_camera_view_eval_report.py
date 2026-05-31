#!/usr/bin/env python
"""Summarize LIBERO-plus camera-view evals and render 16-way failure grids."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path
from typing import Any

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def load_task_meta(repo_root: Path) -> dict[int, dict[str, Any]]:
    path = repo_root.parent / "LIBERO-plus/libero/libero/benchmark/task_classification.json"
    classification = load_json(path)["libero_10"]
    return {int(item["id"]) - 1: item for item in classification}


def camera_view_tuple(task_name: str) -> str:
    match = re.search(r"_view_([^_]+_[^_]+_[^_]+_[^_]+_[^_]+)_", task_name)
    if not match:
        return "unknown"
    return match.group(1).replace("_", ",")


def short_task_name(task_name: str) -> str:
    base = re.sub(r"_view_.*$", "", task_name)
    base = re.sub(r"^[A-Z0-9]+_", "", base)
    return base.lower().replace("_", " ")[:56]


def collect_records(repo_root: Path, eval_infos: list[str], phase: str) -> list[dict[str, Any]]:
    tasks = load_task_meta(repo_root)
    records: list[dict[str, Any]] = []
    for raw_eval_info in eval_infos:
        eval_info_path = repo_root / raw_eval_info
        info = load_json(eval_info_path)
        for item in info["per_task"]:
            task_id = int(item["task_id"])
            task_meta = tasks.get(task_id, {})
            task_name = task_meta.get("name", f"task_{task_id}")
            metrics = item["metrics"]
            successes = metrics.get("successes", [])
            video_paths = metrics.get("video_paths", [])
            sum_rewards = metrics.get("sum_rewards", [])
            max_rewards = metrics.get("max_rewards", [])
            for ep_idx, success in enumerate(successes):
                records.append(
                    {
                        "phase": phase,
                        "task_id": task_id,
                        "episode": ep_idx,
                        "seed": 1000 + ep_idx,
                        "success": bool(success),
                        "task_name": task_name,
                        "short_task": short_task_name(task_name),
                        "category": task_meta.get("category", "Camera Viewpoints"),
                        "difficulty_level": task_meta.get("difficulty_level"),
                        "camera_view_tuple": camera_view_tuple(task_name),
                        "sum_reward": sum_rewards[ep_idx] if ep_idx < len(sum_rewards) else None,
                        "max_reward": max_rewards[ep_idx] if ep_idx < len(max_rewards) else None,
                        "video_path": video_paths[ep_idx] if ep_idx < len(video_paths) else None,
                        "eval_info": raw_eval_info,
                    }
                )
    return records


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def draw_label(frame: np.ndarray, item: dict[str, Any]) -> np.ndarray:
    img = Image.fromarray(frame[:, :, :3].astype(np.uint8))
    draw = ImageDraw.Draw(img, "RGBA")
    badge_w, badge_h = 122, 40
    draw.rounded_rectangle((6, 6, badge_w, badge_h), radius=8, fill=(0, 0, 0, 190))
    draw.rectangle((6, 6, 15, badge_h), fill=(170, 42, 35, 235))
    draw.text(
        (20, 13),
        f"{item['failure_index']:02d} T{item['task_id']} E{item['episode']}",
        fill=(255, 255, 255, 255),
        font=load_font(15, bold=True),
    )
    return np.asarray(img)


def resize_like(frame: np.ndarray, width: int, height: int) -> np.ndarray:
    if frame.shape[1] == width and frame.shape[0] == height:
        return frame[:, :, :3].astype(np.uint8)
    return np.asarray(Image.fromarray(frame[:, :, :3].astype(np.uint8)).resize((width, height)))


def render_grid(
    repo_root: Path,
    failures: list[dict[str, Any]],
    output: Path,
    cols: int,
    fps: float,
    hold_last_frames: int,
) -> None:
    if not failures:
        raise ValueError("No failures to render.")

    readers = []
    states = []
    try:
        for item in failures:
            if not item.get("video_path"):
                raise ValueError(f"Missing video path for failure {item}")
            reader = imageio.get_reader(repo_root / item["video_path"])
            readers.append(reader)
            iterator = iter(reader)
            first = np.asarray(next(iterator))[:, :, :3].astype(np.uint8)
            states.append({"iterator": iterator, "frame": first, "done": False})

        h, w = states[0]["frame"].shape[:2]
        rows = math.ceil(len(failures) / cols)
        output.parent.mkdir(parents=True, exist_ok=True)
        writer = imageio.get_writer(output, fps=fps, macro_block_size=16, codec="libx264")
        try:
            while True:
                active = any(not state["done"] for state in states)
                canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
                for idx, state in enumerate(states):
                    frame = resize_like(state["frame"], w, h)
                    row = idx // cols
                    col = idx % cols
                    canvas[row * h : (row + 1) * h, col * w : (col + 1) * w] = draw_label(frame, failures[idx])
                writer.append_data(canvas)

                for state in states:
                    if state["done"]:
                        continue
                    try:
                        state["frame"] = np.asarray(next(state["iterator"]))[:, :, :3].astype(np.uint8)
                    except StopIteration:
                        state["done"] = True
                if not active:
                    break

            for _ in range(max(0, hold_last_frames)):
                canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
                for idx, state in enumerate(states):
                    frame = resize_like(state["frame"], w, h)
                    row = idx // cols
                    col = idx % cols
                    canvas[row * h : (row + 1) * h, col * w : (col + 1) * w] = draw_label(frame, failures[idx])
                writer.append_data(canvas)
        finally:
            writer.close()
    finally:
        for reader in readers:
            reader.close()


def success_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    success = sum(1 for item in records if item["success"])
    task_ids = sorted({item["task_id"] for item in records})
    per_task = []
    for task_id in task_ids:
        task_records = [item for item in records if item["task_id"] == task_id]
        task_success = sum(1 for item in task_records if item["success"])
        sample = task_records[0]
        per_task.append(
            {
                "task_id": task_id,
                "task_name": sample["task_name"],
                "camera_view_tuple": sample["camera_view_tuple"],
                "episodes": len(task_records),
                "successes": task_success,
                "failures": len(task_records) - task_success,
                "success_rate": task_success / len(task_records) if task_records else 0.0,
            }
        )
    return {
        "episodes": total,
        "successes": success,
        "failures": total - success,
        "success_rate": success / total if total else 0.0,
        "task_count": len(task_ids),
        "task_ids": task_ids,
        "per_task": per_task,
    }


def write_outputs(
    note_dir: Path,
    main_records: list[dict[str, Any]],
    supplement_records: list[dict[str, Any]],
    selected_failures: list[dict[str, Any]],
    grid_paths: list[Path],
    main_eval_infos: list[str],
    supplement_eval_infos: list[str],
    next_camera_index: int | None,
    incomplete_final_grid: bool,
) -> None:
    note_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "main_eval_infos": main_eval_infos,
        "supplement_eval_infos": supplement_eval_infos,
        "main_summary": success_summary(main_records),
        "supplement_summary": success_summary(supplement_records),
        "selected_failure_count": len(selected_failures),
        "selected_failures": selected_failures,
        "grid_videos": [path.name for path in grid_paths],
        "next_camera_index": next_camera_index,
        "incomplete_final_grid": incomplete_final_grid,
    }
    (note_dir / "camera_view_50x5_summary.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    main = payload["main_summary"]
    supplement = payload["supplement_summary"]
    lines = [
        "# pi0.5 LIBERO-plus Camera View 50x5 eval",
        "",
        "Main evaluation uses the first 50 Camera Viewpoints tasks, 5 episodes per task. Supplemental tasks, if any, are only used to fill the last 16-way failure grid.",
        "",
        "## Summary",
        "",
        f"- Main tasks: `{main['task_count']}`",
        f"- Main episodes: `{main['episodes']}`",
        f"- Main success: `{main['successes']}/{main['episodes']}` = `{main['success_rate']:.2%}`",
        f"- Main failures: `{main['failures']}`",
        f"- Supplemental tasks: `{supplement['task_count']}`",
        f"- Supplemental episodes: `{supplement['episodes']}`",
        f"- Selected failure videos in grids: `{len(selected_failures)}`",
        f"- Next camera index to continue from: `{next_camera_index}`",
        "- Success rule: original OpenTau/LIBERO sparse success from `eval_info.json`.",
        "- Seeds per task: episodes use `1000..1004`; with `init_states=True`, these map to fixed predefined initial states.",
        "- Grid rendering: each cell plays independently; shorter episodes hold their final frame.",
        f"- Incomplete final grid allowed: `{incomplete_final_grid}`",
        "",
        "## Grid Videos",
        "",
    ]
    for path in grid_paths:
        lines.append(f"- `{path.name}`")

    lines.extend(
        [
            "",
            "## Failure Legend",
            "",
            "| # | phase | task | ep | seed | view tuple | reward | video |",
            "|---:|---|---:|---:|---:|---|---:|---|",
        ]
    )
    for item in selected_failures:
        lines.append(
            f"| {item['failure_index']} | {item['phase']} | {item['task_id']} | {item['episode']} | "
            f"{item['seed']} | `{item['camera_view_tuple']}` | {item['max_reward']} | `{item['video_path']}` |"
        )

    lines.extend(
        [
            "",
            "## Per-Task Main Results",
            "",
            "| task | success | fail | view tuple | task name |",
            "|---:|---:|---:|---|---|",
        ]
    )
    for item in main["per_task"]:
        lines.append(
            f"| {item['task_id']} | {item['successes']}/{item['episodes']} | {item['failures']} | "
            f"`{item['camera_view_tuple']}` | `{short_task_name(item['task_name'])}` |"
        )

    (note_dir / "camera_view_50x5_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-eval-info", action="append", required=True)
    parser.add_argument("--supplement-eval-info", action="append", default=[])
    parser.add_argument("--output-dir", default="note2")
    parser.add_argument("--grid-prefix", default="camera_view_50x5_failure_grid")
    parser.add_argument("--grid-size", type=int, default=16)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--fps", type=float, default=20.0)
    parser.add_argument("--hold-last-frames", type=int, default=40)
    parser.add_argument("--next-camera-index", type=int, default=None)
    parser.add_argument("--allow-incomplete-final-grid", action="store_true")
    args = parser.parse_args()

    repo_root = Path(os.environ.get("OPENTAU_DIR", Path.cwd())).resolve()
    note_dir = repo_root / args.output_dir

    main_records = collect_records(repo_root, args.main_eval_info, "main")
    supplement_records = collect_records(repo_root, args.supplement_eval_info, "supplement")
    main_failures = [item for item in main_records if not item["success"]]
    all_failures = main_failures + [item for item in supplement_records if not item["success"]]
    if args.allow_incomplete_final_grid:
        required_failures = len(main_failures)
    else:
        required_failures = math.ceil(len(main_failures) / args.grid_size) * args.grid_size if main_failures else 0
    if len(all_failures) < required_failures:
        needed = required_failures - len(all_failures)
        raise RuntimeError(
            f"Need {needed} more failures to fill grids: main_failures={len(main_failures)}, "
            f"available_failures={len(all_failures)}, required={required_failures}."
        )

    selected_failures = []
    for idx, item in enumerate(all_failures[:required_failures], start=1):
        selected = dict(item)
        selected["failure_index"] = idx
        selected_failures.append(selected)

    grid_paths = []
    for grid_idx, start in enumerate(range(0, len(selected_failures), args.grid_size), start=1):
        chunk = selected_failures[start : start + args.grid_size]
        if not chunk:
            continue
        grid_path = note_dir / f"{args.grid_prefix}_{grid_idx:03d}.mp4"
        render_grid(repo_root, chunk, grid_path, args.cols, args.fps, args.hold_last_frames)
        grid_paths.append(grid_path)

    write_outputs(
        note_dir,
        main_records,
        supplement_records,
        selected_failures,
        grid_paths,
        args.main_eval_info,
        args.supplement_eval_info,
        args.next_camera_index,
        bool(args.allow_incomplete_final_grid and len(main_failures) % args.grid_size),
    )
    print(note_dir / "camera_view_50x5_summary.md")
    for path in grid_paths:
        print(path)


if __name__ == "__main__":
    main()
