"""
Profile the STRIVE-specific nuScenes dataset representation.

Initial milestone:
    - instantiate STRIVE's own NuScenesDataset
    - report basic dataset identity
    - do not reimplement STRIVE preprocessing

Run from the STRIVE repository root:

    python tools/profile_nuscenes_strive.py \
        --data_dir ./data/nuscenes \
        --data_version trainval
"""

import argparse
import os
import sys

# Allow imports from STRIVE/src when this script is run from repo root.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(REPO_ROOT, "src")

if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from nuscenes.nuscenes import NuScenes

from datasets.map_env import NuScenesMapEnv
from datasets.nuscenes_dataset import NuScenesDataset


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
        help="Use official nuScenes prediction challenge splits.",
    )

    return parser.parse_args()


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


def print_dataset_summary(name, dataset):
    print()
    print("=" * 60)
    print(f"{name.upper()} DATASET")
    print("=" * 60)

    print(f"split:              {dataset.split}")
    print(f"number of scenes:   {len(dataset.data)}")
    print(f"number of subseqs:  {len(dataset)}")
    print(f"categories:         {dataset.categories}")
    print(f"past timesteps:     {dataset.npast}")
    print(f"future timesteps:   {dataset.nfuture}")
    print(f"sequence length:    {dataset.seq_len}")
    print(f"dt:                 {dataset.dt}")
    print(f"frequency:          {1.0 / dataset.dt:.1f} Hz")
    print(f"flip Singapore:     {dataset.flip_singapore}")
    print(f"full past required: {dataset.require_full_past}")
    print(f"challenge splits:   {dataset.use_challenge_splits}")


def main():
    args = parse_args()

    data_path = os.path.join(args.data_dir, args.data_version)

    if not os.path.isdir(data_path):
        raise FileNotFoundError(
            f"nuScenes directory not found: {data_path}\n"
            "Expected something similar to:\n"
            "  data/nuscenes/trainval/v1.0-trainval\n"
            "  data/nuscenes/trainval/maps"
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

    print_dataset_summary("train", train_dataset)
    print_dataset_summary("validation", val_dataset)


if __name__ == "__main__":
    main()
