# M-01 — Main Traffic Model Card

> **Card ID:** M-01  
> **Card type:** Model Card  
> **Status:** Complete for the public STRIVE release  
> **Model:** STRIVE Main Traffic Model  
> **Upstream:** D-01 — nuScenes Data Card for STRIVE  
> **Downstream:** C-01 Initialization Optimization, C-02 Adversarial Optimization, C-03 Solution Optimization  
> **Primary implementation:** `src/models/traffic_model.py`

---

## 1. Model Details

### 1.1 Model summary

The STRIVE main traffic model is a **graph-based conditional variational autoencoder (CVAE)** trained to model plausible joint future motion of multiple traffic agents. It conditions on each agent's recent trajectory, semantic class, dimensions, local semantic-map context, and interactions with other agents.

The model is not only a trajectory predictor. Within STRIVE it acts as a **learned traffic prior** whose per-agent latent variables can be optimized. That latent-space interface is what enables STRIVE to search for plausible accident-prone scenarios while retaining a learned notion of realistic traffic behavior.

### 1.2 Model type

The released implementation combines:

- per-agent past-trajectory encoding;
- per-agent future-trajectory encoding during training/posterior inference;
- a convolutional semantic-map encoder;
- graph message passing through `SceneInteractionNet`;
- conditional Gaussian prior and posterior distributions;
- per-agent latent variables;
- an autoregressive interaction-aware decoder;
- a kinematic bicycle output parameterization by default.

The prior predicts a Gaussian latent distribution from past motion, map context, semantic class, and interactions. The posterior additionally conditions on future motion during training.

### 1.3 Model version

This card documents the public STRIVE CVPR 2022 implementation in:

```text
nv-tlabs/STRIVE
```

The released checkpoint is not committed directly to GitHub; the repository provides a download location through `model_ckpt/README.md`. A local deployment should record the exact checkpoint filename, cryptographic hash, file size, checkpoint epoch, and repository revision.

### 1.4 Model authors

STRIVE was authored by:

- Davis Rempe
- Jonah Philion
- Leonidas J. Guibas
- Sanja Fidler
- Or Litany

### 1.5 Model date

The STRIVE paper was published at CVPR 2022. This card describes the corresponding public research release.

### 1.6 Model license

- STRIVE source code: **MIT License**.
- The STRIVE README states that released pretrained models and generated scenarios are derived from nuScenes and are separately licensed under **CC-BY-NC-SA-4.0**.
- nuScenes remains governed by its own upstream terms.

### 1.7 Citation

```bibtex
@inproceedings{rempe2022strive,
  author={Rempe, Davis and Philion, Jonah and Guibas, Leonidas J. and Fidler, Sanja and Litany, Or},
  title={Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior},
  booktitle={Conference on Computer Vision and Pattern Recognition (CVPR)},
  year={2022}
}
```

---

## 2. Model Purpose & Role in STRIVE

### 2.1 Primary purpose

The model learns a conditional distribution over plausible multi-agent futures. It supports:

1. reconstruction of observed future motion;
2. stochastic sampling of plausible future traffic;
3. scoring/regularization through the learned latent prior;
4. differentiable decoding of latent variables into trajectories.

### 2.2 Role in STRIVE

STRIVE uses the model as the common generative substrate for scenario optimization. Rather than directly moving agents in Cartesian space, downstream components optimize latent variables and decode them through the learned prior.

This is important to the STRIVE design: the optimization seeks hazardous interactions while penalizing movement away from the learned traffic distribution.

### 2.3 Relationship to D-01

M-01 is trained from D-01, the STRIVE-specific nuScenes view. It inherits D-01's:

- geography;
- category selection;
- 2 Hz trajectory representation;
- map preprocessing;
- split logic;
- filtering;
- normalization;
- missing-data behavior.

The main released paper configuration uses `car` and `truck`.

### 2.4 Downstream dependencies

M-01 is directly consumed by:

```text
C-01 — Initialization Optimization
C-02 — Adversarial Optimization
C-03 — Solution Optimization
```

The model's latent prior, encoder, decoder, and trajectory rollout functions are essential interfaces for those components.

---

## 3. Intended Use

### 3.1 Primary intended uses

Appropriate research uses include:

