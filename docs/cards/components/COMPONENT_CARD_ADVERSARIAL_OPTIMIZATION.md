# C-02 — Adversarial Optimization Component Card

> **Card ID:** C-02  
> **Card type:** Component Card  
> **Status:** Complete for the public STRIVE release  
> **Component:** STRIVE Adversarial Optimization  
> **Upstream:** C-01 — Initialization Optimization, M-01 — Main Traffic Model  
> **Downstream:** C-03 — Solution Optimization  
> **Primary implementation:** `src/utils/adv_gen_optim.py`

---

## 1. Component Summary

### 1.1 Purpose

C-02 searches the learned M-01 traffic-model latent space for a multi-agent future that causes a specified planner to collide with another traffic agent while discouraging implausible or unwanted behavior.

The optimization is adversarial with respect to the planner, but it does not directly optimize raw Cartesian waypoints. Instead, it starts from C-01's fitted latent variables and updates the M-01 latent representation. The resulting latent variables are repeatedly decoded into interacting traffic trajectories.

### 1.2 Role in the STRIVE pipeline

C-02 is the stage that turns a plausible real-scene initialization into an accident-prone scenario:

```text
D-01 nuScenes scene
      │
      ▼
M-01 learned traffic prior
      │
      ▼
C-01 fitted initialization
      │
      ▼
C-02 adversarial latent optimization
      │
      ├── failure → adv_failed
      │
      └── collision with selected attacker
              │
              ▼
        C-03 solution optimization
```

Only adversarially successful scenes proceed to C-03.

### 1.3 Primary implementation

Primary optimizer:

```text
src/utils/adv_gen_optim.py
```

Primary loss definitions:

```text
src/losses/adv_gen_nusc.py
```

Pipeline orchestration:

```text
src/adv_scenario_gen.py
```

Main-paper rule-based configuration:

```text
configs/adv_gen_rule_based.cfg
```

Replay-planner configuration:

```text
configs/adv_gen_replay.cfg
```

---

## 2. Inputs

### 2.1 Initialized latent variables

C-02 starts from:

```text
cur_z = z_init.clone().detach()
```

where `z_init` is produced by C-01.

The latent tensor contains one M-01 latent vector per agent.

### 2.2 Scene graph

The optimizer consumes the M-01-compatible scene graph, including:

- past motion;
- ground-truth future where needed;
- agent dimensions;
- semantics;
- graph edges;
- graph batch pointers;
- map indices.

### 2.3 Traffic-model embeddings

C-02 uses detached M-01 embedding information computed before optimization:

```text
map features
past features
conditional prior mean
conditional prior variance
```

The prior is split into:

```text
tgt_prior_distrib
other_prior_distrib
```

for the planner/target node and non-planner agents.

### 2.4 Planner trajectory

The attacked trajectory depends on planner mode.

For replay:

```text
planner: ego
```

the nuScenes ego future is the planner trajectory.

For the rule-based planner:

```text
planner: hardcode
```

the planner is rolled out against the current generated non-ego traffic during optimization.

### 2.5 Attack-agent information

The optimizer can accept an explicit `attack_agt_idx`, but the standard call in `adv_scenario_gen.py` does not supply one.

Instead, the adversarial loss uses a differentiable soft selection over candidate non-planner agents and eligible timesteps. After optimization, it extracts the final minimum-distance agent and time.

### 2.6 Configuration inputs

Major inputs include:

- optimizer learning rate;
- iteration count;
- collision-loss weights;
- latent-prior weights;
- initialization-distance weights;
- planner matching weights;
- crash-distance weight;
- feasibility constraints;
- planner type/configuration.

---

## 3. Outputs

### 3.1 Adversarial latent variables

C-02 returns the full optimized latent tensor:

```text
cur_z
```

assembled from separately optimized planner/target and non-planner latent tensors.

### 3.2 Adversarial trajectories

The returned final trajectory tensor is:

```text
final_result_traj
```

with an added sample dimension.

For rule-based planning, the ego/planner trajectory in this tensor is replaced by the **actual final rule-based planner rollout**, not merely M-01's internal planner approximation.

### 3.3 Selected attacker

After optimization, the adversarial loss is evaluated once more with:

```text
return_mins=True
```

