#!/usr/bin/env python
"""Collect LIBERO-plus camera-view failures and render a labeled 16-way grid."""

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


DEFAULT_EVAL_INFOS = [
    "outputs/pi05_libero_plus_perturb_eval/libero_10_camera_viewpoints/post-training-eval/libero-libero_10-2-20260526-223949/eval_info.json",
    "outputs/pi05_libero_plus_camera_view_until16/extra_802_804/post-training-eval/libero-libero_10-2-20260527-191102/eval_info.json",
    "outputs/pi05_libero_plus_camera_view_until16/extra_805_809/post-training-eval/libero-libero_10-2-20260527-191549/eval_info.json",
]


def load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def camera_view_tuple(task_name: str) -> str:
    match = re.search(r"_view_([^_]+_[^_]+_[^_]+_[^_]+_[^_]+)_", task_name)
    if not match:
        return "unknown"
    return match.group(1).replace("_", ",")


def short_task_name(task_name: str) -> str:
    base = re.sub(r"_view_.*$", "", task_name)
    base = re.sub(r"^[A-Z0-9]+_", "", base)
    return base.lower().replace("_", " ")[:52]


def collect_failures(repo_root: Path, eval_infos: list[str], limit: int) -> list[dict[str, Any]]:
    classification_path = repo_root.parent / "LIBERO-plus/libero/libero/benchmark/task_classification.json"
    classification = load_json(classification_path)["libero_10"]
    tasks = {int(item["id"]) - 1: item for item in classification}

    failures: list[dict[str, Any]] = []
    for raw_eval_info in eval_infos:
        eval_info_path = repo_root / raw_eval_info
        info = load_json(eval_info_path)
        for item in info["per_task"]:
            task_id = int(item["task_id"])
            task_meta = tasks.get(task_id, {})
            task_name = task_meta.get("name", f"task_{task_id}")
            successes = item["metrics"].get("successes", [])
            video_paths = item["metrics"].get("video_paths", [])
            sum_rewards = item["metrics"].get("sum_rewards", [])
            max_rewards = item["metrics"].get("max_rewards", [])
            for ep_idx, success in enumerate(successes):
                if success:
                    continue
                video_path = video_paths[ep_idx]
                failures.append(
                    {
                        "index": len(failures) + 1,
                        "task_id": task_id,
                        "episode": ep_idx,
                        "task_name": task_name,
                        "short_task": short_task_name(task_name),
                        "category": task_meta.get("category", "Camera Viewpoints"),
                        "difficulty_level": task_meta.get("difficulty_level"),
                        "camera_view_tuple": camera_view_tuple(task_name),
                        "sum_reward": sum_rewards[ep_idx] if ep_idx < len(sum_rewards) else None,
                        "max_reward": max_rewards[ep_idx] if ep_idx < len(max_rewards) else None,
                        "video_path": video_path,
                        "eval_info": raw_eval_info,
                    }
                )
                if len(failures) >= limit:
                    return failures
    return failures


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def draw_label(frame: np.ndarray, item: dict[str, Any], label_mode: str) -> np.ndarray:
    img = Image.fromarray(frame[:, :, :3].astype(np.uint8))
    draw = ImageDraw.Draw(img, "RGBA")
    if label_mode == "index":
        badge_w, badge_h = 112, 38
        draw.rounded_rectangle((6, 6, badge_w, badge_h), radius=8, fill=(0, 0, 0, 185))
        draw.rectangle((6, 6, 14, badge_h), fill=(165, 40, 35, 230))
        draw.text(
            (19, 13),
            f"{item['index']:02d}  T{item['task_id']} E{item['episode']}",
            fill=(255, 255, 255, 255),
            font=load_font(15, bold=True),
        )
        return np.asarray(img)

    title = load_font(17, bold=True)
    body = load_font(13)
    bar_h = 72
    draw.rectangle((0, 0, img.width, bar_h), fill=(0, 0, 0, 185))
    draw.rectangle((0, 0, 10, bar_h), fill=(165, 40, 35, 230))
    draw.text((16, 5), f"FAIL {item['index']:02d} | task {item['task_id']} ep {item['episode']}", fill=(255, 255, 255, 255), font=title)
    draw.text((16, 29), f"Camera Viewpoints | view={item['camera_view_tuple']} | diff={item['difficulty_level']}", fill=(245, 245, 245, 255), font=body)
    draw.text((16, 50), item["short_task"], fill=(230, 230, 230, 255), font=body)
    return np.asarray(img)


