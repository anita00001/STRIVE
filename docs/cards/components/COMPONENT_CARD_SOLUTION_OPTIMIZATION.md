# C-03 — Solution Optimization Component Card

> **Card ID:** C-03  
> **Card type:** Component Card  
> **Status:** Complete for the public STRIVE release  
> **Component:** STRIVE Solution Optimization  
> **Upstream:** C-02 — Adversarial Optimization, M-01 — Main Traffic Model  
> **Downstream:** D-02 — Generated Scenarios Data Card  
> **Primary implementation:** `src/utils/sol_optim.py`

---

## 1. Component Summary

### 1.1 Purpose

C-03 searches for a **collision-free alternative trajectory for the planner/ego agent** after C-02 has successfully generated an adversarial collision.

Its purpose is diagnostic: STRIVE attempts to preserve the adversarial behavior of the surrounding traffic while changing the planner-side latent so that the target agent can avoid both other vehicles and the environment. A successful C-03 result demonstrates that, within the learned M-01 traffic model and finite optimization horizon, the adversarial situation admits a collision-free counterfactual response.

### 1.2 Role in the STRIVE pipeline

C-03 runs only for scenarios where C-02 succeeded:

```text
D-01  nuScenes
  │
  ▼
M-01  learned traffic prior
  │
  ▼
C-01  initialization optimization
  │
  ▼
C-02  adversarial optimization
  │
  ├── adversarial failure ─────────────► adv_failed
  │
  └── adversarial success
          │
          ▼
       C-03 solution optimization
          │
          ├── solution failure ─────────► sol_failed
          │
          └── solution success ─────────► adv_sol_success
                                              │
                                              ▼
                                   D-02 Generated Scenarios
```

### 1.3 Primary implementation

Primary optimizer and success test:

```text
src/utils/sol_optim.py
```

Shared loss functions:

```text
src/losses/adv_gen_nusc.py
```

Pipeline orchestration:

```text
src/adv_scenario_gen.py
```

Primary configurations:

```text
configs/adv_gen_rule_based.cfg
configs/adv_gen_replay.cfg
```

---

## 2. Inputs

### 2.1 Successful adversarial scenario

C-03 receives only the subset of a batch for which:

```text
compute_adv_gen_success(...) == True
```

The caller constructs a new `sol_scene_graph` containing only adversarially successful scenes.

### 2.2 Adversarial latent variables

The input `cur_z` is the latent output of C-02. C-03 does **not** use all of it symmetrically:

- non-planner latents initialize from the C-02 adversarial latents;
- planner/target latent initialization is reset to the M-01 conditional **prior mean**.

This is a major release-specific detail.

### 2.3 Adversarial trajectories

C-03 receives C-02's final trajectory:

```text
final_result_traj
```

and extracts the non-planner adversarial trajectories as the matching target:

```text
other_match_traj
```

These trajectories are the surrounding traffic behavior C-03 attempts to preserve.

### 2.4 Traffic-model embeddings

C-03 receives the M-01 embedding information for the successful subset, including:

- past features;
- map features;
- conditional prior mean/variance.

The prior is separated into planner/target and non-planner distributions.

### 2.5 Scene graph and map

Required context includes:

- graph batch pointers;
- agent dimensions;
- semantic classes;
- map indices;
- map environment;
- M-01 state and attribute normalizers.

### 2.6 Configuration inputs

The function receives:

```text
future_len
lr
loss_weights
num_iters
```

where `future_len` is the solution-specific horizon and `lr` / `num_iters` are shared with the scenario-generation optimization configuration.

---

## 3. Outputs

### 3.1 Solution latent variables

C-03 returns:

```text
cur_z
```

with target/planner and non-planner latent variables collated back into full scene-graph order.

### 3.2 Solution trajectories

The returned solution trajectory is:

```text
sol_result_traj
```

After optimization, STRIVE calls:

```text
model.decode_embedding(cur_z, ...)
```

**without** passing `nfuture=sol_future_len`, so the returned solution uses M-01's default future horizon.

With the released M-01 configuration:

```text
12 steps = 6 seconds
```

### 3.3 Exact non-planner restoration

