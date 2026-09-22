#!/usr/bin/env python3
"""Quantitative profiler for D-01: nuScenes as consumed by STRIVE.

The profiler is intentionally metadata-first. It does not read camera, lidar, or
radar payloads. It can:
  1. profile a local v1.0-trainval or v1.0-mini metadata installation;
  2. calculate category/location/timestamp statistics;
  3. reproduce STRIVE's default scene split and candidate window counts when
     nuscenes-devkit split definitions are available;
  4. write a standalone YAML report; and/or
  5. merge the report under profile.measured in nuscenes_strive.yaml.

Compatible with the Python 3.6-era public STRIVE environment.
"""

import argparse
import copy
import datetime
import json
import math
import os
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


REQUIRED_TABLES = [
    "scene.json",
    "sample.json",
    "sample_annotation.json",
    "instance.json",
    "category.json",
    "log.json",
]

MAIN_RAW_CATEGORIES = ["vehicle.car", "vehicle.truck"]


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_metadata_root(root):
    """Accept common STRIVE/nuScenes root layouts and find the v1.0-* directory."""
    candidates = [
        root,
        root / "v1.0-trainval",
        root / "v1.0-mini",
        root / "trainval" / "v1.0-trainval",
        root / "mini" / "v1.0-mini",
    ]
    for candidate in candidates:
        if (candidate / "scene.json").is_file():
            return candidate
    return root


