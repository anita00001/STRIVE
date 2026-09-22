#!/usr/bin/env python3
"""Profile the STRIVE M-01 traffic-model checkpoint and release configs.

This profiler avoids importing the STRIVE model code. That makes it useful for
artifact inspection even when torch-geometric, nuScenes, or CUDA are unavailable.

It can:
  * hash and size a checkpoint;
  * load the checkpoint on CPU when PyTorch is installed;
  * inspect STRIVE's `model` state dict;
  * count tensors and scalar elements;
  * summarize dtypes and parameter/buffer-shaped entries;
  * report stored epoch/min validation loss;
  * parse train/test YAML-style cfg files;
  * write a standalone YAML report;
  * merge measurements into metadata/models/traffic_model.yaml.

Designed to remain syntax-compatible with Python 3.6.
"""

import argparse
import datetime
import hashlib
import os
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def load_yaml_like(path):
    if path is None:
        return None
    p = Path(path)
    if not p.is_file():
        return {"_error": "file not found: %s" % p}
    if yaml is None:
        return {"_error": "PyYAML unavailable; cannot parse %s" % p}
    try:
        with p.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data if data is not None else {}
    except Exception as exc:
        return {"_error": str(exc)}


def tensor_numel(tensor):
    try:
        return int(tensor.numel())
    except Exception:
        return None


def tensor_shape(tensor):
    try:
        return [int(x) for x in tensor.shape]
    except Exception:
        return None


def tensor_dtype(tensor):
    try:
        return str(tensor.dtype)
    except Exception:
        return None


def inspect_checkpoint(path):
    p = Path(path)
    result = {
        "path": str(p.resolve()),
        "exists": p.is_file(),
        "size_bytes": None,
        "sha256": None,
        "load_status": "not_loaded",
    }
    if not p.is_file():
        return result

    result["size_bytes"] = p.stat().st_size
    result["sha256"] = sha256_file(p)

    try:
        import torch
    except Exception as exc:
        result["load_status"] = "torch_unavailable"
        result["load_error"] = str(exc)
        return result

    try:
        obj = torch.load(str(p), map_location="cpu")
    except Exception as exc:
        result["load_status"] = "load_failed"
        result["load_error"] = str(exc)
        return result

    result["load_status"] = "loaded"

    if isinstance(obj, dict):
        result["top_level_keys"] = sorted([str(k) for k in obj.keys()])
        result["checkpoint_metadata"] = {
            "epoch": obj.get("epoch"),
            "min_val_loss": obj.get("min_val_loss"),
            "has_optimizer_state": "optim" in obj,
            "has_model_state": "model" in obj,
        }
        state = obj.get("model")
        if state is None:
            # Fall back for a plain state_dict-like checkpoint.
            tensor_values = [v for v in obj.values() if hasattr(v, "numel")]
            if tensor_values and len(tensor_values) == len(obj):
                state = obj
                result["checkpoint_metadata"]["plain_state_dict_fallback"] = True
    else:
        state = None
        result["object_type"] = type(obj).__name__

    if not isinstance(state, dict):
        result["state_dict"] = {
            "available": False,
            "error": "No model state dict found under key 'model' and checkpoint is not a plain state dict.",
        }
        return result

    entries = []
    dtype_counts = Counter()
    prefix_counts = Counter()
    total_numel = 0
    total_tensor_bytes = 0
    num_tensors = 0

    for name in sorted(state.keys()):
        value = state[name]
        numel = tensor_numel(value)
        shape = tensor_shape(value)
        dtype = tensor_dtype(value)
        if numel is None:
            continue
        num_tensors += 1
        total_numel += numel
        dtype_counts[dtype] += numel
        prefix = str(name).split(".")[0]
        prefix_counts[prefix] += numel
        try:
            total_tensor_bytes += int(value.element_size()) * numel
        except Exception:
            pass
        entries.append({
            "name": str(name),
            "shape": shape,
            "dtype": dtype,
            "numel": numel,
        })

    result["state_dict"] = {
        "available": True,
        "tensor_count": num_tensors,
        "total_scalar_elements": total_numel,
        "approx_tensor_storage_bytes": total_tensor_bytes,
        "scalar_elements_by_dtype": dict(sorted(dtype_counts.items())),
        "scalar_elements_by_top_level_module": dict(sorted(prefix_counts.items())),
        "entries": entries,
    }
    return result


