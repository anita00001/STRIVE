#!/usr/bin/env python3
"""Profiler for A2-D-01 STRIVE accident-classifier verification data.

This profiler is designed for a target classifier that is described in the
STRIVE paper/supplement but is not present in the inspected public repository.

It can:
  * statically scan a STRIVE checkout for evidence of the binary learned
    accident-mode classifier;
  * summarize public generated-scenario directories/manifests if supplied;
  * validate an assurance JSONL manifest;
  * safely hash an optional classifier artifact without loading/unpickling it.

It does not infer that public M-04 KMeans cluster labeling is the binary
classifier target.

Designed for Python 3.6-compatible syntax.
"""

import argparse
import datetime
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


ALLOWED_LABELS = {"regular", "accident-prone"}
ALLOWED_PARTITIONS = {"development", "verification", "regression"}
ALLOWED_CASE_KINDS = {
    "natural_regular",
    "generated_accident",
    "perturbation",
    "counterexample",
    "regression",
}
ALLOWED_SOURCE_KINDS = {
    "nuscenes",
    "strive_generated",
    "assurance_generated",
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


def scan_public_repo(repo_root):
    """Scan text/code for binary classifier implementation indicators."""
    root = Path(repo_root)
    candidate_hits = []
    search_patterns = [
        re.compile(r"binary\s+classifier", re.I),
        re.compile(r"accident[-_ ]?prone", re.I),
        re.compile(r"accident\s+mode", re.I),
        re.compile(r"regular\s+mode", re.I),
        re.compile(r"binary_cross_entropy", re.I),
        re.compile(r"BCEWithLogitsLoss"),
    ]

    for suffix in ("*.py", "*.cfg", "*.yaml", "*.yml", "*.md", "*.txt"):
        for path in root.rglob(suffix):
            # Ignore this assurance documentation if profiler is run in an augmented checkout.
            rel = str(path.relative_to(root))
            if rel.startswith("docs/cards/assurance/") or rel.startswith("metadata/assurance/"):
                continue
            try:
                txt = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            hits = []
            for pat in search_patterns:
                if pat.search(txt):
                    hits.append(pat.pattern)
            if hits:
                candidate_hits.append({
                    "path": rel,
                    "patterns": hits,
                })

    # An implementation candidate should be Python code with classifier/loss evidence,
    # not merely README title text containing "Accident-Prone".
    implementation_candidates = []
    for hit in candidate_hits:
        p = hit["path"].lower()
        pats = " ".join(hit["patterns"]).lower()
        if p.endswith(".py") and (
            "classifier" in pats
            or "bcewithlogitsloss" in pats
            or "binary_cross_entropy" in pats
            or "accident" in p
            or "classifier" in p
        ):
            implementation_candidates.append(hit)

    known_public_cluster_files = {
        "src/cluster_scenarios.py": (root / "src/cluster_scenarios.py").is_file(),
        "src/eval_adv_gen.py": (root / "src/eval_adv_gen.py").is_file(),
        "data/clustering/cluster_labels.txt": (
            root / "data/clustering/cluster_labels.txt"
        ).is_file(),
    }

    return {
        "pattern_hits": candidate_hits,
        "implementation_candidates": implementation_candidates,
        "binary_classifier_implementation_detected": bool(implementation_candidates),
        "known_public_cluster_workflow_files": known_public_cluster_files,
        "interpretation": (
            "A false result means this static scan did not identify the paper-level "
            "binary classifier in the checkout; it is not a proof that no private/"
            "untracked artifact exists."
        ),
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
    out = {
        "path": str(p),
        "exists": p.is_file(),
        "sha256": sha256_file(p) if p.is_file() else None,
        "rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "duplicate_case_ids": [],
        "label_counts": {},
        "partition_counts": {},
        "case_kind_counts": {},
        "source_kind_counts": {},
        "source_split_counts": {},
        "planner_family_counts": {},
        "property_counts": {},
        "verification_status_counts": {},
        "classifier_hash_counts": {},
        "errors": [],
    }
    if not p.is_file():
        return out

    ids = []
    labels = Counter()
    partitions = Counter()
    kinds = Counter()
    sources = Counter()
    splits = Counter()
    planners = Counter()
    props = Counter()
    statuses = Counter()
    classifier_hashes = Counter()

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
            cid = row.get("case_id")
            partition = row.get("partition")
            kind = row.get("case_kind")
            label = row.get("anchor_label")
            source_kind = row.get("source_kind")
            prop = get_nested(row, "property.property_id")
            pver = get_nested(row, "property.property_version")
            status = get_nested(row, "verification.status", "not_run")
            classifier_hash = get_nested(row, "classifier.checkpoint_sha256")

            if not isinstance(cid, str) or not cid:
                errs.append("missing case_id")
            if partition not in ALLOWED_PARTITIONS:
                errs.append("invalid partition %r" % partition)
            if kind not in ALLOWED_CASE_KINDS:
                errs.append("invalid case_kind %r" % kind)
            if label not in ALLOWED_LABELS:
                errs.append("invalid anchor_label %r" % label)
            if source_kind not in ALLOWED_SOURCE_KINDS:
                errs.append("invalid source_kind %r" % source_kind)
            if not prop or not pver:
                errs.append("missing property_id/property_version")
            if status not in ALLOWED_STATUSES:
                errs.append("invalid verification status %r" % status)
            if classifier_hash is not None:
                if not isinstance(classifier_hash, str) or not re.match(
                    r"^[0-9a-fA-F]{64}$", classifier_hash
                ):
                    errs.append("classifier checkpoint hash must be SHA-256 hex")

            # Basic provenance consistency checks.
            if kind == "natural_regular" and label != "regular":
                errs.append("natural_regular must use regular anchor_label")
            if kind == "generated_accident" and label != "accident-prone":
                errs.append("generated_accident must use accident-prone anchor_label")
            if source_kind == "nuscenes" and kind == "generated_accident":
                errs.append("generated_accident should not declare source_kind=nuscenes")
            if source_kind == "strive_generated" and not row.get("scenario_id"):
                errs.append("strive_generated row should include scenario_id")

            if errs:
                out["invalid_rows"] += 1
                out["errors"].append(
                    "line %d (%s): %s"
                    % (lineno, cid or "<no-id>", "; ".join(errs))
                )
                continue

            out["valid_rows"] += 1
            ids.append(cid)
            labels[label] += 1
            partitions[partition] += 1
            kinds[kind] += 1
            sources[source_kind] += 1
            props["%s@%s" % (prop, pver)] += 1
            statuses[status] += 1

            if row.get("source_split") is not None:
                splits[str(row.get("source_split"))] += 1
            if row.get("planner_family") is not None:
                planners[str(row.get("planner_family"))] += 1
            if classifier_hash is not None:
                classifier_hashes[classifier_hash] += 1

    id_counts = Counter(ids)
    out["duplicate_case_ids"] = sorted(
        key for key, value in id_counts.items() if value > 1
    )
    out["label_counts"] = dict(labels)
    out["partition_counts"] = dict(partitions)
    out["case_kind_counts"] = dict(kinds)
    out["source_kind_counts"] = dict(sources)
    out["source_split_counts"] = dict(splits)
    out["planner_family_counts"] = dict(planners)
    out["property_counts"] = dict(props)
    out["verification_status_counts"] = dict(statuses)
    out["classifier_hash_counts"] = dict(classifier_hashes)
    return out


def profile_scenario_directory(path):
    """Lightweight metadata-only profiler for STRIVE scenario JSON files."""
    p = Path(path)
    out = {
        "path": str(p),
        "exists": p.is_dir(),
        "json_files": 0,
        "files_with_core_fields": 0,
        "files_missing_core_fields": 0,
        "maps": {},
        "agent_count": {
            "min": None,
            "max": None,
            "mean": None,
        },
        "errors": [],
    }
    if not p.is_dir():
        return out

    maps = Counter()
    agent_counts = []
    core = {"N", "dt", "map", "lw", "sem", "past", "fut_adv"}

    for fp in sorted(p.glob("*.json")):
        out["json_files"] += 1
        try:
            row = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as exc:
            out["errors"].append("%s: invalid JSON: %s" % (fp.name, exc))
            continue

        if core.issubset(set(row.keys())):
            out["files_with_core_fields"] += 1
        else:
            out["files_missing_core_fields"] += 1

        if row.get("map") is not None:
            maps[str(row["map"])] += 1
        if isinstance(row.get("N"), int):
            agent_counts.append(row["N"])

    out["maps"] = dict(maps)
    if agent_counts:
        out["agent_count"] = {
            "min": min(agent_counts),
            "max": max(agent_counts),
            "mean": sum(agent_counts) / float(len(agent_counts)),
        }
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
    parser.add_argument(
        "--classifier-artifact",
        help="Optional classifier checkpoint/file to hash only; it is never loaded.",
    )
    parser.add_argument(
        "--manifest",
        help="Optional assurance JSONL manifest.",
    )
    parser.add_argument(
        "--scenario-dir",
        action="append",
        default=[],
        help="Optional STRIVE generated-scenario directory; may be repeated.",
    )
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument(
        "--metadata",
        help="Optional metadata/assurance/data/accident_classifier_verification.yaml to update.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    repo_scan = scan_public_repo(args.repo_root)
    classifier_artifact = (
        file_fact(args.classifier_artifact)
        if args.classifier_artifact else None
    )
    manifest = profile_manifest(args.manifest) if args.manifest else None
    scenario_dirs = [
        profile_scenario_directory(x) for x in args.scenario_dir
    ]

    checks = {
        "public_binary_classifier_not_detected": (
            not repo_scan["binary_classifier_implementation_detected"]
        ),
        "manifest_valid_if_provided": (
            manifest is None
            or (
                manifest["exists"]
                and manifest["invalid_rows"] == 0
                and not manifest["duplicate_case_ids"]
            )
        ),
        "classifier_artifact_exists_if_provided": (
            classifier_artifact is None
            or classifier_artifact["exists"]
        ),
        "scenario_directories_valid_if_provided": all(
            row["exists"] and not row["errors"]
            for row in scenario_dirs
        ),
    }

    warnings = []
    if not checks["public_binary_classifier_not_detected"]:
        warnings.append(
            "possible binary classifier implementation detected; review target-availability statement"
        )
    if classifier_artifact is None:
        warnings.append(
            "no classifier artifact supplied; exact original learned target identity is unavailable"
        )
    if manifest is None:
        warnings.append(
            "no assurance manifest supplied; class/domain/property statistics are not measured"
        )
    elif not checks["manifest_valid_if_provided"]:
        warnings.append("assurance manifest contains validation errors")
    if not scenario_dirs:
        warnings.append(
            "no generated-scenario directory supplied; accident-prone source data are not profiled"
        )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "A2-D-01",
        "profiled_at_utc": (
            datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        ),
        "public_repo_scan": repo_scan,
        "classifier_artifact": classifier_artifact,
        "assurance_manifest": manifest,
        "generated_scenario_directories": scenario_dirs,
        "quality_checks": checks,
        "warnings": warnings,
        "source_facts_not_measured_from_repo": {
            "classifier_history_seconds": 2,
            "ego_feature_size": 64,
            "classification_head": "2-layer MLP",
            "generated_collision_training_examples": "over 1000",
            "generated_source_splits": ["train", "validation"],
            "generated_planner_families": ["Replay", "Rule-based"],
            "loss": "class-imbalance-weighted binary cross entropy",
            "note": (
                "These classifier/training facts come from the STRIVE paper/supplement, "
                "not from a public classifier implementation discovered by this profiler."
            ),
        },
        "interpretation_notes": [
            "The assurance target is the paper-level binary regular/accident-prone classifier, not public M-04 KMeans labeling.",
            "A classifier reproduction is a different assurance target unless equivalence to the original artifact is established.",
            "Regular/accident-prone labels are operational planner-mode labels, not universal formal safety ground truth.",
            "A formal robustness result requires a concrete classifier artifact plus a versioned bounded input domain and property.",
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