def find_maps_root(metadata_root):
    """Find the maps directory used by common nuScenes and STRIVE layouts."""
    candidates = [
        metadata_root / "maps",
        metadata_root.parent / "maps",
        metadata_root.parent.parent / "maps",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return None


def safe_summary(values):
    values = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if not values:
        return None
    return {
        "count": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "mean": statistics.mean(values),
        "max": max(values),
    }


def duplicate_token_count(rows):
    if not rows:
        return 0
    toks = [row.get("token") for row in rows if row.get("token")]
    return len(toks) - len(set(toks))


def raw_category_prefix(category_name):
    """Match STRIVE's '.'.join(category_name.split('.')[:2]) behavior."""
    if not category_name:
        return None
    parts = category_name.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else category_name


def get_standard_split_names():
    """Load nuScenes scene split definitions if the pinned devkit is installed."""
    try:
        from nuscenes.utils.splits import create_splits_scenes
        return create_splits_scenes()
    except Exception:
        return None


def candidate_window_count(scene_names, scene_sample_counts, past_len, future_len, seq_interval):
    """Mirror range(0, T - seq_len, seq_interval) in STRIVE's post_process()."""
    seq_len = past_len + future_len
    total = 0
    missing = []
    per_scene = {}
    for name in scene_names:
        if name not in scene_sample_counts:
            missing.append(name)
            continue
        t = int(scene_sample_counts[name])
        n = len(range(0, max(0, t - seq_len), seq_interval))
        per_scene[name] = n
        total += n
    return total, per_scene, missing


def derive_strive_splits(version_name, all_scene_names, val_size, randomize_val):
    """Reproduce deterministic default STRIVE split logic where possible.

    randomize_val=True depends on repository-specific precomputed index arrays, so
    this metadata-only profiler reports that case as unsupported rather than
    guessing.
    """
    if randomize_val:
        return None, "randomize_val=True requires STRIVE's precomputed index arrays; not reproduced by metadata-only profiler"

    split_defs = get_standard_split_names()
    if split_defs is None:
        return None, "nuscenes-devkit split definitions unavailable"

    if version_name == "v1.0-trainval":
        source_train = list(split_defs["train"])
        source_test = list(split_defs["val"])
        reserve = int(val_size)
    elif version_name == "v1.0-mini":
        source_train = list(split_defs["mini_train"])
        source_test = list(split_defs["mini_val"])
        reserve = 2
    else:
        return None, "unsupported metadata version for STRIVE split derivation: %s" % version_name

    installed = set(all_scene_names)
    source_train = [x for x in source_train if x in installed]
    source_test = [x for x in source_test if x in installed]

    reserve = min(reserve, len(source_train))
    val_scenes = source_train[:reserve]
    train_scenes = source_train[reserve:]
    test_scenes = source_test

    return {
        "train": sorted(train_scenes),
        "val": sorted(val_scenes),
        "test": sorted(test_scenes),
    }, None


def find_prediction_metadata(maps_root):
    if maps_root is None:
        return {
            "maps_root": None,
            "prediction_scenes_json": None,
            "prediction_scene_key_count": None,
            "prediction_target_count": None,
        }
    pred = maps_root / "prediction" / "prediction_scenes.json"
    result = {
        "maps_root": str(maps_root.resolve()),
        "prediction_scenes_json": str(pred.resolve()) if pred.is_file() else None,
        "prediction_scene_key_count": None,
        "prediction_target_count": None,
    }
    if pred.is_file():
        try:
            obj = load_json(pred)
            result["prediction_scene_key_count"] = len(obj)
            result["prediction_target_count"] = sum(len(v) for v in obj.values() if isinstance(v, list))
        except Exception as exc:
            result["error"] = str(exc)
    return result


def build_profile(args):
    supplied_root = Path(args.nuscenes_root).expanduser()
    metadata_root = resolve_metadata_root(supplied_root)
    maps_root = find_maps_root(metadata_root)

    warnings = []
    tables = {}

    for filename in REQUIRED_TABLES:
        path = metadata_root / filename
        if not path.is_file():
            warnings.append("missing required metadata table: %s" % path)
            tables[filename] = None
            continue
        try:
            tables[filename] = load_json(path)
        except Exception as exc:
            warnings.append("failed to parse %s: %s" % (path, exc))
            tables[filename] = None

    scenes = tables.get("scene.json") or []
    samples = tables.get("sample.json") or []
    annotations = tables.get("sample_annotation.json") or []
    instances = tables.get("instance.json") or []
    categories = tables.get("category.json") or []
    logs = tables.get("log.json") or []

    quality = {
        "missing_required_table_count": sum(1 for name in REQUIRED_TABLES if tables.get(name) is None),
        "duplicate_tokens": {
            name: duplicate_token_count(rows)
            for name, rows in tables.items()
            if isinstance(rows, list)
        },
        "broken_scene_sample_chains": 0,
        "non_monotonic_scene_timestamp_steps": 0,
        "scene_declared_sample_count_mismatches": 0,
        "missing_log_references": 0,
    }

    # Index tables.
    sample_by_token = {row.get("token"): row for row in samples if row.get("token")}
    log_by_token = {row.get("token"): row for row in logs if row.get("token")}
    instance_by_token = {row.get("token"): row for row in instances if row.get("token")}

    # Scene/location and temporal-chain statistics.
    scene_count_by_location = Counter()
    scene_sample_counts = {}
    scene_durations = []
    sample_deltas = []

    for scene in scenes:
        name = scene.get("name")
        log = log_by_token.get(scene.get("log_token"))
        if log is None:
            quality["missing_log_references"] += 1
            location = "<missing>"
        else:
            location = log.get("location", "<missing>")
        scene_count_by_location[location] += 1

        token = scene.get("first_sample_token")
        seen = set()
        timestamps = []
        observed = 0
        broken = False

        while token:
            if token in seen or token not in sample_by_token:
                broken = True
                break
            seen.add(token)
            sample = sample_by_token[token]
            observed += 1
            ts = sample.get("timestamp")
            if ts is not None:
                timestamps.append(float(ts) / 1e6)
            token = sample.get("next")

        if broken:
            quality["broken_scene_sample_chains"] += 1

        if name:
            scene_sample_counts[name] = observed

        declared = scene.get("nbr_samples")
        if declared is not None and int(declared) != observed:
            quality["scene_declared_sample_count_mismatches"] += 1

        if len(timestamps) >= 2:
            deltas = []
            for a, b in zip(timestamps[:-1], timestamps[1:]):
                dt = b - a
                deltas.append(dt)
                if dt <= 0:
                    quality["non_monotonic_scene_timestamp_steps"] += 1
            sample_deltas.extend(deltas)
            scene_durations.append(timestamps[-1] - timestamps[0])

    # Category statistics.
    annotation_count_by_category = Counter()
    main_annotation_count = Counter()
    for ann in annotations:
        raw = raw_category_prefix(ann.get("category_name"))
        if raw:
            annotation_count_by_category[raw] += 1
            if raw in MAIN_RAW_CATEGORIES:
                main_annotation_count[raw] += 1

    # Instance category must be inferred from an annotation because instance.json
    # itself does not carry category_name.
    instance_category = {}
    for ann in annotations:
        tok = ann.get("instance_token")
        raw = raw_category_prefix(ann.get("category_name"))
        if tok and raw and tok not in instance_category:
            instance_category[tok] = raw
    instance_count_by_category = Counter(instance_category.values())

    # Basic annotation sanity.
    invalid_size_annotations = 0
    for ann in annotations:
        size = ann.get("size")
        if isinstance(size, list) and any((not isinstance(v, (int, float)) or v <= 0) for v in size):
            invalid_size_annotations += 1
    quality["annotations_with_nonpositive_or_invalid_size"] = invalid_size_annotations

    # STRIVE split and candidate-window statistics.
    version_name = metadata_root.name if metadata_root.name.startswith("v1.0-") else args.version
    all_scene_names = [s.get("name") for s in scenes if s.get("name")]
    split_scenes, split_warning = derive_strive_splits(
        version_name=version_name,
        all_scene_names=all_scene_names,
        val_size=args.val_size,
        randomize_val=args.randomize_val,
    )
    if split_warning:
        warnings.append(split_warning)

    split_scene_counts = None
    split_candidate_counts = None
    split_missing_scenes = None
    if split_scenes is not None:
        split_scene_counts = {k: len(v) for k, v in split_scenes.items()}
        split_candidate_counts = {}
        split_missing_scenes = {}
        for split_name, names in split_scenes.items():
            total, _, missing = candidate_window_count(
                names,
                scene_sample_counts,
                args.past_len,
                args.future_len,
                args.seq_interval,
            )
            split_candidate_counts[split_name] = total
            if missing:
                split_missing_scenes[split_name] = missing

    prediction = find_prediction_metadata(maps_root)
    if maps_root is None:
        warnings.append("maps directory was not found from the supplied root")
    elif prediction.get("prediction_scenes_json") is None:
        warnings.append("maps/prediction/prediction_scenes.json was not found")

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "D-01",
        "profiled_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "input": {
            "supplied_root": str(supplied_root.resolve()),
            "resolved_metadata_root": str(metadata_root.resolve()),
            "resolved_version": version_name,
            "past_len": args.past_len,
            "future_len": args.future_len,
            "seq_interval": args.seq_interval,
            "val_size": args.val_size,
            "randomize_val": bool(args.randomize_val),
        },
        "table_counts": {
            "scenes": len(scenes),
            "samples": len(samples),
            "sample_annotations": len(annotations),
            "instances": len(instances),
            "categories": len(categories),
            "logs": len(logs),
        },
        "scene_count_by_location": dict(sorted(scene_count_by_location.items())),
        "annotation_count_by_category": dict(sorted(annotation_count_by_category.items())),
        "instance_count_by_category": dict(sorted(instance_count_by_category.items())),
        "strive_main_annotation_count": {
            raw: main_annotation_count.get(raw, 0) for raw in MAIN_RAW_CATEGORIES
        },
        "strive_main_instance_count": {
            raw: instance_count_by_category.get(raw, 0) for raw in MAIN_RAW_CATEGORIES
        },
        "scene_sample_count_summary": safe_summary(scene_sample_counts.values()),
        "scene_duration_seconds_summary": safe_summary(scene_durations),
        "sample_delta_seconds_summary": safe_summary(sample_deltas),
        "strive_default_split_scene_counts": split_scene_counts,
        "strive_default_candidate_sequence_counts": split_candidate_counts,
        "split_scene_names_missing_from_metadata": split_missing_scenes,
        "prediction_metadata": prediction,
        "quality_checks": quality,
        "warnings": warnings,
        "measurement_notes": [
            "Annotation/instance category counts are upstream metadata counts before STRIVE map/temporal filtering.",
            "Candidate sequence counts reproduce STRIVE's scene-window enumeration, not the number of retained agent nodes.",
            "Drivable-area/car-park filtering is not recomputed by this metadata-only profiler.",
        ],
    }
    return profile


