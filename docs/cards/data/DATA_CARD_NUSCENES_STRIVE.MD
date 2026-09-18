# Data Card: STRIVE nuScenes-Derived Traffic Dataset

## 1. Dataset Identity

**Name:** STRIVE nuScenes-Derived Traffic Dataset

**Upstream dataset:** nuScenes

**Associated system:** STRIVE — Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior

**Primary use in STRIVE:** Training and evaluating the learned traffic model and providing initial traffic scenes for adversarial scenario generation.

**Documentation status:** In progress

**Upstream dataset version:** nuScenes trainval

---

## 2. Scope

This data card documents the STRIVE-specific use, selection, preprocessing,
representation, and transformation of nuScenes data.

It is not intended to replace the official nuScenes dataset documentation.

The scope of this card is the data pipeline used by the original STRIVE system,
with primary emphasis on the car/truck traffic model used in the main paper.

---

## 3. Dataset Purpose

STRIVE uses nuScenes for two main purposes:

1. Training the learned traffic model that models plausible multi-agent traffic motion.
2. Providing initial real-world traffic scenes from which adversarial scenarios are generated.

The learned traffic model conditions future motion on agent history and map context.

---

## 4. Upstream Dataset

**Dataset:** nuScenes

**Dataset version used by STRIVE:** trainval

**Geographic locations represented by nuScenes:**
- Boston, USA
- Singapore

**Upstream license:** TBD — reference official nuScenes license and terms.

**Upstream documentation:** TBD — add official nuScenes dataset citation/link.

---

## 5. Agent Categories

### Main-paper traffic model

The primary STRIVE traffic model is trained using:

- car
- truck

Other semantic categories are supported by the public STRIVE implementation and
are considered separately in supplementary experiments.

### Excluded from the main-paper traffic model

Examples include:

- pedestrian
- cyclist
- motorcycle
- bus
- trailer
- emergency vehicle
- construction vehicle

These categories should not be interpreted as unsupported by the codebase;
rather, they are outside the main car/truck model documented by this data card.

---

## 6. Temporal Representation

STRIVE represents traffic trajectories at 2 Hz.

For traffic-model training:

- Past context: 2 seconds
- Past timesteps: 4
- Future prediction horizon: 6 seconds
- Future timesteps: 12
- Timestep duration: 0.5 seconds

The resulting traffic-model sample therefore represents an 8-second temporal
window consisting of observed history followed by future motion.

---

## 7. Agent State Representation

The STRIVE implementation represents each agent state using:

- x position
- y position
- heading x-component
- heading y-component
- speed
- heading-rate / yaw-rate quantity

Vehicle attributes include:

- length
- width

Exact normalization statistics will be documented after verification from the
training dataset and implementation.

---

## 8. Map Representation

STRIVE uses local rasterized map context.

The paper reports the following semantic map layers:

- drivable area
- carpark area
- road divider
- lane divider

Reported map crop configuration:

- 256 × 256 pixels
- 4 pixels per meter

The map representation is processed by the traffic model's convolutional map
encoder.

---

## 9. STRIVE-Specific Preprocessing

### 9.1 Trajectory Filtering

The STRIVE preprocessing pipeline removes vehicle frames when more than 30% of
the vehicle overlaps regions outside the drivable-area/carpark representation.

Exact filtering counts are:

**TBD — compute using profiling script if reproducible from available data.**

### 9.2 Derived Motion Quantities

Velocity and yaw-related quantities are derived from trajectory information
using finite differences.

### 9.3 Singapore Transformation

STRIVE flips Singapore maps and trajectories about the x-axis.

The purpose is to place Singapore driving direction into a representation
consistent with the traffic convention used by the model.

This transformation must be documented when interpreting coordinates or
reconstructing scenes.

---

## 10. Dataset Splits

### Programmatically Reproduced Split Behavior

The current STRIVE repository supports two distinct dataset-construction modes.
Both were reproduced using the public STRIVE implementation at commit:

`b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d`

with:

