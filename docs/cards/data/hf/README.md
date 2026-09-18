---
license: other
source_datasets:
- extended
pretty_name: STRIVE nuScenes-Derived Traffic Dataset
license_name: CC BY-NC-SA 4.0 + nuScenes/Motional Dataset Terms
tags:
- autonomous-driving
- nuscenes
- trajectory-prediction
- scene-graph
- timeseries
- strive
---

# Dataset Card for STRIVE nuScenes-Derived Traffic Dataset

> This file is generated from `metadata/data/nuscenes_strive.yaml`.
> Do not edit this generated file manually.

## Dataset Summary

This card documents the STRIVE-specific nuScenes-derived traffic representation
used by the original STRIVE car/truck traffic model.

It is a derived trajectory, scene-graph, and semantic-map representation of
nuScenes rather than a redistribution of the complete multimodal nuScenes
dataset.

## Source and Provenance

- **Upstream dataset:** nuScenes `v1.0-trainval`
- **Associated system:** STRIVE
- **STRIVE repository:** `nv-tlabs/STRIVE`
- **Frozen source commit:** `b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d`
- **Paper:** *Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior*

The exact dataset-construction mode used for the released STRIVE traffic-model
checkpoint has not been independently verified.

## Dataset Structure

### Temporal Representation

- Sampling frequency: 2.0 Hz
- Past steps: 4
- Future steps: 12
- Total sequence length: 16 steps

### Agent Categories

The primary traffic-model representation includes:

- car
- truck

### Model-Facing Graph Tensors

| Field | Shape |
|---|---|
| `past` | `N × 4 × 6` |
| `past_gt` | `N × 4 × 6` |
| `future` | `N × 12 × 6` |
| `future_gt` | `N × 12 × 6` |
| `sem` | `N × 2` |
| `lw` | `N × 2` |
| `past_vis` | `N × 4` |
| `future_vis` | `N × 12` |
| `edge_index` | `2 × E` |

The interaction graph is directed and fully connected without self-edges, so:

\[
E=N(N-1).
\]

The dataset also returns `map_idx`, which is used by STRIVE to generate local
semantic-map crops dynamically during model execution.

## Dataset Splits

### Repository-Default Construction

`use_challenge_splits=False`

| Split | Scenes | Scene-window samples |
|---|---:|---:|
| Train | 500 | 12191 |
| Validation | 200 | 4739 |

### Prediction-Challenge Construction

`use_challenge_splits=True`

| Split | Scenes | Prediction-target samples |
|---|---:|---:|
| Train | 500 | 29884 |
| Validation | 200 | 7705 |

The two modes use different sample semantics and their sample counts should not
be interpreted as directly comparable units.

## Preprocessing

STRIVE performs the following major preprocessing operations:

- map-based non-ego frame filtering;
- finite-difference motion-feature derivation;
- Singapore map/trajectory coordinate flipping;
- mean/std state and vehicle-attribute normalization;
- visibility-mask construction;
- fully connected scene-graph construction.

For ordinary non-challenge tracks, a frame is retained when:

\[
f_{\mathrm{drivable}} \ge 0.30
\]

and:

\[
f_{\mathrm{carpark}} < 0.30.
\]

Prediction-challenge target tracks bypass this ordinary spatial-filtering rule.

## Filtering Attrition

For repository-default train and validation data combined:

| Statistic | Value |
|---|---:|
| Raw non-ego tracks | 26655 |
| Retained non-ego tracks | 12335 |
| Track-drop fraction | 53.724% |
| Raw non-ego annotation frames | 486133 |
| Spatially rejected annotation frames | 246201 |
| Spatial rejection fraction | 50.645% |

These values describe STRIVE's representation-selection process and should not
be interpreted as annotation-error rates in nuScenes.

## Incomplete Histories

STRIVE defaults to `require_full_past=False`.

An agent may therefore appear in a graph even when some earlier historical
states are unavailable, provided that its state at the final timestep of the
past window is valid.

Availability is represented through `past_vis` and `future_vis`.

## Training-Time Augmentation

The current `configs/train_traffic.cfg` uses:

`data_noise_std: 0.01`

Gaussian noise is applied in normalized feature space to training `past`,
`future`, and vehicle-attribute tensors. Validation data do not receive this
augmentation.

## Bias, Risks, and Limitations

The derived representation is affected by STRIVE-specific selection and
processing choices.

In particular:

- the map-based spatial filter removes a substantial portion of raw annotated
  vehicle states;
- filtering rates differ by category and geographic location;
- only car and truck categories are included in the primary traffic model;
- the data are limited to nuScenes coverage in Boston and Singapore;
- prediction-challenge mode has different sample semantics from the repository
  default mode; and
- the exact split used to train the released pretrained traffic-model
  checkpoint remains unverified.

The detailed engineering Data Card contains the complete measured statistics,
evidence classifications, and implementation caveats.

## Licensing

The upstream nuScenes dataset is subject to CC BY-NC-SA 4.0 together with the
applicable nuScenes/Motional Dataset Terms.

The STRIVE source code is distributed under the MIT License.

STRIVE-released pretrained models and generated scenarios derived from nuScenes
are separately described by the STRIVE repository as CC-BY-NC-SA-4.0.

Users remain responsible for complying with the applicable upstream dataset
terms.

## Detailed Documentation

The authoritative detailed Data Card is:

`docs/cards/data/DATA_CARD_NUSCENES_STRIVE.MD`

Machine-readable provenance is stored in:

`metadata/data/nuscenes_strive.yaml`

Profiling evidence is stored under:

`metadata/data/profile_runs/`

## References

- Davis Rempe et al. *Generating Useful Accident-Prone Driving Scenarios via a
  Learned Traffic Prior.* CVPR 2022.
- Holger Caesar et al. *nuScenes: A Multimodal Dataset for Autonomous Driving.*
  CVPR 2020.