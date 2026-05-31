#!/usr/bin/env python
"""Minimal PI0.5 dummy inference smoke test.

This intentionally avoids torch.compile and repeated warmup runs so it can be
used as a basic model-load/action-output check on constrained GPUs.
"""

from __future__ import annotations

import argparse
import time

import torch

from opentau.configs.train import TrainPipelineConfig
from opentau.policies.factory import get_policy_class
from opentau.utils.random_utils import set_seed
from opentau.utils.utils import auto_torch_device, create_dummy_observation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config_path", default="configs/local/pi05_inference_smoke.json")
    parser.add_argument("--device", default=None, help="Override device, e.g. cuda or cpu.")
    args = parser.parse_args()

    cfg = TrainPipelineConfig.from_pretrained(args.config_path)
    if cfg.seed is not None:
        set_seed(cfg.seed)

    device = torch.device(args.device) if args.device else auto_torch_device()
    dtype = torch.bfloat16 if device.type == "cuda" else torch.float32
    print(f"device={device} dtype={dtype}")

    policy_class = get_policy_class(cfg.policy.type)
    policy = policy_class.from_pretrained(cfg.policy.pretrained_path, config=cfg.policy)
    policy.to(device=device, dtype=dtype)
    policy.eval()
    policy.reset()

    observation = create_dummy_observation(cfg, device, dtype=dtype)
    t0 = time.perf_counter()
    with torch.inference_mode():
        actions = policy.sample_actions(observation)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    actions = actions.detach().to("cpu", torch.float32)
    print(f"actions_shape={tuple(actions.shape)} elapsed_ms={elapsed_ms:.2f}")
    print(f"actions_mean={actions.mean().item():.6f} actions_std={actions.std().item():.6f}")


if __name__ == "__main__":
    main()
