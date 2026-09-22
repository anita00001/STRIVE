# S-01 — STRIVE System Card

> **Card ID:** S-01  
> **Card type:** System Card  
> **Status:** Complete for the public STRIVE release  
> **System:** STRIVE — Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior  
> **Primary repository:** `nv-tlabs/STRIVE`  
> **Inspected repository revision:** `b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d`

---

## 1. System Summary

### 1.1 System purpose

STRIVE is a research system for generating useful accident-prone autonomous-driving scenarios by optimizing traffic behavior under a learned multi-agent traffic prior.

Its central use case is **offline planner stress testing**:

1. learn plausible traffic behavior from nuScenes;
2. select feasible source scenes;
3. fit the latent representation to the source/planner initialization;
4. optimize surrounding-agent latents to cause a planner collision;
5. test whether a collision-free counterfactual planner trajectory still exists;
6. serialize, evaluate, cluster, and classify generated scenarios;
7. use challenging cases to analyze and improve planner behavior.

### 1.2 Core idea

STRIVE operates primarily in the latent space of a learned traffic model rather than directly manipulating raw trajectory points.

The core loop is:

```text
nuScenes context
     │
     ▼
learned conditional traffic prior
     │
     ▼
latent-space initialization fit
     │
     ▼
latent-space adversarial traffic optimization
     │
     ▼
planner collision
     │
     ▼
collision-free counterfactual solution search
```

This design attempts to keep generated traffic close to behavior represented by the learned prior while deliberately constructing difficult planner interactions.

### 1.3 System outputs

The public code can produce:

- traffic-model checkpoints and model-evaluation outputs;
- initialization, adversarial, and solution trajectories;
- generated scenario JSON;
- result partitions:
  - `adv_failed`;
  - `sol_failed`;
  - `adv_sol_success`;
- visualizations and videos;
- generated-scenario evaluation CSVs;
- collision-clustering artifacts;
- semantic cluster/classification CSVs;
- planner-evaluation CSVs;
- named rule-based planner configurations.

### 1.4 Primary research context

STRIVE accompanies:

**Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior**, CVPR 2022, by Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, and Or Litany.

The system is a research evaluation/generation framework rather than a deployed autonomous-driving stack.

---

## 2. System Scope

### 2.1 In-scope functionality

The public repository supports:

- nuScenes metadata/map ingestion;
- traffic-model training and testing;
- conditional multi-agent future sampling;
- traffic-sample refinement;
- feasibility filtering;
- initialization optimization;
- adversarial scenario generation;
- replay-planner attacks;
- rule-based-planner attacks;
- solution/counterfactual optimization;
- scenario serialization;
- qualitative scenario rendering;
- quantitative generated-scenario evaluation;
- collision clustering;
- cluster-based scenario classification;
- planner evaluation;
- selection of named rule-based planner configurations.

### 2.2 Out-of-scope functionality

STRIVE is not, by itself:

- a production autonomous-driving controller;
- a perception stack;
- a real-world crash-probability model;
- an accident-causality model;
- a legal-fault model;
- a vehicle safety certification procedure;
- a guarantee of physical executability for every generated trajectory.

### 2.3 Supported planners

Public scenario generation supports:

```text
ego
```

for replaying the observed nuScenes ego future, and:

```text
hardcode
```

for the released rule-based planner.

The rule-based implementation is:

```text
HardcodeNuscPlanner
```

### 2.4 Supported datasets

The principal dataset is nuScenes:

```text
v1.0-trainval
v1.0-mini
```

The README states that only metadata plus map expansion are needed for traffic-model training/testing and scenario generation.

The system also consumes its own D-02 generated-scenario JSON for downstream evaluation.

---

## 3. System Architecture

### 3.1 High-level architecture

```text
                    ┌──────────────────────────────┐
                    │ D-01 nuScenes Data           │
                    │ metadata + annotations + map │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ M-01 Main Traffic Model      │
                    │ graph conditional VAE/prior  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ C-01 Initialization Optim.   │
                    └──────────────┬───────────────┘
                                   │
                         hardcode  │  replay
                    ┌──────────────┴───────────────┐
                    ▼                              │
       ┌────────────────────────┐                  │
       │ M-02 Rule-Based Planner│                  │
       │ lane/speed-profile plan│                  │
       └────────────┬───────────┘                  │
                    └──────────────┬───────────────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │ C-02 Adversarial Optim.      │
                    │ planner-in-the-loop attack   │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ C-03 Solution Optim.         │
                    │ collision-free counterfactual│
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │ D-02 Generated Scenarios     │
                    └───────────┬─────────┬────────┘
                                │         │
                    ┌───────────┘         └──────────────┐
                    ▼                                    ▼
       ┌────────────────────────┐           ┌────────────────────────┐
       │ M-03 Scenario Cluster. │           │ Planner Evaluation     │
       └────────────┬───────────┘           │ includes M-02 rollout  │
                    │                       └────────────┬───────────┘
                    ▼                                    │
       ┌────────────────────────┐                        │
       │ M-04 Scenario Classif. │                        │
       │ public: cluster-based  │                        │
       └────────────┬───────────┘                        │
                    │ analytical relationship            │
                    ▼                                    ▼
       ┌────────────────────────┐◄───────────────────────┘
       │ F-01 Planner Tuning    │
       │ tunes M-02 parameters  │
       └────────────────────────┘
```

