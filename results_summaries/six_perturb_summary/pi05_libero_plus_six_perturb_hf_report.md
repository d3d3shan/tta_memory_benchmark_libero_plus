# pi0.5 LIBERO-plus Perturbation Result Summary

This report combines the three earlier local perturbation uploads with the three `wzxuan` perturbation uploads prepared from `/data/wangjinqiu/tta-memory/libero_plus_eval`.

## Overall

- Categories summarized: `6`
- Micro success: `8399/10350` = `81.15%`
- Macro success across categories: `82.55%`
- Policy: `TensorAuto/tPi0.5-libero`
- Benchmark: LIBERO-plus `libero_10`, 5 episodes per task, seeds `1000..1004`

## Hugging Face Datasets

| Perturbation | HF dataset | Tasks | Episodes | Success | Failure grids | Short analysis |
|---|---|---:|---:|---:|---:|---|
| Camera Viewpoints | [pi05-libero-plus-camera-view-failures](https://huggingface.co/datasets/d3d3shan/pi05-libero-plus-camera-view-failures) | 419 | 2095 | 1197/2095 (57.14%) | 55 | Most brittle among the completed local categories; camera pose changes strongly affect visual grounding. |
| Robot Initial States | [pi05-libero-plus-robot-initial-failures](https://huggingface.co/datasets/d3d3shan/pi05-libero-plus-robot-initial-failures) | 393 | 1965 | 1430/1965 (72.77%) | 32 | Moderate robustness; failures often come from approach pose and grasp recovery sensitivity. |
| Light Conditions | [pi05-libero-plus-light-conditions-failures](https://huggingface.co/datasets/d3d3shan/pi05-libero-plus-light-conditions-failures) | 274 | 1370 | 1209/1370 (88.25%) | 10 | Highest success among completed local categories; illumination shifts are less damaging than geometry/language changes. |
| Background Textures | [pi05-libero-plus-background-textures-failures](https://huggingface.co/datasets/d3d3shan/pi05-libero-plus-background-textures-failures) | 289 | 1445 | 1277/1445 (88.37%) | 11 | Texture/domain shift stresses visual appearance; failures are useful for checking whether policy overfits tabletop/background cues. |
| Language Instructions | [pi05-libero-plus-language-instructions-failures](https://huggingface.co/datasets/d3d3shan/pi05-libero-plus-language-instructions-failures) | 383 | 1915 | 1841/1915 (96.14%) | 5 | Language paraphrase/instruction shift directly tests semantic grounding; low score usually indicates instruction following and target disambiguation errors. |
| Objects Layout | [pi05-libero-plus-objects-layout-failures](https://huggingface.co/datasets/d3d3shan/pi05-libero-plus-objects-layout-failures) | 312 | 1560 | 1445/1560 (92.63%) | 8 | Object layout changes stress spatial search, grasp approach, and collision recovery; failures often expose planning rather than pure perception issues. |

## Caveats

- Success is the LIBERO/OpenTau task-completion predicate from `eval_info.json`; videos are qualitative diagnostics.
- Failed-task reruns are excluded from success-rate computation.
- The three earlier local datasets and the three `wzxuan` datasets were prepared on different machines, but use the same policy, task suite, 5-episode protocol, and seed schedule.
- `Sensor Noise` is not included here because the downloaded `wzxuan` payload did not contain a failure-grid report for that category.
