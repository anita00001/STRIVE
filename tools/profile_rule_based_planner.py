#!/usr/bin/env python3
"""Static profiler for STRIVE M-02 HardcodeNuscPlanner.

The profiler:
  * extracts DEF_CONFIG and TUNED_VAL_FINAL_1 safely from source;
  * compares default/tuned parameters;
  * checks lane processing, candidate generation, collision scoring, and selection;
  * checks C-01/C-02 integration and planner evaluation;
  * detects the released rollout(init_state=...) undefined vehicle_atts issue.

It does not execute planner rollouts.

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


def config_delta(default_cfg, tuned_cfg):
    if not isinstance(default_cfg, dict) or not isinstance(tuned_cfg, dict):
        return None
    changed = {}
    unchanged = {}
    missing = {}
    keys = sorted(set(default_cfg) | set(tuned_cfg))
    for key in keys:
        if key not in default_cfg or key not in tuned_cfg:
            missing[key] = {
                "in_default": key in default_cfg,
                "in_tuned": key in tuned_cfg,
            }
            continue
        d = default_cfg[key]
        t = tuned_cfg[key]
        if d == t:
            unchanged[key] = d
        else:
            row = {"default": d, "tuned": t}
            if isinstance(d, (int, float)) and isinstance(t, (int, float)):
                row["delta"] = t - d
            changed[key] = row
    return {
        "changed": changed,
        "unchanged": unchanged,
        "missing": missing,
        "same_key_set": not bool(missing),
    }


def inspect_planner_source(source):
    return {
        "class_present": "class HardcodeNuscPlanner(PlannerNusc)" in source,
        "default_ego_idx_zero": "self.ego_idx = 0" in source,
        "state_conv_heading_atan2": "h = np.arctan2(hsin, hcos)" in source,
        "lane_ds_0_4": "lane_ds = 0.4" in source,
        "lane_sig_3_5": "lane_sig = 3.5" in source,
        "sbuffer_4_0": "sbuffer = 4.0" in source,
        "constant_heading_fallback": "constant_heading_spline" in source,
        "ego_uses_first_spline": "spline = obj['splines'][0]" in source,
        "two_stage_speed_grid": (
            "for s1 in np.linspace(sbot, stop, NS)" in source
            and "for s2 in np.linspace(sbot, stop, NS)" in source
        ),
        "other_prediction_speed_accel_product": (
            "for sfac in predsfacs for afac in predafacs" in source
        ),
        "five_circle_boxes": "circles = np.empty((B, NA, 5, 3))" in source,
        "min_circle_separation": "dist = np.amin(dist, axis=(2, 3, 4))" in source,
        "score_weight_formula": (
            "w = score_wmin + np.arange(len(dists)) * score_wfac" in source
        ),
        "score_formula": "probs = 1.0 + np.tanh(-dists * w)" in source,
        "overlap_sets_one": "probs[dists < 0] = 1.0" in source,
        "trajectory_score_product": (
            "prob = 1.0 - np.product(1.0 - probs)" in source
        ),
        "threshold_acceptance": (
            "all_probs[i] < col_plim" in source
        ),
        "fallback_min_score": "chosen_ix = np.argmin(all_probs)" in source,
        "progress_max_distance": "distix = np.argmax(dists)" in source,
        "stop_min_distance": "distix = np.argmin(dists)" in source,
        "output_interpolation": "plan_interp = interp1d(" in source,
        "alternate_init_branch_present": "if init_state is not None:" in source,
        "alternate_init_undefined_vehicle_atts": (
            "self.create_init_state(init_state, vehicle_atts, self.B, self.batch_mask)" in source
        ),
    }


def inspect_adv_integration(source):
    return {
        "imports_hardcode_planner": (
            "from planners.hardcode_goalcond_nusc import HardcodeNuscPlanner, CONFIG_DICT" in source
        ),
        "checks_planner_cfg": "assert(planner_cfg in CONFIG_DICT)" in source,
        "constructs_from_config_dict": (
            "PlannerConfig(**CONFIG_DICT[planner_cfg])" in source
        ),
        "c01_initial_planner_rollout": "planner_init = planner.rollout" in source,
        "c01_replaces_ego_target": "init_traj[ego_mask] = planner_init" in source,
        "c01_hardcode_second_fit_100": bool(re.search(
            r"run_init_optim\(.*?100,\s*embed_info",
            source,
            flags=re.DOTALL,
        )),
        "removes_initial_planner_collision": (
            "Planner already caused collision after init, removing from batch" in source
        ),
        "passes_planner_into_c02": "planner=planner" in source,
    }


def inspect_eval_source(source):
    return {
        "constructs_hardcode_planner": "planner = HardcodeNuscPlanner(map_env, plan_cfg)" in source,
        "device_cpu": "device = torch.device('cpu')" in source,
        "adversarial_uses_fut_adv": "non_ego_traj = adv_scene['adv_fut'].numpy()" in source,
        "supports_replay_eval": "if eval_replay_planner:" in source,
        "collision_interp_scale_3": "interp_scale = 3" in source,
        "relative_collision_velocity": "'coll_vel'" in source,
        "mean_acceleration": "'mean_accel'" in source,
        "mean_forward_acceleration": "'mean_accel_fwd'" in source,
        "mean_lateral_acceleration": "'mean_accel_lat'" in source,
        "writes_all_eval_results_csv": "all_eval_results.csv" in source,
    }


def load_yaml(path):
    p = Path(path)
    if not p.is_file():
        return {}
    if yaml is None:
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def eval_cfg_to_planner_cfg(cfg):
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
    for dst, src in mapping.items():
        if src in cfg:
            out[dst] = cfg[src]
    return out


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
    parser.add_argument("--metadata", help="Optional metadata/models/rule_based_planner.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.repo_root)

    paths = {
        "planner": root / "src/planners/hardcode_goalcond_nusc.py",
        "planner_base": root / "src/planners/planner.py",
        "scenario_generation": root / "src/adv_scenario_gen.py",
        "planner_evaluation": root / "src/eval_planner.py",
        "adv_config": root / "configs/adv_gen_rule_based.cfg",
        "eval_config": root / "configs/eval_planner.cfg",
    }

    planner_src = read_text(paths["planner"])
    adv_src = read_text(paths["scenario_generation"])
    eval_src = read_text(paths["planner_evaluation"])

    default_cfg = extract_literal_assignment(planner_src, "DEF_CONFIG")
    tuned_cfg = extract_literal_assignment(planner_src, "TUNED_VAL_FINAL_1")
    delta = config_delta(default_cfg, tuned_cfg)

    implementation = inspect_planner_source(planner_src)
    integration = inspect_adv_integration(adv_src)
    evaluation = inspect_eval_source(eval_src)

    adv_cfg = load_yaml(paths["adv_config"])
    eval_cfg = load_yaml(paths["eval_config"])
    eval_planner_cfg = eval_cfg_to_planner_cfg(eval_cfg)

    derived = {}
    if isinstance(default_cfg, dict):
        if isinstance(default_cfg.get("nsteps"), int) and isinstance(default_cfg.get("preddt"), (int, float)):
            derived["prediction_horizon_seconds"] = (
                default_cfg["nsteps"] * default_cfg["preddt"]
            )
        if isinstance(default_cfg.get("dt"), (int, float)) and default_cfg["dt"] > 0:
            derived["planner_update_hz"] = 1.0 / default_cfg["dt"]
        if isinstance(default_cfg.get("plannspeeds"), int):
            derived["ego_profiles_per_acceleration_factor"] = (
                default_cfg["plannspeeds"] ** 2
            )
        if isinstance(default_cfg.get("predsfacs"), list) and isinstance(default_cfg.get("predafacs"), list):
            derived["other_longitudinal_hypotheses_per_lane_spline"] = (
                len(default_cfg["predsfacs"]) * len(default_cfg["predafacs"])
            )

    expected_changed = {"smax", "accmax", "score_wmin", "score_wfac"}

    checks = {
        "required_files_exist": all(p.is_file() for p in paths.values()),
        "default_config_extracted": isinstance(default_cfg, dict),
        "tuned_config_extracted": isinstance(tuned_cfg, dict),
        "default_and_tuned_same_keys": bool(delta) and delta["same_key_set"],
        "expected_changed_parameters": (
            bool(delta) and set(delta["changed"].keys()) == expected_changed
        ),
        "core_planner_class_detected": implementation["class_present"],
        "lane_processing_constants_detected": (
            implementation["lane_ds_0_4"]
            and implementation["lane_sig_3_5"]
            and implementation["sbuffer_4_0"]
        ),
        "five_circle_collision_scoring_detected": (
            implementation["five_circle_boxes"]
            and implementation["min_circle_separation"]
        ),
        "collision_score_pipeline_detected": (
            implementation["score_weight_formula"]
            and implementation["score_formula"]
            and implementation["trajectory_score_product"]
            and implementation["threshold_acceptance"]
        ),
        "selection_logic_detected": (
            implementation["fallback_min_score"]
            and implementation["progress_max_distance"]
            and implementation["stop_min_distance"]
        ),
        "adv_integration_detected": (
            integration["constructs_from_config_dict"]
            and integration["c01_initial_planner_rollout"]
            and integration["passes_planner_into_c02"]
        ),
        "evaluation_integration_detected": (
            evaluation["constructs_hardcode_planner"]
            and evaluation["adversarial_uses_fut_adv"]
        ),
        "adv_config_uses_default_planner_cfg": (
            adv_cfg.get("planner_cfg") == "default"
        ),
        "eval_config_matches_default_cfg": (
            isinstance(default_cfg, dict)
            and eval_planner_cfg == default_cfg
        ),
        "alternate_init_undefined_vehicle_atts_issue_detected": (
            implementation["alternate_init_branch_present"]
            and implementation["alternate_init_undefined_vehicle_atts"]
        ),
    }

    warnings = []
    if not checks["required_files_exist"]:
        warnings.append("one or more expected M-02 source/config files are missing")
    if not checks["expected_changed_parameters"]:
        warnings.append("default/tuned planner delta differs from documented release")
    if not checks["eval_config_matches_default_cfg"]:
        warnings.append("configs/eval_planner.cfg no longer exactly matches DEF_CONFIG")
    if checks["alternate_init_undefined_vehicle_atts_issue_detected"]:
        warnings.append(
            "released rollout(init_state=...) branch references undefined vehicle_atts; "
            "standard callers that reset before rollout do not use this branch"
        )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "M-02",
        "profiled_at_utc": (
            datetime.datetime.utcnow()
            .replace(microsecond=0)
            .isoformat() + "Z"
        ),
        "source_files": {name: file_fact(path) for name, path in paths.items()},
        "extracted_configs": {
            "default": default_cfg,
            "final_tuned_val_1": tuned_cfg,
            "adv_gen_rule_based_planner_cfg": adv_cfg.get("planner_cfg"),
            "eval_planner_as_planner_cfg": eval_planner_cfg,
        },
        "config_delta": delta,
        "derived_properties": derived,
        "implementation_behavior": implementation,
        "integration_behavior": integration,
        "evaluation_behavior": evaluation,
        "quality_checks": checks,
        "warnings": warnings,
        "measurement_notes": [
            "M-02 is rule-based and has no learned checkpoint.",
            "Default prediction horizon is nsteps*preddt = 5 seconds.",
            "Default ego longitudinal candidate count is plannspeeds^2 = 25 per acceleration factor.",
            "Planner collision scoring uses a five-circle approximation and a heuristic trajectory score, not a calibrated probability.",
            "The rule-based planner is rerun during STRIVE hardcode adversarial generation.",
            "The optional rollout(init_state=...) branch is unsafe in the released code because vehicle_atts is undefined in scope.",
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
