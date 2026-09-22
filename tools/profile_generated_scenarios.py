#!/usr/bin/env python3
"""Profile STRIVE D-02 generated-scenario JSON files.

This profiler is dependency-light: it uses Python's standard library plus
PyYAML only when YAML output/metadata updates are requested.

It supports either:
  1. a local STRIVE `scenario_results` directory containing
     adv_failed/, sol_failed/, and adv_sol_success/; or
  2. a flat directory, such as a success-only released bundle, paired with
     --assume-partition.

It validates JSON structure/shapes, computes partition counts and the success
rates used by STRIVE's evaluator, inventories fields/maps/horizons/latent widths,
checks finite numeric values, and builds a SHA-256 manifest.

It deliberately does NOT reimplement STRIVE's collision geometry. Dynamic
collision correctness should be checked with the repository evaluation code.
"""

import argparse
import datetime
import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


PARTITIONS = ("adv_failed", "sol_failed", "adv_sol_success")
CORE_FIELDS = ("N", "dt", "map", "lw", "sem", "past", "fut_init", "fut_adv")


def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def shape_of(value):
    """Return a rectangular nested-list shape, or None if ragged/non-list."""
    if not isinstance(value, list):
        return []
    if len(value) == 0:
        return [0]
    child_shapes = [shape_of(x) for x in value]
    if any(s is None for s in child_shapes):
        return None
    first = child_shapes[0]
    if any(s != first for s in child_shapes[1:]):
        return None
    return [len(value)] + first


def scan_finite(value, path="$"):
    issues = []
    if isinstance(value, bool) or value is None or isinstance(value, str):
        return issues
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not math.isfinite(value):
            issues.append("%s is non-finite: %r" % (path, value))
        return issues
    if isinstance(value, list):
        for i, item in enumerate(value):
            issues.extend(scan_finite(item, "%s[%d]" % (path, i)))
        return issues
    if isinstance(value, dict):
        for key, item in value.items():
            issues.extend(scan_finite(item, "%s.%s" % (path, key)))
        return issues
    issues.append("%s has unexpected value type %s" % (path, type(value).__name__))
    return issues


def list_scenario_files(root, assume_partition=None):
    root = Path(root)
    found = []
    partition_dirs = [p for p in PARTITIONS if (root / p).is_dir()]
    if partition_dirs:
        for partition in PARTITIONS:
            pdir = root / partition
            if not pdir.is_dir():
                continue
            for p in sorted(pdir.glob("*.json")):
                found.append((partition, p))
        return found, "partitioned"

    if assume_partition is None:
        raise ValueError(
            "No STRIVE partition directories found. For a flat scenario directory, "
            "pass --assume-partition with one of: %s" % ", ".join(PARTITIONS)
        )

    for p in sorted(root.glob("*.json")):
        found.append((assume_partition, p))
    return found, "flat"


def check_shape(name, value, expected_prefix=None, expected_last=None):
    shape = shape_of(value)
    problems = []
    if shape is None:
        problems.append("%s is ragged" % name)
        return shape, problems
    if expected_prefix is not None:
        if len(shape) < len(expected_prefix):
            problems.append("%s shape %s is too short" % (name, shape))
        else:
            for idx, expected in enumerate(expected_prefix):
                if expected is not None and shape[idx] != expected:
                    problems.append(
                        "%s dim %d=%s, expected %s" % (name, idx, shape[idx], expected)
                    )
    if expected_last is not None and (not shape or shape[-1] != expected_last):
        problems.append("%s last dimension %s, expected %s" % (
            name, shape[-1] if shape else None, expected_last
        ))
    return shape, problems


