#!/usr/bin/env python3
"""Static profiler for STRIVE C-01 initialization optimization.

The public STRIVE implementation stores important C-01 settings in both config
and Python call sites. This profiler inspects both so documentation does not
mistakenly assign the global adversarial optimizer settings to initialization.

It also detects the released TgtMatchingLoss behavior in which motion_prior_loss
is computed but tgt_loss.mean() is added to the total loss for the
motion_prior_ext-weighted term.

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
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def file_fact(path):
    p = Path(path)
    return {
        "path": str(p),
        "exists": p.is_file(),
        "sha256": sha256_file(p) if p.is_file() else None,
        "size_bytes": p.stat().st_size if p.is_file() else None,
    }


def compact_ws(text):
    return re.sub(r"\s+", " ", text or "").strip()


def inspect_call_sites(source):
    if not source:
        return []

    # Capture run_init_optim calls across line breaks without trying to fully
    # parse Python expressions. This is intentionally specific to the public
    # STRIVE calling convention.
    calls = []
    pattern = re.compile(r"run_init_optim\s*\((.*?)\)", re.DOTALL)
    for idx, match in enumerate(pattern.finditer(source)):
        body = compact_ws(match.group(1))
        # The public calls place lr after future_vis and num_iters after model/map args.
        # Extract the recognizable literal forms used by the release.
        fact = {"index": idx, "call_text": body}

        if "scene_graph.future_vis, 0.1, loss_weights" in body and ", 75, embed_info" in body:
            fact.update({
                "role": "initial_nuscenes_fit",
                "learning_rate": 0.1,
                "iterations": 75,
            })
        elif "scene_graph.future_vis, lr, loss_weights" in body and ", 100, embed_info" in body:
            fact.update({
                "role": "rule_based_planner_refit",
                "learning_rate_expression": "lr",
                "iterations": 100,
            })
        else:
            fact["role"] = "unclassified"
        calls.append(fact)
    return calls


def inspect_init_optim(source):
    source = source or ""
    return {
        "uses_adam": "optim.Adam(optim_z, lr=lr)" in source,
        "optimizes_only_cur_z_list": "optim_z = [cur_z]" in source,
        "clones_detaches_latent": "cur_z = cur_z.clone().detach()" in source,
        "enables_latent_grad": "cur_z.requires_grad = True" in source,
        "uses_visibility_mask_for_target": "init_traj = model.get_normalizer().unnormalize(init_traj)[traj_vis == 1.0]" in source,
        "uses_visibility_mask_for_prediction": "future_pred = future_pred[traj_vis == 1.0]" in source,
        "decodes_each_iteration": "model.decode_embedding(cur_z" in source,
        "fixed_iteration_loop": "range(num_iters)" in source,
        "returns_latent_trajectory_decoder_output": "return cur_z, init_result_traj, init_decoder_out" in source,
    }


def inspect_loss(source):
    source = source or ""
    prior_calc = "motion_prior_loss = self.motion_prior_loss(z, prior_out)" in source
    reported = "loss_out['motion_prior_ext_loss'] = motion_prior_loss" in source

    # Detect the exact released total-loss expression inside the motion-prior block.
    repeated_target = (
        "self.loss_weights['motion_prior_ext']*tgt_loss.mean()" in source
        or 'self.loss_weights["motion_prior_ext"]*tgt_loss.mean()' in source
    )
    actual_prior = (
        "self.loss_weights['motion_prior_ext']*motion_prior_loss.mean()" in source
        or 'self.loss_weights["motion_prior_ext"]*motion_prior_loss.mean()' in source
    )

    return {
        "motion_prior_loss_computed": prior_calc,
        "motion_prior_loss_reported": reported,
        "motion_prior_weight_multiplies_target_loss_in_total": repeated_target,
        "motion_prior_weight_multiplies_motion_prior_loss_in_total": actual_prior,
        "released_prior_gradient_discrepancy_detected": bool(
            prior_calc and reported and repeated_target and not actual_prior
        ),
    }


def inspect_caller(source):
    source = source or ""
    return {
        "posterior_mean_initialization": "z_init = embed_info_attached['posterior_out'][0].detach()" in source,
        "target_is_future_gt_xy_heading": "init_traj = scene_graph.future_gt[:, :, :4].clone().detach()" in source,
        "rule_based_planner_branch": "planner_name == 'hardcode'" in source,
        "planner_target_replacement": "init_traj[ego_mask] = planner_init" in source,
        "post_init_planner_collision_check": "check_single_veh_coll" in source,
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
    parser.add_argument("--output", help="Optional standalone YAML report.")
    parser.add_argument("--metadata", help="Optional metadata/components/initialization_optimization.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.repo_root)

    paths = {
        "init_optim": root / "src/utils/init_optim.py",
        "loss": root / "src/losses/adv_gen_nusc.py",
        "caller": root / "src/adv_scenario_gen.py",
        "config": root / "configs/adv_gen_rule_based.cfg",
    }

    init_src = read_text(paths["init_optim"])
    loss_src = read_text(paths["loss"])
    caller_src = read_text(paths["caller"])
    cfg = load_yaml(paths["config"])

    calls = inspect_call_sites(caller_src)
    init_facts = inspect_init_optim(init_src)
    loss_facts = inspect_loss(loss_src)
    caller_facts = inspect_caller(caller_src)

    init_weights = {}
    if isinstance(cfg, dict):
        for key in ("init_loss_motion_prior_ext", "init_loss_match_ext", "num_iters", "lr", "planner"):
            if key in cfg:
                init_weights[key] = cfg.get(key)

    first_call = next((x for x in calls if x.get("role") == "initial_nuscenes_fit"), None)
    planner_call = next((x for x in calls if x.get("role") == "rule_based_planner_refit"), None)

    effective_match_coefficient = None
    if loss_facts["released_prior_gradient_discrepancy_detected"]:
        match_w = init_weights.get("init_loss_match_ext")
        prior_w = init_weights.get("init_loss_motion_prior_ext")
        if isinstance(match_w, (int, float)) and isinstance(prior_w, (int, float)):
            effective_match_coefficient = float(match_w) + float(prior_w)

    checks = {
        "required_files_exist": all(path.is_file() for path in paths.values()),
        "first_call_75_iters_lr_0_1": bool(
            first_call
            and first_call.get("iterations") == 75
            and first_call.get("learning_rate") == 0.1
        ),
        "planner_refit_100_iters": bool(planner_call and planner_call.get("iterations") == 100),
        "posterior_mean_initialization": caller_facts["posterior_mean_initialization"],
        "valid_timestep_masking": (
            init_facts["uses_visibility_mask_for_target"]
            and init_facts["uses_visibility_mask_for_prediction"]
        ),
        "latent_only_adam": (
            init_facts["uses_adam"]
            and init_facts["optimizes_only_cur_z_list"]
            and init_facts["enables_latent_grad"]
        ),
        "released_prior_gradient_discrepancy_detected": loss_facts[
            "released_prior_gradient_discrepancy_detected"
        ],
    }

    warnings = []
    if not checks["required_files_exist"]:
        warnings.append("one or more required STRIVE files are missing")
    if not checks["first_call_75_iters_lr_0_1"]:
        warnings.append("initial C-01 call no longer matches the public 75-iteration / 0.1 release behavior")
    if not checks["released_prior_gradient_discrepancy_detected"]:
        warnings.append(
            "TgtMatchingLoss no longer matches the documented public-release prior-term behavior; review C-01 card"
        )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "C-01",
        "profiled_at_utc": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "source_files": {name: file_fact(path) for name, path in paths.items()},
        "config": init_weights,
        "call_sites": calls,
        "source_facts": {
            "run_init_optim": init_facts,
            "caller": caller_facts,
        },
        "loss_behavior": {
            **loss_facts,
            "effective_matching_coefficient_from_release_config": effective_match_coefficient,
            "note": (
                "When the discrepancy is detected, motion_prior_loss is calculated/reported "
                "but the prior-weighted total-loss term reuses target matching loss."
            ),
        },
        "quality_checks": checks,
        "warnings": warnings,
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