### 3.2 Primary dependency chain

The core learned-generation chain is:

```text
D-01 → M-01 → C-01 → C-02 → C-03 → D-02
```

For the released **rule-based (`hardcode`) attack path**, M-02 is an explicit runtime dependency between initialization fitting and adversarial optimization:

```text
D-01 → M-01 → C-01 → M-02 → C-02 → C-03 → D-02
```

For the replay (`ego`) attack path, M-02 is bypassed. Downstream evaluation and tuning can also invoke M-02 directly.

### 3.3 Runtime subsystems

Major source areas include:

```text
src/datasets/
src/models/
src/losses/
src/utils/
src/planners/
```

and top-level scripts such as:

```text
src/train_traffic.py
src/test_traffic.py
src/refine_traffic_optim.py
src/adv_scenario_gen.py
src/eval_adv_gen.py
src/cluster_scenarios.py
src/eval_planner.py
```

### 3.4 Offline vs runtime behavior

STRIVE is primarily an offline research workflow.

Training/fitting:

- M-01 traffic model;
- optional M-03 clustering;
- paper-level planner tuning.

Generation/evaluation:

- C-01/C-02/C-03 optimization;
- D-02 serialization;
- M-03 prediction;
- public M-04 cluster-based classification;
- planner evaluation.

---

## 4. System Components

### 4.1 D-01 — nuScenes Data Card

D-01 documents the nuScenes subset and transformation used by STRIVE.

Main release settings include:

```text
past:   4 steps = 2 s
future: 12 steps = 6 s
dt:     0.5 s
main categories: car, truck
```

Agent state:

```text
x, y, heading_x, heading_y, speed, heading_change_rate
```

Agent physical attributes:

```text
length, width
```

Map crop:

```text
256 × 256
bounds [-17, -38.5, 60, 38.5]
```

with layers:

```text
drivable_area
carpark_area
road_divider
lane_divider
```

### 4.2 M-01 — Main Traffic Model

M-01 is a graph-conditioned latent traffic model.

The public default uses:

```text
latent dimension: 32
past feature:     64
future feature:   64
map feature:      64
```

The model encodes:

- local agent motion;
- physical dimensions;
- semantic category;
- map raster;
- agent interactions.

It provides:

- conditional latent prior;
- posterior during fitting/training;
- future decoding;
- latent likelihood/plausibility signals.

### 4.3 M-02 — Rule-Based Planner

M-02 documents `HardcodeNuscPlanner`, the released reactive planner used by STRIVE's `hardcode` attack path and planner-evaluation/tuning experiments.

Its main loop:

1. matches agents to the nuScenes lane graph;
2. builds lane-following prediction splines;
3. predicts nearby non-ego agents under longitudinal speed/acceleration hypotheses;
4. generates a two-stage grid of ego speed profiles;
5. scores candidate ego trajectories for approximate collision risk;
6. selects a collision-acceptable candidate while preferring progress;
7. applies the first control step and replans.

Released default planning settings include:

```text
planner dt:        0.2 s
prediction dt:     0.2 s
prediction steps:  25
planning horizon:  5.0 s
interaction range: 70 m
ego speed grid:    5 × 5 = 25 profiles
```

Planner collision scoring approximates each vehicle with **five circles**, forms time-dependent distance scores, and aggregates them as:

```text
1 - product(1 - per_step_score)
```

This value is heuristic and is not a calibrated collision probability.

The released tuned configuration `final_tuned_val_1` changes four parameters relative to `DEF_CONFIG`:

```text
smax:        15.0 → 20.0
accmax:       3.0 → 4.0
score_wmin:   0.7 → 0.3
score_wfac:  0.05 → 0.02
```

The M-02 card also records a release-specific issue: the optional `rollout(init_state=...)` branch references an undefined `vehicle_atts` variable. Standard STRIVE callers reset the planner first and do not rely on that branch.

### 4.4 C-01 — Initialization Optimization

C-01 starts from the posterior mean and optimizes latent variables to reproduce the initialization target.

For the first released fitting pass:

```text
Adam
learning rate: 0.1
iterations:    75
```

For the hard-coded planner refit:

