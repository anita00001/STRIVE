# C-01 — Initialization Optimization Component Card

> **Card ID:** C-01  
> **Card type:** Component Card  
> **Status:** Complete for the public STRIVE release  
> **Component:** STRIVE Initialization Optimization  
> **Upstream:** M-01 — Main Traffic Model  
> **Downstream:** C-02 — Adversarial Optimization  
> **Primary implementation:** `src/utils/init_optim.py`

---

## 1. Component Summary

### 1.1 Purpose

Initialization optimization fits STRIVE's learned traffic-model latent variables to the observed future of a real nuScenes scene before adversarial optimization begins.

The traffic model's posterior mean is a good latent-space starting point, but directly decoding it does not necessarily reproduce the observed future exactly. C-01 therefore optimizes the latent variables so that the decoder output closely matches the source future trajectory while remaining connected to the traffic model's prior representation.

### 1.2 Role in the STRIVE pipeline

C-01 converts a real D-01 scene into a model-consistent latent initialization:

```text
observed nuScenes future
        │
        ▼
M-01 posterior mean
        │
        ▼
C-01 optimize latent z
        │
        ▼
decoded initialization trajectory
        │
        ▼
C-02 adversarial optimization
```

For the rule-based planner path, STRIVE performs an additional initialization-fit pass after replacing the ego future with the planner rollout.

### 1.3 Primary implementation

Primary implementation:

```text
src/utils/init_optim.py
```

Primary caller:

```text
src/adv_scenario_gen.py
```

Loss implementation:

```text
src/losses/adv_gen_nusc.py
```

The optimization function is:

```python
run_init_optim(...)
```

---

## 2. Inputs

### 2.1 Scene representation

C-01 receives the same normalized multi-agent scene graph used by M-01, including:

- past trajectory;
- future visibility mask;
- semantic class;
- agent dimensions;
- graph connectivity;
- graph batch pointers;
- map indices.

The matching target is the observed source-scene future:

```text
scene_graph.future_gt[:, :, :4]
```

### 2.2 Traffic-model inputs

Before optimization, `adv_scenario_gen.py` calls:

```text
model.embed(scene_graph, map_idx, map_env)
```

and detaches the resulting embedding information from the encoder computation graph.

C-01 uses:

- detached map features;
- detached past features;
- `prior_out = (prior_mean, prior_var)`;
- the M-01 decoder;
- M-01 state normalizer.

### 2.3 Initial future trajectory

The first initialization target is:

```text
scene_graph.future_gt[:, :, :4]
```

That is, the position/heading-vector portion of the observed normalized future.

The target is unnormalized inside `run_init_optim()` before matching.

For rule-based planner scenario generation, STRIVE later replaces the ego portion of this target with the planner's rollout and runs initialization optimization again.

### 2.4 Configuration inputs

`run_init_optim()` takes:

```text
cur_z
init_traj
traj_vis
lr
loss_weights
model
scene_graph
map_env
map_idx
num_iters
embed_info
prior_distrib
```

The initialization-specific loss weights are selected from the shared loss dictionary by the `init_` prefix.

---

## 3. Outputs

### 3.1 Optimized latent variables

C-01 returns:

```text
cur_z
```

after in-place Adam updates over a cloned/detached latent tensor with `requires_grad=True`.

The optimized latent has shape:

```text
[NA, D]
```

where:

- `NA` = number of agents across the batched scene graphs;
- `D` = M-01 latent dimension, 32 in the default model.

### 3.2 Decoded trajectories

The returned fitted trajectory is:

```text
init_result_traj
```

obtained from:

```text
model.decode_embedding(cur_z, ...)
```

after optimization.

Its primary kinematic output is the M-01 predicted future representation:

```text
[NA, FT, 4]
```

for position and heading-vector components.

### 3.3 Optimization diagnostics

During optimization, the component logs loss values to the progress bar. `TgtMatchingLoss` exposes:

```text
match_ext_loss
motion_prior_ext_loss
loss
```

when their corresponding configured weights are enabled.

The released function does not return a structured optimization trace; it returns only:

```text
optimized z
final fitted trajectory
final decoder output
```

### 3.4 Downstream interface

C-02 receives the optimized initialization latent and fitted trajectory as its starting state.

The initialization latent is also used later as a regularization reference during adversarial optimization.

---

## 4. Optimization Objective

### 4.1 Trajectory matching objective

`TgtMatchingLoss` computes squared error between the decoded future and target future:

```text
L_match(t, a) = ||future_pred[a,t] - target[a,t]||²
```

and averages over retained agent/timestep entries.

The released rule-based adversarial config sets:

