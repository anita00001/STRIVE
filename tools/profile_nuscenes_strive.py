"""
Profile the STRIVE-specific nuScenes dataset representation.

This script uses STRIVE's own NuScenesDataset implementation rather than
reimplementing its preprocessing.

It reports:

    - scene counts
    - dataset sample counts
    - compiled non-ego car/truck records
    - agent participations across dataset samples
    - mean/median agents per sample
    - Boston/Singapore distributions
    - incomplete past-history frequency

Run from the STRIVE repository root.

Repository-default mode:

    python tools/profile_nuscenes_strive.py \
        --data_dir ./data/nuscenes \
        --data_version trainval

Prediction-challenge mode:

    python tools/profile_nuscenes_strive.py \
        --data_dir ./data/nuscenes \
        --data_version trainval \
        --use_challenge_splits
"""

import argparse
import json
import os
import sys
from collections import Counter

import numpy as np
import torch
from tqdm import tqdm


# ---------------------------------------------------------------------
# Import STRIVE source
# ---------------------------------------------------------------------

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


from nuscenes.nuscenes import NuScenes

from datasets.map_env import NuScenesMapEnv
from datasets.nuscenes_dataset import NuScenesDataset


# ---------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Profile STRIVE's nuScenes-derived dataset."
    )

    parser.add_argument(
        "--data_dir",
        type=str,
        default="./data/nuscenes",
        help="Root STRIVE nuScenes directory.",
    )

    parser.add_argument(
        "--data_version",
        type=str,
        default="trainval",
        choices=["trainval", "mini"],
        help="nuScenes version.",
    )

    parser.add_argument(
        "--use_challenge_splits",
        action="store_true",
        help="Use STRIVE's nuScenes prediction-challenge split mode.",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=(
            "Optional output JSON path. If omitted, a mode-specific path "
            "under metadata/data/profile_runs is used."
        ),
    )

    return parser.parse_args()


# ---------------------------------------------------------------------
# Dataset construction
# ---------------------------------------------------------------------

def build_dataset(split, args, nusc_obj, map_env):
    return NuScenesDataset(
        data_path=os.path.join(args.data_dir, args.data_version),
        map_env=map_env,
        version=args.data_version,
        split=split,
        categories=["car", "truck"],
        npast=4,
        nfuture=12,
        nusc=nusc_obj,
        noise_std=0.0,
        use_challenge_splits=args.use_challenge_splits,
        reduce_cats=False,
    )


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def map_to_location(map_name):
    """
    Convert nuScenes map name to high-level geographic location.
    """

    if map_name.startswith("boston"):
        return "Boston"

    if map_name.startswith("singapore"):
        return "Singapore"

    return map_name


def decode_categories(sem, dataset):
    """
    Decode STRIVE one-hot semantic vectors into category names.

    sem shape:
        N_agents x N_categories
    """

    indices = torch.argmax(sem, dim=1).cpu().tolist()
    return [dataset.categories[idx] for idx in indices]


def count_compiled_non_ego_agents(dataset):
    """
    Count non-ego agent records stored in dataset.data.

    An agent appearing in several temporal samples is counted once here
    for its compiled scene record.
    """

    counts = Counter()

    for scene_name, scene_data in dataset.data.items():
        for agent_name, agent_data in scene_data.items():

            if agent_name == "ego":
                continue

            category = agent_data["k"]
            counts[category] += 1

    return dict(counts)


def count_scene_locations(dataset):
    """
    Count source scenes by geographic location.
    """

    counts = Counter()

    for scene_name in dataset.scenes:
        map_name, _ = dataset.scene2map[scene_name]
        location = map_to_location(map_name)
        counts[location] += 1

    return dict(counts)


def count_sample_locations(dataset):
    """
    Count dataset samples by geographic location.

    Works for both:
        (scene_name, start_idx)

    and:
        (scene_name, start_idx, instance_token)
    """

    counts = Counter()

    for seq_info in dataset.seq_map:

        scene_name = seq_info[0]

        map_name, _ = dataset.scene2map[scene_name]
        location = map_to_location(map_name)

        counts[location] += 1

    return dict(counts)


# ---------------------------------------------------------------------
# Main sample-level profiling
# ---------------------------------------------------------------------

