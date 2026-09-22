#!/usr/bin/env python3
"""Static profiler for STRIVE C-03 solution optimization.

This profiler inspects the public STRIVE source/configs without running the
neural model. It verifies release-specific solution behavior, including:

  * target/planner latent initialization from the M-01 prior mean;
  * non-planner initialization from C-02 adversarial latents;
  * target/non-planner gradient isolation;
  * 16-step target optimization versus 12-step final decode;
  * 0.5 m collision buffer and interpolation;
  * final success checks;
  * result partitioning and serialized solution fields;
  * inherited TgtMatchingLoss prior-term behavior.

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


def inspect_solution_optimizer(source):
    source = source or ""
    return {
        "target_initialized_from_prior_mean": "tgt_z = tgt_prior_distrib[0]" in source,
        "target_not_initialized_directly_from_cur_z": "tgt_z = cur_z[tgt_mask]" not in source,
        "other_initialized_from_cur_z": "other_z_all = cur_z[~tgt_mask]" in source,
        "adam_joint_optimizer": "optim.Adam(optim_z, lr=lr)" in source,
        "target_loss_detaches_other_latents": (
            "collate_tgt_other_z(scene_graph, tgt_z, other_z_all.detach())" in source
        ),
        "other_match_loss_detaches_target_latent": (
            "collate_tgt_other_z(scene_graph, tgt_z.detach(), other_z_all)" in source
        ),
        "target_decode_uses_future_len": "nfuture=future_len" in source,
        "other_match_decode_uses_default_horizon": bool(re.search(
            r"match_decoder_out\s*=\s*model\.decode_embedding\("
            r"match_loss_input_z,\s*embed_info,\s*scene_graph,\s*map_idx,\s*map_env\)",
            source,
            flags=re.DOTALL,
        )),
        "final_decode_uses_default_horizon": bool(re.search(
            r"sol_decoder_out\s*=\s*model\.decode_embedding\("
            r"cur_z,\s*embed_info,\s*scene_graph,\s*map_idx,\s*map_env\)",
            source,
            flags=re.DOTALL,
        )),
        "returned_other_trajectories_restored_from_adversarial": (
            "sol_result_traj[~tgt_mask] = model.get_normalizer().normalize(other_match_traj)" in source
        ),
        "single_target_collision_index_zero": "single_veh_idx=0" in source,
        "vehicle_collision_buffer_m": 0.5 if "veh_coll_buffer=0.5" in source else None,
        "fixed_iteration_count": "num_optim_iter = num_iters" in source and "range(num_optim_iter)" in source,
    }


def inspect_loss(source):
    source = source or ""
    return {
        "avoid_collision_interpolation_scale_3": "interp_traj(future_pred, scale_factor=3)" in source,
        "motion_prior_loss_supported": "self.motion_prior_loss(z, prior_out)" in source,
        "init_z_loss_supported": "torch.sum((self.init_z - z)**2" in source,
        "vehicle_iou_threshold_0_02": "VEH_COLL_THRESH = 0.02" in source,
        "target_matching_prior_discrepancy": (
            "motion_prior_loss = self.motion_prior_loss(z, prior_out)" in source
            and "self.loss_weights['motion_prior_ext']*tgt_loss.mean()" in source
        ),
    }


def inspect_success(source):
    source = source or ""
    return {
        "uses_single_vehicle_collision_checker": "check_single_veh_coll" in source,
        "fails_on_any_other_agent_collision": "planner_coll_others = np.sum(planner_coll_all) > 0" in source,
        "map_collision_default_true": "use_map_coll=True" in source,
        "environment_check_ego_only": "ego_only=True" in source,
        "combines_vehicle_or_environment_failure": "sol_impossible = sol_impossible or fin_coll_env[0].item()" in source,
        "returns_negated_impossible": "return not sol_impossible" in source,
    }


def inspect_caller(source):
    source = source or ""
    return {
        "only_adv_successes_enter_solution": (
            "sol_graph_list = [batch_graph_list[b] for b in range(B) if adv_succeeded[b]]" in source
        ),
        "passes_shared_lr_num_iters": bool(re.search(
            r"run_find_solution_optim\(.*?sol_future_len,\s*"
            r"lr,\s*loss_weights,.*?num_iters,",
            source,
            flags=re.DOTALL,
        )),
        "success_called_on_returned_solution": "compute_sol_success(sol_result_traj" in source,
        "partitions_present": all(
            x in source for x in ["'adv_failed'", "'sol_failed'", "'adv_sol_success'"]
        ),
        "serializes_fut_sol": "out_sol_traj" in source and "prepare_output_dict" in source,
        "serializes_z_sol": "out_sol_z" in source and "prepare_output_dict" in source,
    }


def select_config(cfg):
    if not isinstance(cfg, dict):
        return cfg
    keys = [
        "planner", "num_iters", "lr", "sol_future_len",
        "sol_loss_motion_prior", "sol_loss_coll_veh",
        "sol_loss_coll_env", "sol_loss_init_z",
        "sol_loss_motion_prior_ext", "sol_loss_match_ext",
    ]
    out = {k: cfg.get(k) for k in keys if k in cfg}
    if "sol_loss_init_z" not in out:
        out["sol_loss_init_z"] = 0.0
        out["sol_loss_init_z_source"] = "parser default (not overridden by config)"
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
    parser.add_argument("--metadata", help="Optional metadata/components/solution_optimization.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.repo_root)

    paths = {
        "optimizer": root / "src/utils/sol_optim.py",
        "losses": root / "src/losses/adv_gen_nusc.py",
        "caller": root / "src/adv_scenario_gen.py",
        "rule_based_config": root / "configs/adv_gen_rule_based.cfg",
        "replay_config": root / "configs/adv_gen_replay.cfg",
    }

    optimizer_src = read_text(paths["optimizer"])
    loss_src = read_text(paths["losses"])
    caller_src = read_text(paths["caller"])
    rule_cfg = load_yaml(paths["rule_based_config"])
    replay_cfg = load_yaml(paths["replay_config"])

    optimizer_behavior = inspect_solution_optimizer(optimizer_src)
    loss_behavior = inspect_loss(loss_src)
    success_behavior = inspect_success(optimizer_src)
    caller_behavior = inspect_caller(caller_src)

    rule_selected = select_config(rule_cfg)
    replay_selected = select_config(replay_cfg)

    checks = {
        "required_files_exist": all(p.is_file() for p in paths.values()),
        "target_prior_mean_initialization_detected": optimizer_behavior[
            "target_initialized_from_prior_mean"
        ],
        "other_adv_latent_initialization_detected": optimizer_behavior[
            "other_initialized_from_cur_z"
        ],
        "gradient_isolation_detected": (
            optimizer_behavior["target_loss_detaches_other_latents"]
            and optimizer_behavior["other_match_loss_detaches_target_latent"]
        ),
        "solution_16_step_config_detected": (
            isinstance(rule_cfg, dict) and rule_cfg.get("sol_future_len") == 16
        ),
        "final_default_horizon_decode_detected": optimizer_behavior[
            "final_decode_uses_default_horizon"
        ],
        "non_planner_restore_detected": optimizer_behavior[
            "returned_other_trajectories_restored_from_adversarial"
        ],
        "collision_buffer_0_5_detected": optimizer_behavior[
            "vehicle_collision_buffer_m"
        ] == 0.5,
        "success_combines_vehicle_and_environment": (
            success_behavior["fails_on_any_other_agent_collision"]
            and success_behavior["environment_check_ego_only"]
            and success_behavior["combines_vehicle_or_environment_failure"]
        ),
        "only_adv_successes_enter_solution": caller_behavior[
            "only_adv_successes_enter_solution"
        ],
        "result_partitions_detected": caller_behavior["partitions_present"],
        "tgt_matching_prior_discrepancy_detected": loss_behavior[
            "target_matching_prior_discrepancy"
        ],
    }

    warnings = []
    if not checks["required_files_exist"]:
        warnings.append("one or more required C-03 files are missing")
    if not checks["target_prior_mean_initialization_detected"]:
        warnings.append("target/planner latent initialization no longer matches documented prior-mean release behavior")
    if not checks["final_default_horizon_decode_detected"]:
        warnings.append("final C-03 decode appears to specify a horizon; review documented 16-step vs 12-step behavior")
    if not checks["non_planner_restore_detected"]:
        warnings.append("returned non-planner adversarial trajectory restoration not detected")
    if not checks["tgt_matching_prior_discrepancy_detected"]:
        warnings.append("TgtMatchingLoss behavior changed from public release; review C-03 matching documentation")

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "C-03",
        "profiled_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "source_files": {name: file_fact(path) for name, path in paths.items()},
        "rule_based_config": rule_selected,
        "replay_config": replay_selected,
        "optimizer_behavior": optimizer_behavior,
        "loss_behavior": loss_behavior,
        "horizon_behavior": {
            "configured_solution_target_steps": rule_selected.get("sol_future_len") if isinstance(rule_selected, dict) else None,
            "m01_default_steps": 12,
            "target_decode_uses_solution_horizon": optimizer_behavior["target_decode_uses_future_len"],
            "other_match_decode_uses_default_horizon": optimizer_behavior["other_match_decode_uses_default_horizon"],
            "final_decode_uses_default_horizon": optimizer_behavior["final_decode_uses_default_horizon"],
            "returned_non_planner_trajectories_restored": optimizer_behavior[
                "returned_other_trajectories_restored_from_adversarial"
            ],
        },
        "success_behavior": success_behavior,
        "caller_behavior": caller_behavior,
        "quality_checks": checks,
        "warnings": warnings,
        "measurement_notes": [
            "This is a static profiler; it does not execute M-01 or measure solution success rate.",
            "C-03 target optimization uses the configured 16-step horizon, while the final returned decode uses M-01's default horizon.",
            "Failure of C-03 does not prove that no collision-free real-world or model-space solution exists.",
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