```text
iterations: 100
learning rate: configured global lr, released rule config 0.05
```

A release-specific `TgtMatchingLoss` implementation issue is documented in C-01: the configured external motion-prior coefficient multiplies trajectory matching in the total expression rather than the computed motion-prior value.

### 4.5 C-02 — Adversarial Optimization

C-02 modifies planner and non-planner latents through separate gradient paths.

Released rule-based configuration:

```text
Adam iterations: 200
learning rate:   0.05
```

Replay configuration:

```text
iterations: 300
learning rate: 0.05
```

The adversarial objective combines:

- planner-attacker proximity/crash objective;
- traffic-prior regularization;
- latent initialization regularization;
- non-target vehicle collision regularization;
- environment collision regularization;
- planner trajectory matching.

For the rule-based planner, the actual planner is rerun during optimization, while the differentiable crash gradient uses the M-01 target-node prediction as a proxy.

Final adversarial success is checked against the actual planner rollout.

### 4.6 C-03 — Solution Optimization

C-03 runs only after C-02 success.

Its planner latent is reset to the M-01 conditional prior mean, while non-planner latents start from C-02.

Released behavior:

```text
planner optimization horizon: 16 steps = 8 s
returned/saved horizon:       12 steps = 6 s
vehicle collision buffer:     0.5 m
```

The solution attempts to make the planner collision-free while preserving adversarial surrounding traffic.

Final non-planner solution trajectories are explicitly restored to the C-02 adversarial trajectories.

### 4.7 D-02 — Generated Scenarios

Serialized scenario JSON contains core fields such as:

```text
N
dt
map
lw
sem
past
fut_init
fut_adv
```

and conditional fields such as:

```text
fut_internal_ego
fut_sol
attack_agt
attack_t
z_adv
z_sol
z_prior
attack_bike_prof
```

Local generation partitions results into:

```text
adv_failed
sol_failed
adv_sol_success
```

The separately downloadable public scenario bundle described by the README contains scenarios from paper Sections 5.1/5.2 where both adversarial and solution optimization succeeded.

### 4.8 M-03 — Scenario Clustering

M-03 fits K-means on a four-dimensional collision-geometry feature:

```text
[
  collision_direction_x,
  collision_direction_y,
  attacker_heading_x,
  attacker_heading_y
]
```

Released settings:

```text
k = 10
random_state = 0
collision interpolation scale = 5
```

The README states that the supplied paper clustering was fit on over 400 scenarios from various nuScenes subsets and many rule-based planner versions.

### 4.9 M-04 — Scenario Classification

The **public repository** does not contain a separate supervised accident classifier for generated scenario labels.

Its released classification path is:

```text
M-03 feature
→ KMeans.predict(...)
→ cluster index
→ ordered semantic label lookup
```

Ten public labels are supplied in:

```text
data/clustering/cluster_labels.txt
```

This public cluster-based classifier must be distinguished from the **paper-level learned binary accident-mode classifier** described for multi-mode planner tuning. The latter is described in supplementary material but was not identified in the inspected public repository.

### 4.10 F-01 — Planner Tuning

The rule-based planner exposes:

```text
default
final_tuned_val_1
```

The released tuned config changes:

```text
smax:       15.0 → 20.0
accmax:      3.0 → 4.0
score_wmin:  0.7 → 0.3
score_wfac: 0.05 → 0.02
```

The source comments that this configuration was large-scale tuned on generated validation scenarios.

The paper/supplement further describes a 432-combination hyperparameter sweep and multi-mode planner improvement, but the complete sweep implementation and learned binary mode-classifier implementation are not present in the inspected public code.

---

## 5. Data Flow

### 5.1 Source-scene ingestion

`NuScenesDataset` loads:

- scenes;
- samples;
- annotations;
- ego poses;
- maps.

STRIVE operates primarily on metadata and maps rather than requiring camera/lidar/radar payloads for this workflow.

### 5.2 Scene-graph construction

Each scene window becomes a graph with:

- agents as nodes;
- per-agent past/future states;
- length/width;
- semantic classes;
- graph batch pointers;
- map association.

Missing history/future states are represented with NaNs plus visibility masks.

### 5.3 Learned-prior embedding

M-01 transforms each scene into:

- past embedding;
- map embedding;
- graph interaction embedding;
- conditional prior mean/variance;
- posterior when future data is supplied.

### 5.4 Scenario generation

Generation proceeds:

```text
feasibility sample/filter
→ C-01 initialization fit
→ if hardcode: M-02 planner rollout + C-01 planner-target refit
→ C-02 adversarial optimization
→ C-02 collision success check
→ C-03 solution optimization if successful
→ C-03 solution success check
```

For `planner=hardcode`, M-02 is therefore part of the actual generation path, not merely a downstream evaluator.

