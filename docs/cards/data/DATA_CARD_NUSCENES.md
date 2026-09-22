# D-01 — nuScenes Data Card for STRIVE

> **Card ID:** D-01  
> **Card type:** Data Card  
> **Status:** Complete for the public STRIVE release  
> **Dataset:** nuScenes as consumed by STRIVE  
> **Primary downstream artifact:** M-01 Main Traffic Model Card  
> **Scope:** nuScenes metadata, annotations, trajectories, and map expansion used by STRIVE. This card does not document the full raw-sensor nuScenes dataset.

---

## 1. Summary

### 1.1 Dataset summary

STRIVE uses the **nuScenes** autonomous-driving dataset as the source of real multi-agent traffic scenes from which it learns a traffic prior and initializes adversarial scenario generation. The public STRIVE release requires the nuScenes **metadata/annotations and map expansion**; its README explicitly states that raw camera, lidar, and radar payloads are not required for training/testing the traffic model or for scenario generation.

Within STRIVE, nuScenes scenes are converted into variable-size multi-agent graph examples. Each graph contains the ego vehicle and selected traffic agents, their recent motion, vehicle dimensions and semantic category, plus local semantic-map context. The main-paper configuration uses **cars and trucks**.

### 1.2 Why this dataset matters to STRIVE

nuScenes serves four roles in STRIVE:

1. **Training data** for the learned graph-based traffic prior.
2. **Held-out evaluation data** for reconstruction and future-trajectory sampling.
3. **Initialization data** for adversarial and solution optimization.
4. **Map context** for drivable-area, parking-area, road-divider, and lane-divider reasoning.

The downstream generated scenarios are therefore not independent of nuScenes: they are derived from real nuScenes initial conditions and constrained by a traffic model trained on nuScenes.

### 1.3 Key facts

| Property | STRIVE value / behavior |
|---|---|
| Upstream dataset | nuScenes |
| Main version | `v1.0-trainval` |
| Mini support | Yes (`v1.0-mini`) |
| Raw sensor payload required by STRIVE | No; public README says metadata + map expansion are sufficient |
| Native STRIVE trajectory timestep | `0.5 s` (2 Hz) |
| Default past horizon | 4 steps = 2 s |
| Default future horizon | 12 steps = 6 s |
| Total default sequence length | 16 steps = 8 s |
| Main-paper agent categories | `car`, `truck` |
| Default local map crop | 256 × 256 |
| Default map layers | `drivable_area`, `carpark_area`, `road_divider`, `lane_divider` |
| Default map bounds (m) | `[-17.0, -38.5, 60.0, 38.5]` |
| nuScenes devkit pinned by STRIVE | `1.1.5` |
| Default challenge-split mode | Disabled |

---

## 2. Authorship

### 2.1 Dataset publisher

nuScenes is published by Motional / nuTonomy. The official nuScenes site describes the dataset as 1,000 driving scenes of approximately 20 seconds each, collected in Boston and Singapore, with detailed maps and 3D object annotations.

### 2.2 STRIVE data integration authors

The STRIVE project was published by Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, and Or Litany in CVPR 2022. The STRIVE-specific nuScenes loader and preprocessing code are part of the NVIDIA Research public repository.

### 2.3 Dataset owners and maintainers

- **Upstream dataset:** nuScenes / Motional.
- **STRIVE integration:** public STRIVE repository.
- **This card:** project-local documentation of the exact nuScenes view consumed by STRIVE.

Questions about upstream licensing, access, or dataset content should be resolved using the official nuScenes documentation rather than this card.

### 2.4 Funding and institutional context

The STRIVE paper lists affiliations with Stanford University, NVIDIA, the University of Toronto, and the Vector Institute. This card does not infer additional funding or sponsorship beyond what is explicitly documented in the paper/repository.

---

## 3. Dataset Overview

### 3.1 Dataset version

The main STRIVE configuration uses:

```yaml
data_dir: ./data/nuscenes
data_version: trainval
```