- multi-agent trajectory modeling;
- conditional future sampling;
- traffic-scene reconstruction;
- latent-space trajectory optimization;
- scenario generation for planner stress testing;
- studying learned traffic priors.

### 3.2 Intended users

The intended users are researchers and engineers working on autonomous-driving simulation, trajectory prediction, traffic generation, planning, and robustness evaluation.

### 3.3 Out-of-scope uses

M-01 should not be treated as:

- a production autonomous-driving controller;
- a perception system;
- a certified safety model;
- an estimate of real-world accident probability;
- a globally representative model of traffic;
- a guarantee that generated motion is physically feasible or collision-free.

### 3.4 Deployment assumptions

The released model assumes:

- preprocessed multi-agent state sequences compatible with D-01;
- local semantic maps;
- STRIVE category conventions;
- STRIVE normalizers;
- graph connectivity in the expected PyTorch Geometric format.

Its documented role is offline research and simulation rather than safety-critical real-time deployment.

---

## 4. Factors

### 4.1 Geographic factors

The training distribution comes from nuScenes and therefore centers on Boston and Singapore. Generalization to other regions is not established by the release.

### 4.2 Agent-class factors

The main-paper model is trained on:

```text
car
truck
```

The repository also discusses/provides a supplementary model trained on all supported categories. Results from one category configuration should not be silently transferred to another.

### 4.3 Scene-complexity factors

Performance can vary with:

- number of agents;
- interaction density;
- merges/intersections;
- visibility gaps;
- unusual vehicle sizes;
- map complexity.

Graph message passing makes the prediction explicitly interaction-dependent.

### 4.4 Temporal factors

Default timing:

```text
past:   4 steps × 0.5 s = 2 s
future: 12 steps × 0.5 s = 6 s
```

Longer rollouts can be requested during sampling/decoding, but the learned model was configured around the training horizon and may accumulate error outside it.

### 4.5 Map-context factors

The model encodes a local semantic raster crop. Predictions therefore depend on:

- crop bounds;
- map resolution;
- selected layers;
- map accuracy;
- agent pose used to center/orient the crop.

### 4.6 Distribution-shift factors

Relevant shifts include:

- new cities/countries;
- right-/left-driving conventions outside preprocessing assumptions;
- novel road geometries;
- unrepresented traffic participants;
- unusual weather or behavior;
- changes in map semantics;
- different sampling rates.

---

## 5. Architecture

### 5.1 High-level architecture

Conceptually:

```text
past trajectory ──► past encoder ─┐
semantic class ───────────────────┤
agent dimensions ─────────────────┤
local map ───────► map CNN ───────┤
                                  ├─► graph prior ─────► p(z | past, map)
future trajectory ► future encoder┤
                                  └─► graph posterior ─► q(z | past, future, map)

z + past feature + map feature + class + dimensions
                         │
                         ▼
                interaction-aware
                autoregressive decoder
                         │
                         ▼
                future trajectories
```

### 5.2 Agent state representation

The model expects six state values per timestep:

```text
(x, y, heading_x, heading_y, speed, heading_change_rate)
```

The trajectory decoder predicts the spatial/heading state needed for rollout. With bicycle output enabled, the per-step neural output is two values interpreted as acceleration/control-like quantities used by the kinematic rollout.

### 5.3 Past trajectory encoder

Default trajectory encoder type:

```text
MLP
```

For the main default configuration:

- past feature size: `64`;
- state size: `6`;
- vehicle attribute size: `2`;
- one visibility flag per timestep;
- semantic one-hot class appended to the MLP input.

The MLP hidden widths are:

```text
input → 128 → 128 → 128 → 64
```

A GRU trajectory-encoder option exists in code but is not the default.

### 5.4 Future trajectory encoder

The future encoder mirrors the past encoder and is used by the posterior during training/reconstruction.

Default future feature size:

```text
64
```

The future is transformed into the local frame of the last observed past state before encoding.

### 5.5 Map encoder

Default map input:

```text
4 semantic channels
256 × 256 pixels
```

The default convolution stack uses:

```text
kernels: [7, 5, 5, 3, 3, 3]
strides: [2, 2, 2, 2, 2, 2]
filters: [16, 32, 64, 64, 128, 128]
```

Each convolution is followed by GroupNorm with one group and ReLU. The flattened CNN output is projected to a `64`-D map feature.