```yaml
init_loss_match_ext: 10.0
```

### 4.2 Motion-prior regularization

`TgtMatchingLoss` also computes `MotionPriorLoss`, defined as negative log probability of the current latent under the conditional Gaussian prior:

```text
L_prior = -log p(z | past, map, interactions)
```

The released rule-based config sets:

```yaml
init_loss_motion_prior_ext: 0.01
```

### 4.3 Released implementation behavior

There is an important distinction between the **computed diagnostic** and the **effective optimization objective** in the public release.

In `TgtMatchingLoss.forward()`, the code computes:

```text
motion_prior_loss = MotionPriorLoss(z, prior_out)
```

and reports it as:

```text
motion_prior_ext_loss
```

However, the line that adds the initialization prior-weighted term to the total loss uses `tgt_loss.mean()` again rather than `motion_prior_loss.mean()`.

Therefore, in the public code as written, when both initialization weights are positive, the effective optimized loss is:

```text
L_effective =
    init_loss_match_ext        × mean(L_match)
  + init_loss_motion_prior_ext × mean(L_match)
```

rather than the apparently intended:

```text
L_intended =
    init_loss_match_ext        × mean(L_match)
  + init_loss_motion_prior_ext × mean(L_prior)
```

With the released rule-based values, this means the effective first-stage matching coefficient is:

```text
10.0 + 0.01 = 10.01
```

and the calculated motion-prior diagnostic does **not** affect the gradient through the total C-01 loss.

This card documents the released implementation rather than silently correcting it.

### 4.4 Valid-timestep masking

Before optimization, both target and decoded trajectory are filtered using:

```text
traj_vis == 1.0
```

Only valid observed future timesteps contribute to the matching loss.

The masking occurs after trajectories are unnormalized.

---

## 5. Optimization Procedure

### 5.1 Initialization

For scenario generation, STRIVE starts C-01 from the M-01 posterior mean:

```text
z_init = embed_info_attached["posterior_out"][0].detach()
```

This uses the observed future to place the initial latent near a reconstruction-compatible solution.

`run_init_optim()` then clones/detaches that tensor again and enables gradients only on the latent:

```text
cur_z = cur_z.clone().detach()
cur_z.requires_grad = True
```

M-01 parameters are not passed to the optimizer.

### 5.2 Optimizer

Optimizer:

```text
Adam
```

Optimized variable:

```text
cur_z only
```

The model decoder remains differentiable so gradients flow from trajectory matching through `decode_embedding()` back to `cur_z`.

### 5.3 Iteration count and learning rate

The first C-01 call in `adv_scenario_gen.py` is hard-coded as:

```text
learning rate = 0.1
iterations    = 75
```

Specifically:

```text
run_init_optim(..., 0.1, ..., 75, ...)
```

These values are **not** the same as the global adversarial-optimization config values:

```yaml
num_iters: 200
lr: 0.05
```

Those global settings primarily govern later optimization stages.

### 5.4 Rule-based planner fine-tuning pass

When:

```yaml
planner: hardcode
```

STRIVE performs these additional steps:

1. Roll out the rule-based planner against the initially fitted non-ego trajectories.
2. Replace the ego target future with the planner rollout.
3. Run `run_init_optim()` again.

The second pass is called with:

```text
iterations = 100
learning rate = lr
```

where `lr` comes from the scenario-generation config. In the released `adv_gen_rule_based.cfg`:

```text
lr = 0.05
```

Thus the rule-based path normally uses:

```text
pass 1: 75 iterations @ 0.1
pass 2: 100 iterations @ 0.05
```

### 5.5 Differentiable decoding

Each optimization iteration performs:

```text
z
 │
 ▼
M-01 decode_embedding()
 │
 ▼
normalized predicted future
 │
 ▼
unnormalize
 │
 ▼
valid-timestep mask
 │
 ▼
matching loss
 │
 ▼
backpropagation to z
```

### 5.6 Termination

C-01 uses a fixed iteration count. The public implementation does not use:

- early stopping;
- convergence tolerance;
- validation-based termination.

After the fixed loop, it decodes the final optimized latent under `torch.no_grad()`.

---

## 6. Configuration

### 6.1 Relevant configuration file

For the main rule-based STRIVE generation path:

```text
configs/adv_gen_rule_based.cfg
```

Initialization-specific weights:

```yaml
init_loss_motion_prior_ext: 0.01
init_loss_match_ext: 10.0
```

### 6.2 Core hyperparameters

First initialization fit:

