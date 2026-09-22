#!/usr/bin/env python3
"""Static/result profiler for A2-M-01 accident-classifier verification.

This profiler does NOT perform formal verification.

It:
  * scans a STRIVE checkout for evidence of a public binary learned
    regular-vs-accident-prone classifier;
  * distinguishes that target from the public clustering workflow;
  * safely hashes an optional classifier artifact without loading it;
  * validates/summarizes optional JSONL verification results;
  * flags result sets missing artifact/domain/formal-model provenance.

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


ALLOWED_SCOPES = {"full", "head_only", "reproduction"}
ALLOWED_STATUSES = {
    "verified",
    "counterexample",
    "unknown",
    "timeout",
    "error",
    "not_run",
}
ALLOWED_CLASSES = {"regular", "accident-prone"}


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


def scan_public_repo(repo_root):
    root = Path(repo_root)

    patterns = {
        "binary_classifier_phrase": re.compile(r"binary\s+classifier", re.I),
        "accident_prone_phrase": re.compile(r"accident[-_ ]?prone", re.I),
        "binary_cross_entropy": re.compile(r"binary_cross_entropy", re.I),
        "bce_logits": re.compile(r"BCEWithLogitsLoss"),
        "classifier_class": re.compile(r"class\s+\w*Classifier\w*\s*\(", re.I),
    }

    hits = []
    for suffix in ("*.py", "*.cfg", "*.yaml", "*.yml", "*.md", "*.txt"):
        for path in root.rglob(suffix):
            rel = str(path.relative_to(root))
            if rel.startswith("docs/cards/assurance/") or rel.startswith("metadata/assurance/"):
                continue

            try:
                txt = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue

            matched = []
            for name, pattern in patterns.items():
                if pattern.search(txt):
                    matched.append(name)

            if matched:
                hits.append({"path": rel, "patterns": matched})

    implementation_candidates = []
    for hit in hits:
        rel = hit["path"].lower()
        pats = set(hit["patterns"])
        if rel.endswith(".py") and (
            "classifier_class" in pats
            or "binary_cross_entropy" in pats
            or "bce_logits" in pats
            or "classifier" in rel
        ):
            implementation_candidates.append(hit)

    public_cluster = {
        "cluster_scenarios_py": (root / "src/cluster_scenarios.py").is_file(),
        "eval_adv_gen_py": (root / "src/eval_adv_gen.py").is_file(),
        "cluster_labels_txt": (
            root / "data/clustering/cluster_labels.txt"
        ).is_file(),
    }

    return {
        "pattern_hits": hits,
        "binary_classifier_implementation_candidates": implementation_candidates,
        "binary_classifier_implementation_detected": bool(implementation_candidates),
        "public_cluster_workflow": public_cluster,
        "note": (
            "This is a conservative static scan. A negative result means no matching "
            "public implementation was detected in this checkout; it does not prove "
            "that no private/untracked artifact exists."
        ),
    }


def is_sha256(value):
    return isinstance(value, str) and bool(re.match(r"^[0-9a-fA-F]{64}$", value))


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
        "anchor_class_counts": {},
        "required_class_counts": {},
        "verifier_counts": {},
        "counterexample_replay": {
            "counterexamples": 0,
            "replay_confirmed": 0,
            "replay_not_confirmed": 0,
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
    anchors = Counter()
    required = Counter()
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
            scope = row.get("scope")
            status = row.get("status")
            prop = row.get("property_id")
            pver = row.get("property_version")
            anchor = row.get("anchor_class")
            req = row.get("required_class")
            verifier = row.get("verifier")

            if not isinstance(run_id, str) or not run_id:
                errs.append("missing run_id")
            if scope not in ALLOWED_SCOPES:
                errs.append("invalid scope %r" % scope)
            if status not in ALLOWED_STATUSES:
                errs.append("invalid status %r" % status)
            if not prop or not pver:
                errs.append("missing property_id/property_version")
            if anchor not in ALLOWED_CLASSES:
                errs.append("invalid anchor_class %r" % anchor)
            if req not in ALLOWED_CLASSES:
                errs.append("invalid required_class %r" % req)
            if not verifier:
                errs.append("missing verifier")

            for field in (
                "classifier_sha256",
                "domain_sha256",
                "formal_model_sha256",
            ):
                if not is_sha256(row.get(field)):
                    errs.append("%s must be SHA-256 hex" % field)

            runtime = row.get("runtime_seconds")
            if runtime is not None:
                if not isinstance(runtime, (int, float)) or runtime < 0:
                    errs.append("runtime_seconds must be nonnegative numeric")
                else:
                    runtimes.append(float(runtime))

            # Semantics checks for core class-preservation properties.
            if prop == "C-FN":
                if anchor != "accident-prone" or req != "accident-prone":
                    errs.append("C-FN requires accident-prone anchor and required class")
            if prop == "C-FP":
                if anchor != "regular" or req != "regular":
                    errs.append("C-FP requires regular anchor and required class")

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
            props["%s@%s" % (prop, pver)] += 1
            anchors[anchor] += 1
            required[req] += 1
            verifiers[str(verifier)] += 1

            if status == "counterexample":
                out["counterexample_replay"]["counterexamples"] += 1
                replay = row.get("counterexample_replayed")
                if replay is True:
                    out["counterexample_replay"]["replay_confirmed"] += 1
                elif replay is False:
                    out["counterexample_replay"]["replay_not_confirmed"] += 1
                else:
                    out["counterexample_replay"]["replay_missing"] += 1

    id_counts = Counter(ids)
    out["duplicate_run_ids"] = sorted(
        k for k, v in id_counts.items() if v > 1
    )
    out["status_counts"] = dict(statuses)
    out["scope_counts"] = dict(scopes)
    out["property_counts"] = dict(props)
    out["anchor_class_counts"] = dict(anchors)
    out["required_class_counts"] = dict(required)
    out["verifier_counts"] = dict(verifiers)

    if runtimes:
        out["runtime_seconds"] = {
            "count": len(runtimes),
            "min": min(runtimes),
            "max": max(runtimes),
            "mean": sum(runtimes) / float(len(runtimes)),
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
        help="Optional original/reproduction classifier artifact to hash only.",
    )
    parser.add_argument(
        "--results",
        help="Optional JSONL formal-verification result records.",
    )
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument(
        "--metadata",
        help="Optional metadata/assurance/models/accident_classifier_verification.yaml to update.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    repo_scan = scan_public_repo(args.repo_root)
    artifact = (
        file_fact(args.classifier_artifact)
        if args.classifier_artifact else None
    )
    results = profile_results(args.results) if args.results else None

    quality_checks = {
        "public_binary_classifier_not_detected": (
            not repo_scan["binary_classifier_implementation_detected"]
        ),
        "artifact_exists_if_provided": artifact is None or artifact["exists"],
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
    if not quality_checks["public_binary_classifier_not_detected"]:
        warnings.append(
            "possible public binary-classifier implementation detected; review availability statement"
        )
    if artifact is None:
        warnings.append(
            "no classifier artifact supplied; exact verification target identity is not measured"
        )
    if results is None:
        warnings.append(
            "no formal-verification results supplied; no assurance outcome is measured"
        )
    elif not quality_checks["results_valid_if_provided"]:
        warnings.append("verification result file has validation errors")

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "A2-M-01",
        "profiled_at_utc": (
            datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        ),
        "public_repo_scan": repo_scan,
        "classifier_artifact": artifact,
        "formal_results": results,
        "quality_checks": quality_checks,
        "warnings": warnings,
        "published_target_facts_not_reconstructed_from_public_classifier_code": {
            "history_seconds": 2,
            "input": "all-agent recent trajectories + local map information",
            "ego_feature_size": 64,
            "classification_head": "2-layer MLP",
            "output_classes": ["regular", "accident-prone"],
            "note": (
                "These facts come from the project/paper/supplement description, "
                "not from an original public classifier implementation detected here."
            ),
        },
        "interpretation_notes": [
            "The target is the paper-level learned binary mode classifier, not public M-04 clustering.",
            "A reproduction must remain labeled as a reproduction unless equivalence to the original artifact is established.",
            "Formal verification of class stability does not prove that the selected planner mode is safe.",
            "Counterexamples should be replayed in the executable target whenever possible.",
            "Unknown/timeout is not evidence of safety or unsafety.",
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