The actual input-channel count is determined by the number of configured map layers.

### 5.6 Interaction network

`SceneInteractionNet` uses PyTorch Geometric message passing.

Default behavior includes:

- one message-passing round (`k=1`);
- relative edge geometry derived from `(x, y, heading_x, heading_y)`;
- source and target semantic one-hot features;
- MLP-based edge messages;
- **max aggregation**;
- MLP node update/output projections.

The prior and posterior use interaction node width `2 × past_feat_size`, which is `128` under defaults.

### 5.7 Latent representation

Default per-agent latent dimension:

```text
32
```

Both prior and posterior interaction networks emit `2 × latent_size` values per agent:

```text
mean
log variance
```

Variance is obtained with:

```text
variance = exp(log_variance)
```

Sampling uses the reparameterization trick.

### 5.8 Decoder

The decoder is autoregressive. It combines:

- latent `z`;
- past feature;
- current map feature;
- semantic class;
- vehicle dimensions;
- graph interactions.

A 3-layer GRU with hidden width equal to the past feature size supplies decoder state memory.

The decoder can process either one latent per agent or batched multiple samples per agent.

### 5.9 Output parameterization

Default:

```text
model_output_bicycle: true
```

With bicycle output enabled, the interaction decoder emits two values per step and the rollout uses a kinematic bicycle-style update from `models/common.py`.

The model can alternatively predict direct waypoint-style kinematics when bicycle output is disabled.

---

## 6. Inputs

### 6.1 Required inputs

The main forward path expects a scene graph containing:

```text
past
past_vis
future
future_vis
edge_index
lw
sem
batch
ptr
```

plus:

```text
map_idx
map_env
```

The future fields are needed for training/posterior inference. Prior-only sampling does not require a ground-truth future.

### 6.2 Optional inputs

Relevant optional behavior includes:

- external future trajectories during decoding;
- custom future rollout length;
- multiple latent samples;
- posterior mean instead of posterior sampling.

### 6.3 Input tensor schema

Using:

- `NA`: number of agents across batched graphs;
- `PT`: past steps;
- `FT`: future steps;
- `NC`: semantic classes;
- `E`: graph edges;

representative shapes are:

```text
past       [NA, PT, 6]
past_vis   [NA, PT]
future     [NA, FT, 6]
future_vis [NA, FT]
lw         [NA, 2]
sem        [NA, NC]
edge_index [2, E]
map_idx    [B]
```

### 6.4 Normalization

The model stores separate normalizers for:

- state vectors;
- vehicle length/width.

Map cropping temporarily unnormalizes agent pose, extracts the world-space crop, then restores normalized graph state.

### 6.5 Missing-data handling

Visibility masks identify unavailable past/future timesteps. Before trajectory encoding, missing frames are zeroed and the visibility flag is appended as an explicit input feature.

---

## 7. Outputs

### 7.1 Future trajectories

The principal output is:

```text
future_pred
```

For a standard single sample this is shaped approximately:

```text
[NA, FT, 4]
```

representing predicted future position and heading-vector components.

For batched stochastic sampling, an additional sample dimension is used.

### 7.2 Prior distribution

The conditional prior returns:

```text
prior_mu
prior_var
```

with shape:

```text
[NA, latent_size]
```

### 7.3 Posterior distribution

During training/reconstruction the posterior returns:

```text
post_mu
post_var
```

with the same latent shape.

### 7.4 Latent samples

Sampling APIs expose:

- `z_samp`;
- latent log probability;
- latent Mahalanobis-distance-style diagnostic.

These quantities are important to downstream optimization.

### 7.5 Intermediate features

`embed()` additionally exposes:

```text
map_feat
past_feat
prior_out
posterior_out  # if future is present
```

`decode_embedding()` allows downstream components to decode selected/optimized latent values.

---

## 8. Training Data

### 8.1 Primary training dataset

See:

```text
D-01 — nuScenes Data Card for STRIVE
```

The public training configuration points to:

```yaml
data_dir: ./data/nuscenes
data_version: trainval
```

### 8.2 Agent categories

The shared base configuration defaults to:

```yaml
agent_types:
  - car
  - truck
```

This matches the main-paper model described in the repository README.

### 8.3 Split usage

The training script creates STRIVE `train` and `val` datasets using the split semantics documented in D-01.

