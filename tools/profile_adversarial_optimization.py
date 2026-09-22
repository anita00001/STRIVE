#!/usr/bin/env python3
"""Static profiler for STRIVE C-02 adversarial optimization.

This tool inspects the public STRIVE source/configuration to recover the release
behavior of adversarial optimization without running a planner or neural model.

It validates:
  * optimizer settings and adversarial weights;
  * rule-based versus replay planner behavior;
  * latent gradient separation;
  * collision interpolation/buffer settings;
  * feasibility settings and the released feasibility_vel call-site discrepancy;
  * final success criterion and scenario-result partitions.

Designed for Python 3.6-compatible syntax.
"""

import argparse
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


def file_fact(path):
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.is_file(),
        "size_bytes": p.stat().st_size if p.is_file() else None,
        "sha256": sha256_file(p) if p.is_file() else None,
    }


def has_all(source, strings):
    source = source or ""
    return all(s in source for s in strings)


def inspect_optimizer(source):
    source = source or ""
    return {
        "separates_target_and_other_latents": has_all(source, [
            "tgt_z = cur_z[ego_mask].clone().detach()",
            "other_z_all = cur_z[~ego_mask].clone().detach()",
        ]),
        "target_latent_requires_grad": "tgt_z.requires_grad = True" in source,
        "other_latents_require_grad": "other_z_all.requires_grad = True" in source,
        "adam_joint_optimizer": "optim.Adam(optim_z, lr=lr)" in source,
        "target_loss_detaches_other_latents": (
            "collate_tgt_other_z(scene_graph, tgt_z, other_z_all.clone().detach())" in source
        ),
        "adversarial_loss_detaches_target_latents": (
            "collate_tgt_other_z(scene_graph, tgt_z.clone().detach(), other_z_all)" in source
        ),
        "fixed_iteration_loop": "range(num_iters)" in source,
        "rule_based_closed_loop": "Operating in closed-loop for adv gen optimization" in source,
        "rule_based_planner_rerun_in_loop": "planner.rollout(cur_agt_pred" in source,
        "rule_based_internal_target_for_adv_loss": (
            "tgt_traj = planner_fut if not adv_use_own_pred else other_decoder_out['future_pred'][ego_mask]" in source
        ),
        "final_rule_based_planner_replacement": (
            "final_result_traj[ego_inds, torch.zeros_like(ego_inds)] = planner_fut" in source
        ),
        "final_loss_return_mins": "return_mins=True" in source,
        "veh_collision_buffer_default": 0.1 if "veh_coll_buffer=0.1" in source else None,
    }


def inspect_loss(source):
    source = source or ""
    return {
        "crash_softmin": "nn.functional.softmin" in source,
        "crash_distance_squared": "dist_traj = dist_traj.view(-1)**2" in source,
        "motion_prior": "self.motion_prior_loss(z, prior_out)" in source,
        "attacker_prior_reweighting": "loss_motion_prior_atk" in source,
        "attacker_init_reweighting": "loss_init_z_atk" in source,
        "trajectory_interpolation_scale_3": "interp_traj(future_pred, scale_factor=3)" in source,
        "planner_collision_reweighting": "ego_coll_weight[~self.ego_mask] = prior_reweight" in source,
        "final_iou_collision_threshold_0_02": "VEH_COLL_THRESH = 0.02" in source,
        "single_vehicle_collision_uses_polygon_iou": (
            "ai_poly.intersection(aj_poly).area / ai_poly.union(aj_poly).area" in source
        ),
        "tgt_matching_prior_discrepancy": (
            "motion_prior_loss = self.motion_prior_loss(z, prior_out)" in source
            and "self.loss_weights['motion_prior_ext']*tgt_loss.mean()" in source
        ),
    }


def inspect_caller(source):
    source = source or ""
    feasibility_call_uses_zero = bool(re.search(
        r"determine_feasibility_nusc\s*\(\s*sample_pred\['future_pred'\].*?"
        r"feasibility_thresh\s*,\s*feasibility_time\s*,\s*0\.0\s*,",
        source,
        flags=re.DOTALL,
    ))
    return {
        "prior_sample_count_20": "model.sample_batched(scene_graph, map_idx, map_env, 20, include_mean=True)" in source,
        "feasibility_candidate_velocity_argument_zero": feasibility_call_uses_zero,
        "ego_velocity_uses_feasibility_vel": "if max_vel < feasibility_vel" in source,
        "starts_adv_from_z_init": "cur_z = z_init.clone().detach()" in source,
        "success_function_called": "compute_adv_gen_success" in source,
        "only_successes_enter_solution": "sol_graph_list = [batch_graph_list[b] for b in range(B) if adv_succeeded[b]]" in source,
        "result_partitions_present": all(
            x in source for x in ["'adv_failed'", "'sol_failed'", "'adv_sol_success'"]
        ),
    }