to obtain the candidate attacker producing the final soft-minimum crash objective.

The returned local attacker index is converted to a batched/global index before leaving `run_adv_gen_optim()`.

### 3.4 Attack time

The optimizer also returns the selected attack timestep:

```text
cur_min_t
```

corresponding to the final minimum selected by the crash objective.

### 3.5 Optimization diagnostics

During optimization, STRIVE prints losses such as:

```text
tgt_match_loss
adv_loss
adv_crash_loss
motion_prior_loss
init_loss
coll_veh_loss
coll_veh_plan_loss
coll_env_loss
```

depending on enabled weights.

The function does not return a persistent per-iteration trace.

### 3.6 Downstream interface

Successful scenarios provide C-03 with:

- optimized adversarial latent variables;
- adversarial trajectories;
- M-01 embeddings/prior;
- scene graph/map context.

---

## 4. Attack Objective

### 4.1 Planner-crash objective

The core adversarial term minimizes positional distance between the planner/target trajectory and non-planner agents.

For each candidate agent and eligible timestep, STRIVE computes:

```text
distance = ||attacker_position - planner_position||
```

The loss operates over the squared distances after applying a soft selection.

Released rule-based weight:

```yaml
loss_adv_crash: 2.0
```

### 4.2 Soft minimum over agents and time

STRIVE constructs a soft minimum over all eligible non-planner agent/timestep combinations within each scene graph.

The soft-min weights emphasize the agent/time combination currently closest to the planner. These weights are then reused to:

- define the crash objective;
- identify likely attackers;
- reduce prior/initialization regularization on likely attackers;
- reduce certain planner-collision penalties for likely attackers.

This allows the optimization to discover an attacker rather than requiring one to be fixed in advance.

### 4.3 Attacker restrictions

The crash search can be restricted by:

- `attack_agt_idx` passed directly to the optimizer;
- `feasibility_time`;
- `feasibility_infront_min`;
- `adv_attack_with` at the seed-selection stage.

The public main path dynamically selects the attacker after feasibility filtering.

### 4.4 Crash-loss weighting

Main rule-based and replay configs both use:

```text
loss_adv_crash = 2.0
```

---

## 5. Plausibility & Regularization Objectives

### 5.1 Motion-prior loss

For non-planner agents, C-02 uses M-01 latent negative log likelihood:

```text
L_prior = -log p(z | past, map, interactions)
```

Released maximum weight for unlikely/non-attacking agents:

```text
loss_motion_prior = 1.0
```

### 5.2 Attacker motion-prior loss

Likely attackers receive a much smaller prior coefficient:

```text
loss_motion_prior_atk = 0.005
```

The coefficient is interpolated using the crash-objective soft-selection weight. This permits the most likely attacker to move farther into low-prior regions while keeping other traffic better regularized.

### 5.3 Initialization-latent loss

Non-planner latents are also penalized for moving away from the C-01 initialization:

```text
||z_init - z||²
```

Maximum released weight:

```text
loss_init_z = 0.5
```

### 5.4 Attacker initialization loss

Likely attackers receive a reduced initialization-distance weight:

```text
loss_init_z_atk = 0.05
```

As with the prior loss, soft attacker weights interpolate between the attacker and non-attacker coefficients.

### 5.5 External/planner trajectory matching

The planner/target latent is optimized separately with `TgtMatchingLoss` so that the M-01 target prediction follows the externally supplied planner trajectory.

Released weights:

```text
loss_match_ext        = 10.0
loss_motion_prior_ext = 0.0001
```

As documented in C-01, the public `TgtMatchingLoss` implementation computes the motion-prior diagnostic but adds the weighted target matching loss again in the total objective. Therefore this released implementation detail also affects C-02 target/planner latent optimization.

---

## 6. Collision Regularization

### 6.1 Non-planner vehicle collisions

STRIVE penalizes collisions among non-planner vehicles so that the optimization does not create arbitrary multi-vehicle pileups.

Released weight:

```text
loss_coll_veh = 20.0
```

### 6.2 Planner collision weighting

Collisions involving the planner are also penalized:

```text
loss_coll_veh_plan = 20.0
```

but the loss is reweighted so likely attackers receive lower penalty. This allows the desired attacker-planner collision to emerge while discouraging unrelated planner collisions.

