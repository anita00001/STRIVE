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

This data product is derived from the nuScenes autonomous-driving dataset.
STRIVE uses the `v1.0-trainval` release.

The upstream nuScenes dataset contains 1,000 driving scenes, each approximately
20 seconds long, collected in Boston and Singapore. The complete upstream
dataset contains multimodal sensor data, annotations, ego-pose information,
and semantic maps.

STRIVE does not expose the complete multimodal nuScenes record to its learned
traffic model. For the traffic-data pipeline documented here, STRIVE primarily
uses:

- sample and scene metadata;
- ego poses;
- annotated traffic-agent positions, orientations, dimensions, categories,
  and instance identities;
- semantic map information; and
- nuScenes prediction-challenge metadata when
  `use_challenge_splits=True`.

The traffic model itself does not consume raw camera images, lidar point
clouds, or radar measurements as model features.

The resulting STRIVE representation is therefore a derived trajectory,
scene-graph, and semantic-map representation rather than a copy of the full
nuScenes sensor dataset.

### Canonical nuScenes Reference

Holger Caesar, Varun Bankiti, Alex H. Lang, Sourabh Vora,
Venice Erin Liong, Qiang Xu, Anush Krishnan, Yu Pan,
Giancarlo Baldan, and Oscar Beijbom.

*nuScenes: A Multimodal Dataset for Autonomous Driving.*

IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR),
2020, pp. 11621-11631.

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

### 9.1 Spatial Filtering of Non-Ego Vehicle Frames

STRIVE applies map-based filtering to non-ego vehicle annotation frames before
constructing the model-facing trajectory representation.

For ordinary car/truck tracks, an annotated frame is retained when both of the
following conditions hold:

\[
f_{\mathrm{drivable}} \ge 0.30
\]

and

\[
f_{\mathrm{carpark}} < 0.30,
\]

where the overlap fractions are computed between the vehicle footprint and the
corresponding rasterized nuScenes map layers.

Therefore, the filtering rule should not be described as simply removing frames
that have "more than 30% overlap outside the drivable area." The implementation
specifically requires at least 30% overlap with the drivable-area layer and less
than 30% overlap with the carpark-area layer.

Frames failing either condition are omitted from the aligned trajectory before
motion quantities are derived.

If every frame of a non-ego track is unavailable after this processing, the
track is not retained in the postprocessed STRIVE scene representation.

#### Prediction-Challenge Exception

When `use_challenge_splits=True`, STRIVE preserves tracks containing agents
required by the nuScenes prediction-challenge split.

For such tracks, the ordinary drivable-area/carpark spatial filtering step is
bypassed so that required prediction targets remain available.

This exception affects only tracks required by the challenge split; ordinary
non-target tracks continue to use the spatial filtering rule above.

### 9.2 Observed Filtering Attrition

The effect of STRIVE's filtering was measured programmatically using the
repository-default car/truck data pipeline.

For training and validation combined:

| Statistic | Value |
|---|---:|
| Raw non-ego tracks | 26,655 |
| Retained non-ego tracks | 12,335 |
| Tracks absent after preprocessing | 14,320 |
| Track-drop fraction | 53.724% |
| Raw non-ego annotation frames | 486,133 |
| Spatially accepted annotation frames | 239,932 |
| Spatially rejected annotation frames | 246,201 |
| Spatial rejection fraction | 50.645% |
| Postprocessed visible-state frames | 239,311 |

"Spatially rejected annotation frames" refers specifically to the
drivable-area/carpark predicate described above. It should not be interpreted
as the total number of unavailable model states.

The retained-track count matches the previously profiled repository-default
compiled non-ego population:

- 10,377 car tracks;
- 1,958 truck tracks;
- 12,335 total retained non-ego tracks.

#### Additional Visibility Loss After Spatial Filtering

Spatial acceptance does not guarantee that the final state will be marked
visible.

After spatial filtering, STRIVE derives motion quantities using finite
differences. Of the 239,932 spatially accepted annotation frames in
repository-default train and validation data, 239,311 become visible
postprocessed state frames.

The difference is 621 frames, approximately 0.259% of spatially accepted
frames.

This occurs because STRIVE defines postprocessed visibility using the
availability of the derived speed value rather than spatial acceptance alone.

#### Effect of Prediction-Challenge Preservation

For prediction-challenge-mode training and validation combined:

| Statistic | Value |
|---|---:|
| Raw non-ego tracks | 26,655 |
| Tracks using ordinary spatial filtering | 23,393 |
| Tracks bypassing spatial filtering | 3,262 |
| Fraction of raw tracks bypassing filtering | 12.238% |
| Retained non-ego tracks | 12,338 |
| Spatially accepted annotation frames | 240,931 |
| Spatially rejected annotation frames | 245,202 |
| Postprocessed visible-state frames | 240,314 |

This explains the small increase in retained car tracks observed in the
prediction-challenge profile relative to repository-default mode.

The repository-default profile contains 10,377 retained car tracks, whereas the
prediction-challenge profile contains 10,380. Truck counts remain unchanged at
1,958.

### 9.3 Derived Motion Quantities