### 5.5 Scenario serialization

`prepare_output_dict()` unnormalizes trajectories/vehicle dimensions and converts tensors to JSON-compatible arrays.

### 5.6 Downstream analysis

D-02 then supports:

- `eval_adv_gen.py`;
- `cluster_scenarios.py`;
- cluster-based classification;
- `eval_planner.py`;
- planner tuning experiments.

---

## 6. Inputs

### 6.1 nuScenes metadata

Required source content includes:

```text
v1.0-trainval or v1.0-mini metadata
maps/basemap
maps/expansion
maps/prediction
map PNGs
```

### 6.2 Traffic-model checkpoint

Pretrained checkpoint expected by released configs:

```text
./model_ckpt/traffic_model.pth
```

The repository also documents an all-category checkpoint.

### 6.3 Planner configuration

Scenario generation selects:

```text
planner: ego | hardcode
```

For `hardcode`:

```text
planner_cfg: default | final_tuned_val_1
```

in the released `CONFIG_DICT`.

### 6.4 Scenario-generation configuration

Key controls include:

- dataset split;
- validation size;
- sequence interval;
- feasibility thresholds;
- attack category;
- optimizer learning rate;
- iteration count;
- loss weights;
- solution horizon;
- save/viz options.

### 6.5 Optional downstream artifacts

Generated-scenario classification uses:

```text
data/clustering/cluster.pkl
data/clustering/cluster_labels.txt
```

Planner analysis may use:

```text
final_tuned_val_1
```

or explicit planner parameters.

---

## 7. Outputs

### 7.1 Traffic-model artifacts

Traffic-model training saves checkpoint state including:

```text
model
optim
epoch
min_val_loss
```

### 7.2 Generated scenario JSON

D-02 JSON is the central reusable system output.

It preserves:

- initialization;
- adversarial future;
- optional solution;
- latent representations;
- attack metadata;
- map/agent information.

### 7.3 Visualizations

The system can produce:

- model samples;
- before/after refinement views;
- optimization-stage views;
- scenario videos;
- clustering visualizations.

### 7.4 Evaluation reports

Generated-scenario evaluation writes:

- aggregate CSV metrics;
- per-sequence metrics;
- cluster label CSVs;
- scenario-distribution graphics.

Planner evaluation writes per-scenario results and aggregate logs.

### 7.5 Clustering artifacts

M-03 produces:

```text
cluster.pkl
cluster_k<k>.jpg
```

with optional per-cluster visualization directories/videos.

### 7.6 Fitted planner configurations

F-01's released fitted artifact is embedded in Python source rather than stored as an independent checkpoint.

---

## 8. End-to-End Scenario Generation

### 8.1 Candidate scene selection

The released rule-based adversarial config uses:

```text
data_version: trainval
split: val
val_size: 400
seq_interval: 10
shuffle: false
```

At 2 Hz, starts are approximately 5 seconds apart.

### 8.2 Feasibility sampling/filtering

The system samples:

```text
20
```

M-01 futures with:

```text
include_mean=True
```

and filters candidate scenes for plausible planner-attacker interaction.

Important released behavior:

- configured `feasibility_vel` defaults to `0.5`;
- the candidate-agent velocity argument passed into `determine_feasibility_nusc()` is the literal `0.0`;
- `feasibility_vel` is separately applied to ego/planner motion checks.

### 8.3 Initialization fitting

C-01 aligns latent traffic to the source/planner initialization before attack optimization.

### 8.4 Adversarial search

C-02 searches latent variables for a collision involving the selected attacker while regularizing plausibility and undesirable side collisions.

### 8.5 Adversarial success check

Final success is:

```text
selected attacker collides with planner
```

using the final planner trajectory and polygon collision test.

The shared collision threshold is:

```text
IoU > 0.02
```

### 8.6 Solution search

C-03 then searches for a modeled collision-free target/planner response.

### 8.7 Solution success check

Solution success requires:

```text
no planner-other collision
AND
no planner-environment collision
```

under the default map-collision check.

### 8.8 Result partitioning

```text
C-02 fail
   └── adv_failed

C-02 success + C-03 fail
   └── sol_failed

C-02 success + C-03 success
   └── adv_sol_success
```

---

## 9. Traffic Model

### 9.1 Model family

M-01 is a graph conditional variational traffic model that learns a conditional latent distribution over multi-agent futures.

### 9.2 State representation

Per-agent dynamic state:

```text
x
y
heading_x
heading_y
speed
heading_change_rate
```

### 9.3 Latent representation

Released default:

```text
D = 32
```

The model exposes:

- prior mean/variance;
- posterior mean/variance;
- sampled latent values;
- latent log probability;
- Mahalanobis-style diagnostics.

### 9.4 Map representation

Local map raster:

```text
256 × 256
```