def validate_record(record, partition, filename):
    issues = []
    missing = [k for k in CORE_FIELDS if k not in record]
    if missing:
        issues.append("missing core fields: %s" % ", ".join(missing))

    n = record.get("N")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        issues.append("N must be a positive integer")
        n_for_shape = None
    else:
        n_for_shape = n

    dt = record.get("dt")
    if not isinstance(dt, (int, float)) or isinstance(dt, bool) or dt <= 0:
        issues.append("dt must be a positive number")

    if not isinstance(record.get("map"), str) or not record.get("map"):
        issues.append("map must be a non-empty string")

    shapes = {}

    specs = {
        "lw": (n_for_shape, 2),
        "sem": (n_for_shape, None),
        "past": (n_for_shape, 6),
        "fut_init": (n_for_shape, 4),
        "fut_adv": (n_for_shape, 4),
        "fut_sol": (n_for_shape, 4),
        "z_adv": (n_for_shape, None),
        "z_sol": (n_for_shape, None),
    }

    for key, (first_dim, last_dim) in specs.items():
        if key not in record:
            continue
        prefix = [first_dim] if first_dim is not None else None
        shape, probs = check_shape(key, record[key], expected_prefix=prefix, expected_last=last_dim)
        shapes[key] = shape
        issues.extend(probs)

    if "fut_internal_ego" in record:
        shape, probs = check_shape("fut_internal_ego", record["fut_internal_ego"], expected_last=4)
        shapes["fut_internal_ego"] = shape
        issues.extend(probs)

    if "z_prior" in record:
        zp = record["z_prior"]
        if not isinstance(zp, dict):
            issues.append("z_prior must be an object")
        else:
            for key in ("mean", "var"):
                if key not in zp:
                    issues.append("z_prior missing %s" % key)
                    continue
                shape, probs = check_shape(
                    "z_prior.%s" % key,
                    zp[key],
                    expected_prefix=[n_for_shape] if n_for_shape is not None else None,
                )
                shapes["z_prior.%s" % key] = shape
                issues.extend(probs)

    atk = record.get("attack_agt")
    if atk is not None:
        if not isinstance(atk, int) or isinstance(atk, bool):
            issues.append("attack_agt must be integer")
        elif n_for_shape is not None and not (0 <= atk < n_for_shape):
            issues.append("attack_agt=%d outside [0,N)" % atk)

    attack_t = record.get("attack_t")
    if attack_t is not None:
        if not isinstance(attack_t, int) or isinstance(attack_t, bool):
            issues.append("attack_t must be integer")
        else:
            fut_shape = shapes.get("fut_adv")
            if fut_shape and len(fut_shape) >= 2 and not (0 <= attack_t < fut_shape[1]):
                issues.append("attack_t=%d outside fut_adv horizon %d" % (attack_t, fut_shape[1]))

    # Partition expectations from public caller behavior.
    has_sol = "fut_sol" in record
    has_z_sol = "z_sol" in record
    if partition == "adv_failed":
        if has_sol or has_z_sol:
            issues.append("adv_failed unexpectedly contains solution fields")
    elif partition in ("sol_failed", "adv_sol_success"):
        if not has_sol:
            issues.append("%s missing fut_sol" % partition)
        if not has_z_sol:
            issues.append("%s missing z_sol" % partition)

    finite_issues = scan_finite(record)
    if finite_issues:
        # Keep all issues in per-file detail; callers may summarize count.
        issues.extend(finite_issues)

    return shapes, issues


def basic_stats(values):
    values = list(values)
    if not values:
        return None
    values_sorted = sorted(values)
    out = {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / float(len(values)),
        "median": statistics.median(values_sorted),
    }
    return out


def aggregate_manifest(entries):
    h = hashlib.sha256()
    for item in sorted(entries, key=lambda x: x["relative_path"]):
        line = "%s  %s\n" % (item["sha256"], item["relative_path"])
        h.update(line.encode("utf-8"))
    return h.hexdigest()


