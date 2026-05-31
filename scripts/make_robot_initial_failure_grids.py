#!/usr/bin/env python
"""Render Robot Initial States failure videos into 16-way grids."""

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
    return {int(item["id"]) - 1: item for item in load_json(path)["libero_10"]}


def robot_init_id(task_name: str) -> str:
    match = re.search(r"_initstate_([^_]+)$", task_name)
    return match.group(1) if match else "unknown"


def camera_view_tuple(task_name: str) -> str:
    match = re.search(r"_view_([^_]+_[^_]+_[^_]+_[^_]+_[^_]+)_", task_name)
    return match.group(1).replace("_", ",") if match else "unknown"


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
                        "category": task_meta.get("category", "Robot Initial States"),
                        "difficulty_level": task_meta.get("difficulty_level"),
                        "robot_init_state": robot_init_id(task_name),
                        "camera_view_tuple": camera_view_tuple(task_name),
                        "sum_reward": sum_rewards[ep_idx] if ep_idx < len(sum_rewards) else None,
                        "max_reward": max_rewards[ep_idx] if ep_idx < len(max_rewards) else None,
                        "video_path": video_paths[ep_idx] if ep_idx < len(video_paths) else None,
                        "eval_info": raw_eval_info,
                    }
                )
    return records


def choose_failure_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_key: dict[tuple[int, int], dict[str, Any]] = {}
    for record in records:
        if record["success"]:
            continue
        key = (int(record["task_id"]), int(record["episode"]))
        previous = by_key.get(key)
        if previous is None or (not previous.get("video_path") and record.get("video_path")):
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


def load_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


def draw_label(frame: np.ndarray, item: dict[str, Any]) -> np.ndarray:
    img = Image.fromarray(frame[:, :, :3].astype(np.uint8))
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rounded_rectangle((6, 6, 170, 48), radius=8, fill=(0, 0, 0, 190))
    draw.rectangle((6, 6, 15, 48), fill=(170, 42, 35, 235))
    draw.text(
        (20, 11),
        f"{item['failure_index']:03d} T{item['task_id']} E{item['episode']}",
        fill=(255, 255, 255, 255),
        font=load_font(14, bold=True),
    )
    draw.text(
        (20, 29),
        f"L{item.get('difficulty_level')} init={item.get('robot_init_state')}",
        fill=(235, 235, 235, 255),
        font=load_font(12),
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
    readers = []
    states = []
    try:
        for item in failures:
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
                    row = idx // cols
                    col = idx % cols
                    frame = draw_label(resize_like(state["frame"], w, h), failures[idx])
                    canvas[row * h : (row + 1) * h, col * w : (col + 1) * w] = frame
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
                    frame = draw_label(resize_like(state["frame"], w, h), failures[idx])
                    canvas[row * h : (row + 1) * h, col * w : (col + 1) * w] = frame
                writer.append_data(canvas)
        finally:
            writer.close()
    finally:
        for reader in readers:
            reader.close()


def success_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    success = sum(1 for item in records if item["success"])
    return {
        "episodes": total,
        "successes": success,
        "failures": total - success,
        "success_rate": success / total if total else 0.0,
        "task_count": len({item["task_id"] for item in records}),
    }


def write_report(
    output_dir: Path,
    records: list[dict[str, Any]],
    selected_failures: list[dict[str, Any]],
    missing_video: list[dict[str, Any]],
    grid_paths: list[Path],
    eval_infos: list[str],
    grid_size: int,
) -> None:
    payload = {
        "eval_infos": eval_infos,
        "summary": success_summary(records),
        "failure_videos": selected_failures,
        "failure_video_count": len(selected_failures),
        "missing_video_failures": missing_video,
        "missing_video_count": len(missing_video),
        "grid_videos": [path.name for path in grid_paths],
        "grid_size": grid_size,
    }
    (output_dir / "robot_initial_full_failure_grids.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )

    summary = payload["summary"]
    lines = [
        "# Robot Initial States full failure grids",
        "",
        f"- Tasks: `{summary['task_count']}`",
        f"- Episodes: `{summary['episodes']}`",
        f"- Success: `{summary['successes']}/{summary['episodes']}` = `{summary['success_rate']:.2%}`",
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
            "| # | phase | task | ep | seed | level | init state | reward | video |",
            "|---:|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for item in selected_failures:
        lines.append(
            f"| {item['failure_index']} | {item['phase']} | {item['task_id']} | {item['episode']} | "
            f"{item['seed']} | {item.get('difficulty_level')} | {item.get('robot_init_state')} | "
            f"{item['max_reward']} | `{item['video_path']}` |"
        )

    if missing_video:
        lines.extend(
            [
                "",
                "## Missing Video Failures",
                "",
                "| task | ep | seed | level | init state | eval info |",
                "|---:|---:|---:|---:|---:|---|",
            ]
        )
        for item in missing_video:
            lines.append(
                f"| {item['task_id']} | {item['episode']} | {item['seed']} | {item.get('difficulty_level')} | "
                f"{item.get('robot_init_state')} | `{item['eval_info']}` |"
            )

    (output_dir / "robot_initial_full_failure_grids.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-info", action="append", required=True)
    parser.add_argument("--output-dir", default="note3")
    parser.add_argument("--grid-prefix", default="robot_initial_full_failure_grid")
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

    write_report(output_dir, records, selected_failures, missing_video, grid_paths, args.eval_info, args.grid_size)
    print(output_dir / "robot_initial_full_failure_grids.md")
    for path in grid_paths:
        print(path)
    if missing_video:
        print(f"missing_video_failures={len(missing_video)}")


if __name__ == "__main__":
    main()
