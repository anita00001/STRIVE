#!/usr/bin/env python3
"""Static/result profiler for A3-M-01 STRIVE collision-optimizer falsification.

This profiler does NOT run STRIVE optimization and does NOT itself falsify a
safety specification.

It can:
  * inspect a STRIVE checkout for implementation patterns relied upon by A3-M-01;
  * validate a YAML safety-specification registry;
  * validate/summarize JSONL falsification result records;
  * cross-tabulate native STRIVE outcomes against independent A3 outcomes;
  * flag result records that treat search failure as a proof.

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


ALLOWED_PLANNERS = {"replay", "rule_based"}
ALLOWED_A3_STATUS = {
    "counterexample",
    "no_counterexample_found",
    "invalid_candidate",
    "timeout",
    "error",
}
ALLOWED_NATIVE = {
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


def read_text(path):
    p = Path(path)
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def file_fact(path):
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.is_file(),
        "size_bytes": p.stat().st_size if p.is_file() else None,
        "sha256": sha256_file(p) if p.is_file() else None,
    }


def is_sha256(value):
    return isinstance(value, str) and bool(re.match(r"^[0-9a-fA-F]{64}$", value))


def scan_strive(repo_root):
    root = Path(repo_root)
    files = {
        "adv_scenario_gen": root / "src/adv_scenario_gen.py",
        "init_optim": root / "src/utils/init_optim.py",
        "hardcode_planner": root / "src/planners/hardcode_goalcond_nusc.py",
        "adv_loss": root / "src/losses/adv_gen_nusc.py",
        "scenario_utils": root / "src/utils/scenario_gen.py",
        "traffic_model": root / "src/models/traffic_model.py",
    }

    texts = {k: read_text(v) for k, v in files.items()}
    joined = "\n".join(texts.values())

    checks = {
        "adv_generation_entrypoint_present": files["adv_scenario_gen"].is_file(),
        "initialization_optimizer_present": files["init_optim"].is_file(),
        "rule_based_planner_present": files["hardcode_planner"].is_file(),
        "adversarial_loss_present": files["adv_loss"].is_file(),
        "traffic_model_present": files["traffic_model"].is_file(),
        "native_partitions_visible": all(
            token in joined for token in ("adv_failed", "sol_failed", "adv_sol_success")
        ),
        "d02_fut_adv_serialization_visible": "fut_adv" in joined,
        "d02_fut_sol_serialization_visible": "fut_sol" in joined,
        "attack_agent_visible": "attack_agt" in joined,
        "attack_time_visible": "attack_t" in joined,
        "latent_adv_visible": "z_adv" in joined,
        "latent_sol_visible": "z_sol" in joined,
        "planner_dt_0_2_visible": (
            "'dt' : 0.2" in texts["hardcode_planner"]
            or '"dt" : 0.2' in texts["hardcode_planner"]
            or "dt': 0.2" in texts["hardcode_planner"]
            or "dt=0.2" in texts["hardcode_planner"]
        ),
        "traffic_model_dt_0_5_visible": "self.dt = 0.5" in texts["traffic_model"],
    }

    return {
        "source_files": {k: file_fact(v) for k, v in files.items()},
        "implementation_checks": checks,
        "note": (
            "These are static source-pattern checks only. They do not execute the "
            "optimizer or establish a falsification result."
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
    required_fields = [
        "property_id",
        "version",
        "signal",
        "temporal_semantics",
        "horizon",
        "interpolation",
        "geometry",
        "tolerance",
        "evaluator",
    ]

    for idx, prop in enumerate(props):
        if not isinstance(prop, dict):
            out["errors"].append("property %d is not a mapping" % idx)
            continue

        missing = [name for name in required_fields if prop.get(name) is None]
        pid = prop.get("property_id")
        ver = prop.get("version")

        if pid and ver:
            key = "%s@%s" % (pid, ver)
            if key in seen:
                out["errors"].append("duplicate property %s" % key)
            seen.add(key)
        else:
            key = "property_%d" % idx

        if missing:
            out["errors"].append(
                "%s missing fields: %s" % (key, ", ".join(missing))
            )

        out["properties"].append({
            "property_id": pid,
            "version": ver,
            "signal": prop.get("signal"),
            "threshold": prop.get("threshold"),
            "units": prop.get("units"),
            "temporal_semantics": prop.get("temporal_semantics"),
            "geometry": prop.get("geometry"),
            "evaluator": prop.get("evaluator"),
        })

    return out


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
        "planner_counts": {},
        "property_counts": {},
        "a3_status_counts": {},
        "native_status_counts": {},
        "native_vs_a3": {},
        "replay_confirmation": {
            "counterexamples": 0,
            "confirmed": 0,
            "not_confirmed": 0,
            "missing": 0,
        },
        "runtime_seconds": {
            "count": 0,
            "min": None,
            "max": None,
            "mean": None,
        },
        "errors": [],
        "warnings": [],
    }
    if not p.is_file():
        return out

    ids = []
    planners = Counter()
    properties = Counter()
    a3_status = Counter()
    native_status = Counter()
    cross = Counter()
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
            planner = row.get("planner_type")
            prop = row.get("property_id")
            pver = row.get("property_version")
            status = row.get("a3_status")
            native = row.get("native_strive_status")
            replay = row.get("independent_replay_confirmed")
            runtime = row.get("runtime_seconds")

            if not isinstance(run_id, str) or not run_id:
                errs.append("missing run_id")
            if planner not in ALLOWED_PLANNERS:
                errs.append("invalid planner_type %r" % planner)
            if not prop or not pver:
                errs.append("missing property_id/property_version")
            if status not in ALLOWED_A3_STATUS:
                errs.append("invalid a3_status %r" % status)
            if native not in ALLOWED_NATIVE:
                errs.append("invalid native_strive_status %r" % native)

            for field in (
                "traffic_model_checkpoint_sha256",
                "planner_config_sha256",
                "optimizer_config_sha256",
                "spec_registry_sha256",
                "evaluator_sha256",
                "scenario_sha256",
            ):
                if not is_sha256(row.get(field)):
                    errs.append("%s must be SHA-256 hex" % field)

            if runtime is not None:
                if not isinstance(runtime, (int, float)) or runtime < 0:
                    errs.append("runtime_seconds must be nonnegative numeric")
                else:
                    runtimes.append(float(runtime))

            if status == "counterexample" and replay is not True:
                errs.append(
                    "counterexample requires independent_replay_confirmed=true"
                )

            if row.get("claims_property_proved_safe") is True:
                errs.append(
                    "result must not claim property proved safe from falsification search"
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
            properties["%s@%s" % (prop, pver)] += 1
            a3_status[status] += 1
            native_status[str(native)] += 1
            cross["%s | %s" % (native, status)] += 1

            if status == "counterexample":
                out["replay_confirmation"]["counterexamples"] += 1
                if replay is True:
                    out["replay_confirmation"]["confirmed"] += 1
                elif replay is False:
                    out["replay_confirmation"]["not_confirmed"] += 1
                else:
                    out["replay_confirmation"]["missing"] += 1

            # Flag interesting non-equivalences, not errors.
            if native == "adv_failed" and status == "counterexample":
                out["warnings"].append(
                    "%s: external specification counterexample despite native adv_failed"
                    % run_id
                )
            if native in ("sol_failed", "adv_sol_success") and status == "no_counterexample_found":
                out["warnings"].append(
                    "%s: native STRIVE outcome does not imply external specification violation"
                    % run_id
                )

    id_counts = Counter(ids)
    out["duplicate_run_ids"] = sorted(
        key for key, value in id_counts.items() if value > 1
    )
    out["planner_counts"] = dict(planners)
    out["property_counts"] = dict(properties)
    out["a3_status_counts"] = dict(a3_status)
    out["native_status_counts"] = dict(native_status)
    out["native_vs_a3"] = dict(cross)

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
    parser.add_argument("--repo-root", default=".", help="Root of STRIVE checkout.")
    parser.add_argument("--spec-registry", help="Optional YAML safety-specification registry.")
    parser.add_argument("--results", help="Optional JSONL A3 falsification result file.")
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument(
        "--metadata",
        help="Optional metadata/assurance/models/collision_optimizer_falsification.yaml to update.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    source = scan_strive(args.repo_root)
    specs = validate_spec_registry(args.spec_registry) if args.spec_registry else None
    results = profile_results(args.results) if args.results else None

    checks = {
        "expected_core_source_files_present": all(
            source["source_files"][key]["exists"]
            for key in (
                "adv_scenario_gen",
                "init_optim",
                "hardcode_planner",
                "adv_loss",
                "traffic_model",
            )
        ),
        "spec_registry_valid_if_provided": (
            specs is None or (specs["exists"] and not specs["errors"])
        ),
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
    if not checks["expected_core_source_files_present"]:
        warnings.append("one or more expected STRIVE source files are missing")
    if specs is None:
        warnings.append(
            "no specification registry supplied; safety semantics are not frozen"
        )
    elif not checks["spec_registry_valid_if_provided"]:
        warnings.append("specification registry has validation errors")
    if results is None:
        warnings.append(
            "no falsification result records supplied; no A3 outcome is measured"
        )
    elif not checks["results_valid_if_provided"]:
        warnings.append("falsification result file has validation errors")
    if results:
        warnings.extend(results.get("warnings", []))

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "A3-M-01",
        "profiled_at_utc": (
            datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        ),
        "strive_source": source,
        "specification_registry": specs,
        "falsification_results": results,
        "quality_checks": checks,
        "warnings": warnings,
        "interpretation_notes": [
            "This profiler does not run the STRIVE optimizer and does not perform falsification.",
            "Native STRIVE adversarial success and external A3 specification violation are distinct result dimensions.",
            "A3 counterexamples require independent replay confirmation from the saved trajectory.",
            "No counterexample found is not a proof of safety.",
            "C-03 success/failure is operational evidence, not a formal solvability/unsolvability proof.",
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