| Hyperparameter | Released value | Source |
|---|---:|---|
| Adam learning rate | 0.1 | hard-coded call site |
| Iterations | 75 | hard-coded call site |
| Match weight | 10.0 | `adv_gen_rule_based.cfg` |
| Motion-prior diagnostic weight | 0.01 | `adv_gen_rule_based.cfg` |
| Effective match coefficient in released loss | 10.01 | derived from released implementation |

Rule-based planner fine-tune:

| Hyperparameter | Released value |
|---|---:|
| Adam learning rate | 0.05 |
| Iterations | 100 |
| Match weight | 10.0 |
| Motion-prior diagnostic weight | 0.01 |

### 6.3 Model and data dependencies

C-01 depends on:

- D-01-compatible scenes;
- M-01 checkpoint;
- M-01 normalizers;
- M-01 prior/posterior embeddings;
- M-01 decoder;
- consistent map environment and map indices.

### 6.4 Planner dependency

The initial 75-step fit is planner-independent.

The additional 100-step fit occurs on the rule-based planner path after the ego target trajectory is replaced by the planner rollout.

For that branch, C-01 therefore becomes planner-dependent.

---

## 7. Quantitative Analysis

### 7.1 Release-configured values

The public release exposes:

```yaml
init_loss_match_ext: 10.0
init_loss_motion_prior_ext: 0.01
```

and the main call site supplies:

```text
75 iterations
0.1 learning rate
```

The rule-based planner re-fit supplies:

```text
100 iterations
0.05 learning rate in the released config
```

### 7.2 Input/output tensor dimensions

Typical symbolic dimensions:

```text
z                  [NA, 32]
init_traj          [NA, FT, 4]
traj_vis           [NA, FT]
prior_mean         [NA, 32]
prior_var          [NA, 32]
decoded future     [NA, FT, 4]
```

With default M-01 configuration:

```text
FT = 12
```

unless a calling workflow uses a different rollout horizon.

### 7.3 Optimization trace statistics

The release prints per-iteration loss statistics but does not persist a structured trace from `run_init_optim()`.

A local evaluation may record:

- initial matching MSE;
- final matching MSE;
- relative reduction;
- latent L2 displacement;
- initial/final prior NLL;
- finite-value checks;
- optimization time.

These are measurements, not pre-filled release facts.

### 7.4 Runtime measurements

Runtime depends on:

- number of agents;
- graph connectivity;
- decoder complexity;
- GPU/CPU;
- number of optimization passes.

Rule-based generation can invoke C-01 twice per retained scene batch.

### 7.5 Profiler

The companion profiler performs **static release profiling**. It reads:

```text
src/utils/init_optim.py
src/losses/adv_gen_nusc.py
src/adv_scenario_gen.py
configs/adv_gen_rule_based.cfg
```

and reports:

- configured initialization weights;
- hard-coded initialization call parameters;
- presence of Adam latent optimization;
- visibility masking;
- posterior-mean initialization;
- rule-based second-pass parameters;
- the released `TgtMatchingLoss` prior-term discrepancy.

Run:

```bash
python tools/profile_initialization_optimization.py \
  --repo-root . \
  --output ./out/initialization_optimization_profile.yaml
```

or merge into metadata:

```bash
python tools/profile_initialization_optimization.py \
  --repo-root . \
  --metadata ./metadata/components/initialization_optimization.yaml
```

---

## 8. Validation

### 8.1 Functional validation

A suitable functional check compares the M-01 decoded future before and after C-01 and verifies that matching error to the initialization target decreases.

For rule-based planner generation, the second pass should similarly reduce mismatch to the target containing the planner ego rollout.

### 8.2 Numerical validation

Check for:

- non-finite latent values;
- non-finite decoded trajectories;
- non-finite loss;
- degenerate prior variance;
- exploding latent displacement.

### 8.3 Interface validation

Validate compatibility between:

```text
M-01 embed() output
C-01 run_init_optim()
M-01 decode_embedding()
C-02 starting latent/trajectory
```

### 8.4 Reproducibility checks

Record:

- STRIVE repository revision;
- M-01 checkpoint hash;
- scenario-generation config;
- initialization call-site parameters;
- code status of `TgtMatchingLoss`.

The call-site values are important because not all C-01 optimizer settings live in the config file.

---

## 9. Failure Modes

### 9.1 Poor trajectory match

C-01 may fail to reproduce the target closely when:

- the target lies outside M-01's decoder capacity;
- missing observations reduce constraints;
- agent interactions are difficult to reconcile;
- the fixed optimization budget is insufficient.

### 9.2 Out-of-prior latent solution

The design computes a prior-likelihood term, but the public `TgtMatchingLoss` implementation does not add the computed motion-prior loss to the total objective. Therefore the released initialization optimization does not receive the intended direct prior-gradient regularization from `init_loss_motion_prior_ext`.