def inspect_success(source):
    source = source or ""
    return {
        "uses_check_single_veh_coll": "check_single_veh_coll" in source,
        "tests_selected_attacker_only": "attack_coll = planner_coll_all[attack_agt-1]" in source,
        "returns_boolean_attack_collision": "adv_success = bool(attack_coll)" in source,
        "actual_planner_trajectory_documented": "true planner" in source.lower(),
    }


def selected_config(cfg):
    if not isinstance(cfg, dict):
        return cfg
    keys = [
        "data_version", "split", "val_size", "seq_interval", "batch_size",
        "planner", "planner_cfg", "feasibility_check_sep", "num_iters", "lr",
        "loss_coll_veh", "loss_coll_veh_plan", "loss_coll_env",
        "loss_init_z", "loss_init_z_atk",
        "loss_motion_prior", "loss_motion_prior_atk",
        "loss_motion_prior_ext", "loss_match_ext", "loss_adv_crash",
    ]
    return {k: cfg.get(k) for k in keys if k in cfg}


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
    parser.add_argument("--metadata", help="Optional metadata/components/adversarial_optimization.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.repo_root)

    paths = {
        "optimizer": root / "src/utils/adv_gen_optim.py",
        "losses": root / "src/losses/adv_gen_nusc.py",
        "caller": root / "src/adv_scenario_gen.py",
        "scenario_utils": root / "src/utils/scenario_gen.py",
        "rule_based_config": root / "configs/adv_gen_rule_based.cfg",
        "replay_config": root / "configs/adv_gen_replay.cfg",
    }

    optimizer_src = read_text(paths["optimizer"])
    loss_src = read_text(paths["losses"])
    caller_src = read_text(paths["caller"])

    rule_cfg = load_yaml(paths["rule_based_config"])
    replay_cfg = load_yaml(paths["replay_config"])

    optimizer_behavior = inspect_optimizer(optimizer_src)
    loss_behavior = inspect_loss(loss_src)
    caller_behavior = inspect_caller(caller_src)
    success_behavior = inspect_success(optimizer_src)

    checks = {
        "required_files_exist": all(p.is_file() for p in paths.values()),
        "rule_based_200_iters_lr_0_05": (
            isinstance(rule_cfg, dict)
            and rule_cfg.get("num_iters") == 200
            and rule_cfg.get("lr") == 0.05
        ),
        "replay_300_iters_lr_0_05": (
            isinstance(replay_cfg, dict)
            and replay_cfg.get("num_iters") == 300
            and replay_cfg.get("lr") == 0.05
        ),
        "latent_gradient_separation_detected": (
            optimizer_behavior["target_loss_detaches_other_latents"]
            and optimizer_behavior["adversarial_loss_detaches_target_latents"]
        ),
        "rule_based_closed_loop_detected": optimizer_behavior["rule_based_closed_loop"],
        "final_selected_attacker_success_check_detected": (
            success_behavior["uses_check_single_veh_coll"]
            and success_behavior["tests_selected_attacker_only"]
            and success_behavior["returns_boolean_attack_collision"]
        ),
        "candidate_velocity_argument_zero_detected": caller_behavior[
            "feasibility_candidate_velocity_argument_zero"
        ],
        "result_partitions_detected": caller_behavior["result_partitions_present"],
        "tgt_matching_prior_discrepancy_detected": loss_behavior[
            "tgt_matching_prior_discrepancy"
        ],
    }

    warnings = []
    if not checks["required_files_exist"]:
        warnings.append("one or more required C-02 files are missing")
    if not checks["rule_based_200_iters_lr_0_05"]:
        warnings.append("rule-based config differs from documented public-release optimizer settings")
    if not checks["candidate_velocity_argument_zero_detected"]:
        warnings.append(
            "released feasibility call no longer appears to pass 0.0 as candidate-agent velocity threshold; review card"
        )
    if not checks["tgt_matching_prior_discrepancy_detected"]:
        warnings.append(
            "TgtMatchingLoss no longer matches the public release behavior inherited by C-02; review card"
        )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "C-02",
        "profiled_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "source_files": {name: file_fact(path) for name, path in paths.items()},
        "rule_based_config": selected_config(rule_cfg),
        "replay_config": selected_config(replay_cfg),
        "optimizer_behavior": optimizer_behavior,
        "loss_behavior": loss_behavior,
        "feasibility_behavior": {
            **caller_behavior,
            "parser_documented_feasibility_vel_default": 0.5,
            "released_candidate_agent_velocity_argument": 0.0 if caller_behavior[
                "feasibility_candidate_velocity_argument_zero"
            ] else None,
        },
        "success_behavior": success_behavior,
        "quality_checks": checks,
        "warnings": warnings,
        "measurement_notes": [
            "This is a static release profiler; it does not run the neural model or planner.",
            "Dynamic success rate, runtime, and plausibility metrics require executing STRIVE on data.",
            "The final success criterion uses the selected attacker and the actual final planner trajectory.",
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