### 8.4 Data preprocessing dependency

All state construction, map filtering, coordinate handling, category mapping, and normalization assumptions are inherited from D-01 and should not be duplicated inconsistently here.

### 8.5 Data augmentation

The released training configuration sets:

```yaml
data_noise_std: 0.01
```

for Gaussian noise applied through the dataset input path.

---

## 9. Training Procedure

### 9.1 Training script

Released command:

```bash
python src/train_traffic.py --config ./configs/train_traffic.cfg
```

### 9.2 Optimizer

The training script uses **Adam**.

Base optimizer parameters:

```yaml
lr: 1.0e-5
weight_decay: 0.0
```

The release configuration explicitly sets the learning rate and inherits zero weight decay from the parser default.

### 9.3 Learning rate

```text
1e-5
```

### 9.4 Epochs

```text
200
```

in the public `configs/train_traffic.cfg`.

### 9.5 Batch size

```text
4
```

in the released training configuration.

Because scenes have variable numbers of agents, memory use can vary substantially across batches.

### 9.6 Checkpointing and validation

The training parser defaults to:

```text
val_every  = 3 epochs
save_every = 3 epochs
```

The checkpoint helper stores:

```text
model state dict
optimizer state dict
epoch
minimum validation loss
```

### 9.7 Training environment

The README states that the codebase was primarily tested with:

```text
Ubuntu 18.04
Python 3.6
PyTorch 1.9
CUDA 11.1
torch-geometric 1.7.1
nuscenes-devkit 1.1.5
```

---

## 10. Training Objective

### 10.1 Reconstruction loss

The reconstruction term evaluates predicted future `(x, y, heading_x, heading_y)` only at valid future timesteps.

Implementation-wise it is a Gaussian negative log-likelihood with unit variance, equivalent to an MSE-style objective up to constants.

Released weight:

```text
1.0
```

### 10.2 KL divergence

The posterior is regularized toward the learned conditional prior with a Gaussian KL divergence.

Released final weight:

```text
0.004
```

The training code linearly anneals the KL weight from zero to the configured final value, reaching full weight at:

```text
epoch 20
```

### 10.3 Vehicle-collision prior loss

When enabled, the model samples a future from the prior and penalizes vehicle-to-vehicle overlap. Vehicles are approximated by multiple circles along their length.

Released weight:

```text
0.05
```

### 10.4 Environment-collision prior loss

The prior sample also receives a map/environment collision penalty. The training implementation applies this environment prior loss to ego vehicles, which are expected to remain in valid drivable space.

Released weight:

```text
0.1
```

### 10.5 Total objective

Conceptually:

```text
L =
  1.0   × reconstruction
+ w_KL  × KL(posterior || prior)
+ 0.05  × prior vehicle-collision penalty
+ 0.10  × prior environment-collision penalty
```

where `w_KL` is linearly annealed to `0.004`.

---

## 11. Evaluation Data

### 11.1 Default held-out data

The public test script evaluates on the STRIVE held-out nuScenes split by default.

The README explicitly notes that default evaluation is on the **full held-out nuScenes validation split as interpreted by STRIVE**, not only the official prediction-challenge trajectories.

### 11.2 Official prediction-challenge option

The shared configuration exposes:

```text
use_challenge_splits
```

which can switch dataset construction to prediction-challenge instance/sample definitions.

### 11.3 Evaluation configuration

Primary release config:

```text
configs/test_traffic.cfg
```

It points to:

```text
./model_ckpt/traffic_model.pth
```

by default.

### 11.4 Sampling setup

Released settings:

```yaml
test_sample_num: 10
test_sample_future_len: 12
test_sample_disp_err: true
test_sample_coll_rate: true
test_sample_viz_multi: true
```

---

## 12. Evaluation Metrics

### 12.1 Reconstruction losses

The test path computes the same core model losses/errors used during training.

### 12.2 Displacement error

For stochastic samples, the test implementation computes minimum displacement metrics including:

- minimum ADE;
- minimum FDE;
- an angle-oriented error variant.

The exact output names should be taken from the evaluation run for the repository revision used.

### 12.3 Vehicle collision rate

The test script can compute collision frequency between generated vehicles.

Its collision metric uses a separate thresholded overlap criterion from the differentiable training penalty, so the metric and training loss should not be conflated.

