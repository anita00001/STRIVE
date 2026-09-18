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

## 7. Agent State Representation

Each agent state is represented by six values:

\[
(x,\ y,\ h_x,\ h_y,\ s,\ \dot{h})
\]

where:

| Field | Meaning |
|---|---|
| `x` | map-frame x position |
| `y` | map-frame y position |
| `heading_x` | x component of unit heading vector |
| `heading_y` | y component of unit heading vector |
| `speed` | scalar speed |
| `heading_rate` | heading-change rate |

Each agent additionally has two vehicle attributes:

\[
(l,\ w)
\]

representing vehicle length and width.

Speed and heading-rate features are derived during STRIVE preprocessing using
finite-difference operations on the trajectory data.

The main car/truck traffic model represents semantic category using a two-entry
one-hot vector corresponding to `car` and `truck`. The ego vehicle is assigned
the `car` semantic vector by the dataset loader.

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

### Normalization

STRIVE applies mean/std normalization according to

\[
x_{\mathrm{norm}} = \frac{x-\mu}{\sigma}.
\]

For the car/truck traffic model, the repository defines the following constants:

| Quantity | Mean | Standard deviation |
|---|---:|---:|
| x position | 0.0 | 15.0 |
| y position | 0.0 | 15.0 |
| heading x | 0.0 | 1.0 |
| heading y | 0.0 | 1.0 |
| speed | 1.802009 | 3.507907 |
| heading rate | -0.000037 | 0.055684 |
| vehicle length | 4.844294 | 1.084860 |
| vehicle width | 2.021752 | 0.299647 |

These constants are defined in `src/datasets/utils.py` under
`NUSC_NORM_STATS[('car', 'truck')]`.

The public repository provides the constants directly, but the currently
reviewed source does not establish the exact procedure or dataset subset from
which the authors originally estimated every constant. They are therefore
documented here as repository-defined normalization parameters rather than
newly estimated statistics from this profiling exercise.

### Training-Time Noise

The current `configs/train_traffic.cfg` specifies:

`data_noise_std: 0.01`

During construction of training samples, STRIVE adds Gaussian noise with
standard deviation 0.01 to the normalized `past`, `future`, and normalized
vehicle-dimension (`lw`) tensors.

The corresponding `past_gt` and `future_gt` tensors remain unperturbed
normalized copies.

After perturbing trajectory states, STRIVE:

- renormalizes the two heading-vector components to unit length; and
- clamps the first two normalized position components to a minimum of 0.0.

The validation dataset does not receive this augmentation. `train_traffic.py`
passes `data_noise_std` to the training `NuScenesDataset`, while the validation
dataset uses the constructor default `noise_std=0.0`.

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

### Map Input

The dataset does not directly return a 256×256 local map tensor inside each
scene graph. Instead, it returns `map_idx`.

During the traffic-model forward pass, STRIVE sets `scene_graph.pos` to the
last past pose:

`scene_graph.past[:, -1, :4]`

The scene graph is then temporarily unnormalized inside `encode_map()` so that
the local map crop can be queried in world/map coordinates. After map-feature
extraction, the graph is normalized again.

The rendered map observation has shape:

`N × C × 256 × 256`

where the default STRIVE map configuration produces four channels.

### Data Schema details

For a dataset sample containing \(N\) graph nodes, the STRIVE
`NuScenesDataset` returns a PyTorch Geometric scene graph plus a map index.

| Field | Shape | Description |
|---|---|---|
| `past` | `N × 4 × 6` | Normalized past states; may be noised during training |
| `past_gt` | `N × 4 × 6` | Clean normalized past states |
| `future` | `N × 12 × 6` | Normalized future states used by the CVAE posterior; may be noised during training |
| `future_gt` | `N × 12 × 6` | Clean normalized future states |
| `sem` | `N × 2` | One-hot car/truck semantics |
| `lw` | `N × 2` | Normalized vehicle length and width |
| `past_vis` | `N × 4` | Past visibility/validity mask |
| `future_vis` | `N × 12` | Future visibility/validity mask |
| `edge_index` | `2 × E` | Directed graph edges |
| `x` | `N` | Dataset-created placeholder |
| `pos` | `N` at dataset return | Placeholder subsequently replaced by the model |
| `map_idx` | scalar per sample | Index of the sample's nuScenes map |

For \(N\) agents, STRIVE constructs a directed fully connected interaction
graph without self-edges:

\[
E=N(N-1).
\]

### Node Inclusion

An agent is included only when it has a valid state at the final timestep of
the past window. Because `require_full_past=False` by default, earlier history
may still be missing. `past_vis` and `future_vis` explicitly represent this
availability.

### Node Ordering