- `data_version=trainval`
- agent categories `['car', 'truck']`
- 4 past timesteps
- 12 future timesteps
- 0.5-second timestep duration

#### Mode 1: Repository-Default Dataset Construction

Configuration:

`use_challenge_splits=False`

The profiler produced:

| STRIVE split | Source scenes | Scene-window samples |
|---|---:|---:|
| Train | 500 | 12,191 |
| Validation | 200 | 4,739 |
| Total | 700 | 16,930 |

In this mode, each entry in the STRIVE dataset identifies a scene and a
temporal start index:

`(scene_name, start_idx)`

Therefore, the sample counts in this mode represent temporal scene windows.

#### Mode 2: Prediction-Challenge Dataset Construction

Configuration:

`use_challenge_splits=True`

The profiler produced:

| STRIVE split | Source scenes | Prediction-target samples |
|---|---:|---:|
| Train | 500 | 29,884 |
| Validation | 200 | 7,705 |
| Total | 700 | 37,589 |

In this mode, each entry in the STRIVE dataset identifies a scene, a temporal
start index, and a prediction-target agent:

`(scene_name, start_idx, instance_token)`

Therefore, the sample counts in this mode represent prediction-target
agent/sample pairs rather than ordinary scene windows.

The counts from the two modes should not be compared as though they represented
the same unit of observation.

### STRIVE-to-nuScenes Challenge Split Mapping

When `use_challenge_splits=True`, the STRIVE implementation maps its internal
splits as follows:

| STRIVE split | nuScenes prediction-challenge subset |
|---|---|
| `train` | `train` |
| `val` | `train_val` |
| `test` | `val` |

The STRIVE `val` split is therefore a held-out portion of the prediction
challenge training scenes rather than the official nuScenes prediction
challenge validation split.

### Relationship to the Paper

The STRIVE paper reports that traffic-model training uses the nuScenes
prediction challenge training split.

The public repository supports this behavior through the
`use_challenge_splits` option.

However, the current `configs/train_traffic.cfg` does not explicitly enable
this option, and the shared configuration parser defaults
`use_challenge_splits` to `False`.

For this reason, the exact dataset-construction mode used to produce the
released pretrained traffic-model checkpoint remains unverified.

---

## 11. Scenario-Generation Seed Data

STRIVE also uses nuScenes traffic scenes as initialization points for adversarial
scenario generation.

The paper reports constructing approximately 1,200 eight-second scenarios from
nuScenes train/validation data for scenario-generation experiments.

This scenario-generation subset is distinct conceptually from the traffic-model
training dataset and should not be interpreted as an independent upstream
dataset.

Further details about generated adversarial scenarios are documented in:

`DATA_CARD_GENERATED_SCENARIOS.md`

---

## 12. Data Schema

A STRIVE traffic sample includes, at minimum:

### Agent information

- past trajectories
- future trajectories during training/evaluation
- semantic category
- vehicle dimensions
- visibility information where applicable

### Scene information

- local map identifier
- local raster map context
- multi-agent scene graph structure

### Derived quantities

- velocity/speed
- heading representation
- heading-rate quantities

Exact tensor shapes and field names will be added after cross-checking the
dataset implementation.

---

## 13. Dataset Statistics

## 13. Dataset Statistics

### Repository-Default Mode

Configuration:

`use_challenge_splits=False`

| Statistic | Value |
|---|---:|
| Source scenes | 700 |
| Training scenes | 500 |
| Validation scenes | 200 |
| Training scene-window samples | 12,191 |
| Validation scene-window samples | 4,739 |
| Total scene-window samples | 16,930 |

### Prediction-Challenge Mode

Configuration:

`use_challenge_splits=True`

| Statistic | Value |
|---|---:|
| Source scenes | 700 |
| Training scenes | 500 |
| Validation scenes | 200 |
| Training prediction-target samples | 29,884 |
| Validation prediction-target samples | 7,705 |
| Total prediction-target samples | 37,589 |

### Statistics Not Yet Computed

