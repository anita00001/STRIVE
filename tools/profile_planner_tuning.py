#!/usr/bin/env python3
"""Static profiler for STRIVE F-01 planner tuning.

The profiler extracts DEF_CONFIG and TUNED_VAL_FINAL_1 directly from
src/planners/hardcode_goalcond_nusc.py, verifies CONFIG_DICT, compares the two
configurations, checks the public eval/adversarial configs, and scans the public
checkout for evidence of a dedicated hyperparameter sweep implementation.

It does not reproduce the paper's 432-trial sweep because the full sweep
implementation/grid is not present in the inspected public release.

Designed for Python 3.6-compatible syntax.
"""

import argparse
import ast
import datetime
import hashlib
import re
import sys
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


def load_yaml(path):
    p = Path(path)
    if not p.is_file():
        return {"_error": "file not found: %s" % p}
    if yaml is None:
        return {"_error": "PyYAML unavailable"}
    try:
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:
        return {"_error": str(exc)}


def extract_literal_assignment(source, name):
    """Safely parse a literal top-level Python assignment by variable name."""
    if source is None:
        return None
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


def config_delta(default_cfg, tuned_cfg):
    if not isinstance(default_cfg, dict) or not isinstance(tuned_cfg, dict):
        return None
    keys = sorted(set(default_cfg.keys()) | set(tuned_cfg.keys()))
    changed = {}
    unchanged = {}
    missing = {}
    for key in keys:
        in_d = key in default_cfg
        in_t = key in tuned_cfg
        if not in_d or not in_t:
            missing[key] = {
                "in_default": in_d,
                "in_tuned": in_t,
            }
            continue
        d = default_cfg[key]
        t = tuned_cfg[key]
        if d == t:
            unchanged[key] = d
        else:
            item = {"default": d, "tuned": t}
            if isinstance(d, (int, float)) and isinstance(t, (int, float)):
                item["delta"] = t - d
                if d != 0:
                    item["percent_change"] = ((t - d) / float(d)) * 100.0
            changed[key] = item
    return {
        "changed": changed,
        "unchanged": unchanged,
        "missing": missing,
        "same_key_set": not bool(missing),
    }


def inspect_planner_source(source):
    source = source or ""
    return {
        "has_default_config": "DEF_CONFIG" in source,
        "has_tuned_config": "TUNED_VAL_FINAL_1" in source,
        "has_config_dict": "CONFIG_DICT" in source,
        "maps_default_key": "'default' : DEF_CONFIG" in source or '"default" : DEF_CONFIG' in source,
        "maps_tuned_key": (
            "'final_tuned_val_1' : TUNED_VAL_FINAL_1" in source
            or '"final_tuned_val_1" : TUNED_VAL_FINAL_1' in source
        ),
        "tuned_comment_generated_validation": (
            "large-scale tuned on generated scenarios from validation set" in source
        ),
        "score_weight_formula_detected": (
            "w = score_wmin + np.arange(len(dists)) * score_wfac" in source
        ),
        "collision_score_formula_detected": (
            "probs = 1.0 + np.tanh(-dists * w)" in source
        ),
        "candidate_speed_grid_detected": (
            "for s1 in np.linspace(sbot, stop, NS)" in source
            and "for s2 in np.linspace(sbot, stop, NS)" in source
        ),
    }


def eval_cfg_to_planner_cfg(cfg):
    if not isinstance(cfg, dict):
        return None
    mapping = {
        "dt": "planner_dt",
        "preddt": "planner_preddt",
        "nsteps": "planner_nsteps",
        "cdistang": "planner_cdistang",
        "xydistmax": "planner_xydistmax",
        "smax": "planner_smax",
        "accmax": "planner_accmax",
        "predsfacs": "planner_predsfacs",
        "predafacs": "planner_predafacs",
        "interacdist": "planner_interacdist",
        "planaccfacs": "planner_planaccfacs",
        "plannspeeds": "planner_plannspeeds",
        "col_plim": "planner_col_plim",
        "score_wmin": "planner_score_wmin",
        "score_wfac": "planner_score_wfac",
    }
    out = {}
    for planner_key, cfg_key in mapping.items():
        if cfg_key in cfg:
            out[planner_key] = cfg[cfg_key]
    return out