### 12.4 Environment collision rate

The evaluation can compute collisions between sampled/reconstructed ego trajectories and the map/environment.

### 12.5 Latent diagnostics

The loss/evaluation implementation reports:

- posterior-mean log probability under the prior;
- normalized latent-distance diagnostic (`z_mdist`).

### 12.6 Qualitative visualization

The release supports:

- multi-agent reconstruction visualization;
- multi-agent sampled-future visualization;
- per-sample rollout video visualization.

---

## 13. Quantitative Analysis

### 13.1 Paper-reported results

The STRIVE paper uses the learned traffic model primarily as the realism prior supporting scenario generation. Any paper table reproduced in a downstream report should be labeled as **paper-reported** rather than confused with measurements from a local checkpoint.

This card intentionally does not fabricate checkpoint-specific performance values when the checkpoint and local evaluation output have not been profiled.

### 13.2 Release-configured evaluation

The public test configuration enables:

```text
10 prior samples
12-step sampled future
minimum displacement error evaluation
sample collision-rate evaluation
multi-agent sample visualization
```

### 13.3 Checkpoint-specific measurements

Checkpoint-specific measurements should include:

- SHA-256;
- file size;
- stored epoch;
- stored minimum validation loss;
- state-dict tensor count;
- total state-dict scalar elements;
- floating-point parameter/storage dtypes;
- key/shape inventory.

These are populated by the companion profiler.

### 13.4 Parameter count

The repository's runtime `count_params(model)` counts trainable model parameters after instantiation.

The companion profiler computes a checkpoint-state scalar count without importing STRIVE. This is useful for artifact identity, but a checkpoint may include buffers as well as parameters; therefore the checkpoint scalar count should not automatically be labeled "trainable parameter count."

### 13.5 Checkpoint size and hash

These values are environment/artifact specific and must be measured from the actual downloaded `.pth` file.

### 13.6 Profiler

Run:

```bash
python tools/profile_traffic_model.py \
  --checkpoint ./model_ckpt/traffic_model.pth \
  --train-config ./configs/train_traffic.cfg \
  --test-config ./configs/test_traffic.cfg \
  --output ./out/traffic_model_profile.yaml
```

To merge measurements into companion metadata:

```bash
python tools/profile_traffic_model.py \
  --checkpoint ./model_ckpt/traffic_model.pth \
  --train-config ./configs/train_traffic.cfg \
  --test-config ./configs/test_traffic.cfg \
  --metadata ./metadata/models/traffic_model.yaml
```

---

## 14. Performance Considerations

### 14.1 Compute requirements

The released environment is GPU-oriented and was tested with CUDA 11.1. CPU execution may be possible for some operations but is not the release's primary performance target.

### 14.2 Memory considerations

Memory scales with:

- agents per scene;
- batch size;
- graph edge count;
- map crops;
- number of stochastic samples;
- rollout length.

The batched multi-sample API explicitly trades greater memory use for speed.

### 14.3 Runtime characteristics

Three distinct workloads should be separated:

1. training with posterior encoding and prior samples;
2. ordinary reconstruction/sampling;
3. repeated differentiable decoding inside STRIVE optimization.

The third is especially important because downstream components repeatedly optimize latent values through the model.

### 14.4 Scaling with number of agents

Graph interaction requires pairwise edge processing according to the constructed scene graph. Dense scenes therefore increase graph compute and memory.

---

## 15. Ethical Considerations

### 15.1 Safety

M-01 is a research model. Plausibility under a learned prior is not equivalent to real-world safety, feasibility, legality, or probability.

### 15.2 Dataset bias

Biases in D-01 propagate into M-01, including geographic, category, behavioral, annotation, and map-selection biases.

### 15.3 Misuse

The latent prior should not be interpreted as a calibrated probability model for real-world accidents. Downstream optimization intentionally searches unusual high-risk parts of the learned behavior space.

### 15.4 Failure interpretation

A collision or unrealistic trajectory can arise from several sources:

- data limitations;
- model approximation;
- stochastic sampling;
- long-horizon rollout;
- map representation;
- downstream latent optimization.

A failure should not automatically be attributed to the evaluated planner.

---

## 16. Limitations

### 16.1 Learned-prior limitations

