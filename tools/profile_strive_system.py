#!/usr/bin/env python3
"""Static system profiler for STRIVE S-01.

This profiler checks the public STRIVE checkout and, when present, the complete
documentation/card set produced for S-01 and its subordinate cards.

It does not run model training or scenario optimization. It is intended to:
  * hash core sources/configs;
  * verify key public-release invariants;
  * inspect pinned dependencies;
  * verify expected card/metadata files;
  * detect common documentation/source drift.

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


SOURCE_PATHS = [
    "README.md",
    "LICENSE",
    "requirements.txt",
    "src/datasets/nuscenes_dataset.py",
    "src/models/traffic_model.py",
    "src/losses/traffic_model.py",
    "src/losses/adv_gen_nusc.py",
    "src/utils/init_optim.py",
    "src/utils/adv_gen_optim.py",
    "src/utils/sol_optim.py",
    "src/utils/scenario_gen.py",
    "src/adv_scenario_gen.py",
    "src/eval_adv_gen.py",
    "src/cluster_scenarios.py",
    "src/eval_planner.py",
    "src/planners/hardcode_goalcond_nusc.py",
]

CONFIG_PATHS = [
    "configs/train_traffic.cfg",
    "configs/test_traffic.cfg",
    "configs/adv_gen_rule_based.cfg",
    "configs/adv_gen_replay.cfg",
    "configs/eval_planner.cfg",
]

CARD_PATHS = [
    "docs/cards/system/SYSTEM_CARD_STRIVE.md",
    "docs/cards/data/DATA_CARD_NUSCENES_STRIVE.md",
    "docs/cards/models/MODEL_CARD_TRAFFIC.md",
    "docs/cards/models/MODEL_CARD_RULE_BASED_PLANNER_STRIVE.md",
    "docs/cards/components/COMPONENT_CARD_INITIALIZATION_OPTIMIZATION.md",
    "docs/cards/components/COMPONENT_CARD_ADVERSARIAL_OPTIMIZATION.md",
    "docs/cards/components/COMPONENT_CARD_SOLUTION_OPTIMIZATION.md",
    "docs/cards/data/DATA_CARD_GENERATED_SCENARIOS_STRIVE.md",
    "docs/cards/models/MODEL_CARD_CLUSTERING_STRIVE.md",
    "docs/cards/models/MODEL_CARD_ACCIDENT_CLASSIFIER_STRIVE.md",
    "docs/cards/fitted_configs/FITTED_CONFIG_CARD_PLANNER_TUNING_STRIVE.md",
]

METADATA_PATHS = [
    "metadata/system/strive_system.yaml",
    "metadata/data/nuscenes_strive.yaml",
    "metadata/models/traffic_model.yaml",
    "metadata/models/rule_based_planner.yaml",
    "metadata/components/initialization_optimization.yaml",
    "metadata/components/adversarial_optimization.yaml",
    "metadata/components/solution_optimization.yaml",
    "metadata/data/generated_scenarios.yaml",
    "metadata/models/clustering.yaml",
    "metadata/models/accident_classifier.yaml",
    "metadata/fitted_configs/planner_tuning.yaml",
]


def sha256_file(path, chunk_size=1024 * 1024):
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def file_fact(root, relative):
    p = Path(root) / relative
    return {
        "path": relative,
        "exists": p.is_file(),
        "size_bytes": p.stat().st_size if p.is_file() else None,
        "sha256": sha256_file(p) if p.is_file() else None,
    }


def read_text(root, relative):
    p = Path(root) / relative
    if not p.is_file():
        return ""
    return p.read_text(encoding="utf-8", errors="replace")


def load_yaml_file(path):
    if yaml is None:
        return {"_error": "PyYAML unavailable"}
    try:
        with Path(path).open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:
        return {"_error": str(exc)}


def inspect_requirements(text):
    entries = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("--find-links"):
            continue
        entries.append(line)

    parsed = {}
    for line in entries:
        if "==" in line:
            name, version = line.split("==", 1)
            parsed[name.strip().lower()] = version.strip()
        else:
            parsed[line.lower()] = None

    return {
        "entries": entries,
        "pinned": parsed,
        "scikit_learn_present": (
            "scikit-learn" in parsed or "sklearn" in parsed
        ),
        "expected_versions": {
            "numpy": parsed.get("numpy"),
            "torch": parsed.get("torch"),
            "torchvision": parsed.get("torchvision"),
            "torchaudio": parsed.get("torchaudio"),
            "torch-geometric": parsed.get("torch-geometric"),
            "nuscenes-devkit": parsed.get("nuscenes-devkit"),
        },
    }


def inspect_release_invariants(root):
    data_src = read_text(root, "src/datasets/nuscenes_dataset.py")
    config_src = read_text(root, "src/utils/config.py")
    model_src = read_text(root, "src/models/traffic_model.py")
    adv_src = read_text(root, "src/adv_scenario_gen.py")
    adv_opt_src = read_text(root, "src/utils/adv_gen_optim.py")
    sol_src = read_text(root, "src/utils/sol_optim.py")
    loss_src = read_text(root, "src/losses/adv_gen_nusc.py")
    cluster_src = read_text(root, "src/cluster_scenarios.py")
    planner_src = read_text(root, "src/planners/hardcode_goalcond_nusc.py")
    readme = read_text(root, "README.md")
    rule_cfg = read_text(root, "configs/adv_gen_rule_based.cfg")
    replay_cfg = read_text(root, "configs/adv_gen_replay.cfg")

    checks = {
        "data_default_past_len_4": (
            "npast=4" in data_src or "past_len" in config_src and "4" in config_src
        ),
        "data_default_future_len_12": (
            "nfuture=12" in data_src or "future_len" in config_src and "12" in config_src
        ),
        "model_default_latent_32": (
            "latent_size=32" in model_src
            or "latent_size" in config_src and "32" in config_src
        ),
        "feasibility_samples_20_include_mean": (
            "model.sample_batched(scene_graph, map_idx, map_env, 20, include_mean=True)"
            in adv_src
        ),
        "feasibility_candidate_velocity_literal_zero": (
            "feasibility_time,\n                                                                                0.0,"
            in adv_src
            or bool(re.search(
                r"determine_feasibility_nusc\(.*?feasibility_time,\s*0\.0,",
                adv_src,
                flags=re.DOTALL,
            ))
        ),
        "adv_parser_default_iterations_300": (
            "default=300" in adv_src and "--num_iters" in adv_src
        ),
        "rule_config_iterations_200": bool(re.search(
            r"(?m)^\s*num_iters:\s*200\s*$", rule_cfg
        )),
        "replay_config_iterations_300": bool(re.search(
            r"(?m)^\s*num_iters:\s*300\s*$", replay_cfg
        )),
        "release_learning_rate_0_05": bool(re.search(
            r"(?m)^\s*lr:\s*0\.05\s*$", rule_cfg
        )),
        "hardcode_actual_planner_rerun": (
            "planner.rollout" in adv_opt_src
            and "adv_use_own_pred=True" in adv_opt_src
        ),
        "solution_collision_buffer_0_5": "veh_coll_buffer=0.5" in sol_src,
        "solution_uses_configured_future_len": "nfuture=future_len" in sol_src,
        "solution_final_decode_default_horizon": bool(re.search(
            r"sol_decoder_out\s*=\s*model\.decode_embedding\("
            r"cur_z,\s*embed_info,\s*scene_graph,\s*map_idx,\s*map_env\)",
            sol_src,
            flags=re.DOTALL,
        )),
        "solution_restores_nonplanner_adv_trajectory": (
            "sol_result_traj[~tgt_mask] = model.get_normalizer().normalize(other_match_traj)"
            in sol_src
        ),
        "tgt_matching_release_discrepancy": (
            "motion_prior_loss = self.motion_prior_loss(z, prior_out)" in loss_src
            and "self.loss_weights['motion_prior_ext']*tgt_loss.mean()" in loss_src
        ),
        "clustering_k10": (
            "--k" in cluster_src and "default=10" in cluster_src
        ),
        "clustering_random_state_0": (
            "KMeans(n_clusters=k, random_state=0)" in cluster_src
        ),
        "planner_tuned_config_present": (
            "TUNED_VAL_FINAL_1" in planner_src
            and "final_tuned_val_1" in planner_src
        ),
        "planner_five_circle_scoring_present": (
            "circles = np.empty((B, NA, 5, 3))" in planner_src
            and "prob = 1.0 - np.product(1.0 - probs)" in planner_src
        ),
        "planner_default_25_speed_profiles_derivable": (
            "'plannspeeds' : 5" in planner_src
            and "for s1 in np.linspace(sbot, stop, NS)" in planner_src
            and "for s2 in np.linspace(sbot, stop, NS)" in planner_src
        ),
        "planner_alt_init_undefined_vehicle_atts_issue_present": (
            "if init_state is not None:" in planner_src
            and "self.create_init_state(init_state, vehicle_atts, self.B, self.batch_mask)" in planner_src
        ),
        "readme_models_scenarios_cc_by_nc_sa_4": (
            "CC-BY-NC-SA-4.0" in readme
        ),
        "readme_code_environment_python36_pytorch19_cuda111": (
            "Python 3.6" in readme
            and "PyTorch 1.9" in readme
            and "CUDA 11.1" in readme
        ),
    }
    return checks


def inspect_metadata_set(root):
    results = {}
    ids = []
    errors = []
    for rel in METADATA_PATHS:
        p = Path(root) / rel
        fact = file_fact(root, rel)
        item = dict(fact)
        if p.is_file():
            data = load_yaml_file(p)
            item["card_id"] = data.get("card_id") if isinstance(data, dict) else None
            item["status"] = data.get("status") if isinstance(data, dict) else None
            if isinstance(data, dict) and data.get("_error"):
                errors.append("%s: %s" % (rel, data["_error"]))
            if item["card_id"]:
                ids.append(item["card_id"])
        results[rel] = item
    return {
        "files": results,
        "card_ids": ids,
        "duplicate_card_ids": sorted(
            set(x for x in ids if ids.count(x) > 1)
        ),
        "errors": errors,
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
    parser.add_argument("--repo-root", default=".", help="Root of STRIVE plus documentation set.")
    parser.add_argument("--output", help="Optional standalone YAML profile.")
    parser.add_argument("--metadata", help="Optional metadata/system/strive_system.yaml to update.")
    return parser.parse_args()


def main():
    args = parse_args()
    root = Path(args.repo_root)

    source_files = {
        rel: file_fact(root, rel)
        for rel in SOURCE_PATHS
    }
    config_files = {
        rel: file_fact(root, rel)
        for rel in CONFIG_PATHS
    }
    documentation_files = {
        rel: file_fact(root, rel)
        for rel in CARD_PATHS
    }
    metadata = inspect_metadata_set(root)

    req = inspect_requirements(read_text(root, "requirements.txt"))
    invariants = inspect_release_invariants(root)

    expected_card_ids = {
        "S-01", "D-01", "M-01", "M-02", "C-01", "C-02",
        "C-03", "D-02", "M-03", "M-04", "F-01",
    }

    present_metadata_ids = set(metadata["card_ids"])

    quality_checks = {
        "all_core_source_files_present": all(
            x["exists"] for x in source_files.values()
        ),
        "all_primary_config_files_present": all(
            x["exists"] for x in config_files.values()
        ),
        "all_documentation_cards_present": all(
            x["exists"] for x in documentation_files.values()
        ),
        "all_metadata_files_present": all(
            x["exists"] for x in metadata["files"].values()
        ),
        "all_expected_metadata_card_ids_present": (
            expected_card_ids.issubset(present_metadata_ids)
        ),
        "no_duplicate_metadata_card_ids": not metadata["duplicate_card_ids"],
        "all_release_invariants_detected": all(invariants.values()),
        "scikit_learn_pinned": req["scikit_learn_present"],
        "code_license_file_present": source_files["LICENSE"]["exists"],
    }

    warnings = []
    if not quality_checks["all_core_source_files_present"]:
        warnings.append("one or more expected STRIVE core source files are missing")
    if not quality_checks["all_primary_config_files_present"]:
        warnings.append("one or more expected primary config files are missing")
    if not quality_checks["all_documentation_cards_present"]:
        warnings.append(
            "the complete S-01 subordinate card set is not present in this checkout"
        )
    if not quality_checks["all_metadata_files_present"]:
        warnings.append(
            "the complete S-01 metadata set is not present in this checkout"
        )
    if metadata["duplicate_card_ids"]:
        warnings.append(
            "duplicate metadata card IDs: %s"
            % ", ".join(metadata["duplicate_card_ids"])
        )
    if not req["scikit_learn_present"]:
        warnings.append(
            "M-03 uses scikit-learn but requirements.txt does not pin scikit-learn"
        )

    missing_invariants = [
        key for key, value in invariants.items() if not value
    ]
    if missing_invariants:
        warnings.append(
            "documented release invariants not detected: %s"
            % ", ".join(missing_invariants)
        )

    profile = {
        "profile_schema_version": "1.0",
        "card_id": "S-01",
        "profiled_at_utc": (
            datetime.datetime.utcnow()
            .replace(microsecond=0)
            .isoformat() + "Z"
        ),
        "repo_root": str(root.resolve()),
        "source_files": source_files,
        "config_files": config_files,
        "documentation_files": documentation_files,
        "metadata_files": metadata,
        "requirements": req,
        "release_invariants": invariants,
        "quality_checks": quality_checks,
        "warnings": warnings,
        "measurement_notes": [
            "This is a static system profiler; it does not train M-01 or run C-01/C-02/C-03.",
            "A missing invariant may indicate source drift or a profiler pattern that needs updating; inspect before concluding behavior changed.",
            "M-02 HardcodeNuscPlanner is an explicit runtime dependency of the hardcode C-02 path and a direct target of F-01 tuning.",
            "The released M-02 rollout(init_state=...) branch references undefined vehicle_atts; standard callers do not use it.",
            "M-04 public-repo classification is cluster-based and is distinct from the paper-level learned binary accident-mode classifier.",
            "Paper-level planner-tuning results and the 432-combination sweep are not dynamically reproduced by this profiler.",
            "Generated scenario/model licensing is distinct from the MIT source-code license.",
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