def scan_tuning_implementation(repo_root):
    """Look for public code suggestive of a dedicated planner sweep implementation."""
    root = Path(repo_root)
    hits = []
    patterns = [
        re.compile(r"432"),
        re.compile(r"itertools\.product"),
        re.compile(r"GridSearch", re.I),
        re.compile(r"hyperparam.*sweep", re.I),
        re.compile(r"planner.*tuning", re.I),
    ]
    for suffix in ("*.py", "*.cfg", "*.yaml", "*.yml"):
        for path in root.rglob(suffix):
            try:
                text = path.read_text(encoding="utf-8")
            except Exception:
                continue
            matched = []
            for pattern in patterns:
                if pattern.search(text):
                    matched.append(pattern.pattern)
            if matched:
                hits.append({
                    "path": str(path.relative_to(root)),
                    "matched_patterns": matched,
                })
    # Comments/config mentions are evidence that tuning existed, but not a sweep implementation.
    dedicated_candidates = [
        x for x in hits
        if any(token in x["path"].lower() for token in ("tune", "tuning", "search", "sweep", "hyper"))
        and x["path"].endswith(".py")
    ]
    return {
        "all_pattern_hits": hits,
        "dedicated_python_candidates": dedicated_candidates,
        "dedicated_sweep_implementation_identified": bool(dedicated_candidates),
        "interpretation": (
            "A false value means no dedicated tuning/sweep Python file was identified "
            "by these static naming/content patterns; it is not a proof of absence."
        ),
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
    parser.add_argument("--repo-root", default=".", help="Root of a STRIVE checkout.")
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument("--metadata", help="Optional metadata/fitted_configs/planner_tuning.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.repo_root)

    paths = {
        "planner": root / "src/planners/hardcode_goalcond_nusc.py",
        "planner_base": root / "src/planners/planner.py",
        "scenario_generation": root / "src/adv_scenario_gen.py",
        "planner_evaluation": root / "src/eval_planner.py",
        "eval_config": root / "configs/eval_planner.cfg",
        "adv_config": root / "configs/adv_gen_rule_based.cfg",
    }

    planner_src = read_text(paths["planner"])
    default_cfg = extract_literal_assignment(planner_src, "DEF_CONFIG")
    tuned_cfg = extract_literal_assignment(planner_src, "TUNED_VAL_FINAL_1")
    delta = config_delta(default_cfg, tuned_cfg)

    eval_cfg_raw = load_yaml(paths["eval_config"])
    eval_planner_cfg = eval_cfg_to_planner_cfg(eval_cfg_raw)
    adv_cfg = load_yaml(paths["adv_config"])

    release_behavior = inspect_planner_source(planner_src)
    tuning_scan = scan_tuning_implementation(root)

    derived = {}
    if isinstance(default_cfg, dict):
        if isinstance(default_cfg.get("nsteps"), int) and isinstance(default_cfg.get("preddt"), (int, float)):
            derived["default_prediction_horizon_seconds"] = (
                default_cfg["nsteps"] * default_cfg["preddt"]
            )
        if isinstance(default_cfg.get("plannspeeds"), int):
            derived["default_candidate_speed_profiles_per_accel_factor_per_lane"] = (
                default_cfg["plannspeeds"] ** 2
            )
    if isinstance(tuned_cfg, dict):
        if isinstance(tuned_cfg.get("nsteps"), int) and isinstance(tuned_cfg.get("preddt"), (int, float)):
            derived["tuned_prediction_horizon_seconds"] = (
                tuned_cfg["nsteps"] * tuned_cfg["preddt"]
            )
        if isinstance(tuned_cfg.get("plannspeeds"), int):
            derived["tuned_candidate_speed_profiles_per_accel_factor_per_lane"] = (
                tuned_cfg["plannspeeds"] ** 2
            )

    checks = {
        "required_files_exist": all(p.is_file() for p in paths.values()),
        "default_config_extracted": isinstance(default_cfg, dict),
        "tuned_config_extracted": isinstance(tuned_cfg, dict),
        "config_dict_mapping_detected": (
            release_behavior["maps_default_key"]
            and release_behavior["maps_tuned_key"]
        ),
        "default_and_tuned_have_same_keys": (
            bool(delta) and delta.get("same_key_set")
        ),
        "expected_changed_parameter_set": (
            bool(delta)
            and set(delta.get("changed", {}).keys())
            == {"smax", "accmax", "score_wmin", "score_wfac"}
        ),
        "eval_config_matches_default_config": (
            isinstance(default_cfg, dict)
            and isinstance(eval_planner_cfg, dict)
            and default_cfg == eval_planner_cfg
        ),
        "adv_config_defaults_to_default_planner": (
            isinstance(adv_cfg, dict) and adv_cfg.get("planner_cfg") == "default"
        ),
        "planner_score_formula_detected": (
            release_behavior["score_weight_formula_detected"]
            and release_behavior["collision_score_formula_detected"]
        ),
    }

    warnings = []
    if not checks["required_files_exist"]:
        warnings.append("one or more required F-01 source/config files are missing")
    if not checks["expected_changed_parameter_set"]:
        warnings.append(
            "default-to-tuned changed parameter set differs from documented public release"
        )
    if not checks["eval_config_matches_default_config"]:
        warnings.append(
            "configs/eval_planner.cfg no longer exactly matches DEF_CONFIG"
        )
    if tuning_scan["dedicated_sweep_implementation_identified"]:
        warnings.append(
            "a possible dedicated tuning implementation was detected; review card statement about sweep-code availability"
        )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "F-01",
        "profiled_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "source_files": {name: file_fact(path) for name, path in paths.items()},
        "extracted_configs": {
            "default": default_cfg,
            "final_tuned_val_1": tuned_cfg,
            "eval_planner_config_as_planner_params": eval_planner_cfg,
            "adv_gen_rule_based_planner_cfg": (
                adv_cfg.get("planner_cfg") if isinstance(adv_cfg, dict) else None
            ),
        },
        "config_delta": delta,
        "derived_properties": derived,
        "release_behavior": release_behavior,
        "tuning_implementation_scan": tuning_scan,
        "paper_context_not_derived_from_repo": {
            "documented_sweep_combinations": 432,
            "initial_regular_scenarios": 800,
            "selection": "lowest collision rate; lowest acceleration as tie-breaker",
            "reported_search_ranges": {
                "p_max": [0.05, 0.2],
                "max_speed_m_per_s": [12.5, 20.0],
                "max_acceleration_m_per_s2": [3.0, 4.5],
            },
            "note": (
                "These values come from the STRIVE paper/supplement and are included "
                "for comparison; this static profiler does not infer them from repository code."
            ),
        },
        "quality_checks": checks,
        "warnings": warnings,
        "measurement_notes": [
            "The public source exposes exactly one named tuned dictionary: final_tuned_val_1.",
            "The public eval_planner.cfg contains DEF_CONFIG values, so tuned evaluation requires changing those planner_* options.",
            "The repository comment says final_tuned_val_1 was large-scale tuned on generated validation scenarios.",
            "The exact mapping of final_tuned_val_1 to an individual Table 3 paper row is not explicitly stated in the inspected source.",
            "The full 432-trial paper sweep is not reproduced by this profiler.",
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