### 6.3 Environment collisions

Non-planner trajectories are penalized for leaving drivable space:

```text
loss_coll_env = 20.0
```

### 6.4 Trajectory interpolation

Before collision penalties are evaluated, `AdvGenLoss` interpolates trajectories by a factor of:

```text
3
```

This reduces the chance of "jumping through" a collision between the native 2 Hz prediction points.

Final success is evaluated separately with oriented vehicle polygons and an IoU threshold, so the differentiable optimization collision penalty and final success test are not the same collision model.

---

## 7. Optimization Procedure

### 7.1 Latent initialization

The full C-01 latent tensor is partitioned into:

```text
tgt_z       = ego/planner latent(s)
other_z_all = all non-planner latent(s)
```

Both are cloned/detached and set to require gradients.

### 7.2 Optimized variables

Adam jointly optimizes:

```text
[tgt_z, other_z_all]
```

but STRIVE deliberately separates gradient pathways in the two decoder passes:

- the target-loss pass detaches non-planner latents;
- the adversarial-loss pass detaches target/planner latents.

This lets the planner-model latent fit its external trajectory without receiving gradients from the adversarial agent loss, while non-planner latents receive the crash/plausibility gradients.

### 7.3 Optimizer

Optimizer:

```text
Adam
```

### 7.4 Iteration count

Main rule-based configuration:

```text
200
```

Replay configuration:

```text
300
```

The parser default is also `300`.

### 7.5 Learning rate

Both released rule-based and replay configurations use:

```text
0.05
```

### 7.6 Planner-in-the-loop behavior

The rule-based path is explicitly logged as:

```text
closed-loop
```

During each optimizer iteration:

1. M-01 decodes current generated traffic.
2. The rule-based planner is rolled out against the current non-ego predictions.
3. The planner trajectory is normalized.
4. The target/planner model trajectory is matched to this rollout.
5. The non-planner traffic is optimized against a differentiable target trajectory.

### 7.7 Internal planner approximation in the crash loss

For:

```text
planner_name == hardcode
```

the crash objective uses M-01's current target-node prediction:

```text
other_decoder_out["future_pred"][ego_mask]
```

rather than differentiating through the actual rule-based planner, which is non-differentiable in this optimization path.

The actual planner is still rerun each iteration and used as the target for the planner-matching loss.

At finalization, STRIVE replaces the planner trajectory with an actual rule-based rollout and evaluates success against that real rollout.

### 7.8 Replay planner behavior

For:

```text
planner_name == ego
```

the observed nuScenes ego future is used as the planner future, and it can be injected as an external future during decoding.

### 7.9 Attack-agent/time determination

At the end of optimization, STRIVE recomputes `AdvGenLoss` against the **true final planner trajectory** with `return_mins=True`.

This returns:

- final selected attacker;
- final selected attack timestep.

### 7.10 Termination

The released optimizer uses a fixed number of iterations. There is no early-stopping criterion based on collision achievement or convergence.

---

## 8. Planner Integration

### 8.1 Supported planner types

The scenario-generation parser supports:

```text
ego      = replay the observed nuScenes ego trajectory
hardcode = STRIVE rule-based planner
```

### 8.2 Rule-based planner

For the rule-based planner:

- planner state is reset from the final observed past state;
- generated non-ego traffic is unnormalized;
- the planner rolls out against that traffic;
- rollout length follows the adversarial future horizon;
- the final saved/evaluated planner path is the actual planner output.

### 8.3 Replay planner

For the replay planner, the ground-truth nuScenes ego future acts as the fixed planner trajectory.

### 8.4 Planner configuration

The main rule-based release config uses:

```yaml
planner: hardcode
planner_cfg: default
```

and comments that:

```text
final_tuned_val_1
```

can be used after planner hyperparameter tuning.

---

## 9. Feasibility Filtering

### 9.1 Seed feasibility

Before C-01/C-02 optimization, STRIVE draws:

```text
20
```

future samples from M-01, including the prior mean, and checks whether another agent can come sufficiently close to the ego/planner.

Default parser threshold:

```text
feasibility_thresh = 10.0 m
```

### 9.2 Minimum time

Default:

```text
feasibility_time = 4
```

