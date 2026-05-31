# Partial supplement status

The supplemental run was stopped by request before completion.

- Config: `configs/local/libero_plus_camera_view_50x5_part_050_069.json`
- Intended supplemental slice: `camera_viewpoints[50:70]`, task ids `732..751`
- Completed `grid_summary.mp4` files on disk: `12`
- Episode videos on disk: `62`
- `eval_info.json`: not produced, because the run did not reach normal eval completion.
- Formal success-rate accounting: excluded from `camera_view_50x5_summary.md/json`.
- Next clean continuation point for metric evaluation: start from camera index `50` again if exact metrics are required.

The partial videos are kept under:

`outputs/pi05_libero_plus_camera_view_50x5/part_050_069/post-training-eval/libero-libero_10-5-20260527-210158/videos/`