with four released layers.

A convolutional encoder maps this crop to the model map feature.

### 9.5 Interaction modeling

`SceneInteractionNet` performs graph message passing using relative agent transforms and semantic information.

### 9.6 Decoder / vehicle dynamics

Default output represents per-step:

```text
acceleration
heading-change rate
```

which is rolled through the vehicle dynamics to generate future state.

The decoder is autoregressive and interaction-aware.

---

## 10. Planner Integration

### 10.1 Replay planner

`planner=ego` treats the observed nuScenes ego trajectory as the planner future.

This is useful for replay-based scenario generation but is not a reactive closed-loop planner.

### 10.2 Rule-based planner

`planner=hardcode` instantiates the M-02 `HardcodeNuscPlanner`.

M-02 is the authoritative model card for its lane-graph matching, spline generation, surrounding-agent hypotheses, 25-profile default ego search, five-circle collision scoring, candidate selection, rollout behavior, and default/tuned configurations.

### 10.3 Closed-loop adversarial interaction

During C-02 rule-based optimization, STRIVE reruns the actual rule-based planner against the current generated non-ego trajectory on each iteration.

### 10.4 Internal differentiable proxy

Because the rule-based planner is not differentiated through, C-02 uses M-01's decoded target-node future as the differentiable crash target for the relevant adversarial gradient path.

Planner matching separately encourages this internal target representation to track the actual planner.

### 10.5 Planner evaluation

`eval_planner.py` evaluates:

- generated adversarial traffic;
- corresponding regular/source scenarios;
- rule-based or replay planner.

Main metrics include collision, collision relative speed, and acceleration.

---

## 11. Optimization Stack

### 11.1 Shared latent-space formulation

C-01/C-02/C-03 optimize latent variables decoded by M-01 rather than directly treating every trajectory coordinate as an unconstrained decision variable.

### 11.2 C-01 objectives

C-01 primarily matches initialization trajectories.

It also computes a motion-prior diagnostic.

### 11.3 C-02 objectives

C-02 includes:

- differentiable crash objective;
- motion-prior regularization;
- latent-distance regularization;
- non-target vehicle collision penalties;
- environment collision penalties;
- planner matching.

Attacker likelihood is handled differently from unlikely non-attacker agents through soft weighting.

### 11.4 C-03 objectives

C-03 includes:

- planner-to-agent collision avoidance;
- planner-to-environment avoidance;
- planner motion prior;
- non-planner adversarial-trajectory preservation.

### 11.5 Optimizers and stopping

All three stages use Adam-based latent optimization.

The public implementations use fixed iteration counts rather than convergence-based early stopping.

### 11.6 Known release-specific objective discrepancy

`TgtMatchingLoss` computes a motion-prior term but, in the released total-loss expression, applies `motion_prior_ext` to the trajectory-matching mean again.

This affects:

- C-01 external-prior weighting;
- C-02 planner matching branch;
- C-03 non-planner matching branch.

The subordinate cards document exact effective released behavior rather than silently correcting the implementation.

---

## 12. Evaluation

### 12.1 Traffic-model evaluation

The traffic model supports metrics such as:

- reconstruction errors;
- minimum ADE/FDE-style errors;
- angle error;
- vehicle collision rate;
- environment collision rate;
- latent likelihood diagnostics.

### 12.2 Adversarial-generation evaluation

`eval_adv_gen.py` reports quantities including:

- adversarial collision occurrence;
- solution success;
- non-planner collision rate;
- attacker/other environment collision;
- acceleration plausibility;
- latent prior log likelihood;
- internal planner matching error.

### 12.3 Solution evaluation

C-03 success is a final binary geometric criterion rather than simply a low optimization loss.

Downstream evaluation may additionally report solution velocity, acceleration, and heading-rate statistics.

### 12.4 Scenario clustering/classification

M-03/M-04 summarize collision geometry with ten public semantic categories.

The public workflow is unsupervised clustering plus hard cluster assignment, not supervised accident diagnosis.

### 12.5 Planner evaluation

Planner evaluation compares:

```text
regular
adversarial
total
```

scenario behavior.

### 12.6 Paper-level tuning results

The paper/supplement reports held-out planner-tuning results including:

| Improvement | Collision % Reg / Coll | Collision velocity m/s Reg / Coll | Acceleration m/s² Reg / Coll |
|---|---:|---:|---:|
| None (regular-tuned) | 4.6 / 68.6 | 4.59 / 10.48 | 1.96 / 2.26 |
| + Challenging data | 6.0 / 51.4 | 5.48 / 13.88 | 2.29 / 2.50 |
| + Extra learned mode | 4.6 / 54.3 | 4.60 / 10.86 | 2.02 / 2.55 |
| + Extra oracle mode | 4.6 / 54.3 | 4.59 / 10.40 | 1.96 / 2.39 |

