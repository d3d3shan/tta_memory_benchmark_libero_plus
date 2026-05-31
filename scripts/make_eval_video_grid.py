#!/usr/bin/env python
"""Create a plain comparison grid from eval videos.

Inputs can be eval_info.json files or direct mp4 paths. This script does not add
success/failure color overlays, so the final frames keep their original colors.
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

import imageio.v2 as imageio
import numpy as np


def collect_paths(inputs: list[str], repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for value in inputs:
        path = Path(value)
        if path.suffix == ".json":
            with open(path, encoding="utf-8") as f:
                info = json.load(f)
            video_paths = info.get("overall", {}).get("video_paths", [])
            for video_path in video_paths:
                vp = Path(video_path)
                paths.append(vp if vp.is_absolute() else repo_root / vp)
        else:
            paths.append(path if path.is_absolute() else repo_root / path)
    return paths


def read_video(path: Path, max_frames: int | None) -> list[np.ndarray]:
    frames = imageio.mimread(path)
    if max_frames is not None:
        frames = frames[:max_frames]
    rgb_frames = []
    for frame in frames:
        arr = np.asarray(frame)
        if arr.ndim == 3 and arr.shape[2] >= 3:
            rgb_frames.append(arr[:, :, :3].astype(np.uint8))
    if not rgb_frames:
        raise ValueError(f"No RGB frames found in {path}")
    return rgb_frames


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="eval_info.json files or mp4 paths")
    parser.add_argument("--output", required=True)
    parser.add_argument("--cols", type=int, default=3)
    parser.add_argument("--fps", type=float, default=10)
    parser.add_argument("--max-frames", type=int, default=None)
    args = parser.parse_args()

    repo_root = Path(os.environ.get("OPENTAU_DIR", Path.cwd())).resolve()
    video_paths = collect_paths(args.inputs, repo_root)
    if not video_paths:
        raise ValueError("No videos found from inputs.")

    videos = [read_video(path, args.max_frames) for path in video_paths]
    h, w = videos[0][0].shape[:2]
    max_len = max(len(v) for v in videos)
    cols = max(1, args.cols)
    rows = math.ceil(len(videos) / cols)
    output_frames = []

    for frame_idx in range(max_len):
        canvas = np.zeros((rows * h, cols * w, 3), dtype=np.uint8)
        for i, video in enumerate(videos):
            row = i // cols
            col = i % cols
            frame = video[min(frame_idx, len(video) - 1)]
            frame = frame[:h, :w, :3]
            canvas[row * h : (row + 1) * h, col * w : (col + 1) * w] = frame
        output_frames.append(canvas)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(output, output_frames, fps=args.fps)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