def dump_yaml(data):
    if yaml is None:
        raise RuntimeError("PyYAML is required to write YAML. STRIVE requirements pin pyyaml==5.4.1.")
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=110)


def write_report(profile, output):
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(dump_yaml(profile), encoding="utf-8")
    else:
        sys.stdout.write(dump_yaml(profile))


def update_metadata(metadata_path, profile):
    if yaml is None:
        raise RuntimeError("PyYAML is required to update metadata.")
    path = Path(metadata_path)
    if not path.is_file():
        raise FileNotFoundError("metadata file not found: %s" % path)
    with path.open("r", encoding="utf-8") as f:
        metadata = yaml.safe_load(f) or {}
    metadata.setdefault("profile", {})
    metadata["profile"]["measurement_status"] = "measured"
    metadata["profile"]["measured"] = profile
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(metadata, f, sort_keys=False, allow_unicode=True, width=110)


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--nuscenes-root",
        required=True,
        help="Path to a nuScenes root, STRIVE trainval/mini folder, or v1.0-* metadata directory.",
    )
    parser.add_argument("--output", help="Optional standalone YAML profile output path.")
    parser.add_argument(
        "--metadata",
        help="Optional metadata/data/nuscenes_strive.yaml to update under profile.measured.",
    )
    parser.add_argument("--version", default="v1.0-trainval", help="Fallback version when root name is ambiguous.")
    parser.add_argument("--past-len", type=int, default=4)
    parser.add_argument("--future-len", type=int, default=12)
    parser.add_argument("--seq-interval", type=int, default=1)
    parser.add_argument("--val-size", type=int, default=200)
    parser.add_argument("--randomize-val", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    profile = build_profile(args)
    if args.metadata:
        update_metadata(args.metadata, profile)
    if args.output or not args.metadata:
        write_report(profile, args.output)


if __name__ == "__main__":
    main()