These are paper experimental results, not values measured by the system profiler.

---

## 13. Configuration

### 13.1 Data configuration

Main release:

```text
data_dir: ./data/nuscenes
data_version: trainval
past_len: 4
future_len: 12
agent_types: car truck
```

### 13.2 M-01 training configuration

Released training config includes:

```text
epochs: 200
lr: 1e-5
data_noise_std: 0.01
loss_kl: 0.004
kl_anneal_end: 20
loss_recon: 1.0
loss_veh_coll_prior: 0.05
loss_env_coll_prior: 0.1
```

### 13.3 Rule-based adversarial generation

Primary released rule config includes:

```text
num_iters: 200
lr: 0.05
planner: hardcode
planner_cfg: default
feasibility_check_sep: true
```

### 13.4 Replay adversarial generation

Replay config uses:

```text
planner: ego
num_iters: 300
lr: 0.05
```

### 13.5 Planner configurations

The planner source provides:

```text
default
final_tuned_val_1
```

The default adversarial config intentionally selects:

```text
planner_cfg: default
```

and comments that the tuned key may be substituted after tuning.

---

## 14. Reproducibility

### 14.1 Public repository revision

This documentation set was grounded against:

```text
b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d
```

from `nv-tlabs/STRIVE`.

### 14.2 Runtime environment

README-tested environment:

```text
Ubuntu 18.04
Python 3.6
PyTorch 1.9
CUDA 11.1
```

Pinned requirements include:

```text
numpy 1.19.5
torch 1.9.0+cu111
torchvision 0.10.0+cu111
torchaudio 0.9.0
matplotlib 3.3.4
pyyaml 5.4.1
wandb 0.10.32
ConfigArgParse 1.5
torch-scatter 2.0.7
torch-sparse 0.6.10
torch-geometric 1.7.1
nuscenes-devkit 1.1.5
```

M-03 imports scikit-learn, but `scikit-learn` is not pinned in the inspected `requirements.txt`.

### 14.3 Required external data

Required for core training/generation:

- nuScenes metadata;
- nuScenes map expansion.

### 14.4 Required downloadable artifacts

The README separately provides:

- pretrained traffic-model weights;
- generated success scenarios.

The repository itself contains the public clustering label artifact and references a precomputed clustering.

### 14.5 Randomness and nondeterminism

Results can depend on:

- model initialization/training randomness;
- latent sampling;
- split randomization when enabled;
- GPU operations;
- optimizer numerics;
- scikit-learn version/defaults for re-fitted clustering.

### 14.6 Companion cards and metadata

This system card summarizes:

```text
D-01
M-01
M-02
C-01
C-02
C-03
D-02
M-03
M-04
F-01
```

Each subordinate card remains authoritative for implementation-level details specific to that component.

---

## 15. Quantitative System Profile

### 15.1 Source-code inventory

The companion system profiler checks the expected implementation surface:

```text
README.md
LICENSE
requirements.txt
src/datasets/nuscenes_dataset.py
src/models/traffic_model.py
src/losses/traffic_model.py
src/utils/init_optim.py
src/utils/adv_gen_optim.py
src/utils/sol_optim.py
src/utils/scenario_gen.py
src/adv_scenario_gen.py
src/eval_adv_gen.py
src/cluster_scenarios.py
src/eval_planner.py
src/planners/hardcode_goalcond_nusc.py
```

plus primary configs.

### 15.2 Component configuration summary

The profiler statically detects selected release invariants such as:

```text
M-01 latent size:            32
data past/future:            4 / 12
C-02 default iterations:     300 parser default
rule config iterations:      200
rule config learning rate:   0.05
C-03 solution horizon:       16
M-03 k:                      10
planner tuned key:           final_tuned_val_1
```

### 15.3 Documentation dependency validation

When run in a checkout containing this documentation set, the profiler can verify presence of:

```text
docs/cards/system/SYSTEM_CARD_STRIVE.md
docs/cards/data/DATA_CARD_NUSCENES_STRIVE.md
docs/cards/models/MODEL_CARD_TRAFFIC.md
docs/cards/models/MODEL_CARD_RULE_BASED_PLANNER_STRIVE.md
docs/cards/components/COMPONENT_CARD_INITIALIZATION_OPTIMIZATION.md
docs/cards/components/COMPONENT_CARD_ADVERSARIAL_OPTIMIZATION.md
docs/cards/components/COMPONENT_CARD_SOLUTION_OPTIMIZATION.md
docs/cards/data/DATA_CARD_GENERATED_SCENARIOS_STRIVE.md
docs/cards/models/MODEL_CARD_CLUSTERING_STRIVE.md
docs/cards/models/MODEL_CARD_ACCIDENT_CLASSIFIER_STRIVE.md
docs/cards/fitted_configs/FITTED_CONFIG_CARD_PLANNER_TUNING_STRIVE.md
```