| Statistic | Value |
|---|---:|
| Number of car agent instances | TBD |
| Number of truck agent instances | TBD |
| Mean agents per dataset sample | TBD |
| Median agents per dataset sample | TBD |
| Boston sample count | TBD |
| Singapore sample count | TBD |
| Frequency of incomplete histories | TBD |
| Samples/frames removed by filtering | TBD |

These remaining statistics will be generated programmatically using
`tools/profile_nuscenes_strive.py`.

---

## 14. Data Quality and Filtering

Relevant quality considerations include:

- incomplete agent histories or futures
- visibility and annotation availability
- filtering based on drivable-map overlap
- finite-difference estimation of motion quantities
- coordinate transformations for Singapore
- category reduction from detailed nuScenes classes to STRIVE classes

The quantitative impact of these operations should be measured where possible.

### Incomplete History

The public `NuScenesDataset` implementation sets `require_full_past=False`
by default.

Therefore, full past history is not required for every returned non-ego agent
unless this option is explicitly enabled.

The prevalence of incomplete histories should be measured by the dataset
profiling script.

---

## 15. Known Coverage Limitations

The main-paper training configuration focuses on cars and trucks.

Consequently, the primary traffic model does not represent the full diversity
of road users present in nuScenes.

The paper specifically identifies pedestrians and cyclists as important
extensions beyond the primary evaluation setting.

The dataset is also constrained by the geographic, environmental, behavioral,
and annotation coverage of nuScenes.

---

## 16. Potential Sources of Bias

Potential sources of dataset bias include:

- geographic concentration in Boston and Singapore
- differences in driving conventions between collection locations
- car/truck category restriction in the primary model
- filtering of trajectories based on map overlap
- dependence on nuScenes annotation and map quality
- selection of scenes used for STRIVE scenario generation

No claim is made that these factors exhaust all possible sources of bias.

---

## 17. Intended Uses

This derived dataset representation is intended for:

- training the STRIVE traffic model
- evaluating traffic prediction behavior
- initializing STRIVE adversarial scenario generation
- reproducing STRIVE experiments

---

## 18. Out-of-Scope Uses

This data card does not establish suitability for:

- real-world autonomous-driving deployment
- safety certification
- perception-system evaluation
- complete road-user modeling
- geographic regions not represented in nuScenes
- safety claims beyond the experiments documented by STRIVE

---

## 19. Relationship to Other STRIVE Artifacts

This dataset is an input to:

- `MODEL_CARD_TRAFFIC_MODEL_CAR_TRUCK.md`
- `MODEL_CARD_TRAFFIC_MODEL_ALL_CATEGORIES.md`
- `COMPONENT_CARD_INITIALIZATION_OPTIMIZATION.md`
- `COMPONENT_CARD_ADVERSARIAL_OPTIMIZATION.md`

Generated scenarios derived from this data are documented separately in:

- `DATA_CARD_GENERATED_SCENARIOS.md`

---

## 20. Reproducibility and Provenance

### Source repository

Repository:

`nv-tlabs/STRIVE`

Exact repository commit used for this documentation:

**TBD — record commit SHA**

### Relevant implementation files

- `src/datasets/nuscenes_dataset.py`
- `src/datasets/nuscenes_utils.py`
- `src/datasets/map_env.py`
- `src/train_traffic.py`
- `configs/train_traffic.cfg`
- `configs/train_traffic_all_cats.cfg`

### Provenance policy

Facts in this card should be classified as one of:

- paper-reported
- repository-verified
- artifact-verified
- programmatically computed
- not specified

Unknown values must not be inferred.

---

## 21. Licensing

The STRIVE repository documentation states that pretrained models and generated
scenarios derived from nuScenes are subject to separate nuScenes-derived
licensing conditions.

The exact applicable upstream and derived-data licensing terms should be
verified against the current official nuScenes terms before redistribution.

---

## 22. References

- Rempe et al., "Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior."
- nuScenes dataset documentation.
- STRIVE public source repository.

---

## 23. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1 | TBD | Initial data-card skeleton |