def quality_checks(checkpoint, train_cfg, test_cfg):
    checks = {
        "checkpoint_exists": bool(checkpoint.get("exists")),
        "checkpoint_loaded": checkpoint.get("load_status") == "loaded",
        "model_state_available": bool(checkpoint.get("state_dict", {}).get("available")),
        "train_config_parsed": isinstance(train_cfg, dict) and "_error" not in train_cfg,
        "test_config_parsed": isinstance(test_cfg, dict) and "_error" not in test_cfg,
    }

    warnings = []
    if not checks["checkpoint_exists"]:
        warnings.append("checkpoint file not found")
    elif not checks["checkpoint_loaded"]:
        warnings.append("checkpoint could not be loaded; hash/size may still be valid")

    if isinstance(train_cfg, dict):
        expected_train = {
            "epochs": 200,
            "lr": 1e-5,
            "loss_kl": 0.004,
            "loss_recon": 1.0,
            "loss_veh_coll_prior": 0.05,
            "loss_env_coll_prior": 0.1,
        }
        mismatches = {}
        for key, expected in expected_train.items():
            if key in train_cfg and train_cfg.get(key) != expected:
                mismatches[key] = {
                    "observed": train_cfg.get(key),
                    "public_release_card_value": expected,
                }
        checks["train_config_release_value_mismatches"] = mismatches
        if mismatches:
            warnings.append("train config differs from public-release values documented in M-01")

    if isinstance(test_cfg, dict):
        ckpt = test_cfg.get("ckpt")
        checks["test_config_checkpoint"] = ckpt

    return checks, warnings


def dump_yaml(data):
    if yaml is None:
        raise RuntimeError("PyYAML is required to write YAML.")
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110)


def update_metadata(path, profile):
    if yaml is None:
        raise RuntimeError("PyYAML is required to update metadata.")
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError("metadata file not found: %s" % p)
    with p.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    data.setdefault("profile", {})
    data["profile"]["measurement_status"] = "measured"
    data["profile"]["measured"] = profile
    with p.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=110)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", required=True, help="Path to STRIVE traffic model .pth checkpoint.")
    parser.add_argument("--train-config", default="./configs/train_traffic.cfg")
    parser.add_argument("--test-config", default="./configs/test_traffic.cfg")
    parser.add_argument("--output", help="Optional standalone YAML report.")
    parser.add_argument("--metadata", help="Optional metadata/models/traffic_model.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()

    train_cfg = load_yaml_like(args.train_config)
    test_cfg = load_yaml_like(args.test_config)
    checkpoint = inspect_checkpoint(args.checkpoint)
    checks, warnings = quality_checks(checkpoint, train_cfg, test_cfg)

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "M-01",
        "profiled_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "checkpoint": {
            "path": checkpoint.get("path"),
            "exists": checkpoint.get("exists"),
            "size_bytes": checkpoint.get("size_bytes"),
            "sha256": checkpoint.get("sha256"),
            "load_status": checkpoint.get("load_status"),
            "load_error": checkpoint.get("load_error"),
        },
        "checkpoint_metadata": checkpoint.get("checkpoint_metadata"),
        "state_dict": checkpoint.get("state_dict"),
        "train_config": train_cfg,
        "test_config": test_cfg,
        "quality_checks": checks,
        "warnings": warnings,
        "measurement_notes": [
            "State-dict scalar count can include buffers and should not automatically be labeled trainable parameter count.",
            "This profiler does not import or instantiate STRIVE, so it does not require torch-geometric or nuScenes.",
            "Checkpoint loading still requires a PyTorch version compatible with the serialized artifact.",
        ],
    }

    if args.metadata:
        update_metadata(args.metadata, profile)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(dump_yaml(profile), encoding="utf-8")
    elif not args.metadata:
        sys.stdout.write(dump_yaml(profile))


if __name__ == "__main__":
    main()
