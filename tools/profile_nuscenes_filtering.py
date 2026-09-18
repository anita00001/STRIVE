"""
Profile filtering attrition in STRIVE's nuScenes preprocessing.

This script subclasses STRIVE's NuScenesDataset only to record statistics
around the repository's post-processing stage. The actual dataset output is
still produced by NuScenesDataset.post_process().

Run from the STRIVE repository root.
"""

import argparse
import json
import os
import sys
from collections import Counter

import numpy as np
import torch


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


from nuscenes.nuscenes import NuScenes

from datasets.map_env import NuScenesMapEnv
from datasets.nuscenes_dataset import NuScenesDataset
import datasets.nuscenes_utils as nutils


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data_dir",
        type=str,
        default="./data/nuscenes",
    )

    parser.add_argument(
        "--data_version",
        type=str,
        default="trainval",
        choices=["trainval", "mini"],
    )

    parser.add_argument(
        "--use_challenge_splits",
        action="store_true",
    )

    parser.add_argument(
        "--output",
        type=str,
        default=None,
    )

    return parser.parse_args()


def high_level_location(map_name):
    if map_name.startswith("boston"):
        return "Boston"

    if map_name.startswith("singapore"):
        return "Singapore"

    return map_name


def new_stats():
    return {
        "raw_non_ego_tracks": 0,
        "raw_non_ego_observation_frames": 0,

        "spatial_filter_applied_tracks": 0,
        "spatial_filter_bypassed_tracks": 0,

        "spatially_accepted_observation_frames": 0,
        "spatially_rejected_observation_frames": 0,

        "retained_non_ego_tracks": 0,
        "dropped_non_ego_tracks": 0,

        "postprocessed_visible_state_frames": 0,

        "by_category": {},
        "by_location": {},
    }


def counter_dict():
    return {
        "raw_tracks": Counter(),
        "raw_observation_frames": Counter(),
        "spatially_accepted_frames": Counter(),
        "spatially_rejected_frames": Counter(),
        "retained_tracks": Counter(),
        "visible_state_frames": Counter(),
    }