Downstream C-02 contains its own prior-related regularization.

### 9.3 Missing trajectory observations

Only timesteps with:

```text
traj_vis == 1
```

participate in the matching objective. Sparse observations reduce constraints on the optimized latent.

### 9.4 Optimization instability

Potential causes include:

- large learning rate;
- pathological decoder gradients;
- highly coupled multi-agent interactions;
- numerically unstable latent/prior values.

The first pass uses `lr=0.1`, which is separately hard-coded from the later adversarial `lr`.

### 9.5 Planner-initialization collision

After the rule-based planner fine-tune, STRIVE explicitly checks whether the planner already collides with scene trajectories.

If a scene already causes a collision after initialization, that scenario can be removed before adversarial optimization proceeds.

---

## 10. Limitations

### 10.1 Local optimization

C-01 is gradient-based optimization in a non-convex neural latent space. The result depends on:

- posterior initialization;
- optimizer;
- learning rate;
- iteration budget;
- decoder geometry.

### 10.2 Model dependence

C-01 cannot fit behavior that M-01 cannot express well. The initialization is therefore model-relative, not a lossless reconstruction of nuScenes.

### 10.3 Horizon dependence

The optimization only matches the future horizon passed through M-01. It does not constrain behavior beyond the decoded rollout.

### 10.4 Dataset dependence

All D-01/M-01 limitations propagate into C-01.

### 10.5 Loss-implementation discrepancy

The released implementation computes but does not optimize the motion-prior term in `TgtMatchingLoss` as apparently intended. Reimplementations that replace the second `tgt_loss.mean()` with `motion_prior_loss.mean()` will no longer be behaviorally identical to the public STRIVE release.

---

## 11. Safety & Interpretation

### 11.1 Meaning of a successful initialization

A successful C-01 fit means that M-01 can decode an optimized latent close to the selected initialization target. It does not establish:

- physical correctness;
- real-world likelihood;
- absence of collisions;
- safety.

### 11.2 Downstream risk

C-02 begins from C-01's latent solution. Poor initialization can alter:

- which attacker is selected;
- collision-search behavior;
- prior regularization;
- scenario plausibility;
- optimization success.

### 11.3 Plausibility interpretation

Any notion of plausibility is relative to M-01 and its training data. In the public C-01 implementation, the computed prior diagnostic is not part of the effective optimization gradient because of the loss expression described above.

---

## 12. Reproducibility

### 12.1 Source files

```text
src/utils/init_optim.py
src/losses/adv_gen_nusc.py
src/adv_scenario_gen.py
src/utils/scenario_gen.py
```

### 12.2 Configuration files

Primary main-paper rule-based configuration:

```text
configs/adv_gen_rule_based.cfg
```

`configs/refine_traffic_optim.cfg` uses related optimization machinery but is not the C-01 scenario-generation initialization call documented here.

### 12.3 Companion metadata

```text
metadata/components/initialization_optimization.yaml
```

### 12.4 Quantitative profiler

```text
tools/profile_initialization_optimization.py
```

### 12.5 Required dependencies

C-01 requires:

- M-01 model/checkpoint;
- M-01 normalizers;
- compatible D-01 scene graph;
- map environment;
- PyTorch autograd;
- Adam optimizer.

---

## 13. Relationships

### 13.1 Upstream

```text
D-01 — nuScenes Data Card
  │
  ▼
M-01 — Main Traffic Model
```

### 13.2 Downstream

```text
C-02 — Adversarial Optimization
```

### 13.3 Dependency chain

```text
D-01  nuScenes Data Card
  │
  ▼
M-01  Main Traffic Model
  │
  ▼
C-01  Initialization Optimization
  │
  ▼
C-02  Adversarial Optimization
```

---

## 14. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.  
   https://openaccess.thecvf.com/content/CVPR2022/html/Rempe_Generating_Useful_Accident-Prone_Driving_Scenarios_via_a_Learned_Traffic_Prior_CVPR_2022_paper.html

2. STRIVE public repository.  
   https://github.com/nv-tlabs/STRIVE

3. Relevant release files:
   - `src/utils/init_optim.py`
   - `src/losses/adv_gen_nusc.py`
   - `src/adv_scenario_gen.py`
   - `src/utils/scenario_gen.py`
   - `configs/adv_gen_rule_based.cfg`

4. M-01 — Main Traffic Model Card.

5. D-01 — nuScenes Data Card for STRIVE.

---

## 15. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed C-01 for the public STRIVE release, including exact call-site optimizer settings and released loss behavior. |