After the final default-horizon decode, STRIVE replaces every non-planner trajectory with the original C-02 adversarial trajectory:

```text
sol_result_traj[~tgt_mask] = normalized(other_match_traj)
```

Therefore the saved solution differs from the adversarial scenario primarily through the planner/target response; surrounding agents are explicitly restored to the C-02 trajectories for the returned scenario.

### 3.4 Solution success

`compute_sol_success()` returns a Boolean.

Success requires:

- no collision between the solution planner and any other agent; and
- when map collision checking is enabled, no planner collision with the environment.

### 3.5 Diagnostics

The optimization loop exposes losses such as:

```text
tgt_coll_veh_loss
tgt_coll_env_loss
tgt_motion_prior_loss
tgt_init_loss
other_match_ext_loss
other_motion_prior_ext_loss
```

depending on weights.

The downstream evaluation stack additionally computes kinematic and plausibility statistics for saved solution trajectories.

### 3.6 Downstream serialization

For adversarially successful scenes, `prepare_output_dict()` can serialize:

```text
fut_sol
z_sol
```

alongside initialization and adversarial trajectories.

These fields become part of D-02.

---

## 4. Solution Objective

### 4.1 Planner collision avoidance

C-03 constructs `AvoidCollLoss` with:

```text
single_veh_idx = 0
```

for each scene graph.

Thus the differentiable vehicle-collision objective only includes collisions involving the target/planner node.

Released weight:

```yaml
sol_loss_coll_veh: 10.0
```

### 4.2 Environment collision avoidance

Because `single_veh_idx=0`, the environment collision term is also restricted to the planner/target trajectory.

Released weight:

```yaml
sol_loss_coll_env: 10.0
```

### 4.3 Motion-prior regularization

The target/planner latent is regularized under the M-01 prior using `MotionPriorLoss`:

```text
-log p(z_target | past, map, interactions)
```

Released weight:

```yaml
sol_loss_motion_prior: 0.005
```

### 4.4 Initialization-latent regularization

`AvoidCollLoss` supports an initialization-latent penalty:

```text
||z_initial - z||²
```

The parser default is:

```text
sol_loss_init_z = 0.0
```

and the public rule-based/replay config files do not override it.

Therefore this target-latent initialization penalty is disabled in the released configs.

### 4.5 Non-planner trajectory preservation

Non-planner agents are decoded in a separate pass and matched to their C-02 adversarial trajectories using `TgtMatchingLoss`.

Released matching weight:

```yaml
sol_loss_match_ext: 10.0
```

### 4.6 Non-planner prior diagnostic / released loss behavior

Released weight:

```yaml
sol_loss_motion_prior_ext: 0.001
```

As in C-01 and the target-matching branch of C-02, the public `TgtMatchingLoss` computes the non-planner motion-prior loss but the total-loss expression applies `motion_prior_ext` to `tgt_loss.mean()` again rather than to `motion_prior_loss.mean()`.

Therefore the public C-03 non-planner matching objective effectively weights trajectory matching by:

```text
10.0 + 0.001 = 10.001
```

while the computed non-planner motion-prior value is diagnostic rather than gradient-contributing in that matching loss.

### 4.7 Weighted total objective

For the released configurations, the target/planner branch is conceptually:

```text
L_target =
  10.0  × vehicle-collision avoidance
+ 10.0  × environment-collision avoidance
+ 0.005 × target motion-prior NLL
+ 0.0   × target latent-distance penalty
```

The non-planner branch preserves C-02 trajectories with the released `TgtMatchingLoss` behavior described above.

The full optimization loss is:

```text
L = L_target + L_other
```

---

## 5. Optimization Procedure

### 5.1 Planner latent initialization

The planner/target latent is initialized from:

```text
tgt_prior_distrib[0]
```

which is the M-01 conditional prior mean.

It is **not** initialized from the planner latent produced by C-02.

The tensor is reshaped to:

```text
[B, 1, D]
```

and optimized with gradients enabled.

### 5.2 Non-planner latent initialization

Non-planner latents are initialized from C-02:

```text
other_z_all = cur_z[~tgt_mask]
```

and reshaped to:

```text
[NA-B, 1, D]
```

### 5.3 Optimized variables