def profile_dataset(root, assume_partition=None):
    root = Path(root)
    files, layout = list_scenario_files(root, assume_partition=assume_partition)

    partition_counts = Counter()
    field_presence = Counter()
    map_counts = Counter()
    n_values = []
    dt_values = []
    past_steps = []
    future_steps = defaultdict(list)
    semantic_widths = []
    latent_widths = defaultdict(list)
    attack_agents = []
    attack_times = []
    manifest = []
    per_file_issues = {}
    unreadable = 0

    for partition, path in files:
        rel = str(path.relative_to(root))
        digest = sha256_file(path)
        manifest.append({
            "relative_path": rel,
            "partition": partition,
            "size_bytes": path.stat().st_size,
            "sha256": digest,
        })
        partition_counts[partition] += 1

        try:
            with path.open("r", encoding="utf-8") as f:
                record = json.load(f)
        except Exception as exc:
            unreadable += 1
            per_file_issues[rel] = ["JSON load failed: %s" % exc]
            continue

        if not isinstance(record, dict):
            per_file_issues[rel] = ["top-level JSON value is not an object"]
            continue

        for key in record.keys():
            field_presence[key] += 1

        shapes, issues = validate_record(record, partition, rel)
        if issues:
            per_file_issues[rel] = issues

        if isinstance(record.get("N"), int) and not isinstance(record.get("N"), bool):
            n_values.append(record["N"])
        if isinstance(record.get("dt"), (int, float)) and not isinstance(record.get("dt"), bool):
            dt_values.append(float(record["dt"]))
        if isinstance(record.get("map"), str):
            map_counts[record["map"]] += 1

        pshape = shapes.get("past")
        if pshape and len(pshape) >= 3:
            past_steps.append(pshape[1])

        for key in ("fut_init", "fut_adv", "fut_sol"):
            shape = shapes.get(key)
            if shape and len(shape) >= 3:
                future_steps[key].append(shape[1])

        sem_shape = shapes.get("sem")
        if sem_shape and len(sem_shape) >= 2:
            semantic_widths.append(sem_shape[1])

        for key in ("z_adv", "z_sol", "z_prior.mean", "z_prior.var"):
            shape = shapes.get(key)
            if shape and len(shape) >= 2:
                latent_widths[key].append(shape[-1])

        if isinstance(record.get("attack_agt"), int) and not isinstance(record.get("attack_agt"), bool):
            attack_agents.append(record["attack_agt"])
        if isinstance(record.get("attack_t"), int) and not isinstance(record.get("attack_t"), bool):
            attack_times.append(record["attack_t"])

    total = len(files)
    adv_success = partition_counts["adv_sol_success"] + partition_counts["sol_failed"]
    adv_rate = (adv_success / float(total)) if total else None
    sol_rate = (
        partition_counts["adv_sol_success"] / float(adv_success)
        if adv_success else None
    )
    total_success = (adv_rate * sol_rate) if adv_rate is not None and sol_rate is not None else None

    field_rates = {}
    for field, count in sorted(field_presence.items()):
        field_rates[field] = {
            "count": count,
            "fraction_of_files": count / float(total) if total else None,
        }

    shape_statistics = {
        "past_steps": dict(Counter(past_steps)),
        "future_steps": {k: dict(Counter(v)) for k, v in future_steps.items()},
        "semantic_widths": dict(Counter(semantic_widths)),
        "latent_widths": {k: dict(Counter(v)) for k, v in latent_widths.items()},
    }

    quality_checks = {
        "scenario_file_count": total,
        "unreadable_json_count": unreadable,
        "files_with_issues": len(per_file_issues),
        "all_json_readable": unreadable == 0,
        "all_files_pass_lightweight_validation": len(per_file_issues) == 0,
        "partition_layout_detected": layout == "partitioned",
    }

    return {
        "profile_schema_version": "1.0",
        "card_id": "D-02",
        "profiled_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "dataset_root": str(root.resolve()),
        "layout": layout,
        "assumed_flat_partition": assume_partition if layout == "flat" else None,
        "manifest_sha256": aggregate_manifest(manifest),
        "partition_counts": {p: partition_counts[p] for p in PARTITIONS},
        "success_rates": {
            "adversarial_success_rate": adv_rate,
            "solution_success_rate_conditional_on_adversarial_success": sol_rate,
            "total_success_rate": total_success,
            "definitions": {
                "adversarial_success": "(adv_sol_success + sol_failed) / total",
                "solution_success": "adv_sol_success / (adv_sol_success + sol_failed)",
                "total_success": "adversarial_success * solution_success",
            },
        },
        "field_presence": field_rates,
        "map_counts": dict(sorted(map_counts.items())),
        "agent_count_stats": basic_stats(n_values),
        "dt_stats": basic_stats(dt_values),
        "shape_statistics": shape_statistics,
        "attack_statistics": {
            "attack_agent_index_stats": basic_stats(attack_agents),
            "attack_time_step_stats": basic_stats(attack_times),
            "attack_agent_index_counts": dict(sorted(Counter(attack_agents).items())),
            "attack_time_step_counts": dict(sorted(Counter(attack_times).items())),
        },
        "quality_checks": quality_checks,
        "issues": per_file_issues,
        "manifest": manifest,
        "measurement_notes": [
            "This profiler validates JSON/schema/shape/statistical properties only.",
            "It does not reimplement STRIVE polygon/map collision checks.",
            "For a flat success-only public bundle, use --assume-partition adv_sol_success.",
            "Result partition is provenance carried by directory location; it is not serialized inside each JSON file.",
        ],
    }


def dump_yaml(data):
    if yaml is None:
        raise RuntimeError("PyYAML is required to write YAML.")
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=115)


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
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=115)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenarios",
        required=True,
        help="STRIVE scenario_results directory or flat scenario JSON directory.",
    )
    parser.add_argument(
        "--assume-partition",
        choices=PARTITIONS,
        help="Partition label for a flat directory, e.g. a success-only public bundle.",
    )
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument("--metadata", help="Optional metadata/data/generated_scenarios.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    profile = profile_dataset(args.scenarios, assume_partition=args.assume_partition)

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