At 2 Hz this excludes the earliest 2 seconds of the sampled future from attack-distance consideration.

The same value is passed into the adversarial crash loss as `crash_loss_min_time`.

### 9.3 Relative-position constraints

Default:

```text
feasibility_infront_min = 0.0
```

This is a cosine-similarity threshold that excludes candidates behind the ego for feasibility/crash selection.

### 9.4 Velocity constraints

The parser exposes:

```text
feasibility_vel = 0.5
```

and its help text describes this as a candidate-agent sampled-motion threshold.

However, the released caller invokes:

```text
determine_feasibility_nusc(..., feasibility_time, 0.0, ...)
```

so the candidate-agent velocity threshold passed into that helper is **0.0**, not `feasibility_vel`.

The configured `feasibility_vel` is instead used separately to require meaningful motion from:

- the observed ego future in replay mode; or
- at least one sampled ego future in rule-based mode.

This distinction is part of the released implementation and should be preserved for exact reproduction.

### 9.5 Map-separation check

The rule-based and replay release configs set:

```yaml
feasibility_check_sep: true
```

This rejects candidates where the closest ego/attacker pair is separated by non-drivable map space according to STRIVE's raster check.

### 9.6 Agent-category restriction

Optional:

```text
adv_attack_with
```

can restrict feasible attackers to:

```text
pedestrian
cyclist
motorcycle
car
truck
```

The main release config leaves this unset.

---

## 10. Configuration

### 10.1 Primary configuration

```text
configs/adv_gen_rule_based.cfg
```

Main data/scenario settings:

```yaml
data_version: trainval
split: val
val_size: 400
seq_interval: 10
batch_size: 1
planner: hardcode
planner_cfg: default
```

`seq_interval: 10` corresponds to 5 seconds between candidate sequence starts at D-01's 2 Hz rate.

### 10.2 Optimization parameters

Rule-based:

```yaml
num_iters: 200
lr: 0.05
```

Replay:

```yaml
num_iters: 300
lr: 0.05
```

### 10.3 Adversarial loss weights

Released rule-based configuration:

| Loss | Weight |
|---|---:|
| `loss_coll_veh` | 20.0 |
| `loss_coll_veh_plan` | 20.0 |
| `loss_coll_env` | 20.0 |
| `loss_init_z` | 0.5 |
| `loss_init_z_atk` | 0.05 |
| `loss_motion_prior` | 1.0 |
| `loss_motion_prior_atk` | 0.005 |
| `loss_motion_prior_ext` | 0.0001 |
| `loss_match_ext` | 10.0 |
| `loss_adv_crash` | 2.0 |

The replay config uses the same adversarial weights.

### 10.4 Feasibility parameters

Parser defaults:

| Parameter | Default |
|---|---:|
| `feasibility_thresh` | 10.0 m |
| `feasibility_time` | 4 steps |
| `feasibility_vel` | 0.5 position-units/step threshold for ego-motion check in released caller |
| `feasibility_infront_min` | 0.0 |
| `feasibility_check_sep` | false parser default; enabled in released rule/replay configs |

### 10.5 Planner parameters

Main rule-based release:

```yaml
planner: hardcode
planner_cfg: default
```

Replay release:

```yaml
planner: ego
```

---

## 11. Quantitative Analysis

### 11.1 Release-configured values

The main-paper rule-based path uses:

```text
200 optimization iterations
Adam learning rate 0.05
vehicle collision weight 20
planner collision weight 20
environment collision weight 20
crash-distance weight 2
```

with substantially lower prior/initialization regularization for the likely attacker.

### 11.2 Latent dimensions

With default M-01:

```text
latent dimension D = 32
```

For a scene batch:

```text
tgt_z       [B, 32]
other_z_all [NA-B, 32]
cur_z       [NA, 32]
```

### 11.3 Collision-success metrics

The final success function:

```text
compute_adv_gen_success(...)
```

tests collision between the **actual final planner trajectory** and all non-planner agents using `check_single_veh_coll`.

`adv_success` is:

```text
True
```

only when the final selected attacking agent collides with the planner.

### 11.4 Final collision criterion

`check_single_veh_coll` constructs oriented vehicle polygons and computes intersection-over-union.

The public code counts a collision when:

