# pi0.5 LIBERO-plus Camera View 50x5 eval

Main evaluation uses the first 50 Camera Viewpoints tasks, 5 episodes per task. Supplemental tasks, if any, are only used to fill the last 16-way failure grid.

## Summary

- Main tasks: `50`
- Main episodes: `250`
- Main success: `247/250` = `98.80%`
- Main failures: `3`
- Supplemental tasks: `9`
- Supplemental episodes: `45`
- Selected failure videos in grids: `16`
- Next camera index to continue from: `150`
- Success rule: original OpenTau/LIBERO sparse success from `eval_info.json`.
- Seeds per task: episodes use `1000..1004`; with `init_states=True`, these map to fixed predefined initial states.
- Grid rendering: each cell plays independently; shorter episodes hold their final frame.
- Incomplete final grid allowed: `False`

## Grid Videos

- `camera_view_50x5_failure_rerun_grid_001.mp4`

## Failure Legend

| # | phase | task | ep | seed | view tuple | reward | video |
|---:|---|---:|---:|---:|---|---:|---|
| 1 | main | 683 | 0 | 1000 | `0,0,100,2,8` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/part_000_049/post-training-eval/libero-libero_10-5-20260527-201627/videos/libero_10_683_rank0/eval_episode_0.mp4` |
| 2 | main | 683 | 2 | 1002 | `0,0,100,2,8` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/part_000_049/post-training-eval/libero-libero_10-5-20260527-201627/videos/libero_10_683_rank0/eval_episode_2.mp4` |
| 3 | main | 695 | 4 | 1004 | `9,15,100,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/part_000_049/post-training-eval/libero-libero_10-5-20260527-201627/videos/libero_10_695_rank0/eval_episode_4.mp4` |
| 4 | supplement | 736 | 0 | 1000 | `0,0,123,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_736_rank0/eval_episode_0.mp4` |
| 5 | supplement | 736 | 2 | 1002 | `0,0,123,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_736_rank0/eval_episode_2.mp4` |
| 6 | supplement | 738 | 0 | 1000 | `0,0,125,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_738_rank0/eval_episode_0.mp4` |
| 7 | supplement | 739 | 2 | 1002 | `0,0,126,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_739_rank0/eval_episode_2.mp4` |
| 8 | supplement | 740 | 2 | 1002 | `0,0,127,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_740_rank0/eval_episode_2.mp4` |
| 9 | supplement | 740 | 3 | 1003 | `0,0,127,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_740_rank0/eval_episode_3.mp4` |
| 10 | supplement | 741 | 2 | 1002 | `0,0,128,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_741_rank0/eval_episode_2.mp4` |
| 11 | supplement | 741 | 3 | 1003 | `0,0,128,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_741_rank0/eval_episode_3.mp4` |
| 12 | supplement | 742 | 0 | 1000 | `0,0,129,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_742_rank0/eval_episode_0.mp4` |
| 13 | supplement | 742 | 1 | 1001 | `0,0,129,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_742_rank0/eval_episode_1.mp4` |
| 14 | supplement | 742 | 3 | 1003 | `0,0,129,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_742_rank0/eval_episode_3.mp4` |
| 15 | supplement | 742 | 4 | 1004 | `0,0,129,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_selected16/post-training-eval/libero-libero_10-5-20260528-002433/videos/libero_10_742_rank0/eval_episode_4.mp4` |
| 16 | supplement | 743 | 1 | 1001 | `0,0,130,0,0` | 0.0 | `outputs/pi05_libero_plus_camera_view_50x5/failure_rerun_extra743/post-training-eval/libero-libero_10-5-20260528-003507/videos/libero_10_743_rank0/eval_episode_1.mp4` |

## Per-Task Main Results

| task | success | fail | view tuple | task name |
|---:|---:|---:|---|---|
| 682 | 5/5 | 0 | `0,0,100,2,6` | `room scene2 put both the alphabet soup and the tomato sa` |
| 683 | 3/5 | 2 | `0,0,100,2,8` | `room scene2 put both the alphabet soup and the tomato sa` |
| 684 | 5/5 | 0 | `0,0,100,2,10` | `room scene2 put both the alphabet soup and the tomato sa` |
| 685 | 5/5 | 0 | `0,0,100,2,350` | `room scene2 put both the alphabet soup and the tomato sa` |
| 686 | 5/5 | 0 | `0,0,100,2,352` | `room scene2 put both the alphabet soup and the tomato sa` |
| 687 | 5/5 | 0 | `0,0,100,2,354` | `room scene2 put both the alphabet soup and the tomato sa` |
| 688 | 5/5 | 0 | `1,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 689 | 5/5 | 0 | `2,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 690 | 5/5 | 0 | `4,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 691 | 5/5 | 0 | `5,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 692 | 5/5 | 0 | `6,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 693 | 5/5 | 0 | `7,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 694 | 5/5 | 0 | `8,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 695 | 4/5 | 1 | `9,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 696 | 5/5 | 0 | `10,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 697 | 5/5 | 0 | `11,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 698 | 5/5 | 0 | `12,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 699 | 5/5 | 0 | `13,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 700 | 5/5 | 0 | `14,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 701 | 5/5 | 0 | `15,15,100,0,0` | `room scene2 put both the alphabet soup and the tomato sa` |
| 702 | 5/5 | 0 | `0,0,119,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 703 | 5/5 | 0 | `0,0,100,4,6` | `room scene2 put both the cream cheese box and the butter` |
| 704 | 5/5 | 0 | `0,0,100,4,8` | `room scene2 put both the cream cheese box and the butter` |
| 705 | 5/5 | 0 | `0,0,100,4,10` | `room scene2 put both the cream cheese box and the butter` |
| 706 | 5/5 | 0 | `0,0,100,4,350` | `room scene2 put both the cream cheese box and the butter` |
| 707 | 5/5 | 0 | `0,0,100,4,352` | `room scene2 put both the cream cheese box and the butter` |
| 708 | 5/5 | 0 | `0,0,100,4,354` | `room scene2 put both the cream cheese box and the butter` |
| 709 | 5/5 | 0 | `16,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 710 | 5/5 | 0 | `17,0,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 711 | 5/5 | 0 | `17,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 712 | 5/5 | 0 | `18,0,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 713 | 5/5 | 0 | `18,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 714 | 5/5 | 0 | `19,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 715 | 5/5 | 0 | `20,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 716 | 5/5 | 0 | `21,0,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 717 | 5/5 | 0 | `21,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 718 | 5/5 | 0 | `22,0,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 719 | 5/5 | 0 | `22,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 720 | 5/5 | 0 | `23,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 721 | 5/5 | 0 | `24,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 722 | 5/5 | 0 | `25,0,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 723 | 5/5 | 0 | `25,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 724 | 5/5 | 0 | `26,0,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 725 | 5/5 | 0 | `26,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 726 | 5/5 | 0 | `27,0,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 727 | 5/5 | 0 | `27,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 728 | 5/5 | 0 | `28,0,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 729 | 5/5 | 0 | `28,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 730 | 5/5 | 0 | `29,0,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
| 731 | 5/5 | 0 | `29,15,100,0,0` | `room scene2 put both the cream cheese box and the butter` |