class ProfilingNuScenesDataset(NuScenesDataset):

    def post_process(self, data):

        stats = new_stats()

        cat_stats = counter_dict()
        loc_stats = counter_dict()

        drivable_raster = self.map_env.nusc_raster[:, 0]

        carpark_raster = None
        if "carpark_area" in self.map_env.layer_map:
            carpark_raster = self.map_env.nusc_raster[
                :,
                self.map_env.layer_map["carpark_area"],
            ]

        # ------------------------------------------------------------
        # Measure raw observations and exact spatial-filter predicate
        # before normal STRIVE post-processing.
        # ------------------------------------------------------------

        for scene_name, scene_data in data.items():

            map_name = self.scene2map[scene_name][0]
            location = high_level_location(map_name)
            map_idx = self.scene2map[scene_name][1]

            ego_sample_tokens = [
                row["samp_tok"]
                for row in scene_data["ego"]["traj"]
            ]

            challenge_set = set()

            if self.use_challenge_splits:
                challenge_set = set(
                    self.pred_challenge_scenes.get(scene_name, [])
                )

            for agent_name, agent_data in scene_data.items():

                if agent_name == "ego":
                    continue

                category = agent_data["k"]
                rows = agent_data["traj"]

                num_raw = len(rows)

                stats["raw_non_ego_tracks"] += 1
                stats["raw_non_ego_observation_frames"] += num_raw

                cat_stats["raw_tracks"][category] += 1
                cat_stats["raw_observation_frames"][category] += num_raw

                loc_stats["raw_tracks"][location] += 1
                loc_stats["raw_observation_frames"][location] += num_raw

                # ----------------------------------------------------
                # Challenge targets bypass ordinary spatial filtering.
                # This matches the condition in NuScenesDataset.
                # ----------------------------------------------------

                bypass_filter = False

                if self.use_challenge_splits:
                    target_tokens = [
                        agent_name + "_" + sample_token
                        for sample_token in ego_sample_tokens
                    ]

                    bypass_filter = any(
                        token in challenge_set
                        for token in target_tokens
                    )

                if bypass_filter:

                    valid_frame = np.ones(
                        num_raw,
                        dtype=bool,
                    )

                    stats["spatial_filter_bypassed_tracks"] += 1

                else:

                    stats["spatial_filter_applied_tracks"] += 1

                    x_list = np.array(
                        [
                            [
                                row["x"],
                                row["y"],
                                row["hcos"],
                                row["hsin"],
                            ]
                            for row in rows
                        ]
                    )

                    lw = np.array(
                        [
                            agent_data["l"],
                            agent_data["w"],
                        ]
                    )

                    torch_xlist = torch.from_numpy(
                        x_list
                    ).to(drivable_raster.device)

                    torch_lw = (
                        torch.from_numpy(lw)
                        .to(drivable_raster.device)
                        .unsqueeze(0)
                        .expand(num_raw, 2)
                    )

                    mapixes = (
                        torch.tensor(
                            [map_idx],
                            device=drivable_raster.device,
                        )
                        .long()
                        .expand(num_raw)
                    )

                    drivable_frac = nutils.check_on_layer(
                        drivable_raster,
                        self.map_env.nusc_dx,
                        torch_xlist,
                        torch_lw,
                        mapixes,
                    )

                    valid_frame = (
                        drivable_frac >= 0.30
                    ).cpu().numpy()

                    if carpark_raster is not None:

                        carpark_frac = nutils.check_on_layer(
                            carpark_raster,
                            self.map_env.nusc_dx,
                            torch_xlist,
                            torch_lw,
                            mapixes,
                        )

                        not_on_carpark = (
                            carpark_frac < 0.30
                        ).cpu().numpy()

                        valid_frame = np.logical_and(
                            valid_frame,
                            not_on_carpark,
                        )

                accepted = int(np.sum(valid_frame))
                rejected = int(num_raw - accepted)

                stats[
                    "spatially_accepted_observation_frames"
                ] += accepted

                stats[
                    "spatially_rejected_observation_frames"
                ] += rejected

                cat_stats[
                    "spatially_accepted_frames"
                ][category] += accepted

                cat_stats[
                    "spatially_rejected_frames"
                ][category] += rejected

                loc_stats[
                    "spatially_accepted_frames"
                ][location] += accepted

                loc_stats[
                    "spatially_rejected_frames"
                ][location] += rejected

        # ------------------------------------------------------------
        # Let STRIVE perform its normal preprocessing.
        # ------------------------------------------------------------

        scene2info, seq_map = super().post_process(data)

        # ------------------------------------------------------------
        # Measure resulting compiled tracks and visible states.
        # ------------------------------------------------------------

        for scene_name, scene_data in scene2info.items():

            map_name = self.scene2map[scene_name][0]
            location = high_level_location(map_name)

            for agent_name, agent_data in scene_data.items():

                if agent_name == "ego":
                    continue

                category = agent_data["k"]

                stats["retained_non_ego_tracks"] += 1

                cat_stats[
                    "retained_tracks"
                ][category] += 1

                loc_stats[
                    "retained_tracks"
                ][location] += 1

                visible = int(
                    np.sum(agent_data["is_vis"])
                )

                stats[
                    "postprocessed_visible_state_frames"
                ] += visible

                cat_stats[
                    "visible_state_frames"
                ][category] += visible

                loc_stats[
                    "visible_state_frames"
                ][location] += visible

        stats["dropped_non_ego_tracks"] = (
            stats["raw_non_ego_tracks"]
            - stats["retained_non_ego_tracks"]
        )

        raw_frames = stats[
            "raw_non_ego_observation_frames"
        ]

        rejected_frames = stats[
            "spatially_rejected_observation_frames"
        ]

        raw_tracks = stats[
            "raw_non_ego_tracks"
        ]

        dropped_tracks = stats[
            "dropped_non_ego_tracks"
        ]

        stats["spatial_rejection_fraction"] = (
            rejected_frames / raw_frames
            if raw_frames
            else None
        )

        stats["dropped_track_fraction"] = (
            dropped_tracks / raw_tracks
            if raw_tracks
            else None
        )

        stats["by_category"] = {
            key: dict(value)
            for key, value in cat_stats.items()
        }

        stats["by_location"] = {
            key: dict(value)
            for key, value in loc_stats.items()
        }

        self.filter_profile = stats

        return scene2info, seq_map


