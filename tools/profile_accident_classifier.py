#!/usr/bin/env python3
"""Profile the STRIVE M-04 cluster-based accident/scenario classifier.

The public release does not contain a separate supervised accident classifier.
Classification is implemented by:
  1. extracting the M-03 4-D collision feature;
  2. calling clustering.predict(scene_feats);
  3. mapping the cluster index through cluster_labels.txt.

This profiler validates that contract statically and can optionally:
  * inspect a TRUSTED local cluster.pkl;
  * summarize one or more *_labels.csv classification outputs.

WARNING: Python pickle can execute arbitrary code during loading. Never pass an
untrusted pickle to --cluster-pkl.

Designed for Python 3.6-compatible syntax.
"""

import argparse
import csv
import datetime
import hashlib
import pickle
import platform
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


EXPECTED_LABELS = [
    "Merge from Right",
    "Head On",
    "Behind",
    "Cutoff Left & Front",
    "T-Bone Left",
    "Front from Right",
    "Merge from Left",
    "T-Bone Right",
    "Cutoff Right",
    "Front from Left",
]


def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_text(path):
    p = Path(path)
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8")


def file_fact(path):
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.is_file(),
        "size_bytes": p.stat().st_size if p.is_file() else None,
        "sha256": sha256_file(p) if p.is_file() else None,
    }


def parse_labels(path):
    p = Path(path)
    if not p.is_file():
        return {
            "path": str(p),
            "exists": False,
            "labels": [],
            "count": 0,
        }
    text = p.read_text(encoding="utf-8").strip()
    first = text.splitlines()[0] if text else ""
    labels = [x.strip() for x in first.split(",") if x.strip()]
    return {
        "path": str(p),
        "exists": True,
        "sha256": sha256_file(p),
        "labels": labels,
        "count": len(labels),
    }


def inspect_eval_source(source):
    source = source or ""
    return {
        "loads_cluster_pickle": "clustering = pickle.load(f)" in source,
        "loads_cluster_labels_text": "cluster_labels = line.split(',')" in source,
        "strips_label_whitespace": "cluster_labels = [label.strip() for label in cluster_labels]" in source,
        "predicts_cluster_index": "scene_labels = clustering.predict(scene_feats)" in source,
        "maps_index_to_semantic_label": "cluster_labels[scene_labels[si]]" in source,
        "stores_label_idx": "scene['label_idx'] = scene_labels[si]" in source,
        "writes_classification_csv": "['scene', 'cluster_idx', 'cluster_name']" in source,
        "classifies_adv_sol_success": "'adv_sol_success'" in source,
        "classifies_sol_failed": "'sol_failed'" in source,
        "does_not_classify_adv_failed_in_cluster_loop": (
            "for coll_sname in ['adv_sol_success', 'sol_failed']" in source
        ),
        "no_probability_api_detected": (
            "predict_proba(" not in source and "decision_function(" not in source
        ),
    }


def inspect_feature_contract(source):
    source = source or ""
    return {
        "interpolation_scale_5": "interp_scale = 5" in source,
        "uses_earliest_collision": (
            "min_coll_t = np.amin(planner_coll_time_interp)" in source
            and "min_coll_idx = np.argmin(planner_coll_time_interp)" in source
        ),
        "normalizes_collision_direction": (
            "coll_pos = local_atk_states[:2] / torch.norm(local_atk_states[:2], dim=0)" in source
        ),
        "feature_concat_angvec_hvec": (
            "scene_feats = np.concatenate([angvec, hvec], axis=1)" in source
        ),
        "relative_speed_computed_but_not_in_predict_feature": (
            "'rel_s' : coll_rel_s" in source
            and "scene_feats = np.concatenate([angvec, hvec], axis=1)" in source
        ),
        "feature_dimension_expected": 4,
        "feature_order": [
            "collision_direction_x",
            "collision_direction_y",
            "attacker_heading_x",
            "attacker_heading_y",
        ],
    }


def inspect_requirements(source):
    source = source or ""
    entries = []
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(line)
    sklearn_lines = [
        x for x in entries
        if x.lower().startswith("scikit-learn") or x.lower().startswith("sklearn")
    ]
    return {
        "scikit_learn_lines": sklearn_lines,
        "scikit_learn_pinned": bool(sklearn_lines),
    }