Adam jointly receives:

```text
[tgt_z, other_z_all]
```

However, the two decoder passes isolate gradients:

- target collision-avoidance decode uses `other_z_all.detach()`;
- non-planner matching decode uses `tgt_z.detach()`.

This separates the planner solution search from surrounding-traffic preservation.

### 5.4 Optimizer

Optimizer:

```text
Adam
```

### 5.5 Iteration count

C-03 receives the same `num_iters` variable used by C-02.

Released rule-based configuration:

```text
200 iterations
```

Released replay configuration:

```text
300 iterations
```

### 5.6 Learning rate

C-03 receives the same configured learning rate as C-02:

```text
0.05
```

for both released rule-based and replay configs.

### 5.7 Differentiable decoding

Each iteration performs two decodes.

#### Target/planner branch

```text
planner prior mean z
      │
      ▼
optimize target z
      │
      ▼
M-01 decode with nfuture = sol_future_len
      │
      ▼
planner-only vehicle/environment avoidance
+ planner prior regularization
```

#### Non-planner branch

```text
C-02 non-planner z
      │
      ▼
optimize non-planner z
      │
      ▼
M-01 decode with default future horizon
      │
      ▼
match C-02 adversarial non-planner trajectories
```

### 5.8 Termination

Optimization uses a fixed iteration count. There is no early stopping on:

- collision-free status;
- loss convergence;
- latent displacement.

The final success criterion is evaluated only after the final returned trajectory is built.

---

## 6. Collision Avoidance

### 6.1 Planner-to-agent collision loss

`AvoidCollLoss` constructs `VehCollLoss` with:

```text
single_veh_idx = 0
```

so only vehicle collisions involving the planner/target are penalized.

The differentiable collision approximation uses five circles along each vehicle body.

### 6.2 Planner-to-environment collision loss

The environment loss checks the target vehicle against the drivable-area raster and penalizes penetration into non-drivable space.

### 6.3 Collision interpolation

Before collision penalties, `AvoidCollLoss` applies:

```text
interp_traj(..., scale_factor=3)
```

to reduce between-timestep collision tunneling.

### 6.4 Collision buffer

C-03 instantiates `AvoidCollLoss` with:

```text
veh_coll_buffer = 0.5
```

meters.

This is larger than C-02's default adversarial optimization buffer (`0.1`), giving the solution planner additional clearance during differentiable collision avoidance.

### 6.5 Final vehicle-collision validation

`compute_sol_success()` uses the polygon-based `check_single_veh_coll()` test rather than the differentiable circle loss.

The shared public threshold is:

```text
vehicle polygon IoU > 0.02
```

for a collision.

---

## 7. Non-Planner Preservation

### 7.1 Adversarial trajectory target

The non-planner matching target comes directly from C-02's final adversarial scenario:

```text
final_result_traj[:, 0]
```

with planner nodes removed.

### 7.2 Matching loss

The non-planner branch minimizes squared error between the decoded non-planner future and the adversarial target future.

Released weight:

```text
sol_loss_match_ext = 10.0
```

### 7.3 Motion-prior term

The config supplies:

```text
sol_loss_motion_prior_ext = 0.001
```

but, due to the public `TgtMatchingLoss` implementation, this coefficient multiplies the trajectory matching term in the total loss rather than the calculated motion-prior term.

### 7.4 Gradient isolation

During target/planner optimization:

```text
other_z_all.detach()
```

prevents target collision losses from changing non-planner latents.

During non-planner matching:

```text
tgt_z.detach()
```

prevents matching losses from changing the planner latent.

### 7.5 Returned non-planner trajectories

Even though non-planner latents are optimized during C-03, the returned `sol_result_traj` explicitly overwrites non-planner decoder results with the original C-02 adversarial trajectories.

Thus D-02's saved `fut_sol` preserves adversarial non-planner motion exactly at the returned horizon.

---

## 8. Future Horizon

### 8.1 Default solution optimization horizon

Released value:

```yaml
sol_future_len: 16
```

At M-01's 2 Hz timestep:

```text
16 steps = 8 seconds
```

### 8.2 Relationship to M-01 horizon

M-01 default:

