# Run Examples

Run from the repository root unless noted otherwise.

## Smoke Test

```bash
source .venv-opentau/bin/activate
cd OpenTau
bash ../scripts/run_libero_plus_smoke.sh
```

## Standard 7-Perturbation Smoke

```bash
source .venv-opentau/bin/activate
cd OpenTau
bash ../scripts/run_libero_plus_7perturb_smoke.sh
```

## Recreate Evaluation Configs

```bash
source .venv-opentau/bin/activate
cd OpenTau
python ../scripts/make_robot_initial_eval_configs.py
python ../scripts/make_light_conditions_eval_configs.py
```

## Run Completed Queue Types Again

```bash
source .venv-opentau/bin/activate
cd OpenTau
bash ../scripts/run_robot_initial_queue.sh
bash ../scripts/run_light_conditions_queue.sh
```

## Run A Specific Config

```bash
source .venv-opentau/bin/activate
cd OpenTau
bash ../scripts/run_libero_plus_eval_config.sh ../configs/local/light_conditions_50x5/light_conditions_low_l1_l3_metrics.json
```

## Notes

- The configs are set for a 12GB GPU and prioritize reliability over throughput.
- For a larger GPU, test higher `batch_size` only after the smoke run succeeds.
- Failure reruns are for video collection only; benchmark success rates should use the original metrics/direct-video configs, not the rerun configs.