### 15.4 Metadata validation

It can also check the corresponding YAML metadata locations when present.

### 15.5 Profiler

Run:

```bash
python tools/profile_strive_system.py \
  --repo-root . \
  --output ./out/strive_system_profile.yaml
```

or merge measurements into system metadata:

```bash
python tools/profile_strive_system.py \
  --repo-root . \
  --metadata ./metadata/system/strive_system.yaml
```

---

## 16. Known Limitations

### 16.1 Simulation/log-replay limitations

Much of STRIVE evaluation uses fixed surrounding-agent trajectories.

Those agents do not react to the planner as fully interactive real-world traffic would.

### 16.2 Learned-prior limitations

The traffic prior can only regularize toward patterns represented by its training data/model capacity.

A high prior likelihood does not guarantee real-world validity.

### 16.3 Planner limitations

The released rule-based planner is intentionally simple and lane-following.

It has structural limitations, including inability to robustly perform lane-changing behavior, which contributes to some failure modes.

### 16.4 Optimization limitations

C-01/C-02/C-03 are non-convex local optimization procedures.

Failure to find an adversarial or solution trajectory does not establish global non-existence.

### 16.5 Collision-model limitations

Optimization uses differentiable approximations such as vehicle circles and raster environment penalties.

Final vehicle success checks use oriented polygon IoU.

These representations can disagree at boundaries.

### 16.6 Finite-horizon limitations

Main saved futures are:

```text
12 steps = 6 s
```

C-03 uses:

```text
16 steps = 8 s
```

internally for planner solution optimization, but returns the default 12-step trajectory.

### 16.7 Dataset limitations

The main workflow inherits:

- nuScenes geographic coverage;
- nuScenes traffic distribution;
- car/truck focus;
- generated-scenario selection bias.

### 16.8 M-02 released alternate-initial-state issue

The optional M-02 `rollout(init_state=...)` path references an undefined `vehicle_atts` symbol in the released implementation. Standard repository callers use `reset(...)` and do not depend on this branch, but direct consumers should avoid it unless corrected.

### 16.9 Public-release gaps

Important gaps include:

- no full public implementation of the paper's 432-combination planner sweep identified;
- no public implementation of the paper's learned binary accident-mode classifier identified;
- scikit-learn not pinned despite M-03 use;
- generated JSON does not embed complete provenance such as checkpoint hash/config hash/source token;
- several paper experiments therefore require external reconstruction beyond a single checked-in script.

---

## 17. Failure Modes

### 17.1 No feasible attacker

Candidate scenes can be skipped when:

- only ego is present;
- no nearby feasible attacker exists;
- requested attack category is unavailable;
- ego/planner motion is insufficient;
- optional map-separation checks fail.

### 17.2 Initialization-fit failure

C-01 can fail to reproduce the desired initialization closely enough or can converge to undesirable latent values.

### 17.3 Adversarial optimization failure

C-02 can finish without the selected attacker colliding with the final planner.

Such scenarios enter:

```text
adv_failed
```

### 17.4 Solution optimization failure

C-02 may succeed while C-03 still returns a planner trajectory colliding with another vehicle or environment.

Such scenarios enter:

```text
sol_failed
```

### 17.5 Planner/map failures

Possible issues include:

- lane-graph mismatch;
- poor spline assignment;
- replay-induced unavoidable collision;
- finite-horizon edge cases;
- invalid map/data association.

### 17.6 Downstream artifact mismatch

Examples:

- wrong `cluster_labels.txt` paired with `cluster.pkl`;
- re-fitted clustering with permuted indices;
- generated scenarios evaluated with mismatched split/config;
- tuned configuration evaluated with default parameters;
- stale card/YAML metadata after source changes.

---

## 18. Safety, Ethics & Interpretation

### 18.1 Intended safety use

STRIVE is intended to help researchers discover and analyze planner weaknesses in controlled offline experiments.

### 18.2 Synthetic scenario interpretation

A STRIVE-generated collision is:

```text
a model-constrained synthetic stress-test case
```

not:

```text
an observed real-world accident
```

and not a calibrated estimate of crash probability.

### 18.3 Planner-failure interpretation

A failure is conditional on:

- the planner;
- the traffic model;
- source scene;
- generated traffic;
- map representation;
- finite horizon;
- collision definitions.

### 18.4 Counterfactual solution interpretation

A C-03 solution means that the STRIVE learned model found a collision-free alternative trajectory under its optimization assumptions.

It does not prove that the attacked real planner could execute that response.

### 18.5 Misuse boundaries

System outputs should not be used alone for:

