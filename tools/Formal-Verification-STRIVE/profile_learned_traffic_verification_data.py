#!/usr/bin/env python3
"""Profile data/evidence for A1-D-01: STRIVE learned traffic model verification.

This tool is deliberately verifier-neutral. It can:
  * inspect the STRIVE checkout for implementation facts that constrain A1-D-01;
  * hash a model checkpoint without unpickling it;
  * validate and summarize a JSONL verification-case manifest;
  * validate a YAML property registry;
  * merge the measured profile into the A1-D-01 metadata.

A manifest is optional because the evidence corpus may not yet exist.

Recommended JSONL record shape (minimum):
{
  "case_id": "case_0001",
  "partition": "verification",
  "case_kind": "natural",
  "model": {
    "checkpoint_sha256": "...",
    "repository_revision": "..."
  },
  "property": {
    "property_id": "P-A",
    "property_version": "1.0.0"
  },
  "verification": {
    "status": "verified"
  }
}

Designed for Python 3.6-compatible syntax.
"""

import argparse
import ast
import datetime
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


ALLOWED_PARTITIONS = {"development", "verification", "regression"}
ALLOWED_CASE_KINDS = {
    "natural",
    "bounded_perturbation",
    "boundary_case",
    "counterexample",
    "regression",
    "synthetic_domain_sample",
}
ALLOWED_STATUSES = {
    "verified",
    "counterexample",
    "unknown",
    "timeout",
    "error",
    "not_run",
}


def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        while True:
            block = f.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def file_fact(path):
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.is_file(),
        "size_bytes": p.stat().st_size if p.is_file() else None,
        "sha256": sha256_file(p) if p.is_file() else None,
    }


def read_text(path):
    p = Path(path)
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def extract_literal_assignment(source, name):
    try:
        tree = ast.parse(source)
    except Exception:
        return None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    try:
                        return ast.literal_eval(node.value)
                    except Exception:
                        return None
    return None


def inspect_strive(repo_root):
    root = Path(repo_root)
    paths = {
        "traffic_model": root / "src/models/traffic_model.py",
        "model_common": root / "src/models/common.py",
        "interaction_net": root / "src/models/interaction_net.py",
        "dataset_utils": root / "src/datasets/utils.py",
        "nuscenes_dataset": root / "src/datasets/nuscenes_dataset.py",
        "traffic_loss": root / "src/losses/traffic_model.py",
        "base_config": root / "src/utils/config.py",
        "train_config": root / "configs/train_traffic.cfg",
        "test_config": root / "configs/test_traffic.cfg",
    }

    tm = read_text(paths["traffic_model"])
    common = read_text(paths["model_common"])
    du = read_text(paths["dataset_utils"])
    loss = read_text(paths["traffic_loss"])
    cfg = read_text(paths["base_config"])

    bike = extract_literal_assignment(du, "NUSC_BIKE_PARAMS")
    checks = {
        "traffic_model_class": "class TrafficModel(nn.Module)" in tm,
        "dt_0_5": "self.dt = 0.5" in tm,
        "state_size_6": "self.state_size = 6" in tm,
        "attribute_size_2": "self.att_feat_size = 2" in tm,
        "bicycle_raw_output_size_2": (
            "self.traj_out_size = 2" in tm
            and "(a,hdot)" in tm
        ),
        "default_latent_32": (
            "latent_size=32" in tm
            or ("--latent_size" in cfg and "default=32" in cfg)
        ),
        "default_past_4": "--past_len" in cfg and "default=4" in cfg,
        "default_future_12": "--future_len" in cfg and "default=12" in cfg,
        "raw_acceleration_unnormalized": (
            "a_out = dynamics_out[:,:,:,0]*self.bicycle_params['a_stats'][1]" in tm
        ),
        "raw_ddh_unnormalized": (
            "ddh_out = dynamics_out[:,:,:,1]*self.bicycle_params['ddh_stats'][1]" in tm
        ),
        "speed_clamped": ".clamp(0.0, max_s)" in common,
        "heading_rate_clamped": ".clamp(-max_hdot, max_hdot)" in common,
        "raw_acceleration_not_clamped_in_dynamics": (
            "news = (kinematics[:, :, six] + a * dt).clamp(0.0, max_s)" in common
        ),
        "vehicle_collision_threshold_0_02": "VEH_COLL_THRESH = 0.02" in loss,
        "environment_collision_threshold_0_05": "ENV_COLL_THRESH = 0.05" in loss,
    }

    derived = {}
    if isinstance(bike, dict):
        derived["NUSC_BIKE_PARAMS"] = bike
        if "maxhdot" in bike:
            derived["maxhdot_over_pi"] = bike["maxhdot"] / math.pi
    else:
        derived["NUSC_BIKE_PARAMS"] = None

    return {
        "source_files": {k: file_fact(v) for k, v in paths.items()},
        "implementation_checks": checks,
        "derived_constants": derived,
    }