def to_builtin(value):
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "tolist"):
        try:
            return value.tolist()
        except Exception:
            pass
    if isinstance(value, dict):
        return {str(k): to_builtin(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_builtin(v) for v in value]
    return repr(value)


def inspect_pickle(path):
    p = Path(path)
    result = {
        "path": str(p.resolve()),
        "exists": p.is_file(),
        "size_bytes": p.stat().st_size if p.is_file() else None,
        "sha256": sha256_file(p) if p.is_file() else None,
        "load_status": "not_loaded",
    }
    if not p.is_file():
        return result

    try:
        import sklearn
        result["inspection_environment_sklearn_version"] = sklearn.__version__
    except Exception as exc:
        result["inspection_environment_sklearn_version"] = None
        result["sklearn_import_error"] = str(exc)

    try:
        with p.open("rb") as f:
            obj = pickle.load(f)
    except Exception as exc:
        result["load_status"] = "load_failed"
        result["load_error"] = str(exc)
        return result

    result["load_status"] = "loaded"
    result["estimator_module"] = obj.__class__.__module__
    result["estimator_class"] = obj.__class__.__name__

    if hasattr(obj, "get_params"):
        try:
            result["parameters"] = to_builtin(obj.get_params(deep=False))
        except Exception as exc:
            result["parameters_error"] = str(exc)

    centers = getattr(obj, "cluster_centers_", None)
    if centers is not None:
        result["cluster_centers"] = to_builtin(centers)
        try:
            result["cluster_center_shape"] = [int(x) for x in centers.shape]
        except Exception:
            result["cluster_center_shape"] = None

    return result


def summarize_labels_csv(path):
    p = Path(path)
    result = {
        "path": str(p),
        "exists": p.is_file(),
        "sha256": sha256_file(p) if p.is_file() else None,
        "row_count": 0,
        "valid_row_count": 0,
        "invalid_rows": [],
        "class_index_counts": {},
        "class_name_counts": {},
        "index_name_pairs": {},
    }
    if not p.is_file():
        return result

    index_counts = Counter()
    name_counts = Counter()
    index_name_pairs = {}

    with p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        expected = {"scene", "cluster_idx", "cluster_name"}
        if reader.fieldnames is None or not expected.issubset(set(reader.fieldnames)):
            result["invalid_rows"].append(
                "header must include scene, cluster_idx, cluster_name"
            )
            return result

        for row_num, row in enumerate(reader, start=2):
            result["row_count"] += 1
            try:
                idx = int(row["cluster_idx"])
            except Exception:
                result["invalid_rows"].append(
                    "row %d has invalid cluster_idx %r" % (row_num, row.get("cluster_idx"))
                )
                continue
            name = (row.get("cluster_name") or "").strip()
            if not name:
                result["invalid_rows"].append(
                    "row %d has empty cluster_name" % row_num
                )
                continue

            result["valid_row_count"] += 1
            index_counts[idx] += 1
            name_counts[name] += 1

            if idx in index_name_pairs and index_name_pairs[idx] != name:
                result["invalid_rows"].append(
                    "cluster index %d maps to multiple names: %r and %r"
                    % (idx, index_name_pairs[idx], name)
                )
            else:
                index_name_pairs[idx] = name

    result["class_index_counts"] = {
        int(k): int(v) for k, v in sorted(index_counts.items())
    }
    result["class_name_counts"] = dict(sorted(name_counts.items()))
    result["index_name_pairs"] = {
        int(k): v for k, v in sorted(index_name_pairs.items())
    }
    return result


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
    parser.add_argument("--repo-root", default=".", help="Root of a STRIVE checkout.")
    parser.add_argument(
        "--cluster-pkl",
        help="Optional TRUSTED local cluster.pkl to inspect.",
    )
    parser.add_argument(
        "--cluster-labels",
        help="Optional cluster label file. Defaults to data/clustering/cluster_labels.txt.",
    )
    parser.add_argument(
        "--labels-csv",
        action="append",
        default=[],
        help="Optional classification CSV to summarize; may be passed multiple times.",
    )
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument("--metadata", help="Optional metadata/models/accident_classifier.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.repo_root)

    paths = {
        "eval_source": root / "src/eval_adv_gen.py",
        "clustering_source": root / "src/cluster_scenarios.py",
        "scenario_loader": root / "src/datasets/utils.py",
        "planner_eval_source": root / "src/eval_planner.py",
        "requirements": root / "requirements.txt",
    }

    label_path = (
        Path(args.cluster_labels)
        if args.cluster_labels
        else root / "data/clustering/cluster_labels.txt"
    )

    eval_src = read_text(paths["eval_source"])
    req_src = read_text(paths["requirements"])
    classification_behavior = inspect_eval_source(eval_src)
    feature_contract = inspect_feature_contract(eval_src)
    requirements = inspect_requirements(req_src)
    labels = parse_labels(label_path)

    artifact = (
        inspect_pickle(args.cluster_pkl)
        if args.cluster_pkl
        else {
            "supplied": False,
            "note": "Pass --cluster-pkl only for a trusted local pickle.",
        }
    )

    csv_profiles = [summarize_labels_csv(p) for p in args.labels_csv]

    checks = {
        "required_source_files_exist": all(p.is_file() for p in paths.values()),
        "classification_predict_call_detected": classification_behavior[
            "predicts_cluster_index"
        ],
        "index_to_label_lookup_detected": classification_behavior[
            "maps_index_to_semantic_label"
        ],
        "classification_restricted_to_collision_partitions": classification_behavior[
            "does_not_classify_adv_failed_in_cluster_loop"
        ],
        "four_dimensional_feature_contract_detected": (
            feature_contract["interpolation_scale_5"]
            and feature_contract["uses_earliest_collision"]
            and feature_contract["normalizes_collision_direction"]
            and feature_contract["feature_concat_angvec_hvec"]
        ),
        "public_label_count_10": labels["count"] == 10,
        "public_label_order_matches_expected": labels.get("labels") == EXPECTED_LABELS,
        "no_probability_api_in_public_classifier": classification_behavior[
            "no_probability_api_detected"
        ],
        "scikit_learn_pinned_in_public_requirements": requirements[
            "scikit_learn_pinned"
        ],
    }

    warnings = []
    if not checks["required_source_files_exist"]:
        warnings.append("one or more required M-04 source files are missing")
    if not checks["classification_predict_call_detected"]:
        warnings.append("public classification no longer appears to use clustering.predict")
    if not checks["public_label_count_10"]:
        warnings.append("semantic label count differs from the public ten-class contract")
    if not checks["public_label_order_matches_expected"]:
        warnings.append("semantic label ordering differs from the documented public release")
    if not checks["scikit_learn_pinned_in_public_requirements"]:
        warnings.append(
            "scikit-learn is used by the upstream clustering model but is not pinned in requirements.txt"
        )

    if args.cluster_pkl and artifact.get("load_status") == "loaded":
        shape = artifact.get("cluster_center_shape")
        if shape is not None:
            if len(shape) != 2 or shape[1] != 4:
                warnings.append(
                    "supplied cluster.pkl does not expose a 4-D cluster-center matrix"
                )
            if labels["count"] and shape[0] != labels["count"]:
                warnings.append(
                    "cluster center count does not match semantic label count"
                )

    for csv_profile in csv_profiles:
        for idx, name in csv_profile.get("index_name_pairs", {}).items():
            if 0 <= idx < len(labels.get("labels", [])):
                expected = labels["labels"][idx]
                if name != expected:
                    warnings.append(
                        "CSV %s maps cluster %d to %r but label artifact maps it to %r"
                        % (csv_profile["path"], idx, name, expected)
                    )
            else:
                warnings.append(
                    "CSV %s contains cluster index %d outside label range"
                    % (csv_profile["path"], idx)
                )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "M-04",
        "profiled_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "inspection_environment": {
            "python_version": platform.python_version(),
        },
        "source_files": {name: file_fact(path) for name, path in paths.items()},
        "classification_behavior": classification_behavior,
        "feature_contract": feature_contract,
        "labels": labels,
        "requirements": requirements,
        "artifact": artifact,
        "classification_csvs": csv_profiles,
        "quality_checks": checks,
        "warnings": warnings,
        "measurement_notes": [
            "M-04 is not a separate supervised classifier in the public STRIVE release.",
            "Its numeric prediction is the M-03 KMeans cluster index; its semantic class is an ordered label lookup.",
            "The public classification output is a hard label without calibrated probabilities.",
            "No direct released code path was identified that feeds these semantic classes into planner tuning.",
            "Only load trusted pickle artifacts.",
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