def profile_samples(dataset):
    """
    Iterate through the dataset exactly through NuScenesDataset.__getitem__.

    This captures the actual scene graph presented to the model.
    """

    agents_per_sample = []

    all_category_participations = Counter()
    non_ego_category_participations = Counter()

    total_agent_participations = 0
    total_non_ego_participations = 0

    incomplete_history_agents = 0
    incomplete_history_non_ego_agents = 0

    missing_past_timesteps = 0
    total_past_timesteps = 0

    missing_past_timesteps_non_ego = 0
    total_past_timesteps_non_ego = 0

    samples_with_any_incomplete_history = 0

    for idx in tqdm(
        range(len(dataset)),
        desc=f"Profiling {dataset.split} samples",
    ):

        scene_graph, _ = dataset[idx]

        num_agents = scene_graph.past.shape[0]
        agents_per_sample.append(num_agents)

        categories = decode_categories(scene_graph.sem, dataset)

        # -------------------------------------------------------------
        # Determine actual ego-node index.
        #
        # Normal STRIVE mode:
        #     node 0 = ego
        #
        # Challenge mode:
        #     node 0 = prediction target
        #     node 1 = ego
        # -------------------------------------------------------------

        if dataset.use_challenge_splits:
            ego_idx = 1
        else:
            ego_idx = 0

        sample_has_incomplete_history = False

        for agent_idx, category in enumerate(categories):

            all_category_participations[category] += 1
            total_agent_participations += 1

            past_vis = scene_graph.past_vis[agent_idx]

            missing_steps = int(
                torch.sum(past_vis <= 0).item()
            )

            num_past_steps = int(past_vis.numel())

            missing_past_timesteps += missing_steps
            total_past_timesteps += num_past_steps

            if missing_steps > 0:
                incomplete_history_agents += 1
                sample_has_incomplete_history = True

            # ---------------------------------------------------------
            # Statistics excluding the actual ego vehicle
            # ---------------------------------------------------------

            if agent_idx != ego_idx:

                non_ego_category_participations[category] += 1
                total_non_ego_participations += 1

                missing_past_timesteps_non_ego += missing_steps
                total_past_timesteps_non_ego += num_past_steps

                if missing_steps > 0:
                    incomplete_history_non_ego_agents += 1

        if sample_has_incomplete_history:
            samples_with_any_incomplete_history += 1

    agents_array = np.asarray(agents_per_sample)

    results = {
        "agents_per_sample": {
            "mean": float(np.mean(agents_array)),
            "median": float(np.median(agents_array)),
            "min": int(np.min(agents_array)),
            "max": int(np.max(agents_array)),
        },

        "agent_participations": {
            "all_agents": {
                "total": int(total_agent_participations),
                "by_category": dict(all_category_participations),
            },

            "excluding_actual_ego": {
                "total": int(total_non_ego_participations),
                "by_category": dict(
                    non_ego_category_participations
                ),
            },
        },

        "incomplete_history": {
            "all_agents": {
                "agents_with_incomplete_past": int(
                    incomplete_history_agents
                ),

                "fraction_agents_with_incomplete_past": (
                    float(incomplete_history_agents)
                    / total_agent_participations
                    if total_agent_participations > 0
                    else None
                ),

                "missing_past_timesteps": int(
                    missing_past_timesteps
                ),

                "total_past_timesteps": int(
                    total_past_timesteps
                ),

                "fraction_missing_past_timesteps": (
                    float(missing_past_timesteps)
                    / total_past_timesteps
                    if total_past_timesteps > 0
                    else None
                ),
            },

            "excluding_actual_ego": {
                "agents_with_incomplete_past": int(
                    incomplete_history_non_ego_agents
                ),

                "fraction_agents_with_incomplete_past": (
                    float(incomplete_history_non_ego_agents)
                    / total_non_ego_participations
                    if total_non_ego_participations > 0
                    else None
                ),

                "missing_past_timesteps": int(
                    missing_past_timesteps_non_ego
                ),

                "total_past_timesteps": int(
                    total_past_timesteps_non_ego
                ),

                "fraction_missing_past_timesteps": (
                    float(missing_past_timesteps_non_ego)
                    / total_past_timesteps_non_ego
                    if total_past_timesteps_non_ego > 0
                    else None
                ),
            },

            "samples": {
                "samples_with_any_incomplete_history": int(
                    samples_with_any_incomplete_history
                ),

                "fraction_samples_with_any_incomplete_history": (
                    float(samples_with_any_incomplete_history)
                    / len(dataset)
                    if len(dataset) > 0
                    else None
                ),
            },
        },
    }

    return results


# ---------------------------------------------------------------------
# Full split profile
# ---------------------------------------------------------------------

def profile_split(dataset):
    return {
        "split": dataset.split,

        "dataset_identity": {
            "number_of_scenes": len(dataset.data),
            "number_of_dataset_samples": len(dataset),
            "categories": list(dataset.categories),
            "past_timesteps": dataset.npast,
            "future_timesteps": dataset.nfuture,
            "sequence_length": dataset.seq_len,
            "dt_seconds": dataset.dt,
            "frequency_hz": 1.0 / dataset.dt,
            "flip_singapore": dataset.flip_singapore,
            "require_full_past": dataset.require_full_past,
            "use_challenge_splits": dataset.use_challenge_splits,
        },

        "compiled_non_ego_agents": (
            count_compiled_non_ego_agents(dataset)
        ),

        "source_scene_locations": (
            count_scene_locations(dataset)
        ),

        "dataset_sample_locations": (
            count_sample_locations(dataset)
        ),

        "sample_level_statistics": (
            profile_samples(dataset)
        ),
    }