def get_nested(obj, path, default=None):
    cur = obj
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def profile_manifest(path):
    p = Path(path)
    summary = {
        "path": str(p),
        "exists": p.is_file(),
        "sha256": sha256_file(p) if p.is_file() else None,
        "rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "duplicate_case_ids": [],
        "partition_counts": {},
        "case_kind_counts": {},
        "property_counts": {},
        "status_counts": {},
        "source_split_counts": {},
        "checkpoint_hash_counts": {},
        "repository_revision_counts": {},
        "errors": [],
    }
    if not p.is_file():
        return summary

    ids = []
    counters = {
        "partition": Counter(),
        "case_kind": Counter(),
        "property": Counter(),
        "status": Counter(),
        "source_split": Counter(),
        "checkpoint": Counter(),
        "revision": Counter(),
    }

    with p.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            summary["rows"] += 1
            try:
                row = json.loads(line)
            except Exception as exc:
                summary["invalid_rows"] += 1
                summary["errors"].append("line %d: invalid JSON: %s" % (lineno, exc))
                continue

            errs = []
            case_id = row.get("case_id")
            partition = row.get("partition")
            case_kind = row.get("case_kind")
            checkpoint = get_nested(row, "model.checkpoint_sha256")
            revision = get_nested(row, "model.repository_revision")
            prop_id = get_nested(row, "property.property_id")
            prop_ver = get_nested(row, "property.property_version")
            status = get_nested(row, "verification.status", "not_run")

            if not isinstance(case_id, str) or not case_id:
                errs.append("missing/non-string case_id")
            if partition not in ALLOWED_PARTITIONS:
                errs.append("invalid partition %r" % partition)
            if case_kind not in ALLOWED_CASE_KINDS:
                errs.append("invalid case_kind %r" % case_kind)
            if not isinstance(checkpoint, str) or len(checkpoint) != 64:
                errs.append("checkpoint_sha256 must be a 64-character SHA-256 hex string")
            elif not re.match(r"^[0-9a-fA-F]{64}$", checkpoint):
                errs.append("checkpoint_sha256 is not hexadecimal")
            if not isinstance(revision, str) or not revision:
                errs.append("missing repository_revision")
            if not isinstance(prop_id, str) or not prop_id:
                errs.append("missing property_id")
            if not isinstance(prop_ver, str) or not prop_ver:
                errs.append("missing property_version")
            if status not in ALLOWED_STATUSES:
                errs.append("invalid verification status %r" % status)

            if errs:
                summary["invalid_rows"] += 1
                summary["errors"].append(
                    "line %d (%s): %s"
                    % (lineno, case_id or "<no-id>", "; ".join(errs))
                )
                continue

            summary["valid_rows"] += 1
            ids.append(case_id)
            counters["partition"][partition] += 1
            counters["case_kind"][case_kind] += 1
            counters["property"]["%s@%s" % (prop_id, prop_ver)] += 1
            counters["status"][status] += 1
            if row.get("source_split") is not None:
                counters["source_split"][str(row.get("source_split"))] += 1
            counters["checkpoint"][checkpoint] += 1
            counters["revision"][revision] += 1

    id_counts = Counter(ids)
    summary["duplicate_case_ids"] = sorted(
        k for k, v in id_counts.items() if v > 1
    )
    summary["partition_counts"] = dict(counters["partition"])
    summary["case_kind_counts"] = dict(counters["case_kind"])
    summary["property_counts"] = dict(counters["property"])
    summary["status_counts"] = dict(counters["status"])
    summary["source_split_counts"] = dict(counters["source_split"])
    summary["checkpoint_hash_counts"] = dict(counters["checkpoint"])
    summary["repository_revision_counts"] = dict(counters["revision"])
    return summary


