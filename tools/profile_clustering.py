#!/usr/bin/env python3
"""Profile STRIVE M-03 scenario clustering.

By default this performs static profiling of a STRIVE checkout:
  * hashes relevant source files;
  * verifies the released 4-D collision-feature construction;
  * verifies k=10, random_state=0, and interpolation scale=5;
  * reads the ordered semantic cluster labels;
  * checks whether scikit-learn is pinned in requirements.txt.

Optionally, --cluster-pkl loads a TRUSTED local pickle and reports fitted KMeans
metadata. Python pickle can execute arbitrary code while loading; never pass an
untrusted artifact.

Designed for Python 3.6-compatible syntax.
"""

import argparse
import datetime
import hashlib
import json
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


def parse_label_file(path):
    p = Path(path)
    if not p.is_file():
        return {
            "exists": False,
            "path": str(p),
            "labels": [],
            "count": 0,
        }
    text = p.read_text(encoding="utf-8").strip()
    first_line = text.splitlines()[0] if text else ""
    labels = [x.strip() for x in first_line.split(",") if x.strip()]
    return {
        "exists": True,
        "path": str(p),
        "sha256": sha256_file(p),
        "labels": labels,
        "count": len(labels),
    }


def inspect_source(source):
    source = source or ""
    return {
        "imports_sklearn_kmeans": "from sklearn.cluster import KMeans" in source,
        "default_k_10": bool(re.search(
            r"add_argument\(\s*['\"]--k['\"].*?default\s*=\s*10",
            source,
            flags=re.DOTALL,
        )),
        "kmeans_random_state_0": "KMeans(n_clusters=k, random_state=0).fit(scene_feats)" in source,
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
        "saves_pickle": "pickle.dump(clustering, f)" in source,
        "feature_dimension_expected": 4,
    }


def inspect_assignment(source):
    source = source or ""
    return {
        "predicts_with_cluster_model": "clustering.predict(scene_feats)" in source,
        "maps_index_to_label": "cluster_labels[scene_labels[si]]" in source,
        "writes_scene_cluster_csv": (
            "['scene', 'cluster_idx', 'cluster_name']" in source
        ),
        "assigns_collision_partitions": all(
            x in source for x in ["'adv_sol_success'", "'sol_failed'"]
        ),
    }


def inspect_requirements(source):
    source = source or ""
    lines = []
    for raw in source.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    sklearn_lines = [
        line for line in lines
        if line.lower().startswith("scikit-learn")
        or line.lower().startswith("sklearn")
    ]
    return {
        "scikit_learn_requirement_lines": sklearn_lines,
        "scikit_learn_pinned": bool(sklearn_lines),
        "requirements_entry_count": len(lines),
    }


def to_builtin(value):
    """Convert common numpy/scalar/container values to YAML/JSON-friendly values."""
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
    """Load a TRUSTED pickle explicitly supplied by the user."""
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

    labels = getattr(obj, "labels_", None)
    if labels is not None:
        labels_list = to_builtin(labels)
        result["fit_label_count"] = len(labels_list)
        result["fit_label_counts"] = {
            int(k): int(v) for k, v in sorted(Counter(labels_list).items())
        }

    for attr in ("inertia_", "n_iter_", "n_features_in_"):
        if hasattr(obj, attr):
            result[attr.rstrip("_")] = to_builtin(getattr(obj, attr))

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
        help="Optional TRUSTED local cluster.pkl to unpickle and inspect.",
    )
    parser.add_argument(
        "--labels",
        help="Optional cluster_labels.txt path. Defaults to data/clustering/cluster_labels.txt.",
    )
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument("--metadata", help="Optional metadata/models/clustering.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.repo_root)

    paths = {
        "fit_source": root / "src/cluster_scenarios.py",
        "assignment_source": root / "src/eval_adv_gen.py",
        "scenario_loader": root / "src/datasets/utils.py",
        "requirements": root / "requirements.txt",
    }
    label_path = Path(args.labels) if args.labels else root / "data/clustering/cluster_labels.txt"

    fit_src = read_text(paths["fit_source"])
    assignment_src = read_text(paths["assignment_source"])
    req_src = read_text(paths["requirements"])

    source_behavior = inspect_source(fit_src)
    assignment_behavior = inspect_assignment(assignment_src)
    requirements = inspect_requirements(req_src)
    labels = parse_label_file(label_path)
    artifact = inspect_pickle(args.cluster_pkl) if args.cluster_pkl else {
        "supplied": False,
        "note": "Pass --cluster-pkl only for a trusted local pickle to inspect fitted estimator state.",
    }

    expected_public_labels = [
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

    checks = {
        "required_source_files_exist": all(p.is_file() for p in paths.values()),
        "kmeans_release_pattern_detected": (
            source_behavior["imports_sklearn_kmeans"]
            and source_behavior["default_k_10"]
            and source_behavior["kmeans_random_state_0"]
        ),
        "four_dimensional_feature_detected": (
            source_behavior["normalizes_collision_direction"]
            and source_behavior["feature_concat_angvec_hvec"]
        ),
        "interpolation_scale_5_detected": source_behavior["interpolation_scale_5"],
        "label_file_has_10_entries": labels["count"] == 10,
        "label_file_matches_public_order": labels.get("labels") == expected_public_labels,
        "assignment_predict_and_label_mapping_detected": (
            assignment_behavior["predicts_with_cluster_model"]
            and assignment_behavior["maps_index_to_label"]
        ),
        "scikit_learn_is_pinned_in_requirements": requirements["scikit_learn_pinned"],
    }

    warnings = []
    if not checks["required_source_files_exist"]:
        warnings.append("one or more required M-03 source files are missing")
    if not checks["kmeans_release_pattern_detected"]:
        warnings.append("KMeans release pattern differs from documented k=10/random_state=0 behavior")
    if not checks["label_file_has_10_entries"]:
        warnings.append("cluster label count does not match public k=10 clustering")
    if not checks["label_file_matches_public_order"]:
        warnings.append("cluster label ordering differs from the public STRIVE label file")
    if not checks["scikit_learn_is_pinned_in_requirements"]:
        warnings.append(
            "scikit-learn is imported by clustering code but is not pinned in the inspected requirements.txt"
        )

    if args.cluster_pkl and artifact.get("load_status") == "loaded":
        shape = artifact.get("cluster_center_shape")
        if shape is not None and shape != [10, 4]:
            warnings.append(
                "supplied cluster.pkl center shape is %r rather than public expected [10, 4]" % shape
            )
        if labels["count"] and shape and labels["count"] != shape[0]:
            warnings.append(
                "label count does not match number of fitted cluster centers"
            )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "M-03",
        "profiled_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "inspection_environment": {
            "python_version": platform.python_version(),
        },
        "source_files": {name: file_fact(path) for name, path in paths.items()},
        "source_behavior": source_behavior,
        "assignment_behavior": assignment_behavior,
        "labels": labels,
        "requirements": requirements,
        "artifact": artifact,
        "quality_checks": checks,
        "warnings": warnings,
        "measurement_notes": [
            "Public fitting features are [angvec_x, angvec_y, hvec_x, hvec_y].",
            "The public label file is a separate artifact and must remain paired with the corresponding cluster.pkl.",
            "The README describes the supplied paper clustering as fitted on over 400 scenarios from multiple nuScenes subsets and planner versions.",
            "scikit-learn is not pinned in the inspected public requirements.txt, so refitting behavior can depend on local sklearn defaults.",
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