STRIVE aligns non-ego trajectories to the ego-vehicle timeline and represents
unavailable states using missing values.

It then derives motion quantities from the trajectory sequence using finite
differences.

For each agent, the six-dimensional state is:

\[
(x,\ y,\ h_x,\ h_y,\ s,\ \dot{h}),
\]

where:

- \(x,y\) are position;
- \(h_x,h_y\) are the heading-vector components;
- \(s\) is scalar speed; and
- \(\dot{h}\) is heading-change rate.

Speed is obtained from finite-difference velocity computed from position.
Heading-change rate is derived from the heading-angle sequence.

The preprocessing code also computes acceleration-related quantities internally,
including acceleration magnitude and heading acceleration, although these are
not included in the six-dimensional model-facing state returned by the standard
`NuScenesDataset` scene graph.

A frame is marked visible in the postprocessed representation when its derived
speed is available.

### 9.4 Incomplete Trajectory Histories

The repository default is:

`require_full_past=False`

An agent therefore does not need to have all four historical states available
to appear in a model sample.

The dataset loader requires the agent to have a valid state at the final
timestep of the past window. Earlier historical states may remain unavailable
and are represented through `past_vis`.

The profiling results showed that incomplete histories are non-negligible.

For repository-default mode:

| Split | Non-ego participations with incomplete past | Fraction |
|---|---:|---:|
| Train | 9,979 | 9.603% |
| Validation | 4,395 | 10.105% |

For prediction-challenge mode:

| Split | Non-ego participations with incomplete past | Fraction |
|---|---:|---:|
| Train | 53,038 | 15.164% |
| Validation | 14,956 | 16.518% |

These are sample-level agent participations, not counts of unique physical
vehicles.

### 9.5 Singapore Coordinate Transformation

STRIVE flips Singapore maps and trajectories about the x-axis.

For Singapore scenes, the transformation is applied consistently to the map
representation and trajectory coordinates so that the driving orientation is
represented consistently with the convention used by the STRIVE model.

This transformation affects interpretation of the processed coordinate frame
and must therefore be accounted for when reconstructing or visualizing STRIVE
scenes.

The public repository enables this behavior by default through
`flip_singapore=True`.

### 9.6 Normalization

STRIVE applies mean/std normalization according to

\[
x_{\mathrm{norm}} = \frac{x-\mu}{\sigma}.
\]

For the car/truck traffic model, the repository defines the following
normalization constants:

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

These constants are defined in:

`src/datasets/utils.py`

under:

`NUSC_NORM_STATS[('car', 'truck')]`.

The state normalizer applies the six state statistics to `past`, `past_gt`,
`future`, and `future_gt`.

A separate vehicle-attribute normalizer applies the length and width statistics
to `lw`.

The public repository provides these constants directly. The currently reviewed
source does not establish the exact procedure or exact source subset originally
used by the authors to estimate every normalization constant.

They are therefore documented here as repository-defined normalization
parameters rather than statistics independently re-estimated by this Data Card
profiling process.

### 9.7 Training-Time Noise Augmentation

The current:

`configs/train_traffic.cfg`

specifies:

`data_noise_std: 0.01`

During construction of training samples, STRIVE first normalizes the data and
then adds Gaussian noise with standard deviation 0.01 to:

- `past`;
- `future`; and
- normalized vehicle dimensions `lw`.

The noise is therefore applied in normalized feature space rather than directly
in physical units such as meters or meters per second.

The corresponding:

- `past_gt`; and
- `future_gt`

remain clean normalized copies and do not receive this perturbation.

After trajectory noise is added, STRIVE:

- renormalizes the `heading_x` and `heading_y` components to unit length; and
- clamps the first two normalized position components to a minimum value of
  `0.0`.

Gaussian noise with the same configured standard deviation is also added to the
normalized vehicle-attribute tensor `lw`.

The validation dataset does not receive this augmentation.
`train_traffic.py` passes `data_noise_std` to the training `NuScenesDataset`,
while the validation dataset uses the constructor default:

`noise_std=0.0`

Accordingly, this noise should be understood as training-time augmentation
rather than an intrinsic property of the underlying STRIVE-derived dataset.

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
ordinary spatial filtering would otherwise be applied.<br>
Incomplete-history statistics are reported because the repository defaults to
`require_full_past=False`. A non-ego participant is counted as having an
incomplete past when one or more of its four past visibility steps are missing.
---

## 14. Data Quality and Filtering

STRIVE applies substantial filtering to the raw car/truck annotation tracks
available in the selected nuScenes scenes.

For ordinary, non-challenge agents, an annotated frame is retained when:

\[
f_{\mathrm{drivable}} \ge 0.30
\]

and

\[
f_{\mathrm{carpark}} < 0.30.
\]

Here the overlap fractions are computed between the vehicle footprint and the
corresponding rasterized map layers.

Across repository-default training and validation data, this spatial predicate
rejects 246,201 of 486,133 raw non-ego annotation frames, or approximately
50.645%.

At the track level, 14,320 of 26,655 raw non-ego tracks have no retained
postprocessed track, corresponding to approximately 53.724%.