In repository-default mode:

- node 0 is the ego vehicle.

In prediction-challenge mode:

- node 0 is the prediction target;
- node 1 is the ego vehicle.

The remaining eligible traffic participants follow afterward.

### Map Input

The dataset does not directly store an independent 256×256 map tensor inside
each returned graph. It returns `map_idx`. During the traffic-model forward
pass, STRIVE sets each node's `pos` from the final past pose and uses
`NuScenesMapEnv` to render the corresponding local map crop.

The resulting local map observation has shape:

`N × C × 256 × 256`

where, for the default STRIVE map configuration, \(C=4\).

---

## 13. Dataset Statistics

### Repository-Default Mode

Configuration:

`use_challenge_splits=False`

| Statistic | Train | Validation |
|---|---:|---:|
| Source scenes | 500 | 200 |
| Dataset samples | 12,191 | 4,739 |
| Compiled non-ego car records | 7,487 | 2,890 |
| Compiled non-ego truck records | 1,238 | 720 |
| Boston scenes | 283 | 107 |
| Singapore scenes | 217 | 93 |
| Boston dataset samples | 6,917 | 2,538 |
| Singapore dataset samples | 5,274 | 2,201 |
| Mean agents per sample | 9.524 | 10.178 |
| Median agents per sample | 8 | 7 |
| Minimum agents per sample | 1 | 1 |
| Maximum agents per sample | 60 | 48 |
| Non-ego car participations | 87,123 | 33,600 |
| Non-ego truck participations | 16,797 | 9,893 |
| Non-ego agents with incomplete past | 9,979 | 4,395 |
| Fraction of non-ego participations with incomplete past | 9.603% | 10.105% |

"Compiled non-ego agent records" count the agent records stored in the
preprocessed scene representation. An agent participating in multiple temporal
dataset samples is counted once in this statistic for its compiled scene record.

"Agent participations" count appearances in the actual scene graphs supplied
to the model. The same physical agent can therefore contribute to multiple
dataset samples.

"Incomplete past" means that at least one of the four past visibility steps
for a non-ego agent is missing, consistent with the repository default
`require_full_past=False`.

#### Combined Train + Validation Summary

| Statistic | Value |
|---|---:|
| Source scenes | 700 |
| Dataset samples | 16,930 |
| Compiled non-ego car records | 10,377 |
| Compiled non-ego truck records | 1,958 |
| Boston scenes | 390 |
| Singapore scenes | 310 |
| Boston dataset samples | 9,455 |
| Singapore dataset samples | 7,475 |
| Total agent participations | 164,343 |
| Total non-ego participations | 147,413 |
| Non-ego agents with incomplete past | 14,374 |
| Combined incomplete-past participation rate | 9.751% |

### Prediction-Challenge Mode

Configuration:

`use_challenge_splits=True`

| Statistic | Train | Validation |
|---|---:|---:|
| Source scenes | 500 | 200 |
| Prediction-target samples | 29,884 | 7,705 |
| Compiled non-ego car records | 7,489 | 2,891 |
| Compiled non-ego truck records | 1,238 | 720 |
| Boston scenes | 283 | 107 |
| Singapore scenes | 217 | 93 |
| Boston prediction-target samples | 18,726 | 5,222 |
| Singapore prediction-target samples | 11,158 | 2,483 |
| Mean agents per sample | 12.704 | 12.751 |
| Median agents per sample | 11 | 11 |
| Minimum agents per sample | 2 | 2 |
| Maximum agents per sample | 60 | 48 |
| Non-ego car participations | 299,299 | 70,007 |
| Non-ego truck participations | 50,455 | 20,535 |
| Non-ego participations with incomplete past | 53,038 | 14,956 |
| Fraction of non-ego participations with incomplete past | 15.164% | 16.518% |
| Samples containing at least one incomplete-history agent | 17,276 | 4,705 |
| Fraction of samples containing incomplete history | 57.810% | 61.064% |

In prediction-challenge mode, one dataset sample corresponds to a prediction
target agent at a particular sample time rather than to a unique temporal scene
window. Multiple prediction targets may therefore correspond to overlapping
portions of the same source scene.

The same physical traffic participant may also appear in many dataset samples.
Accordingly, "agent participations" should not be interpreted as counts of
unique physical vehicles.

The compiled non-ego car counts are slightly larger in prediction-challenge
mode than in repository-default mode. This is consistent with the repository
logic that preserves agents required by the prediction-challenge split even when
ordinary spatial filtering would otherwise be applied.

Incomplete-history statistics are reported because the repository defaults to
`require_full_past=False`. A non-ego participant is counted as having an
incomplete past when one or more of its four past visibility steps are missing.
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