```text
12 steps = 6 seconds
```

C-03's planner collision-avoidance branch therefore optimizes four additional future steps.

### 8.3 Motivation

The parser help text states that using a solution horizon longer than the model/data future length helps avoid:

```text
irrecoverable final states
```

In practical terms, the optimizer should not merely move a collision just beyond the ordinary 6-second horizon if the state at that boundary is already unrecoverable.

### 8.4 Asymmetric optimization horizons

The two C-03 decoder branches use different horizons:

- target/planner collision-avoidance decode: `16` steps by default;
- non-planner trajectory-matching decode: M-01 default `12` steps.

This is the public implementation.

### 8.5 Returned and saved horizon

After optimization, C-03 calls `decode_embedding()` without an `nfuture` override. Therefore:

- final returned planner solution: default 12 steps;
- restored non-planner adversarial trajectories: 12 steps;
- saved `fut_sol`: default 12-step horizon.

The 16-step horizon is used for optimization regularization, not for the final serialized solution trajectory.

---

## 9. Configuration

### 9.1 Primary configuration

Main rule-based configuration:

```text
configs/adv_gen_rule_based.cfg
```

Replay configuration:

```text
configs/adv_gen_replay.cfg
```

### 9.2 Optimization parameters

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

C-03 inherits these global optimizer settings.

### 9.3 Solution loss weights

Both released configs use:

| Parameter | Value |
|---|---:|
| `sol_future_len` | 16 |
| `sol_loss_motion_prior` | 0.005 |
| `sol_loss_coll_veh` | 10.0 |
| `sol_loss_coll_env` | 10.0 |
| `sol_loss_motion_prior_ext` | 0.001 |
| `sol_loss_match_ext` | 10.0 |

### 9.4 Optional initialization penalty

Parser default:

```text
sol_loss_init_z = 0.0
```

The released rule-based/replay config files omit this key, so the default remains active and the target initialization-latent loss is disabled.

### 9.5 Replay vs rule-based behavior

The core C-03 optimization implementation does not receive a planner object or `planner_name`. It operates on the successful C-02 scenario representation and M-01.

The main differences between released rule-based and replay workflows that reach C-03 are therefore inherited from:

- the C-02 scenario;
- the global iteration count (`200` vs `300`);
- upstream planner behavior.

---

## 10. Quantitative Analysis

### 10.1 Release-configured values

Rule-based C-03:

```text
200 Adam iterations
learning rate 0.05
16-step planner optimization horizon
0.5 m differentiable vehicle-collision buffer
vehicle collision weight 10.0
environment collision weight 10.0
planner prior weight 0.005
non-planner match weight 10.0
```

Replay C-03 differs primarily in using:

```text
300 iterations
```

### 10.2 Latent and trajectory shapes

With M-01 latent dimension `D=32`:

```text
tgt_z            [B, 1, 32]
other_z_all      [NA-B, 1, 32]

target decode
future_pred      [NA, 1, 16, 4]  # multi-sample latent dimension retained

other match decode
future_pred      [NA, 1, 12, 4]  # default M-01 horizon

returned sol_result_traj
                 [NA, 12, 4]
```

Exact shapes depend on M-01's multi-sample decoding behavior and configured horizons.

### 10.3 Kinematic statistics

Downstream scenario evaluation can report solution statistics including:

```text
sol_vel_mean
sol_vel_max
sol_acc_mean
sol_acc_max
sol_hdot_mean
sol_hdot_max
sol_hddot_mean
sol_hddot_max
```

These are evaluation outputs, not intrinsic C-03 optimization parameters.

### 10.4 Collision metrics

Downstream metrics include:

```text
sol_coll_others
sol_coll_env
sol_success
```

The authoritative binary success function for generation is `compute_sol_success()`.

### 10.5 Runtime / convergence

Runtime scales with:

- number of successful C-02 scenes;
- agent count;
- graph complexity;
- 16-step target rollout;
- 200/300 optimizer iterations;
- M-01 decode cost.

Only adversarial successes incur C-03 cost.

### 10.6 Profiler

Run:

```bash
python tools/profile_solution_optimization.py \
  --repo-root . \
  --output ./out/solution_optimization_profile.yaml
```

