#!/usr/bin/env python3

from pathlib import Path

import yaml
from huggingface_hub import DatasetCard, DatasetCardData


REPO_ROOT = Path(__file__).resolve().parents[1]

METADATA_PATH = REPO_ROOT / "metadata" / "data" / "nuscenes_strive.yaml"
TEMPLATE_PATH = (
    REPO_ROOT
    / "docs"
    / "cards"
    / "data"
    / "hf"
    / "DATASET_CARD_TEMPLATE.md"
)
OUTPUT_PATH = (
    REPO_ROOT
    / "docs"
    / "cards"
    / "data"
    / "hf"
    / "README.md"
)


def require(mapping, *keys):
    value = mapping

    for key in keys:
        if key not in value:
            raise KeyError(
                "Missing required metadata field: "
                + ".".join(keys)
            )

        value = value[key]

    return value


def pct(value):
    return f"{100.0 * float(value):.3f}"


def main():
    with METADATA_PATH.open("r", encoding="utf-8") as f:
        metadata = yaml.safe_load(f)

    status = require(
        metadata,
        "scope",
        "status",
    )

    if status != "complete":
        raise ValueError(
            "Refusing to generate Hugging Face card because "
            f"metadata scope status is {status!r}, not 'complete'."
        )

    default_split = require(
        metadata,
        "splits",
        "repository_default",
    )

    challenge_split = require(
        metadata,
        "splits",
        "prediction_challenge_mode",
    )

    filtering = require(
        metadata,
        "filtering_attrition",
        "repository_default",
        "combined",
    )

    card_data = DatasetCardData(
        pretty_name=require(
            metadata,
            "dataset",
            "name",
        ),
        license="other",
        license_name="CC BY-NC-SA 4.0 + nuScenes/Motional Dataset Terms",
        source_datasets=["extended"],
        tags=[
            "autonomous-driving",
            "nuscenes",
            "trajectory-prediction",
            "scene-graph",
            "timeseries",
            "strive",
        ],
    )

    card = DatasetCard.from_template(
        card_data=card_data,
        template_path=str(TEMPLATE_PATH),

        pretty_name=require(
            metadata,
            "dataset",
            "name",
        ),

        repository=require(
            metadata,
            "source",
            "repository",
        ),

        source_commit=require(
            metadata,
            "source",
            "commit",
        ),

        paper=require(
            metadata,
            "source",
            "paper",
        ),

        frequency_hz=require(
            metadata,
            "temporal",
            "frequency_hz",
        ),

        past_steps=require(
            metadata,
            "temporal",
            "past",
            "steps",
        ),

        future_steps=require(
            metadata,
            "temporal",
            "future",
            "steps",
        ),

        total_steps=require(
            metadata,
            "temporal",
            "total_steps",
        ),

        default_train_scenes=require(
            default_split,
            "train",
            "scenes",
        ),

        default_train_samples=require(
            default_split,
            "train",
            "scene_window_samples",
        ),

        default_val_scenes=require(
            default_split,
            "validation",
            "scenes",
        ),

        default_val_samples=require(
            default_split,
            "validation",
            "scene_window_samples",
        ),

        challenge_train_scenes=require(
            challenge_split,
            "train",
            "scenes",
        ),

        challenge_train_samples=require(
            challenge_split,
            "train",
            "prediction_target_samples",
        ),

        challenge_val_scenes=require(
            challenge_split,
            "validation",
            "scenes",
        ),

        challenge_val_samples=require(
            challenge_split,
            "validation",
            "prediction_target_samples",
        ),

        raw_tracks=require(
            filtering,
            "raw_non_ego_tracks",
        ),

        retained_tracks=require(
            filtering,
            "retained_non_ego_tracks",
        ),

        track_drop_pct=pct(
            require(
                filtering,
                "dropped_track_fraction",
            )
        ),

        raw_frames=require(
            filtering,
            "raw_non_ego_observation_frames",
        ),

        rejected_frames=require(
            filtering,
            "spatially_rejected_observation_frames",
        ),

        frame_reject_pct=pct(
            require(
                filtering,
                "spatial_rejection_fraction",
            )
        ),
    )

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    card.save(OUTPUT_PATH)

    # Local parse check: verifies that the generated YAML front matter can be
    # read back as a Hugging Face DatasetCard.
    loaded = DatasetCard.load(OUTPUT_PATH)

    print("HF DATASET CARD GENERATED")
    print("output:", OUTPUT_PATH)
    print("pretty_name:", loaded.data.pretty_name)
    print("license:", loaded.data.license)
    print("source_datasets:", loaded.data.source_datasets)


if __name__ == "__main__":
    main()
