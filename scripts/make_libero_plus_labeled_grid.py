#!/usr/bin/env python
"""Create a labeled comparison grid from LIBERO-plus eval videos."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def load_summary(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_video_metadata(summary: dict) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    for row in summary["rows"]:
        category = row["category"]
        eval_info_path = Path(row["eval_info"])
        with open(eval_info_path, encoding="utf-8") as f:
            info = json.load(f)
        for item in info["per_task"]:
            task_id = str(item["task_id"])
            successes = item["metrics"]["successes"]
            for ep_idx, video_path in enumerate(item["metrics"].get("video_paths", [])):
                metadata[video_path] = {
                    "category": category,
                    "task_id": task_id,
                    "episode": str(ep_idx),
                    "success": "SUCCESS" if successes[ep_idx] else "FAIL",
                }
    return metadata


def read_video(path: Path, max_frames: int | None) -> list[np.ndarray]:
    frames = imageio.mimread(path)
    if max_frames is not None:
        frames = frames[:max_frames]
    out = []
    for frame in frames:
        arr = np.asarray(frame)
        if arr.ndim == 3 and arr.shape[2] >= 3:
            out.append(arr[:, :, :3].astype(np.uint8))
    if not out:
        raise ValueError(f"No RGB frames found in {path}")
    return out


def short_path_label(path: str) -> str:
    task_match = re.search(r"/libero_10_(\d+)_rank\d+/eval_episode_(\d+)\.mp4$", path)
    if task_match:
        return f"task {task_match.group(1)} ep {task_match.group(2)}"
    return Path(path).name


def draw_label(frame: np.ndarray, label: str, ok: bool | None) -> np.ndarray:
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img, "RGBA")
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 18)
        small = ImageFont.truetype("DejaVuSans.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
        small = font

    bar_h = 52
    color = (28, 110, 58, 210) if ok is True else (150, 42, 35, 210) if ok is False else (0, 0, 0, 200)
    draw.rectangle((0, 0, img.width, bar_h), fill=(0, 0, 0, 170))
    draw.rectangle((0, 0, 9, bar_h), fill=color)

    parts = label.split(" | ")
    draw.text((14, 6), parts[0], fill=(255, 255, 255, 255), font=font)
    if len(parts) > 1:
        draw.text((14, 30), " | ".join(parts[1:]), fill=(235, 235, 235, 255), font=small)
    return np.asarray(img)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary-json", default="note/pi05_libero_plus_standard.json")
    parser.add_argument("--video-list", default="note/pi05_libero_plus_standard_representative_videos.txt")
    parser.add_argument("--output", default="note/pi05_libero_plus_standard_representative_labeled_grid.mp4")
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--fps", type=float, default=10)
    parser.add_argument("--max-frames", type=int, default=220)
    parser.add_argument("--hold-last-frames", type=int, default=30)
    args = parser.parse_args()

    repo_root = Path(os.environ.get("OPENTAU_DIR", Path.cwd())).resolve()
    summary = load_summary(repo_root / args.summary_json)
    metadata = build_video_metadata(summary)

    raw_paths = [
        line.strip()
        for line in (repo_root / args.video_list).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not raw_paths:
        raise ValueError("No videos listed.")

    videos = []
    labels = []
    statuses = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        abs_path = path if path.is_absolute() else repo_root / path
        meta = metadata.get(raw_path, {})
        status = meta.get("success")
        ok = True if status == "SUCCESS" else False if status == "FAIL" else None
        label = (
            f"{meta.get('category', 'Unknown')} | task {meta.get('task_id', '?')} "
            f"ep {meta.get('episode', '?')} | {status or short_path_label(raw_path)}"
        )
        video = read_video(abs_path, args.max_frames)
        if args.hold_last_frames > 0:
            video = video + [video[-1]] * args.hold_last_frames
        videos.append(video)
        labels.append(label)
        statuses.append(ok)

    h, w = videos[0][0].shape[:2]
    cols = max(1, args.cols)
    rows = math.ceil(len(videos) / cols)
    max_len = max(len(v) for v in videos)
    grid_frames = []

    for frame_idx in range(max_len):
        canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
        for i, video in enumerate(videos):
            row = i // cols
            col = i % cols
            frame = video[min(frame_idx, len(video) - 1)]
            frame = frame[:h, :w, :3]
            frame = draw_label(frame, labels[i], statuses[i])
            canvas[row * h : (row + 1) * h, col * w : (col + 1) * w] = frame
        grid_frames.append(canvas)

    output = repo_root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(output, grid_frames, fps=args.fps)
    print(output)


if __name__ == "__main__":
    main()