or merge into metadata:

```bash
python tools/profile_solution_optimization.py \
  --repo-root . \
  --metadata ./metadata/components/solution_optimization.yaml
```

---

## 11. Success Criteria

### 11.1 Vehicle collision criterion

C-03 fails if the returned planner solution collides with **any** other agent according to `check_single_veh_coll()`.

The result is:

```text
planner_coll_others = any(planner_coll_all)
```

### 11.2 Environment collision criterion

With the default:

```text
use_map_coll = True
```

C-03 also fails if the planner/ego solution collides with the environment according to `compute_coll_rate_env(..., ego_only=True)`.

### 11.3 Combined success

The public logic is:

```text
sol_impossible =
    planner_collides_with_any_other_agent
    OR
    planner_collides_with_environment
```

and:

```text
sol_success = not sol_impossible
```

### 11.4 Relationship to C-02

C-03 is only run on scenes for which C-02's selected attacker successfully collided with the planner.

Therefore `sol_success` should always be interpreted conditional on prior adversarial success.

### 11.5 No claim of global impossibility

A failed C-03 optimization means the released optimizer did not find a collision-free modeled response under its settings. It does **not** prove that no valid real-world or model-space solution exists.

---

## 12. Scenario Partitioning

### 12.1 `adv_sol_success`

A scene enters:

```text
adv_sol_success
```

when:

```text
C-02 adversarial success = True
C-03 solution success    = True
```

### 12.2 `sol_failed`

A scene enters:

```text
sol_failed
```

when:

```text
C-02 adversarial success = True
C-03 solution success    = False
```

### 12.3 `adv_failed`

A scene enters:

```text
adv_failed
```

when C-02 fails. C-03 is not run for that scene.

### 12.4 Downstream D-02 implications

The saved scenario JSON can include:

```text
fut_init
fut_adv
fut_sol        # when C-02 succeeded and C-03 was run
z_adv
z_sol
z_prior
attack_agt
attack_t
```

The folder partition communicates whether adversarial and solution optimization succeeded.

D-02 should preserve that distinction rather than treating all generated JSON files as equivalent examples.

---

## 13. Validation

### 13.1 Collision validation

Final success should be recomputed from the returned solution trajectory using:

- polygon vehicle-collision checks;
- environment collision checks.

Do not infer success only from the differentiable training losses.

### 13.2 Environment validation

Verify that the final 12-step planner trajectory does not trigger the environment-collision metric with `ego_only=True`.

### 13.3 Preservation validation

Because non-planner trajectories are explicitly restored from C-02 in the returned solution, verify exact equality after normalization/serialization where practical.

### 13.4 Plausibility validation

Useful checks include:

- planner latent NLL under M-01 prior;
- planner velocity/acceleration;
- heading rate/acceleration;
- visual inspection;
- final clearance from vehicles and map boundaries.

### 13.5 Numerical validation

Check:

- finite target and other latents;
- finite decoder outputs;
- finite prior variances;
- finite losses;
- valid map indices;
- correct horizon lengths.

### 13.6 Reproducibility validation

Record:

- M-01 checkpoint;
- C-02 configuration/outcome;
- `sol_future_len`;
- `num_iters`;
- `lr`;
- solution loss weights;
- code revision.

---

## 14. Failure Modes

### 14.1 No collision-free solution found

The local optimizer may end with a planner collision, causing `sol_failed`.

This does not establish that the adversarial situation is globally unavoidable.

### 14.2 Environment violation

The planner can avoid traffic but move into non-drivable space. With map collision checks enabled, this is still a solution failure.

### 14.3 Non-planner drift during optimization

Non-planner latents are optimized in the matching branch and can drift internally. The returned trajectory is later overwritten with the exact C-02 adversarial non-planner trajectories, but latent values may not perfectly correspond to those overwritten trajectories.

### 14.4 Implausible planner trajectory

The target motion-prior weight is small (`0.005`) relative to collision penalties (`10.0` each). A collision-free solution can therefore move toward lower-prior regions and should be reviewed for plausibility.

### 14.5 Horizon edge effects

The planner is optimized for 16 steps but success is computed on the returned default-horizon 12-step trajectory in the generation caller.