These values describe the STRIVE preprocessing pipeline and should not be
interpreted as errors in the upstream nuScenes annotations. The filtering rule
deliberately selects traffic states that satisfy STRIVE's map-based criteria.

### Post-Spatial-Filtering Visibility

Spatial acceptance is not identical to final model-state visibility.

STRIVE computes speed using finite differences and defines visibility from the
availability of the resulting speed value. Across repository-default train and
validation data, 239,932 annotation frames satisfy the map-based spatial
predicate, while 239,311 are visible in the postprocessed representation.

The difference is 621 frames, or approximately 0.259% of spatially accepted
frames.

### Prediction-Challenge Exception

When `use_challenge_splits=True`, tracks containing required prediction targets
bypass the ordinary spatial filter.

Across prediction-challenge-mode training and validation:

- 3,262 of 26,655 raw non-ego tracks contain a target that triggers this
  exception;
- those tracks represent approximately 12.238% of the raw non-ego tracks;
- 240,931 annotation frames are spatially accepted, compared with 239,932 in
  repository-default mode; and
- 12,338 non-ego tracks remain after preprocessing, compared with 12,335 in
  repository-default mode.

This explains the small increase in compiled-agent counts observed previously
for prediction-challenge mode.

---

## 15. Known Coverage Limitations

The main-paper training configuration focuses on cars and trucks.

Consequently, the primary traffic model does not represent the full diversity
of road users present in nuScenes.

The paper specifically identifies pedestrians and cyclists as important
extensions beyond the primary evaluation setting.

The dataset is also constrained by the geographic, environmental, behavioral,
and annotation coverage of nuScenes.

### Map-Based Selection of Traffic States

The STRIVE-derived dataset is not a neutral retention of every annotated
car/truck state available in the selected nuScenes scenes.

Its map-based preprocessing removes a substantial proportion of raw annotation
frames and complete tracks. In repository-default train and validation data,
approximately 50.645% of raw non-ego annotation frames fail the spatial
acceptance predicate and approximately 53.724% of raw non-ego tracks do not
remain as postprocessed tracks.

Consequently, the resulting model-training distribution emphasizes vehicles
that overlap sufficiently with STRIVE's rasterized drivable-area representation
and are not substantially within the carpark-area layer.

Coverage of parking-area activity, off-drivable-surface vehicles, and
annotations affected by map/annotation alignment is therefore intentionally
reduced.

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

### Differential Filtering by Category and Location

The measured filtering rates are not uniform across the profiled data.

For repository-default train and validation data combined:

| Group | Spatial frame rejection | Track drop |
|---|---:|---:|
| Cars | 52.489% | 55.190% |
| Trucks | 40.174% | 44.009% |
| Boston | 53.364% | 55.648% |
| Singapore | 41.366% | 47.463% |

These measurements show that the preprocessing step changes the composition of
the available dataset differently across the observed categories and
locations.

The profile alone does not establish why these differences occur. Possible
contributors include differences in driving context, parking prevalence,
annotation geometry, map geometry, and the interaction between vehicle
footprints and the rasterized filtering rule.

Accordingly, these rates should be treated as observed representation effects,
not as evidence that the upstream nuScenes data are intrinsically biased or
incorrect.

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

**STRIVE source commit:** `b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d`

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

### Upstream nuScenes Data

The official nuScenes Terms of Use state that, unless specifically labeled
otherwise, nuScenes datasets are provided under the Creative Commons
Attribution-NonCommercial-ShareAlike 4.0 International license
(CC BY-NC-SA 4.0), together with additional nuScenes/Motional Dataset Terms.

Where the additional Dataset Terms conflict with CC BY-NC-SA 4.0, the Dataset
Terms prevail.

The official terms also note that some third-party data may be governed by
different redistribution or reuse conditions. Users of this STRIVE-derived
representation remain responsible for complying with the applicable upstream
nuScenes terms.

The official terms reviewed for this Data Card state that they were last
updated on November 16, 2021. They were re-verified for this documentation on
September 18, 2026.

### STRIVE Code

The public STRIVE source repository is distributed under the MIT License.

### STRIVE-Released Derived Artifacts

The STRIVE README identifies the released pretrained models and generated
scenarios derived from nuScenes as licensed under CC-BY-NC-SA-4.0.

These licensing statements apply to different artifacts and should not be
treated as interchangeable:

- STRIVE source code: MIT;
- upstream nuScenes data: CC BY-NC-SA 4.0 plus the applicable Dataset Terms;
- STRIVE-released derived models/scenarios: licensing reported separately by
  the STRIVE repository.

---

## 22. References

1. Davis Rempe et al. *Generating Useful Accident-Prone Driving Scenarios via
   a Learned Traffic Prior.* CVPR 2022.

2. Holger Caesar et al. *nuScenes: A Multimodal Dataset for Autonomous
   Driving.* CVPR 2020, pp. 11621-11631.

3. nuScenes / Motional. *Terms of Use — Non-Commercial Use.*
   Official nuScenes dataset terms.

4. NVIDIA Toronto AI Lab. *STRIVE public source repository.*

---

## 23. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-09-18 | Initial data-card skeleton |
