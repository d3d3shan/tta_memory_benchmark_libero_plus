# pi0.5 LIBERO-plus standard failure-mode analysis

## Executive Summary

This analysis uses the completed `standard` run: 7 perturbation categories, 8 stride-sampled tasks per category, 2 episodes per task, 112 total episodes.

The dominant failures are concentrated in three categories:

| Category | Failures | Success |
| --- | ---: | ---: |
| Camera Viewpoints | 10/16 | 37.50% |
| Robot Initial States | 9/16 | 43.75% |
| Sensor Noise | 7/16 | 56.25% |
| Other four categories combined | 5/64 | 92.19% |

So `26/31 = 83.9%` of all failures come from camera viewpoint, robot initial state, and sensor noise. The policy is comparatively robust to background texture, lighting, language paraphrase, and object-layout perturbations in this sampled run.

## Failure Mode 1: Viewpoint Shift Breaks Visual Grounding

`Camera Viewpoints` is the weakest category: `6/16` successes.

Consistently failed tasks:

| Task id | Failures | Perturbation |
| ---: | ---: | --- |
| 801 | 2/2 | `KITCHEN_SCENE4...view_46_15_100_0_0` |
| 861 | 2/2 | `LIVING_ROOM_SCENE5...view_68_15_100_0_0` |
| 921 | 2/2 | `STUDY_SCENE1...view_299_0_100_0_0` |
| 1100 | 2/2 | `KITCHEN_SCENE6...view_359_15_100_0_0` |

Interpretation: pi0.5 is sensitive to camera pose changes that alter object appearance and spatial relations. The failures are not limited to one scene type; they appear across kitchen, living room, and study scenes. That suggests the bottleneck is not a single task semantic, but visual grounding under viewpoint distribution shift.

Practical implication: for policy comparison, `Camera Viewpoints` should be kept as a separate robustness axis instead of only reporting an overall score. A policy can look strong on average while failing badly here.

## Failure Mode 2: Initial-State Shift Exposes Weak Closed-Loop Recovery

`Robot Initial States` succeeds on `7/16`.

Consistently failed tasks:

| Task id | Failures | Perturbation |
| ---: | ---: | --- |
| 345 | 2/2 | `initstate_292` |
| 401 | 2/2 | `initstate_403` |
| 625 | 2/2 | `initstate_359` |
| 681 | 2/2 | `initstate_500` |

Interpretation: the policy can execute familiar trajectories, but some shifted starts likely put the gripper/object relation outside the policy's comfortable basin of attraction. This is a closed-loop recovery issue: if the first grasp/approach is off, the model often does not recover within the episode.

This is different from camera failure. The camera is nominal here, but the physical state distribution has shifted. So this category is closer to testing control robustness and recovery, not just perception.

## Failure Mode 3: Sensor Noise Causes Long-Horizon Drift

`Sensor Noise` succeeds on `9/16`, but costs much more time: `50.63s/episode` vs roughly `12-16s/episode` for most other categories.

Consistently failed tasks:

| Task id | Failures | Perturbation |
| ---: | ---: | --- |
| 1612 | 2/2 | `KITCHEN_SCENE3...noise_50` |
| 1676 | 2/2 | `LIVING_ROOM_SCENE5...noise_18` |
| 1932 | 2/2 | `KITCHEN_SCENE6...noise_50` |

Interpretation: failures here often run close to the full episode horizon, which explains the large runtime. The state normalization warnings during eval are consistent with the perturbation pushing state values slightly outside the training normalization range. This points to degraded proprioceptive/control feedback, not just image perception.

Practical implication: use runtime as a secondary signal. A low success category with very high `eval_s/episode` usually means many episodes timed out rather than failing quickly.

## Non-Dominant Failures

The other categories are mostly stable:

| Category | Failure pattern |
| --- | --- |
| Background Textures | 1 failure, task 206, living-room two-mug/plate placement |
| Language Instructions | 2 failures, no broad collapse |
| Light Conditions | 1 failure, task 2284 |
| Objects Layout | 1 failure, task 2066 |

These are not currently the main bottleneck for pi0.5 on this sampled standard run.

## Task-Level Pattern

Several base tasks reappear across failed categories:

| Base task | Failure categories |
| --- | --- |
| `KITCHEN_SCENE6_put_the_yellow_and_white_mug_in_the_microwave_and_close_it` | camera, robot init, sensor noise, language |
| `LIVING_ROOM_SCENE5_put_the_white_mug_on_the_left_plate_and_put_the_yellow_and_white_mug_on_the_right_plate` | camera, robot init, sensor noise, background |
| `KITCHEN_SCENE3_turn_on_the_stove_and_put_the_moka_pot_on_it` | robot init, sensor noise, light |
| `KITCHEN_SCENE8_put_both_moka_pots_on_the_stove` | camera, robot init, sensor noise |

Interpretation: long-horizon or multi-object tasks are more fragile. This matters when selecting a cheap benchmark subset: include these recurring hard base tasks, otherwise the benchmark may overestimate policy robustness.

## Recommended Next Analysis

1. Visual audit: inspect one success and one failure video per weak category, especially:
   - `Camera Viewpoints`: task 801 or 1100
   - `Robot Initial States`: task 345 or 681
   - `Sensor Noise`: task 1612 or 1932
2. Add automatic episode metadata if future runs need deeper diagnosis:
   - episode length until termination
   - final reward and max reward
   - gripper/object distance if available
   - action norm / action saturation
3. For future policy comparison, report both:
   - macro average across 7 perturbation categories
   - separate scores for camera, robot init, and sensor noise

## Current Representative Videos

The current representative grid is:

`note/pi05_libero_plus_standard_representative_grid.mp4`

The source videos are listed in:

`note/pi05_libero_plus_standard_representative_videos.txt`