The longer horizon regularizes the solution against near-boundary failures, but the saved success check does not directly validate all 16 optimization steps.

### 14.6 Optimization instability

Potential issues include:

- non-convexity;
- high gradients near collision boundaries;
- map raster discontinuities;
- decoder sensitivity;
- numerical instability in latent likelihood.

---

## 15. Limitations

### 15.1 Local non-convex optimization

Adam with a fixed iteration budget provides no global guarantee. A failure to find a solution is optimizer- and initialization-dependent.

### 15.2 Learned-prior dependence

The solution space is constrained by M-01. Behaviors that a real vehicle could execute may not be well represented by the learned decoder.

### 15.3 Collision approximation

Training uses interpolated circle/map penalties, while final vehicle collision success uses polygon IoU. The two may disagree around geometric boundaries.

### 15.4 Finite horizon

The optimization extends the planner horizon to 8 seconds but remains finite.

### 15.5 Planner interpretation

The C-03 solution is a trajectory generated through M-01 latent optimization. It is not the output of the attacked rule-based planner and is not automatically dynamically executable by a production controller.

### 15.6 Returned-horizon asymmetry

The public release optimizes the target for 16 steps but returns and validates a default 12-step solution. Reimplementations that return all 16 steps are behaviorally different from the public implementation.

---

## 16. Safety & Interpretation

### 16.1 Meaning of solution success

A successful C-03 result shows that STRIVE's learned model found a collision-free counterfactual planner trajectory while preserving the adversarial surrounding traffic at the returned horizon.

It does not prove that the attacked planner itself could produce that response.

### 16.2 Counterfactual interpretation

The solution is best understood as:

```text
"Within the STRIVE model, a collision-free alternative trajectory exists."
```

rather than:

```text
"The real planner was guaranteed to be able to avoid the collision."
```

### 16.3 Use in planner diagnosis

The adversarial/solution pair helps separate:

- scenarios where the tested planner fails despite a modeled alternative; from
- scenarios where the released solution optimizer cannot find an alternative.

This remains model- and optimizer-dependent.

### 16.4 Research-use boundary

C-03 is intended for offline scenario analysis and planner robustness research, not direct operational control.

---

## 17. Reproducibility

### 17.1 Source files

```text
src/utils/sol_optim.py
src/losses/adv_gen_nusc.py
src/adv_scenario_gen.py
src/utils/adv_gen_optim.py
```

### 17.2 Configuration files

```text
configs/adv_gen_rule_based.cfg
configs/adv_gen_replay.cfg
```

### 17.3 Companion metadata

```text
metadata/components/solution_optimization.yaml
```

### 17.4 Quantitative profiler

```text
tools/profile_solution_optimization.py
```

### 17.5 Required dependencies

C-03 requires:

- a C-02 adversarial success;
- M-01 checkpoint and normalizers;
- M-01 embeddings/prior;
- map environment;
- PyTorch autograd;
- scene graph and agent dimensions.

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
  │
  ▼
C-02 — Adversarial Optimization
```

### 18.2 Downstream

```text
D-02 — Generated Scenarios Data Card
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
  │
  ▼
D-02  Generated Scenarios Data Card
```

---

## 19. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.  
   https://openaccess.thecvf.com/content/CVPR2022/html/Rempe_Generating_Useful_Accident-Prone_Driving_Scenarios_via_a_Learned_Traffic_Prior_CVPR_2022_paper.html

2. STRIVE public repository.  
   https://github.com/nv-tlabs/STRIVE

3. Relevant release files:
   - `src/utils/sol_optim.py`
   - `src/losses/adv_gen_nusc.py`
   - `src/adv_scenario_gen.py`
   - `src/utils/adv_gen_optim.py`
   - `configs/adv_gen_rule_based.cfg`
   - `configs/adv_gen_replay.cfg`

4. C-02 — Adversarial Optimization Component Card.

5. C-01 — Initialization Optimization Component Card.

6. M-01 — Main Traffic Model Card.

---

## 20. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed C-03 for the public STRIVE release, including prior-mean planner initialization, 16-step optimization horizon, 12-step returned horizon, and final success semantics. |