```text
IoU > 0.02
```

This threshold is different from the continuous circle-based loss used during optimization.

### 11.5 Plausibility metrics

The scenario-generation/evaluation stack can later report:

- latent log likelihood;
- planner/attacker collision status;
- other-agent collisions;
- environment collisions;
- external trajectory matching error.

Those evaluation metrics belong to the generated-scenario/evaluation layer; C-02 itself primarily exposes optimization losses and final success.

### 11.6 Runtime / convergence metrics

Runtime depends on:

- number of agents;
- 200/300 iterations;
- number of graph edges;
- M-01 decoder cost;
- rule-based planner rollout cost;
- GPU/CPU configuration.

The public caller logs elapsed optimization time per processed batch.

### 11.7 Profiler

Run:

```bash
python tools/profile_adversarial_optimization.py \
  --repo-root . \
  --output ./out/adversarial_optimization_profile.yaml
```

or merge into metadata:

```bash
python tools/profile_adversarial_optimization.py \
  --repo-root . \
  --metadata ./metadata/components/adversarial_optimization.yaml
```

The profiler statically verifies release configs and key implementation behavior without running adversarial generation.

---

## 12. Success Criteria

### 12.1 Adversarial success

A scenario is successful if the final selected attacker collides with the actual planner trajectory according to `check_single_veh_coll`.

This criterion is binary.

### 12.2 Target collision

The success check specifically indexes:

```text
planner_coll_all[attack_agt - 1]
```

for the selected local attacking-agent index.

Thus a collision involving a different agent is not, by itself, sufficient to mark the selected attack successful.

### 12.3 Unwanted collisions

Separate optimization penalties discourage:

- non-planner vehicle collisions;
- non-attacker planner collisions;
- non-planner environment collisions.

These affect plausibility/quality but are not the sole binary `adv_success` criterion.

### 12.4 Saved scenario status

The caller partitions results as:

```text
adv_failed
sol_failed
adv_sol_success
```

C-02 determines whether a case is `adv_failed`. Adversarial successes continue to C-03, whose outcome determines `sol_failed` versus `adv_sol_success`.

---

## 13. Validation

### 13.1 Collision validation

Do not infer success directly from the crash-distance loss. Validate with the final polygon-IoU collision test against the actual planner trajectory.

### 13.2 Planner consistency

For rule-based scenarios, confirm that:

- the planner was rolled out against final generated non-ego traffic;
- the saved planner trajectory is the actual rollout;
- success was calculated using that final rollout.

### 13.3 Plausibility validation

Recommended checks include:

- prior likelihood of optimized latents;
- latent displacement from C-01;
- non-target vehicle collisions;
- map collisions;
- qualitative trajectory review.

### 13.4 Numerical validation

Check:

- finite `z`;
- finite decoded trajectories;
- finite prior variance;
- finite loss;
- successful planner rollout;
- valid selected attacker/time.

### 13.5 Reproducibility validation

Record:

- M-01 checkpoint hash;
- C-01 behavior/version;
- planner type/configuration;
- adversarial config;
- code revision;
- feasibility parameters;
- randomization/order settings.

---

## 14. Failure Modes

### 14.1 No feasible attacker

A scene can be skipped before C-02 when no sampled traffic agent satisfies the proximity/map/position constraints.

### 14.2 Optimization fails to induce collision

If the final selected attacker does not collide with the actual planner, the scenario is stored in:

```text
adv_failed
```

when saving is enabled.

### 14.3 Unintended collision

The optimizer can create:

- non-attacker collisions;
- traffic-traffic collisions;
- environment collisions.

The loss terms reduce but do not mathematically guarantee their absence.

### 14.4 Planner/model mismatch

In the rule-based path, C-02 cannot differentiate through the actual planner. It uses M-01's internal target-node prediction for the differentiable crash objective while fitting that prediction toward repeated actual planner rollouts.

If the learned target approximation cannot track planner reactions well, the adversarial gradient may be imperfect.

### 14.5 Implausible latent movement

The attacker receives intentionally reduced prior and initialization regularization. This is necessary for adversarial search but can produce lower-likelihood trajectories that require later plausibility assessment.

### 14.6 Map exploitation