# ---------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------

def print_profile_summary(name, results):

    identity = results["dataset_identity"]
    stats = results["sample_level_statistics"]

    print()
    print("=" * 70)
    print(f"{name.upper()} PROFILE")
    print("=" * 70)

    print(
        f"Scenes:                    "
        f"{identity['number_of_scenes']}"
    )

    print(
        f"Dataset samples:           "
        f"{identity['number_of_dataset_samples']}"
    )

    print(
        f"Categories:                "
        f"{identity['categories']}"
    )

    print(
        f"Compiled non-ego agents:   "
        f"{results['compiled_non_ego_agents']}"
    )

    print(
        f"Scene locations:           "
        f"{results['source_scene_locations']}"
    )

    print(
        f"Sample locations:          "
        f"{results['dataset_sample_locations']}"
    )

    aps = stats["agents_per_sample"]

    print(
        f"Mean agents/sample:        "
        f"{aps['mean']:.3f}"
    )

    print(
        f"Median agents/sample:      "
        f"{aps['median']:.3f}"
    )

    print(
        f"Agent range/sample:        "
        f"{aps['min']} - {aps['max']}"
    )

    print(
        "Agent participations:      "
        f"{stats['agent_participations']['all_agents']['by_category']}"
    )

    non_ego = stats[
        "agent_participations"
    ]["excluding_actual_ego"]

    print(
        "Non-ego participations:    "
        f"{non_ego['by_category']}"
    )

    incomplete = stats[
        "incomplete_history"
    ]["excluding_actual_ego"]

    print(
        "Non-ego incomplete past:   "
        f"{incomplete['agents_with_incomplete_past']}"
    )

    if (
        incomplete[
            "fraction_agents_with_incomplete_past"
        ]
        is not None
    ):
        print(
            "Non-ego incomplete rate:   "
            f"{100.0 * incomplete['fraction_agents_with_incomplete_past']:.3f}%"
        )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    args = parse_args()

    data_path = os.path.join(
        args.data_dir,
        args.data_version,
    )

    if not os.path.isdir(data_path):
        raise FileNotFoundError(
            f"nuScenes directory not found: {data_path}"
        )

    mode_name = (
        "prediction_challenge"
        if args.use_challenge_splits
        else "repository_default"
    )

    print(
        f"Profiling mode: {mode_name}"
    )

    print("Creating STRIVE map environment...")

    map_env = NuScenesMapEnv(
        data_path,
        bounds=[-17.0, -38.5, 60.0, 38.5],
        layers=[
            "drivable_area",
            "carpark_area",
            "road_divider",
            "lane_divider",
        ],
        L=256,
        W=256,
        device="cpu",
        flip_singapore=True,
        pix_per_m=4,
    )

    print("Creating nuScenes object...")

    nusc_obj = NuScenes(
        version=f"v1.0-{args.data_version}",
        dataroot=data_path,
        verbose=False,
    )

    print("Creating STRIVE training dataset...")

    train_dataset = build_dataset(
        split="train",
        args=args,
        nusc_obj=nusc_obj,
        map_env=map_env,
    )

    print("Creating STRIVE validation dataset...")

    val_dataset = build_dataset(
        split="val",
        args=args,
        nusc_obj=nusc_obj,
        map_env=map_env,
    )

    print()
    print("Profiling training dataset...")

    train_results = profile_split(
        train_dataset
    )

    print()
    print("Profiling validation dataset...")

    val_results = profile_split(
        val_dataset
    )

    results = {
        "profile_schema_version": "0.1",

        "configuration": {
            "data_version": args.data_version,
            "agent_categories": [
                "car",
                "truck",
            ],
            "past_timesteps": 4,
            "future_timesteps": 12,
            "use_challenge_splits": (
                args.use_challenge_splits
            ),
            "mode": mode_name,
        },

        "train": train_results,
        "validation": val_results,
    }

    if args.output is None:

        output_dir = os.path.join(
            REPO_ROOT,
            "metadata",
            "data",
            "profile_runs",
        )

        os.makedirs(
            output_dir,
            exist_ok=True,
        )

        output_path = os.path.join(
            output_dir,
            (
                "nuscenes_strive_"
                f"{args.data_version}_"
                f"{mode_name}.json"
            ),
        )

    else:
        output_path = args.output

        output_parent = os.path.dirname(
            os.path.abspath(output_path)
        )

        os.makedirs(
            output_parent,
            exist_ok=True,
        )

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            results,
            f,
            indent=2,
        )

    print_profile_summary(
        "train",
        train_results,
    )

    print_profile_summary(
        "validation",
        val_results,
    )

    print()
    print(
        f"Saved profile to: {output_path}"
    )


if __name__ == "__main__":
    main()