The loader supports `trainval` and `mini`.

The expected nuScenes metadata object is instantiated as:

```text
v1.0-<data_version>
```

therefore the primary release configuration corresponds to `v1.0-trainval`.

### 3.2 Dataset scope

This card covers only the parts of nuScenes that STRIVE uses:

- scene/sample metadata;
- ego pose metadata;
- 3D sample annotations;
- object categories and dimensions;
- map/location metadata;
- nuScenes map expansion;
- prediction challenge split metadata when explicitly enabled.

The STRIVE README states that **only metadata and the map expansion are required** for its traffic-model and scenario-generation workflow.

### 3.3 Unit of data

The upstream nuScenes unit is a scene/sample/annotation hierarchy. STRIVE converts it into a **sequence-level multi-agent scene graph**.

For non-challenge-split operation, one STRIVE dataset item is identified by:

```text
(scene_name, sequence_start_index)
```

For official prediction-challenge operation, the item additionally identifies the prediction-target instance.

### 3.4 Data modalities used by STRIVE

STRIVE uses:

- ego trajectory from nuScenes ego poses;
- non-ego annotated agent trajectories;
- agent size (`length`, `width`);
- semantic category;
- timestamps;
- scene-to-map location;
- rasterized semantic map layers;
- optional prediction-challenge instance/sample identifiers.

It does not require camera images, raw lidar point clouds, or radar returns for the workflow documented by the public STRIVE README.

### 3.5 Sensitive or restricted data

Although the upstream dataset includes sensor recordings of public-road environments, STRIVE's documented traffic-model workflow operates on metadata, annotations, and maps. This reduces direct exposure to raw visual content, but it does not remove the need to comply with nuScenes access and license terms.

### 3.6 Dataset maintenance

The upstream dataset and devkit are maintained independently of STRIVE. The STRIVE release pins `nuscenes-devkit==1.1.5`; upgrading the devkit should be treated as a reproducibility change and re-profiled.

---

## 4. Example of Data Points

### 4.1 STRIVE scene example

A processed STRIVE scene contains a variable number of agents. Node 0 is normally the ego vehicle. Additional nodes represent selected nuScenes traffic agents that satisfy the configured category and visibility/filtering rules.

Conceptually:

```text
scene graph
├── ego
│   ├── past:   [4, 6]
│   ├── future: [12, 6]
│   └── size:   [length, width]
├── agent 1
│   ├── category: car/truck/...
│   ├── past:   [4, 6]
│   ├── future: [12, 6]
│   └── size:   [length, width]
├── ...
└── map index / local map observations
```

Actual tensor shapes depend on the number of agents present in each scene.

### 4.2 Agent state representation

The loader constructs a 6-D state:

```text
(x, y, heading_x, heading_y, speed, heading_change_rate)
```

where the heading is stored as a unit-vector representation using cosine/sine components.

### 4.3 Vehicle attributes

Each agent has:

```text
(length, width)
```

plus a one-hot semantic category representation derived from the configured STRIVE category set.

### 4.4 Temporal structure

Defaults from `src/utils/config.py`:

- `past_len = 4`
- `future_len = 12`
- `dt = 0.5 s`

Thus the default sample contains 2 seconds of past motion and 6 seconds of future motion.

### 4.5 Map context

Default map settings:

```yaml
map_obs_size_pix: 256
map_obs_bounds: [-17.0, -38.5, 60.0, 38.5]
map_layers:
  - drivable_area
  - carpark_area
  - road_divider
  - lane_divider
```

The bounds are expressed in meters in the agent-centered observation frame.

---

## 5. Motivations & Intentions

### 5.1 Motivation for using nuScenes

STRIVE requires real multi-agent motion and detailed map context to learn a prior over plausible traffic behavior. nuScenes provides annotated urban scenes, map information, multiple vehicle classes, and a standardized scene structure suitable for this purpose.

### 5.2 Intended uses in STRIVE