def render_grid(
    repo_root: Path,
    failures: list[dict[str, Any]],
    output: Path,
    cols: int,
    fps: float,
    hold_last_frames: int,
    label_mode: str,
) -> None:
    if not failures:
        raise ValueError("No failures to render.")

    readers = []
    states = []
    try:
        for item in failures:
            video_path = repo_root / item["video_path"]
            reader = imageio.get_reader(video_path)
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
                canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
                active = False
                for idx, state in enumerate(states):
                    if not state["done"]:
                        active = True
                    frame = state["frame"]
                    row = idx // cols
                    col = idx % cols
                    canvas[row * h : (row + 1) * h, col * w : (col + 1) * w] = draw_label(
                        frame, failures[idx], label_mode
                    )
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
                    row = idx // cols
                    col = idx % cols
                    canvas[row * h : (row + 1) * h, col * w : (col + 1) * w] = draw_label(
                        state["frame"], failures[idx], label_mode
                    )
                writer.append_data(canvas)
        finally:
            writer.close()
    finally:
        for reader in readers:
            reader.close()


def write_reports(note_dir: Path, failures: list[dict[str, Any]], grid_path: Path, eval_infos: list[str]) -> None:
    note_dir.mkdir(parents=True, exist_ok=True)
    json_path = note_dir / "camera_view_failures_16.json"
    md_path = note_dir / "camera_view_failures_16.md"
    json_path.write_text(json.dumps({"failures": failures, "eval_infos": eval_infos}, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# pi0.5 LIBERO-plus camera-view failure sample",
        "",
        "This is a stop-at-16 failure sample, not the full 419-task Camera Viewpoints evaluation.",
        "",
        f"- Grid video: `{grid_path.name}`",
        "- Suite: `libero_10`",
        "- Category: `Camera Viewpoints`",
        "- Policy: `TensorAuto/tPi0.5-libero`",
        "- Episodes per newly sampled task: `2`",
        "- Horizon: `520` env steps, matching the current LIBERO-10 eval config.",
        "- Video grid rendering: each cell is allowed to finish independently; shorter cells hold their last frame instead of cutting the whole grid.",
        "- Success rule: original OpenTau/LIBERO sparse success; failed videos listed here have `success=False` and `max_reward=0`.",
        "",
        "| # | task | ep | view tuple | diff | reward | video |",
        "|---:|---:|---:|---|---:|---:|---|",
    ]
    for item in failures:
        lines.append(
            f"| {item['index']} | {item['task_id']} | {item['episode']} | "
            f"`{item['camera_view_tuple']}` | {item['difficulty_level']} | "
            f"{item['max_reward']} | `{item['video_path']}` |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-info", action="append", dest="eval_infos", default=None)
    parser.add_argument("--limit", type=int, default=16)
    parser.add_argument("--output-dir", default="note1")
    parser.add_argument("--grid-name", default="camera_view_failures_16_labeled_grid.mp4")
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--fps", type=float, default=20.0)
    parser.add_argument("--hold-last-frames", type=int, default=40)
    parser.add_argument("--label-mode", choices=["detail", "index"], default="detail")
    args = parser.parse_args()

    repo_root = Path(os.environ.get("OPENTAU_DIR", Path.cwd())).resolve()
    eval_infos = args.eval_infos or DEFAULT_EVAL_INFOS
    failures = collect_failures(repo_root, eval_infos, args.limit)
    if len(failures) < args.limit:
        raise RuntimeError(f"Only found {len(failures)} failures, expected {args.limit}.")

    note_dir = repo_root / args.output_dir
    grid_path = note_dir / args.grid_name
    render_grid(repo_root, failures, grid_path, args.cols, args.fps, args.hold_last_frames, args.label_mode)
    write_reports(note_dir, failures, grid_path, eval_infos)
    print(grid_path)
    print(note_dir / "camera_view_failures_16.md")
    print(note_dir / "camera_view_failures_16.json")


if __name__ == "__main__":
    main()
