#!/usr/bin/env python3
"""Static/result profiler for A1-M-01 STRIVE traffic-model verification.

This tool does NOT perform formal verification.

It:
  * inspects the STRIVE source for the M-01 architecture/dynamics facts relied on
    by the assurance card;
  * safely hashes an optional checkpoint without torch.load/unpickling;
  * summarizes optional JSONL formal-verification result records;
  * checks that construction invariants are not misreported as learned guarantees.

Recommended result JSONL row:
{
  "run_id": "run_001",
  "case_id": "case_001",
  "property_id": "P-A",
  "property_version": "1.0.0",
  "scope": "decoder_centered",
  "status": "verified",
  "verifier": "tool-name",
  "verifier_version": "x.y",
  "runtime_seconds": 12.3,
  "checkpoint_sha256": "...",
  "domain_hash": "...",
  "formal_model_hash": "...",
  "counterexample_replayed": null
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
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


ALLOWED_SCOPES = {"full", "decoder_centered", "reduced"}
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


def inspect_source(repo_root):
    root = Path(repo_root)
    paths = {
        "traffic_model": root / "src/models/traffic_model.py",
        "interaction_net": root / "src/models/interaction_net.py",
        "model_common": root / "src/models/common.py",
        "dataset_utils": root / "src/datasets/utils.py",
        "traffic_loss": root / "src/losses/traffic_model.py",
        "base_config": root / "src/utils/config.py",
    }

    tm = read_text(paths["traffic_model"])
    inter = read_text(paths["interaction_net"])
    common = read_text(paths["model_common"])
    du = read_text(paths["dataset_utils"])
    cfg = read_text(paths["base_config"])

    bike = extract_literal_assignment(du, "NUSC_BIKE_PARAMS")

    checks = {
        "traffic_model_class": "class TrafficModel(nn.Module)" in tm,
        "map_conv_groupnorm_relu": (
            "nn.Conv2d" in tm and "nn.GroupNorm" in tm and "nn.ReLU()" in tm
        ),
        "default_mlp_trajectory_encoder": "traj_encoder='mlp'" in tm,
        "gru_trajectory_encoder_supported": "TRAJ_ENCODER_CHOICES = ['mlp', 'gru']" in tm,
        "latent_size_32_default": (
            "latent_size=32" in tm
            or ("--latent_size" in cfg and "default=32" in cfg)
        ),
        "prior_scene_interaction_net": "self.prior_net = SceneInteractionNet" in tm,
        "posterior_scene_interaction_net": "self.posterior_net = SceneInteractionNet" in tm,
        "decoder_scene_interaction_net": "self.decoder_net = SceneInteractionNet" in tm,
        "decoder_gru_3_layers": (
            "self.num_memory_layers = 3" in tm
            and "self.decoder_memory = nn.GRU(4" in tm
        ),
        "message_passing_max_aggregation": "aggr='max'" in inter,
        "message_flow_source_to_target": "flow='source_to_target'" in inter,
        "relative_transform_in_messages": "transform2frame(pos_i, pos_j.unsqueeze(1))" in inter,
        "nan_relative_transform_zeroed": (
            "torch.where(torch.isnan(rel_trans), torch.zeros_like(rel_trans), rel_trans)" in inter
        ),
        "bicycle_raw_output_two_channels": (
            "self.traj_out_size = 2" in tm and "(a,hdot)" in tm
        ),
        "acceleration_unnormalization": (
            "a_out = dynamics_out[:,:,:,0]*self.bicycle_params['a_stats'][1]" in tm
        ),
        "ddh_unnormalization": (
            "ddh_out = dynamics_out[:,:,:,1]*self.bicycle_params['ddh_stats'][1]" in tm
        ),
        "speed_clamp": ".clamp(0.0, max_s)" in common,
        "heading_rate_clamp": ".clamp(-max_hdot, max_hdot)" in common,
        "dynamic_map_recropping": (
            "scene_graph.pos = cur_state_global.detach()" in tm
            and "cur_map_feat = self.encode_map(scene_graph, map_idx, map_env)" in tm
        ),
        "default_past_4": "--past_len" in cfg and "default=4" in cfg,
        "default_future_12": "--future_len" in cfg and "default=12" in cfg,
    }

    derived = {
        "NUSC_BIKE_PARAMS": bike,
        "default_horizon_seconds": 6.0,
        "construction_invariants": {
            "speed_m_per_s": [0.0, bike.get("maxs")] if isinstance(bike, dict) else None,
            "heading_rate_rad_per_s": (
                [-bike.get("maxhdot"), bike.get("maxhdot")]
                if isinstance(bike, dict) and bike.get("maxhdot") is not None
                else None
            ),
        },
    }

    return {
        "source_files": {name: file_fact(path) for name, path in paths.items()},
        "checks": checks,
        "derived": derived,
    }


def profile_results(path):
    p = Path(path)
    out = {
        "path": str(p),
        "exists": p.is_file(),
        "sha256": sha256_file(p) if p.is_file() else None,
        "rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "duplicate_run_ids": [],
        "status_counts": {},
        "scope_counts": {},
        "property_counts": {},
        "verifier_counts": {},
        "counterexample_replay": {
            "formal_counterexamples": 0,
            "replay_true": 0,
            "replay_false": 0,
            "replay_missing": 0,
        },
        "runtime_seconds": {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
        },
        "errors": [],
    }
    if not p.is_file():
        return out

    ids = []
    statuses = Counter()
    scopes = Counter()
    props = Counter()
    verifiers = Counter()
    runtimes = []

    with p.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            if not line.strip():
                continue
            out["rows"] += 1
            try:
                row = json.loads(line)
            except Exception as exc:
                out["invalid_rows"] += 1
                out["errors"].append("line %d: invalid JSON: %s" % (lineno, exc))
                continue

            errs = []
            run_id = row.get("run_id")
            status = row.get("status")
            scope = row.get("scope")
            prop_id = row.get("property_id")
            prop_ver = row.get("property_version")
            verifier = row.get("verifier")
            checkpoint = row.get("checkpoint_sha256")
            domain_hash = row.get("domain_hash")
            formal_hash = row.get("formal_model_hash")

            if not isinstance(run_id, str) or not run_id:
                errs.append("missing run_id")
            if status not in ALLOWED_STATUSES:
                errs.append("invalid status %r" % status)
            if scope not in ALLOWED_SCOPES:
                errs.append("invalid scope %r" % scope)
            if not prop_id or not prop_ver:
                errs.append("missing property_id/property_version")
            if not verifier:
                errs.append("missing verifier")
            for field, value in [
                ("checkpoint_sha256", checkpoint),
                ("domain_hash", domain_hash),
                ("formal_model_hash", formal_hash),
            ]:
                if not isinstance(value, str) or not re.match(r"^[0-9a-fA-F]{64}$", value):
                    errs.append("%s must be SHA-256 hex" % field)

            runtime = row.get("runtime_seconds")
            if runtime is not None:
                if not isinstance(runtime, (int, float)) or runtime < 0:
                    errs.append("runtime_seconds must be nonnegative numeric")
                else:
                    runtimes.append(float(runtime))

            if errs:
                out["invalid_rows"] += 1
                out["errors"].append(
                    "line %d (%s): %s"
                    % (lineno, run_id or "<no-run-id>", "; ".join(errs))
                )
                continue

            out["valid_rows"] += 1
            ids.append(run_id)
            statuses[status] += 1
            scopes[scope] += 1
            props["%s@%s" % (prop_id, prop_ver)] += 1
            verifiers[str(verifier)] += 1

            if status == "counterexample":
                out["counterexample_replay"]["formal_counterexamples"] += 1
                replay = row.get("counterexample_replayed")
                if replay is True:
                    out["counterexample_replay"]["replay_true"] += 1
                elif replay is False:
                    out["counterexample_replay"]["replay_false"] += 1
                else:
                    out["counterexample_replay"]["replay_missing"] += 1

    id_counts = Counter(ids)
    out["duplicate_run_ids"] = sorted(
        k for k, v in id_counts.items() if v > 1
    )
    out["status_counts"] = dict(statuses)
    out["scope_counts"] = dict(scopes)
    out["property_counts"] = dict(props)
    out["verifier_counts"] = dict(verifiers)

    if runtimes:
        out["runtime_seconds"] = {
            "count": len(runtimes),
            "min": min(runtimes),
            "max": max(runtimes),
            "mean": sum(runtimes) / float(len(runtimes)),
        }

    return out


def construction_invariant_warning(result_profile):
    """Flag suspicious result sets that call P-S/P-H verified without context."""
    warnings = []
    if not result_profile or not result_profile.get("exists"):
        return warnings

    for prop in result_profile.get("property_counts", {}):
        pid = prop.split("@", 1)[0]
        if pid in ("P-S", "P-H"):
            warnings.append(
                "%s results exist: distinguish a proof of the released clamp bound "
                "from a tighter learned-behavior specification." % pid
            )
    return warnings


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
    parser.add_argument(
        "--checkpoint",
        help="Optional M-01 checkpoint to hash only; no torch.load/unpickling is performed.",
    )
    parser.add_argument(
        "--results",
        help="Optional JSONL formal-verification result file.",
    )
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument(
        "--metadata",
        help="Optional metadata/assurance/models/traffic_model_verification.yaml to update.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    source = inspect_source(args.repo_root)
    checkpoint = file_fact(args.checkpoint) if args.checkpoint else None
    results = profile_results(args.results) if args.results else None

    quality_checks = {
        "all_expected_source_files_present": all(
            x["exists"] for x in source["source_files"].values()
        ),
        "all_expected_source_invariants_detected": all(source["checks"].values()),
        "checkpoint_exists_if_provided": checkpoint is None or checkpoint["exists"],
        "results_valid_if_provided": (
            results is None
            or (
                results["exists"]
                and results["invalid_rows"] == 0
                and not results["duplicate_run_ids"]
            )
        ),
    }

    warnings = []
    if not quality_checks["all_expected_source_files_present"]:
        warnings.append("one or more expected M-01 source files are missing")
    if not quality_checks["all_expected_source_invariants_detected"]:
        missing = [k for k, v in source["checks"].items() if not v]
        warnings.append(
            "documented source invariant(s) not detected: %s" % ", ".join(missing)
        )
    if checkpoint is None:
        warnings.append(
            "no checkpoint supplied; target learned artifact identity is not measured"
        )
    if results is None:
        warnings.append(
            "no verification result JSONL supplied; no formal assurance outcome is measured"
        )
    elif not quality_checks["results_valid_if_provided"]:
        warnings.append("verification result file has validation errors")
    if results:
        warnings.extend(construction_invariant_warning(results))

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "A1-M-01",
        "profiled_at_utc": (
            datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        ),
        "target_source": source,
        "checkpoint": checkpoint,
        "formal_results": results,
        "quality_checks": quality_checks,
        "warnings": warnings,
        "interpretation_notes": [
            "This profiler does not perform formal verification.",
            "A1-M-01 currently has no selected verifier and no claimed verified properties.",
            "Speed [0,50] m/s and heading-rate +/-2pi are construction invariants from released clamps.",
            "Raw learned acceleration and raw ddh are not directly clamped before dynamics.",
            "A formal result is meaningful only with checkpoint, domain, formal-model, property, and verifier provenance.",
            "Counterexamples should be replayed in original PyTorch M-01 whenever technically possible.",
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