The STRIVE-specific dataset view is intended for:

- traffic-model training;
- traffic-model reconstruction/sampling evaluation;
- refinement optimization of sampled traffic;
- initialization of adversarial scenario generation;
- generation of "regular" comparison scenes for planner evaluation;
- map-aware collision and plausibility checks.

### 5.3 Out-of-scope uses

This dataset view should not be treated as:

- a dataset of real-world traffic accidents;
- an estimate of accident frequency or collision prevalence;
- a complete representation of global driving behavior;
- a safety-certification dataset;
- a raw-sensor perception benchmark in the STRIVE workflow.

### 5.4 Intended users

Researchers and engineers studying trajectory prediction, traffic modeling, adversarial scenario generation, planning robustness, and simulation-based autonomous-vehicle evaluation.

---

## 6. Access, Retention & Wipeout

### 6.1 Access requirements

Users obtain nuScenes through the official nuScenes distribution and separately obtain the map expansion. STRIVE does not redistribute the complete upstream dataset.

### 6.2 Expected local directory structure

The STRIVE README shows the following structure:

```text
data/nuscenes/
└── trainval/
    ├── v1.0-trainval/
    │   └── *.json
    └── maps/
        ├── basemap/
        ├── expansion/
        ├── prediction/
        └── *.png
```

The mini dataset is supported using the corresponding version directory.

### 6.3 Redistribution constraints

Redistribution and use of nuScenes remain subject to the official nuScenes terms. Do not infer redistribution rights from the MIT license on STRIVE source code.

### 6.4 Retention

The public STRIVE repository does not define an independent retention period for a local nuScenes installation.

### 6.5 Deletion / wipeout

A locally downloaded copy can be removed from the configured `data_dir`. Deletion of local files does not modify any upstream nuScenes account, registration, or source distribution.

---

## 7. Provenance

### 7.1 Upstream source

