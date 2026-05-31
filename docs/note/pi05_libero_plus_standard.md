# pi0.5 LIBERO-plus standard eval

## Scope

This is a cost-effective standard run on `libero_10`: 7 perturbation categories, 8 stride-sampled tasks per category, 2 fixed-seed episodes per task, 112 episodes total.

Important: LIBERO-plus original category counts are not equal. This run intentionally uses equal samples per category for macro comparison across perturbation types; it is not the full original-distribution weighted benchmark.

## Overall

- Macro success across 7 categories: `72.32%`
- Micro success across sampled episodes: `72.32%` (81/112)
- Total eval wall time recorded by eval loop: `2105.6s`

## Per Category

| Category | Original count | Sampled tasks | Episodes | Success | Eval s | Eval s/ep |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Background Textures | 289 | 8 | 16 | 93.75% (15/16) | 190.1 | 11.88 |
| Camera Viewpoints | 419 | 8 | 16 | 37.50% (6/16) | 257.8 | 16.11 |
| Language Instructions | 383 | 8 | 16 | 87.50% (14/16) | 194.7 | 12.17 |
| Light Conditions | 274 | 8 | 16 | 93.75% (15/16) | 199.3 | 12.46 |
| Objects Layout | 312 | 8 | 16 | 93.75% (15/16) | 207.3 | 12.96 |
| Robot Initial States | 393 | 8 | 16 | 43.75% (7/16) | 246.4 | 15.40 |
| Sensor Noise | 449 | 8 | 16 | 56.25% (9/16) | 810.1 | 50.63 |

## Config

- Policy: `TensorAuto/tPi0.5-libero`
- Suite: `libero_10`
- Sampling: `stride`, `tasks_per_category=8`, `episodes_per_task=2`, seed `1000`
- Runtime: `batch_size=1`, `action_chunk=10`, `MUJOCO_GL=egl`, Hugging Face offline mode
- Memory control: policy is loaded once; LIBERO envs are created lazily one task at a time
- Video: per-task grids and all episode videos are under each category output directory

## Output Files

- CSV summary: `note/pi05_libero_plus_standard.csv`
- JSON summary: `note/pi05_libero_plus_standard.json`
- Representative video list: `note/pi05_libero_plus_standard_representative_videos.txt`
- Representative video grid: `note/pi05_libero_plus_standard_representative_grid.mp4`
- Manifest: `configs/local/libero_plus_perturb_eval/manifest_libero_10.json`

## Task-Level Successes

- Background Textures: `{"0": [true, true], "41": [true, true], "82": [true, true], "123": [true, true], "165": [true, true], "206": [false, true], "247": [true, true], "288": [true, true]}`
- Camera Viewpoints: `{"682": [true, true], "742": [true, true], "801": [false, false], "861": [false, false], "921": [false, false], "981": [false, true], "1040": [true, false], "1100": [false, false]}`
- Language Instructions: `{"1101": [true, true], "1156": [true, false], "1210": [true, true], "1265": [true, true], "1319": [true, true], "1374": [true, true], "1428": [true, true], "1483": [false, true]}`
- Light Conditions: `{"2245": [true, true], "2284": [false, true], "2323": [true, true], "2362": [true, true], "2401": [true, true], "2440": [true, true], "2479": [true, true], "2518": [true, true]}`
- Objects Layout: `{"1933": [true, true], "1977": [true, true], "2022": [true, true], "2066": [true, false], "2111": [true, true], "2155": [true, true], "2200": [true, true], "2244": [true, true]}`
- Robot Initial States: `{"289": [true, true], "345": [false, false], "401": [false, false], "457": [false, true], "513": [true, true], "569": [true, true], "625": [false, false], "681": [false, false]}`
- Sensor Noise: `{"1484": [true, true], "1548": [true, true], "1612": [false, false], "1676": [false, false], "1740": [true, true], "1804": [true, true], "1868": [true, false], "1932": [false, false]}`