The prior can only learn patterns supported by its training distribution and architecture. Low prior cost does not guarantee human plausibility.

### 16.2 Collision artifacts

The STRIVE README explicitly notes that sampled futures may contain vehicle or environment collisions, especially in crowded scenes or long rollouts. The project provides refinement optimization to mitigate these artifacts.

### 16.3 Agent-category limitations

The main-paper checkpoint focuses on cars and trucks. Interactions involving pedestrians, cyclists, buses, motorcycles, and other categories require appropriate category-compatible training/checkpoints.

### 16.4 Geographic/domain limitations

The model inherits nuScenes' Boston/Singapore domain and STRIVE-specific preprocessing.

### 16.5 Long-horizon limitations

The decoder is autoregressive. Prediction and interaction errors can compound as rollout length increases beyond the trained horizon.

### 16.6 Map-model limitations

The model sees rasterized local semantic map context rather than the complete road graph or raw sensor environment. Map inaccuracies or missing semantics can affect predictions.

---

## 17. Caveats & Recommendations

### 17.1 Appropriate interpretation

Use the model as a learned **traffic prior**, not as ground truth. A high-likelihood latent/trajectory indicates compatibility with the learned model, not proof of real-world likelihood.

### 17.2 Validation before reuse

Re-evaluate after changes to:

- dataset/city;
- category set;
- temporal rate;
- map representation;
- normalization;
- checkpoint;
- model architecture;
- output parameterization.

### 17.3 Reproducibility recommendations

Always record:

- repository commit;
- checkpoint SHA-256;
- checkpoint stored epoch;
- train/test config;
- D-01 version;
- dependency versions.

### 17.4 Downstream optimization caution

C-01/C-02/C-03 optimize model latents. Optimization can expose decoder/prior weaknesses not obvious under ordinary random sampling. Generated trajectories therefore require separate plausibility and quality checks.

---

## 18. Reproducibility

### 18.1 Source files

Primary files:

```text
src/models/traffic_model.py
src/models/interaction_net.py
src/models/common.py
src/losses/traffic_model.py
src/train_traffic.py
src/test_traffic.py
src/utils/torch.py
```

### 18.2 Configuration files

```text
configs/train_traffic.cfg
configs/test_traffic.cfg
```

Shared defaults are defined in:

```text
src/utils/config.py
```

### 18.3 Checkpoint location

Default test path:

```text
./model_ckpt/traffic_model.pth
```

The repository provides a separate download link rather than storing the weights directly in Git.

### 18.4 Companion metadata

```text
metadata/models/traffic_model.yaml
```

### 18.5 Quantitative profiler

```text
tools/profile_traffic_model.py
```

### 18.6 Required versions

The public requirements/environment include:

```text
Python 3.6
PyTorch 1.9.0
torch-geometric 1.7.1
numpy 1.19.5
nuscenes-devkit 1.1.5
```

with CUDA 11.1 used by the released PyTorch setup.

---

## 19. Relationships

### 19.1 Upstream

```text
D-01 — nuScenes Data Card for STRIVE
```

### 19.2 Downstream

```text
C-01 — Initialization Optimization
C-02 — Adversarial Optimization
C-03 — Solution Optimization
```

### 19.3 Dependency chain

```text
D-01  nuScenes Data Card
  │
  ▼
M-01  Main Traffic Model Card
  │
  ├── C-01 Initialization Optimization
  ├── C-02 Adversarial Optimization
  └── C-03 Solution Optimization
```

---

## 20. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.  
   https://openaccess.thecvf.com/content/CVPR2022/html/Rempe_Generating_Useful_Accident-Prone_Driving_Scenarios_via_a_Learned_Traffic_Prior_CVPR_2022_paper.html

2. STRIVE public repository.  
   https://github.com/nv-tlabs/STRIVE

3. Relevant STRIVE implementation:
   - `src/models/traffic_model.py`
   - `src/models/interaction_net.py`
   - `src/models/common.py`
   - `src/losses/traffic_model.py`
   - `src/train_traffic.py`
   - `src/test_traffic.py`
   - `src/utils/config.py`
   - `src/utils/torch.py`

4. D-01 — nuScenes Data Card for STRIVE.

---

## 21. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed M-01 for the public STRIVE traffic model; added machine-readable metadata and checkpoint profiler contract. |