Official source: [nuScenes](https://www.nuscenes.org/).

The official site describes:

- 1,000 scenes;
- approximately 20 seconds per scene;
- Boston and Singapore collection locations;
- detailed map information;
- manually annotated 3D bounding boxes.

### 7.2 Relationship to source

STRIVE does not create a separate raw copy of nuScenes. It loads upstream metadata and transforms the annotations/poses into model-ready trajectories, scene graphs, normalized attributes, and local map observations.

### 7.3 Collection process

The underlying collection process is owned and documented by nuScenes. STRIVE consumes the resulting annotations and maps rather than defining the original sensor-collection protocol.

### 7.4 Geographic coverage

nuScenes includes Boston and Singapore. The STRIVE loader distinguishes map/location names and, by default, applies an x-axis reflection to Singapore trajectories so that left/right-driving orientation is normalized for model learning.

### 7.5 Temporal coverage

The upstream scenes are approximately 20 seconds long. STRIVE works at a `0.5 s` timestep (2 Hz) and slices scenes into shorter sequence windows.

### 7.6 Versioning

Reproducibility should record all of:

- nuScenes release (`v1.0-trainval` or `v1.0-mini`);
- nuScenes devkit version;
- STRIVE repository commit;
- STRIVE configuration;
- profiler output.

---

## 8. Collection & Selection Criteria

### 8.1 Scene selection

For `v1.0-trainval`, STRIVE's default loader behavior repurposes the official nuScenes splits:

- STRIVE `train` and `val` are drawn from the official nuScenes **train** scenes.
- STRIVE `test` uses the official nuScenes **val** scenes.
- By default, the first `val_size` scenes of the official train list are reserved for STRIVE validation.
- `val_size` defaults to 200 in the loader.
- With the standard 700-scene official train split, this yields 500 STRIVE training scenes and 200 STRIVE validation scenes; the 150 official validation scenes become STRIVE test scenes.
- `randomize_val=True` switches to repository-defined precomputed validation indices for supported sizes (200 or 400).

If `use_challenge_splits=True`, STRIVE instead follows the prediction-challenge instance/sample definitions.

### 8.2 Agent selection

The loader supports these high-level categories:

```text
car
truck
bus
motorcycle
trailer
cyclist
pedestrian
emergency
construction
```

The main-paper configuration uses:

```text
car, truck
```

Mappings include:

```text
vehicle.car      -> car
vehicle.truck    -> truck
vehicle.bus      -> bus
vehicle.bicycle  -> cyclist
human.pedestrian -> pedestrian
...
```

### 8.3 Trajectory eligibility

For a normal sequence item, STRIVE keeps an agent only when it has an annotation at the final frame of the past context. Missing trajectory values are represented with `NaN` and accompanied by visibility masks.

The optional `require_full_past` mode imposes a stricter history requirement.

### 8.4 Map eligibility

The release requires the nuScenes map expansion. Non-ego agent frames are filtered using drivable-area and car-park-area raster checks unless prediction-challenge behavior overrides that filtering.

### 8.5 Scenario-generation selection

Other STRIVE configurations may further control:

- split (`train`, `val`, `test`);
- `val_size`;
- randomized validation subsets;
- `seq_interval`;
- agent types;
- challenge-split use.

Those are downstream experiment settings, not intrinsic properties of the upstream nuScenes dataset.

---

## 9. Processing, Transformation & Labeling

### 9.1 Trajectory preprocessing

For each trajectory, STRIVE derives:

- position `(x, y)`;
- heading angle and heading vector;
- speed from timestamped positions;
- acceleration for diagnostics;
- heading-change rate;
- heading acceleration for diagnostics.

The model state retained by the traffic dataset is six-dimensional:

```text
(x, y, cos(heading), sin(heading), speed, heading_change_rate)
```

### 9.2 Coordinate transformations

For Singapore scenes, `flip_singapore=True` by default. The loader reflects the y-coordinate relative to map height and flips the heading sine term. This normalizes left-hand traffic orientation relative to other map locations.

### 9.3 Map preprocessing

STRIVE constructs local semantic raster context from selected nuScenes map layers. Default observation parameters are defined in `src/utils/config.py`.

### 9.4 Category mapping

The loader maps nuScenes category strings to configurable STRIVE high-level categories. With `reduce_cats=True`, some upstream categories are collapsed into broader car/truck/cyclist/pedestrian-style groups.

### 9.5 Filtering

For non-challenge data, non-ego frames are retained only when:

- at least 30% of the agent box lies on the `drivable_area` layer; and
- if `carpark_area` is available, less than 30% of the box lies on that layer.

Agents with no valid remaining frames are discarded.

This threshold comes directly from the public STRIVE loader implementation.

### 9.6 Noise or augmentation

The released traffic-training configuration sets:

```yaml
data_noise_std: 0.01
```

which adds Gaussian noise to model input state through the dataset path.

### 9.7 Derived labels

nuScenes provides the underlying semantic categories and annotations. STRIVE derives motion quantities, visibility masks, sequence membership, normalized categories, and scene-graph structure. Collision-mode labels used later in STRIVE are **not** part of D-01; they belong to generated scenario analysis.

---

## 10. Dataset Structure & Schema

### 10.1 Raw upstream files used

Relevant nuScenes metadata tables include, at minimum, information reachable through:

- `scene`
- `sample`
- `sample_annotation`
- `instance`
- `category`
- `log`
- `sample_data`
- `ego_pose`

Map expansion files are also required.

### 10.2 STRIVE loader

Primary loader:

```text
src/datasets/nuscenes_dataset.py
```

Related map and utility code:

```text
src/datasets/map_env.py
src/datasets/nuscenes_utils.py
src/datasets/utils.py
```

### 10.3 Scene graph schema

A model-ready item contains:

- variable number of agent nodes;
- past state tensors;
- future state tensors;
- semantic one-hot vectors;
- agent length/width;
- visibility masks;
- map index and local map context;
- graph batch/connectivity information.

### 10.4 Core tensor shapes

Using:

- `N` = agents retained in one sequence;
- `P` = past steps;
- `F` = future steps;
- `S=6` = state dimension;
- `C` = configured semantic classes;

representative structures are:

```text
past       [N, P, 6]
future     [N, F, 6]
length/width [N, 2]
semantic   [N, C]
past visibility   [N, P]
future visibility [N, F]
```

Exact graph fields should be confirmed against the repository revision used for the experiment.

### 10.5 Missing-data representation

The loader aligns incomplete agent tracks to the ego timeline using `NaN` for unavailable states. Visibility masks distinguish usable and missing frames. Derived speed can also invalidate an isolated observed position when there is insufficient temporal context.

---

## 11. Quantitative Analysis

### 11.1 Upstream dataset counts

Official nuScenes documentation reports:

- 1,000 scenes total;
- standard train/val/test split sizes of 700 / 150 / 150 scenes;
- approximately 20 seconds per scene.

The `v1.0-trainval` package contains the annotated train and validation portion used by STRIVE.

### 11.2 STRIVE-effective counts

For the standard full release and default `val_size=200`, the loader's scene-selection logic corresponds to:

| STRIVE split | Upstream scene source | Expected scene count |
|---|---|---:|
| `train` | official train minus first 200 reserved scenes | 500 |
| `val` | first 200 official train scenes | 200 |
| `test` | official validation scenes | 150 |

These are **configuration-derived scene counts**, not measurements of retained agents or valid trajectories.

The exact number of sequence examples depends on the number of samples in each selected scene, `past_len`, `future_len`, and `seq_interval`. The profiler calculates this from the installed metadata.

### 11.3 Distribution by agent category

The profiler reports:

- annotation count by raw nuScenes category;
- unique instance count by category;
- counts for the main STRIVE categories (`vehicle.car`, `vehicle.truck`).

These counts are upstream annotation/instance statistics. They are not identical to the number of model graph nodes after STRIVE's map and temporal filtering.

### 11.4 Distribution by location

The profiler joins `scene.log_token` to `log.location` and reports scene counts per map/location.

### 11.5 Scene and trajectory statistics

The profiler computes:

- scene count;
- sample count;
- annotation count;
- instance count;
- per-scene sample-count summary;
- observed timestamp-delta summary;
- candidate sequence-window counts for STRIVE splits when the nuScenes devkit split definitions are available.

### 11.6 Data-quality checks

The profiler flags:

- missing required JSON tables;
- malformed/unparseable JSON;
- duplicate tokens;
- broken scene sample chains;
- non-monotonic timestamps;
- missing map/prediction metadata;
- mismatches between declared and observed scene sample counts.

### 11.7 Profiler

Run from the repository root:

```bash
python tools/profile_nuscenes_strive.py \
  --nuscenes-root ./data/nuscenes/trainval \
  --output ./out/nuscenes_strive_profile.yaml
```

To update the machine-readable card metadata directly:

```bash
python tools/profile_nuscenes_strive.py \
  --nuscenes-root ./data/nuscenes/trainval \
  --metadata ./metadata/data/nuscenes_strive.yaml
```

The profiler does not require raw sensor files.

---

## 12. Validation & Quality Assurance

### 12.1 Structural validation

Before use, validate that:

- the selected `v1.0-*` metadata directory exists;
- required JSON tables parse;
- map expansion files exist;
- scene/sample links are internally consistent;
- the configured version matches the directory.

### 12.2 Semantic validation

Recommended checks include:

- configured STRIVE categories occur in `sample_annotation`;
- scene location names correspond to available map assets;
- timestamps are monotonic within scenes;
- annotation dimensions are non-negative;
- car/truck coverage is non-zero.

### 12.3 Leakage considerations

STRIVE intentionally defines its own train/validation/test interpretation over nuScenes for trajectory modeling. Do not assume that a model described as "validation" or "test" in STRIVE is using the same split semantics as another nuScenes benchmark.

Generated scenarios should also be tracked separately from their source scenes to prevent downstream planner-tuning experiments from accidentally reusing evaluation source material.

### 12.4 Reproducibility checks

Archive:

- the companion YAML;
- profiler output;
- exact STRIVE config files;
- repository commit hash;
- nuScenes version;
- nuScenes devkit version.

---

## 13. Known Applications & Benchmarks

### 13.1 STRIVE traffic-model training

D-01 is the source dataset for M-01, the graph-based conditional traffic model.

Released command:

```bash
python src/train_traffic.py --config ./configs/train_traffic.cfg
```

### 13.2 Traffic-model evaluation

The release evaluates the trained model on a held-out STRIVE nuScenes split and supports reconstruction, sampling, displacement-error, and collision-rate analysis.

By default, this is not restricted to the official nuScenes prediction-challenge trajectories.

### 13.3 Scenario generation

Real nuScenes subsequences are used to initialize adversarial scenario generation. STRIVE optimizes in the learned traffic-model latent space rather than directly treating D-01 as an accident dataset.

### 13.4 Planner evaluation and tuning

Generated scenarios derived from D-01 are later used for planner stress testing and parameter tuning. Those derived artifacts require their own data card (D-02).

---

## 14. Known Limitations

### 14.1 Geographic limitations

nuScenes covers specific locations in Boston and Singapore. It does not represent global road geometry, traffic law, weather, driver culture, vehicle fleet, or infrastructure.

### 14.2 Agent-class limitations

The main STRIVE traffic model focuses on cars and trucks even though the loader supports additional categories. This narrows the behavior distribution represented by M-01.

### 14.3 Sampling and temporal limitations

STRIVE works on a 2 Hz state representation with finite history/future windows. Fast transient behavior may be under-resolved relative to higher-frequency control systems.

### 14.4 Behavior coverage

Rare safety-critical behavior is inherently sparse in real-world data—the motivation for STRIVE itself. The learned prior cannot represent behaviors absent or poorly represented in D-01.

### 14.5 Map and annotation limitations

Agent boxes, semantic maps, and derived kinematics are approximations. STRIVE's drivable-area/car-park filtering can exclude observations based on map rasterization and overlap thresholds.

### 14.6 STRIVE-specific limitations

The effective model dataset is altered by:

- category selection;
- scene split logic;
- temporal slicing;
- Singapore flipping;
- map filtering;
- missing-data handling;
- normalization;
- optional input noise.

Consequently, statistics from the upstream nuScenes website are not sufficient to describe the actual examples seen by STRIVE.

---

## 15. Ethical, Safety & Societal Considerations

### 15.1 Privacy considerations

The documented STRIVE workflow does not require raw camera imagery. Nevertheless, users remain responsible for complying with upstream data-access and privacy requirements.

### 15.2 Safety considerations

Neither D-01 nor models trained on it provide a guarantee of safe autonomous driving. Dataset coverage is necessarily incomplete, especially for rare and hazardous interactions.

### 15.3 Bias and representativeness

Bias can arise from:

- collection geography;
- route and time-of-day distribution;
- annotation policy;
- selected vehicle categories;
- STRIVE's map filtering;
- source split construction.

### 15.4 Misuse risks

Do not use D-01 or downstream STRIVE scenarios as direct evidence of real-world collision rates, legal responsibility, demographic risk, or safety certification without additional validated evidence.

---

## 16. Licensing & Terms

### 16.1 nuScenes license / terms

nuScenes is distributed under its own terms and is described by the official site as free for non-commercial use, with commercial licensing handled separately by Motional. Always consult the current official terms before redistribution or commercial use.

### 16.2 STRIVE code license

The public STRIVE source repository is released under the MIT License.

### 16.3 Derived-artifact licensing

The STRIVE README states that the released pretrained models and generated scenarios are derived from nuScenes and are separately licensed under `CC-BY-NC-SA-4.0`.

That statement applies to those STRIVE derivative artifacts; it does not replace the upstream nuScenes terms for D-01.

---

## 17. Reproducibility & Maintenance

### 17.1 Required versions

Public release environment includes:

```text
Python 3.6
PyTorch 1.9
CUDA 11.1
nuscenes-devkit 1.1.5
```

The README says this was the environment primarily tested by the authors.

### 17.2 Required configuration

At minimum, record:

```yaml
data_dir: ./data/nuscenes
data_version: trainval
past_len: 4
future_len: 12
agent_types: [car, truck]
map_obs_size_pix: 256
map_obs_bounds: [-17.0, -38.5, 60.0, 38.5]
map_layers:
  - drivable_area
  - carpark_area
  - road_divider
  - lane_divider
use_challenge_splits: false
```

Also record split-specific values such as `val_size`, `randomize_val`, and `seq_interval` for each experiment.

### 17.3 Companion metadata

Machine-readable facts:

```text
metadata/data/nuscenes_strive.yaml
```

Static/configuration facts belong directly in the YAML. Environment-specific counts belong under the profiler-populated `profile.measured` section.

### 17.4 Quantitative profiler

Profiler:

```text
tools/profile_nuscenes_strive.py
```

The profiler is designed for the metadata-only installation documented by STRIVE.

### 17.5 Update policy

Revisit D-01 when any of the following changes:

- nuScenes version;
- nuScenes devkit;
- category mapping;
- map layers/bounds;
- split logic;
- temporal horizon;
- frame filtering;
- missing-data rules;
- coordinate transformation;
- data augmentation.

---

## 18. Relationships

### 18.1 Upstream

```text
nuScenes
```

### 18.2 Downstream

```text
M-01 — Main Traffic Model
```

### 18.3 Dependency chain

```text
D-01  nuScenes Data Card
  │
  ▼
M-01  Main Traffic Model Card
```

D-01 also provides the real-world initialization source used later by STRIVE's scenario-generation components.

---

## 19. Terms of Art

### 19.1 Scene

An upstream nuScenes driving snippet of approximately 20 seconds. STRIVE selects scenes according to its split logic and slices them into shorter sequences.

### 19.2 Sample

An annotated nuScenes timestamp/keyframe. STRIVE aligns ego and non-ego trajectories to the sample timeline.

### 19.3 Agent

The ego vehicle or an annotated traffic participant retained by the configured category/filtering rules.

### 19.4 Scene graph

STRIVE's variable-size graph representation of all retained agents in one temporal sequence. Agents are graph nodes and are jointly processed by the traffic model.

### 19.5 Past / future trajectory

The temporal context and prediction target used by the traffic model. Defaults are 4 past steps and 12 future steps at 2 Hz.

### 19.6 Map crop

An agent-centered raster observation constructed from selected nuScenes semantic map layers.

---

## 20. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.  
   https://openaccess.thecvf.com/content/CVPR2022/html/Rempe_Generating_Useful_Accident-Prone_Driving_Scenarios_via_a_Learned_Traffic_Prior_CVPR_2022_paper.html

2. STRIVE public repository.  
   https://github.com/nv-tlabs/STRIVE

3. nuScenes official site.  
   https://www.nuscenes.org/

4. nuScenes devkit tutorial.  
   https://www.nuscenes.org/tutorials/nuscenes_tutorial.html

5. nuScenes devkit split definitions.  
   https://github.com/nutonomy/nuscenes-devkit/blob/master/python-sdk/nuscenes/utils/splits.py

6. STRIVE implementation files used for this card:
   - `src/datasets/nuscenes_dataset.py`
   - `src/utils/config.py`
   - `configs/train_traffic.cfg`
   - `configs/test_traffic.cfg`
   - `requirements.txt`
   - `README.md`

---

## 21. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed D-01 card for the public STRIVE release; added companion metadata/profiler contract. |