- real-world harmful maneuver planning;
- legal fault assignment;
- driver/vehicle risk scoring;
- safety certification;
- claims about real-world accident prevalence.

### 18.6 Bias and representativeness

Bias can enter through:

```text
nuScenes
→ category filtering
→ M-01
→ feasibility filtering
→ optimization objectives
→ planner behavior
→ success filtering
→ clustering/semantic labels
```

Any reported result should identify that chain.

---

## 19. Licensing & Distribution

### 19.1 Source-code license

The repository `LICENSE` is:

```text
MIT
```

### 19.2 Model/scenario artifact license

The README states that pretrained models and generated scenarios derived from nuScenes are separately licensed under:

```text
CC-BY-NC-SA-4.0
```

### 19.3 Upstream dataset terms

nuScenes remains an upstream dataset dependency.

Users should review current nuScenes terms for their intended use and redistribution context.

### 19.4 Redistribution considerations

A redistributed STRIVE-derived artifact should preserve:

- code license where code is included;
- model/scenario artifact license;
- nuScenes-related obligations;
- provenance;
- configuration/checkpoint identity when materially relevant.

---

## 20. Relationships

### 20.1 Card inventory

```text
S-01  STRIVE System Card
│
├── D-01  nuScenes Data Card
├── M-01  Main Traffic Model Card
├── M-02  Rule-Based Planner Model Card
├── C-01  Initialization Optimization Component Card
├── C-02  Adversarial Optimization Component Card
├── C-03  Solution Optimization Component Card
├── D-02  Generated Scenarios Data Card
├── M-03  Scenario Clustering Model Card
├── M-04  Accident / Scenario Classifier Model Card
└── F-01  Planner Tuning Fitted-Config Card
```

### 20.2 End-to-end dependency graph

```text
D-01
  │
  ▼
M-01
  │
  ▼
C-01
  │
  ├──────────── replay ────────────┐
  │                                │
  └──► M-02 Rule-Based Planner ────┤
                                   ▼
                                  C-02
                                   │
                                   ▼
                                  C-03
                                   │
                                   ▼
                                  D-02
                                   │
                                   ├──► M-03 ───► M-04
                                   │
                                   └──► M-02 Planner Evaluation
                                              │
                                              ▼
                                             F-01
```

For the `hardcode` path, C-02 depends on **both M-01 and M-02**: M-01 supplies the differentiable traffic/target model and M-02 supplies the actual rule-based planner rollout. F-01 tunes M-02's configuration.

### 20.3 Relationship caveat

The diagram above is the **documentation architecture**.

In the public code:

- M-02 is an executable planner dependency for the `hardcode` C-02 path and for planner evaluation;
- F-01 directly tunes M-02 parameters;
- M-04 is cluster-based scenario classification;
- F-01's released tuned config does not directly consume those public M-04 cluster labels.

The paper's multi-mode tuning experiment instead uses a separately described learned binary accident-mode classifier that was not identified in the public repository.

---

## 21. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.

2. STRIVE public repository:  
   `https://github.com/nv-tlabs/STRIVE`

3. STRIVE project page:  
   `https://nv-tlabs.github.io/STRIVE/`

4. nuScenes:  
   `https://www.nuscenes.org/`

5. Primary public source files:
   - `README.md`
   - `requirements.txt`
   - `LICENSE`
   - `src/datasets/nuscenes_dataset.py`
   - `src/models/traffic_model.py`
   - `src/losses/traffic_model.py`
   - `src/utils/init_optim.py`
   - `src/utils/adv_gen_optim.py`
   - `src/utils/sol_optim.py`
   - `src/utils/scenario_gen.py`
   - `src/adv_scenario_gen.py`
   - `src/eval_adv_gen.py`
   - `src/cluster_scenarios.py`
   - `src/eval_planner.py`
   - `src/planners/hardcode_goalcond_nusc.py`

6. Subordinate documentation:
   - D-01 — nuScenes Data Card
   - M-01 — Main Traffic Model Card
   - M-02 — Rule-Based Planner Model Card
   - C-01 — Initialization Optimization Component Card
   - C-02 — Adversarial Optimization Component Card
   - C-03 — Solution Optimization Component Card
   - D-02 — Generated Scenarios Data Card
   - M-03 — Scenario Clustering Model Card
   - M-04 — Accident / Scenario Classifier Model Card
   - F-01 — Planner Tuning Fitted-Config Card

---

## 22. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.1 | 2026-09-21 | Added M-02 Rule-Based Planner as an explicit system component; corrected hardcode dependency paths, planner-tuning relationship, profiler inventories, and system-level known issue coverage. |
| 1.0.0 | 2026-09-21 | Completed S-01 across the full STRIVE generation, analysis, classification, planner-evaluation, and planner-tuning workflow. |