def build_dataset(
    split,
    args,
    nusc_obj,
    map_env,
):

    return ProfilingNuScenesDataset(
        data_path=os.path.join(
            args.data_dir,
            args.data_version,
        ),
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


def print_summary(split, dataset):

    s = dataset.filter_profile

    print()
    print("=" * 70)
    print(f"{split.upper()} FILTER PROFILE")
    print("=" * 70)

    print(
        "Raw non-ego tracks:                 ",
        s["raw_non_ego_tracks"],
    )

    print(
        "Retained non-ego tracks:            ",
        s["retained_non_ego_tracks"],
    )

    print(
        "Dropped non-ego tracks:             ",
        s["dropped_non_ego_tracks"],
    )

    print(
        "Dropped-track rate:                 ",
        f"{100 * s['dropped_track_fraction']:.3f}%",
    )

    print(
        "Raw non-ego observation frames:     ",
        s["raw_non_ego_observation_frames"],
    )

    print(
        "Spatially accepted frames:          ",
        s["spatially_accepted_observation_frames"],
    )

    print(
        "Spatially rejected frames:          ",
        s["spatially_rejected_observation_frames"],
    )

    print(
        "Spatial-rejection rate:             ",
        f"{100 * s['spatial_rejection_fraction']:.3f}%",
    )

    print(
        "Postprocessed visible-state frames: ",
        s["postprocessed_visible_state_frames"],
    )

    print(
        "Filter-applied tracks:              ",
        s["spatial_filter_applied_tracks"],
    )

    print(
        "Filter-bypassed tracks:             ",
        s["spatial_filter_bypassed_tracks"],
    )


def main():

    args = parse_args()

    data_path = os.path.join(
        args.data_dir,
        args.data_version,
    )

    mode = (
        "prediction_challenge"
        if args.use_challenge_splits
        else "repository_default"
    )

    map_env = NuScenesMapEnv(
        data_path,
        bounds=[
            -17.0,
            -38.5,
            60.0,
            38.5,
        ],
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

    nusc_obj = NuScenes(
        version=f"v1.0-{args.data_version}",
        dataroot=data_path,
        verbose=False,
    )

    train_dataset = build_dataset(
        "train",
        args,
        nusc_obj,
        map_env,
    )

    val_dataset = build_dataset(
        "val",
        args,
        nusc_obj,
        map_env,
    )

    results = {
        "profile_schema_version": "0.1",
        "mode": mode,
        "configuration": {
            "data_version": args.data_version,
            "categories": [
                "car",
                "truck",
            ],
            "use_challenge_splits":
                args.use_challenge_splits,
            "drivable_minimum_overlap": 0.30,
            "carpark_maximum_overlap_exclusive": 0.30,
        },
        "train": train_dataset.filter_profile,
        "validation": val_dataset.filter_profile,
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
            f"nuscenes_strive_filtering_{mode}.json",
        )

    else:
        output_path = args.output

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

    print_summary(
        "train",
        train_dataset,
    )

    print_summary(
        "validation",
        val_dataset,
    )

    print()
    print(
        f"Saved filter profile to: {output_path}"
    )


if __name__ == "__main__":
    main()