Rasterized map collision penalties and finite-resolution trajectory checks may permit behavior that would be invalid under a higher-fidelity map or dynamics model.

---

## 15. Limitations

### 15.1 Local non-convex optimization

C-02 uses fixed-budget gradient descent in a neural latent space. Different initialization, numerical environment, or model checkpoint can lead to different local solutions.

### 15.2 Planner-specific scenarios

Generated scenarios are conditional on the attacked planner:

```text
ego replay
or
specific rule-based planner configuration
```

A failure case for one planner is not automatically a failure case for another.

### 15.3 Learned-prior limitations

Plausibility regularization is defined by M-01, which inherits D-01's coverage and model limitations.

### 15.4 Collision-model approximations

Optimization uses differentiable circle-based collision penalties with interpolated trajectories. Final success uses oriented polygon IoU. These are intentionally different mechanisms and can disagree near boundaries.

### 15.5 Finite horizon

The attack search occurs within the modeled rollout horizon. Hazards requiring substantially longer setup are not represented by the default search.

### 15.6 Feasibility-velocity implementation detail

The configured `feasibility_vel` is not passed as the candidate-agent velocity threshold to `determine_feasibility_nusc()` in the released caller. Reimplementations that change this argument from `0.0` to the configured value will not reproduce the public release exactly.

---

## 16. Safety & Interpretation

### 16.1 Meaning of adversarial success

Adversarial success means that, under a specific STRIVE scene/model/planner setup, the generated selected attacker collides with the planner according to the released collision test.

It does not measure real-world accident probability.

### 16.2 Research-use boundary

C-02 is intended for controlled simulation and robustness research. Generated scenarios should be interpreted as synthetic stress tests rather than instructions for real-world harmful behavior.

### 16.3 Dependence on model/planner

Results are conditional on:

- D-01;
- M-01;
- C-01;
- planner implementation/configuration;
- loss settings;
- feasibility filtering.

### 16.4 Human interpretation

A binary successful collision should be accompanied by qualitative and quantitative review of:

- plausibility;
- collision geometry;
- planner behavior;
- non-target agent behavior;
- map compliance.

---

## 17. Reproducibility

### 17.1 Source files

```text
src/utils/adv_gen_optim.py
src/losses/adv_gen_nusc.py
src/adv_scenario_gen.py
src/utils/scenario_gen.py
```

### 17.2 Configuration files

```text
configs/adv_gen_rule_based.cfg
configs/adv_gen_replay.cfg
```

Additional category-specific replay configs should be documented separately if used.

### 17.3 Companion metadata

```text
metadata/components/adversarial_optimization.yaml
```

### 17.4 Quantitative profiler

```text
tools/profile_adversarial_optimization.py
```

### 17.5 Required dependencies

C-02 requires:

- D-01-compatible scene data;
- M-01 checkpoint and normalizers;
- C-01 initialization;
- semantic map environment;
- PyTorch autograd;
- selected planner;
- planner configuration for rule-based mode.

---

## 18. Relationships

### 18.1 Upstream

```text
D-01 — nuScenes Data Card
  │
  ▼
M-01 — Main Traffic Model
  │
  ▼
C-01 — Initialization Optimization
```

### 18.2 Downstream

```text
C-03 — Solution Optimization
```

### 18.3 Dependency chain

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
  │
  ▼
C-03  Solution Optimization
```

---

## 19. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.  
   https://openaccess.thecvf.com/content/CVPR2022/html/Rempe_Generating_Useful_Accident-Prone_Driving_Scenarios_via_a_Learned_Traffic_Prior_CVPR_2022_paper.html

2. STRIVE public repository.  
   https://github.com/nv-tlabs/STRIVE

3. Relevant release files:
   - `src/utils/adv_gen_optim.py`
   - `src/losses/adv_gen_nusc.py`
   - `src/adv_scenario_gen.py`
   - `src/utils/scenario_gen.py`
   - `configs/adv_gen_rule_based.cfg`
   - `configs/adv_gen_replay.cfg`

4. C-01 — Initialization Optimization Component Card.

5. M-01 — Main Traffic Model Card.

6. D-01 — nuScenes Data Card for STRIVE.

---

## 20. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed C-02 for the public STRIVE release, including planner-in-loop behavior, final success criterion, and feasibility-call details. |