def profile_property_registry(path):
    p = Path(path)
    out = {
        "path": str(p),
        "exists": p.is_file(),
        "sha256": sha256_file(p) if p.is_file() else None,
        "properties": [],
        "errors": [],
    }
    if not p.is_file():
        return out
    if yaml is None:
        out["errors"].append("PyYAML unavailable")
        return out

    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as exc:
        out["errors"].append("invalid YAML: %s" % exc)
        return out

    props = data.get("properties", []) if isinstance(data, dict) else []
    if not isinstance(props, list):
        out["errors"].append("top-level properties must be a list")
        return out

    seen = set()
    for idx, prop in enumerate(props):
        if not isinstance(prop, dict):
            out["errors"].append("property %d is not a mapping" % idx)
            continue
        pid = prop.get("property_id")
        version = prop.get("version")
        if not pid or not version:
            out["errors"].append("property %d missing property_id/version" % idx)
            continue
        key = "%s@%s" % (pid, version)
        if key in seen:
            out["errors"].append("duplicate property %s" % key)
        seen.add(key)
        out["properties"].append({
            "property_id": pid,
            "version": version,
            "signal": prop.get("signal"),
            "units": prop.get("units"),
            "lower": prop.get("lower"),
            "upper": prop.get("upper"),
            "thresholds_complete": (
                prop.get("lower") is not None or prop.get("upper") is not None
            ),
        })
    return out


def dump_yaml(data):
    if yaml is None:
        raise RuntimeError("PyYAML is required to write YAML.")
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120)


def update_metadata(path, profile):
    if yaml is None:
        raise RuntimeError("PyYAML is required to update metadata.")
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError("metadata file not found: %s" % p)
    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    data.setdefault("profile", {})
    data["profile"]["measurement_status"] = "measured"
    data["profile"]["measured"] = profile
    p.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120),
        encoding="utf-8",
    )


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Root of a STRIVE checkout.")
    parser.add_argument("--manifest", help="Optional JSONL A1-D-01 verification-case manifest.")
    parser.add_argument("--property-spec", help="Optional YAML property registry.")
    parser.add_argument(
        "--checkpoint",
        help=(
            "Optional traffic-model checkpoint to hash only. "
            "This profiler does not torch.load/unpickle the checkpoint."
        ),
    )
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument(
        "--metadata",
        help="Optional metadata/assurance/data/traffic_model_verification.yaml to update.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    strive = inspect_strive(args.repo_root)
    manifest = profile_manifest(args.manifest) if args.manifest else None
    properties = (
        profile_property_registry(args.property_spec)
        if args.property_spec else None
    )
    checkpoint = file_fact(args.checkpoint) if args.checkpoint else None

    quality_checks = {
        "all_expected_source_files_present": all(
            x["exists"] for x in strive["source_files"].values()
        ),
        "all_implementation_checks_detected": all(
            strive["implementation_checks"].values()
        ),
        "manifest_valid_if_provided": (
            manifest is None
            or (
                manifest["exists"]
                and manifest["invalid_rows"] == 0
                and not manifest["duplicate_case_ids"]
            )
        ),
        "property_registry_valid_if_provided": (
            properties is None
            or (properties["exists"] and not properties["errors"])
        ),
        "checkpoint_exists_if_provided": (
            checkpoint is None or checkpoint["exists"]
        ),
    }

    warnings = []
    if not quality_checks["all_expected_source_files_present"]:
        warnings.append("one or more expected STRIVE source/config files are missing")
    if not quality_checks["all_implementation_checks_detected"]:
        missing = [
            k for k, v in strive["implementation_checks"].items() if not v
        ]
        warnings.append(
            "documented implementation pattern(s) not detected: %s"
            % ", ".join(missing)
        )
    if manifest is None:
        warnings.append(
            "no verification-case manifest supplied; corpus-level statistics are not measured"
        )
    elif not quality_checks["manifest_valid_if_provided"]:
        warnings.append("verification-case manifest has validation errors")
    if properties is None:
        warnings.append(
            "no formal property registry supplied; assurance thresholds remain unmeasured"
        )
    elif not quality_checks["property_registry_valid_if_provided"]:
        warnings.append("property registry has validation errors")
    if checkpoint is None:
        warnings.append(
            "no checkpoint supplied; checkpoint identity is not measured by this run"
        )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "A1-D-01",
        "profiled_at_utc": (
            datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        ),
        "strive_implementation": strive,
        "checkpoint": checkpoint,
        "verification_manifest": manifest,
        "property_registry": properties,
        "quality_checks": quality_checks,
        "warnings": warnings,
        "interpretation_notes": [
            "This profiler is verifier-neutral and does not perform formal verification.",
            "M-01 post-dynamics speed is clamped to [0,50] m/s and heading-rate to +/-2pi in the released implementation.",
            "Raw learned acceleration is not directly clamped; a bounded raw-acceleration property therefore targets learned behavior more directly.",
            "Normalization statistics are not safety limits and must not be substituted for formal property thresholds.",
            "A finite manifest of sampled cases is testing evidence unless each row also represents a formally quantified bounded domain.",
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
