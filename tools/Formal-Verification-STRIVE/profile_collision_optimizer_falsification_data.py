#!/usr/bin/env python3
"""Profiler for A3-D-01 STRIVE specification-driven falsification evidence.

This tool does NOT perform falsification.

It:
  * inspects a STRIVE checkout for source/config invariants used by A3-D-01;
  * validates a JSONL falsification-run manifest;
  * profiles D-02-style generated scenario JSON directories;
  * validates a YAML specification registry;
  * cross-tabulates native STRIVE outcome and external specification outcome.

Designed for Python 3.6-compatible syntax.
"""

import argparse
import datetime
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


ALLOWED_PLANNERS = {"replay", "rule_based"}
ALLOWED_RESULTS = {
    "counterexample",
    "no_counterexample_found",
    "invalid_candidate",
    "timeout",
    "error",
}
ALLOWED_NATIVE_PARTITIONS = {
    "adv_failed",
    "sol_failed",
    "adv_sol_success",
    None,
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


def is_sha256(value):
    return isinstance(value, str) and bool(re.match(r"^[0-9a-fA-F]{64}$", value))


def get_nested(obj, path, default=None):
    cur = obj
    for key in path.split("."):
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def inspect_strive(repo_root):
    root = Path(repo_root)
    paths = {
        "adv_scenario_gen": root / "src/adv_scenario_gen.py",
        "init_optim": root / "src/utils/init_optim.py",
        "adv_optim": root / "src/utils/adv_optim.py",
        "scenario_gen": root / "src/utils/scenario_gen.py",
        "hardcode_planner": root / "src/planners/hardcode_goalcond_nusc.py",
        "adv_rule_cfg": root / "configs/adv_gen_rule_based.cfg",
        "adv_replay_cfg": root / "configs/adv_gen_replay.cfg",
    }

    texts = {k: read_text(v) for k, v in paths.items()}
    joined = "\n".join(texts.values())

    checks = {
        "adv_scenario_generation_entrypoint_present": paths["adv_scenario_gen"].is_file(),
        "c01_init_optimizer_present": paths["init_optim"].is_file(),
        "scenario_serialization_present": paths["scenario_gen"].is_file(),
        "rule_based_planner_present": paths["hardcode_planner"].is_file(),
        "adv_sol_success_partition_present": "adv_sol_success" in joined,
        "sol_failed_partition_present": "sol_failed" in joined,
        "adv_failed_partition_present": "adv_failed" in joined,
        "fut_adv_serialized": "'fut_adv'" in joined or '"fut_adv"' in joined,
        "fut_init_serialized": "'fut_init'" in joined or '"fut_init"' in joined,
        "attack_agt_serialized": "attack_agt" in joined,
        "attack_t_serialized": "attack_t" in joined,
        "z_adv_serialized": "z_adv" in joined,
        "z_sol_serialized": "z_sol" in joined,
    }

    # Avoid assuming exact file names for optimizer internals if repository layout differs.
    existing = {k: file_fact(v) for k, v in paths.items()}
    return {
        "source_files": existing,
        "implementation_checks": checks,
        "note": (
            "Static pattern checks validate only that expected public STRIVE artifacts/"
            "serialization concepts are visible; they do not run the optimizer."
        ),
    }


def validate_spec_registry(path):
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
        ver = prop.get("version")
        if not pid or not ver:
            out["errors"].append("property %d missing property_id/version" % idx)
            continue

        key = "%s@%s" % (pid, ver)
        if key in seen:
            out["errors"].append("duplicate property %s" % key)
        seen.add(key)

        has_temporal = bool(prop.get("temporal_semantics"))
        has_eval = bool(prop.get("evaluator"))
        out["properties"].append({
            "property_id": pid,
            "version": ver,
            "signal": prop.get("signal"),
            "operator": prop.get("operator"),
            "threshold": prop.get("threshold"),
            "units": prop.get("units"),
            "temporal_semantics_declared": has_temporal,
            "evaluator_declared": has_eval,
        })

        if not has_temporal:
            out["errors"].append("%s missing temporal_semantics" % key)
        if not has_eval:
            out["errors"].append("%s missing evaluator" % key)

    return out


def profile_manifest(path):
    p = Path(path)
    out = {
        "path": str(p),
        "exists": p.is_file(),
        "sha256": sha256_file(p) if p.is_file() else None,
        "rows": 0,
        "valid_rows": 0,
        "invalid_rows": 0,
        "duplicate_run_ids": [],
        "planner_counts": {},
        "property_counts": {},
        "result_counts": {},
        "native_partition_counts": {},
        "independent_replay_counts": {},
        "cross_tab_native_vs_external": {},
        "errors": [],
    }
    if not p.is_file():
        return out

    ids = []
    planners = Counter()
    props = Counter()
    results = Counter()
    native = Counter()
    replay = Counter()
    cross = Counter()

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
            seed_id = row.get("seed_case_id")
            planner = row.get("planner_type")
            prop = get_nested(row, "property.property_id")
            pver = get_nested(row, "property.property_version")
            strive_rev = get_nested(row, "strive.revision")
            ckpt = get_nested(row, "strive.traffic_model_checkpoint_sha256")
            opt_hash = get_nested(row, "strive.optimizer_config_sha256")
            scenario_hash = get_nested(row, "artifact.scenario_sha256")
            status = get_nested(row, "result.status")
            native_part = get_nested(row, "result.native_strive_partition")
            replay_confirmed = get_nested(row, "result.independent_replay_confirmed")

            if not isinstance(run_id, str) or not run_id:
                errs.append("missing run_id")
            if not isinstance(seed_id, str) or not seed_id:
                errs.append("missing seed_case_id")
            if planner not in ALLOWED_PLANNERS:
                errs.append("invalid planner_type %r" % planner)
            if not prop or not pver:
                errs.append("missing property_id/property_version")
            if not isinstance(strive_rev, str) or not strive_rev:
                errs.append("missing strive revision")
            for field, value in (
                ("traffic_model_checkpoint_sha256", ckpt),
                ("optimizer_config_sha256", opt_hash),
                ("scenario_sha256", scenario_hash),
            ):
                if not is_sha256(value):
                    errs.append("%s must be SHA-256 hex" % field)
            if status not in ALLOWED_RESULTS:
                errs.append("invalid result status %r" % status)
            if native_part not in ALLOWED_NATIVE_PARTITIONS:
                errs.append("invalid native STRIVE partition %r" % native_part)
            if status == "counterexample" and replay_confirmed is not True:
                errs.append(
                    "counterexample must set result.independent_replay_confirmed=true"
                )

            if errs:
                out["invalid_rows"] += 1
                out["errors"].append(
                    "line %d (%s): %s"
                    % (lineno, run_id or "<no-run-id>", "; ".join(errs))
                )
                continue

            out["valid_rows"] += 1
            ids.append(run_id)
            planners[planner] += 1
            props["%s@%s" % (prop, pver)] += 1
            results[status] += 1
            native[str(native_part)] += 1
            replay[str(bool(replay_confirmed))] += 1
            cross["%s | %s" % (native_part, status)] += 1

    id_counts = Counter(ids)
    out["duplicate_run_ids"] = sorted(
        key for key, value in id_counts.items() if value > 1
    )
    out["planner_counts"] = dict(planners)
    out["property_counts"] = dict(props)
    out["result_counts"] = dict(results)
    out["native_partition_counts"] = dict(native)
    out["independent_replay_counts"] = dict(replay)
    out["cross_tab_native_vs_external"] = dict(cross)
    return out


def profile_scenario_directory(path):
    p = Path(path)
    out = {
        "path": str(p),
        "exists": p.is_dir(),
        "json_files": 0,
        "valid_json_files": 0,
        "core_schema_files": 0,
        "native_partition_hint": p.name if p.name in {
            "adv_failed", "sol_failed", "adv_sol_success"
        } else None,
        "maps": {},
        "dt_counts": {},
        "agent_count": {"min": None, "max": None, "mean": None},
        "errors": [],
    }
    if not p.is_dir():
        return out

    maps = Counter()
    dts = Counter()
    counts = []
    core = {"N", "dt", "map", "lw", "sem", "past", "fut_init", "fut_adv"}

    for fp in sorted(p.glob("*.json")):
        out["json_files"] += 1
        try:
            row = json.loads(fp.read_text(encoding="utf-8"))
        except Exception as exc:
            out["errors"].append("%s: invalid JSON: %s" % (fp.name, exc))
            continue
        out["valid_json_files"] += 1

        if core.issubset(set(row.keys())):
            out["core_schema_files"] += 1

        if row.get("map") is not None:
            maps[str(row["map"])] += 1
        if row.get("dt") is not None:
            dts[str(row["dt"])] += 1
        if isinstance(row.get("N"), int):
            counts.append(row["N"])

    out["maps"] = dict(maps)
    out["dt_counts"] = dict(dts)
    if counts:
        out["agent_count"] = {
            "min": min(counts),
            "max": max(counts),
            "mean": sum(counts) / float(len(counts)),
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
    parser.add_argument("--repo-root", default=".", help="Root of STRIVE checkout.")
    parser.add_argument("--manifest", help="Optional A3 JSONL falsification-run manifest.")
    parser.add_argument("--spec-registry", help="Optional YAML specification registry.")
    parser.add_argument(
        "--scenario-dir",
        action="append",
        default=[],
        help="Optional D-02 scenario directory; may be repeated.",
    )
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument(
        "--metadata",
        help="Optional metadata/assurance/data/collision_optimizer_falsification.yaml to update.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    source = inspect_strive(args.repo_root)
    manifest = profile_manifest(args.manifest) if args.manifest else None
    specs = validate_spec_registry(args.spec_registry) if args.spec_registry else None
    scenarios = [profile_scenario_directory(x) for x in args.scenario_dir]

    checks = {
        "expected_core_source_files_present": all(
            source["source_files"][k]["exists"]
            for k in ("adv_scenario_gen", "init_optim", "scenario_gen", "hardcode_planner")
        ),
        "manifest_valid_if_provided": (
            manifest is None
            or (
                manifest["exists"]
                and manifest["invalid_rows"] == 0
                and not manifest["duplicate_run_ids"]
            )
        ),
        "spec_registry_valid_if_provided": (
            specs is None
            or (specs["exists"] and not specs["errors"])
        ),
        "scenario_dirs_valid_if_provided": all(
            x["exists"] and not x["errors"] for x in scenarios
        ),
    }

    warnings = []
    if not checks["expected_core_source_files_present"]:
        warnings.append("one or more expected STRIVE source files are missing")
    if manifest is None:
        warnings.append(
            "no falsification manifest supplied; no A3 outcome statistics are measured"
        )
    elif not checks["manifest_valid_if_provided"]:
        warnings.append("falsification manifest has validation errors")
    if specs is None:
        warnings.append(
            "no specification registry supplied; TTC/separation semantics remain unfrozen"
        )
    elif not checks["spec_registry_valid_if_provided"]:
        warnings.append("specification registry has validation errors")
    if not scenarios:
        warnings.append(
            "no generated-scenario directories supplied; D-02 candidate corpus not profiled"
        )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "A3-D-01",
        "profiled_at_utc": (
            datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        ),
        "strive_source": source,
        "specification_registry": specs,
        "falsification_manifest": manifest,
        "scenario_directories": scenarios,
        "quality_checks": checks,
        "warnings": warnings,
        "interpretation_notes": [
            "This profiler does not run STRIVE optimization or perform falsification.",
            "A native STRIVE adversarial success is not automatically an A3 specification violation.",
            "A TTC/separation violation may be valid even when native STRIVE collision success is false.",
            "No counterexample found is not proof of safety.",
            "C-03 solution success is operational evidence, not a formal solvability proof.",
            "Final A3 counterexamples should be independently re-evaluated from saved trajectory artifacts.",
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
