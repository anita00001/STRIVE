# C-03 — Solution Optimization Component Card

> **Card ID:** C-03  
> **Card type:** Component Card  
> **Status:** Skeleton  
> **Component:** STRIVE Solution Optimization  
> **Upstream:** C-02 — Adversarial Optimization, M-01 — Main Traffic Model  
> **Downstream:** D-02 — Generated Scenarios Data Card

---

## 1. Component Summary

### 1.1 Purpose
<!-- What does solution optimization do after a successful adversarial scenario is found? -->

### 1.2 Role in the STRIVE pipeline
<!-- Explain how this stage searches for an alternative planner/ego trajectory that avoids the generated collision. -->

### 1.3 Primary implementation
<!-- `src/utils/sol_optim.py`, `src/adv_scenario_gen.py`, relevant loss code. -->

---

## 2. Inputs

### 2.1 Successful adversarial scenario
<!-- Inputs inherited from C-02. -->

### 2.2 Adversarial latent variables
<!-- Starting latent state and which portion is optimized. -->

### 2.3 Adversarial trajectories
<!-- Planner and non-planner futures from C-02. -->

### 2.4 Traffic-model embeddings
<!-- M-01 prior/map/past features. -->

### 2.5 Scene graph and map
<!-- Required agent attributes, graph structure, map indices. -->

### 2.6 Configuration inputs
<!-- Future horizon, optimizer settings, solution loss weights. -->

---

## 3. Outputs

### 3.1 Solution latent variables
<!-- `z_sol` or equivalent. -->

### 3.2 Solution trajectories
<!-- Collision-avoiding future trajectory. -->

### 3.3 Solution success
<!-- Boolean outcome and definition. -->

### 3.4 Diagnostics
<!-- Collision, prior, kinematic, and matching metrics. -->

### 3.5 Downstream serialization
<!-- Fields passed to D-02 generated-scenario JSON. -->

---

## 4. Solution Objective

### 4.1 Planner collision avoidance
<!-- Avoid vehicle collisions involving the planner/target agent. -->

### 4.2 Environment collision avoidance
<!-- Keep planner trajectory in valid drivable area. -->

### 4.3 Motion-prior regularization
<!-- Keep optimized planner latent likely under M-01. -->

### 4.4 Initialization-latent regularization
<!-- Optional penalty relative to C-02 planner latent. -->

### 4.5 Non-planner trajectory preservation
<!-- Keep other agents close to adversarial trajectories. -->

### 4.6 Weighted total objective
<!-- Mathematical description and released weights. -->

---

## 5. Optimization Procedure

### 5.1 Initialization
<!-- Start from C-02 latent/trajectory. -->

### 5.2 Optimized variables
<!-- Which planner/other-agent latents are optimized or held fixed. -->

### 5.3 Optimizer
<!-- Adam and any relevant setup. -->

### 5.4 Iteration count
<!-- Released setting. -->

### 5.5 Learning rate
<!-- Released setting. -->

### 5.6 Extended future horizon
<!-- Why solution uses a longer rollout than default M-01 horizon. -->

### 5.7 Differentiable decoding
<!-- How M-01 is used inside the optimization loop. -->

### 5.8 Termination
<!-- Fixed iteration count / success evaluation. -->

---

## 6. Collision Avoidance

### 6.1 Planner-to-agent collision loss
<!-- Collision loss for the planner against other agents. -->

### 6.2 Planner-to-environment collision loss
<!-- Map/non-drivable collision loss. -->

### 6.3 Collision interpolation
<!-- Any interpolation used before evaluating differentiable collision losses. -->

### 6.4 Collision buffer
<!-- Buffer distance if configured. -->

---

## 7. Non-Planner Preservation

### 7.1 Adversarial trajectory target
<!-- Other agents should preserve the challenging scenario from C-02. -->

### 7.2 Matching loss
<!-- How non-planner trajectories are matched. -->

### 7.3 Motion-prior regularization
<!-- Prior weight for non-planner/external latents. -->

### 7.4 Gradient isolation
<!-- Which latent groups are detached in target/other loss passes. -->

---

## 8. Future Horizon

### 8.1 Default solution horizon
<!-- `sol_future_len`. -->

### 8.2 Relationship to M-01 horizon
<!-- Default M-01 12-step future vs solution 16-step rollout. -->

### 8.3 Motivation
<!-- Avoid solutions that postpone an unavoidable collision beyond the standard horizon. -->

### 8.4 Saved horizon
<!-- Distinguish optimization horizon from scenario serialization/evaluation horizon if applicable. -->

---

## 9. Configuration

### 9.1 Primary configuration
<!-- `configs/adv_gen_rule_based.cfg`. -->

### 9.2 Optimization parameters
<!-- Shared num_iters/lr vs solution-specific settings. -->

### 9.3 Solution loss weights
<!-- `sol_loss_motion_prior`, `sol_loss_coll_veh`, etc. -->

### 9.4 Optional initialization penalty
<!-- `sol_loss_init_z`. -->

### 9.5 Replay vs rule-based behavior
<!-- Whether solution logic differs by planner mode. -->

---

## 10. Quantitative Analysis

### 10.1 Release-configured values
<!-- Exact solution-stage values. -->

### 10.2 Latent and trajectory shapes
<!-- Symbolic/default dimensions. -->

### 10.3 Kinematic statistics
<!-- Velocity, acceleration, heading-rate metrics reported downstream. -->

### 10.4 Collision metrics
<!-- Vehicle/environment collision results. -->

### 10.5 Runtime / convergence
<!-- Optional local measurement. -->

### 10.6 Profiler
<!-- `tools/profile_solution_optimization.py` -->

---

## 11. Success Criteria

### 11.1 Vehicle collision criterion
<!-- Definition of planner-vs-other collision-free success. -->

### 11.2 Environment collision criterion
<!-- Definition of planner map collision-free success. -->

### 11.3 Combined success
<!-- Boolean logic used by `compute_sol_success`. -->

### 11.4 Relationship to C-02
<!-- Solution is only evaluated for adversarially successful scenes. -->

---

## 12. Scenario Partitioning

### 12.1 `adv_sol_success`
<!-- C-02 succeeds and C-03 succeeds. -->

### 12.2 `sol_failed`
<!-- C-02 succeeds but C-03 fails. -->

### 12.3 `adv_failed`
<!-- C-03 not run because C-02 failed. -->

### 12.4 Downstream D-02 implications
<!-- Which partitions are released/evaluated and how success status is represented. -->

---

## 13. Validation

### 13.1 Collision validation
<!-- Confirm planner avoids all other agents. -->

### 13.2 Environment validation
<!-- Confirm planner remains on valid map area. -->

### 13.3 Preservation validation
<!-- Confirm non-planner traffic remains close to C-02 scenario. -->

### 13.4 Plausibility validation
<!-- Prior likelihood and kinematic reasonableness. -->

### 13.5 Numerical validation
<!-- Finite latents/trajectories/losses. -->

### 13.6 Reproducibility validation
<!-- Config, checkpoint, source revision. -->

---

## 14. Failure Modes

### 14.1 No collision-free solution
<!-- Optimizer cannot find planner trajectory avoiding the scenario. -->

### 14.2 Environment violation
<!-- Planner avoids agents but leaves drivable area. -->

### 14.3 Non-planner drift
<!-- Other agents move too far from adversarial scenario. -->

### 14.4 Implausible planner trajectory
<!-- Prior regularization insufficient. -->

### 14.5 Horizon edge effects
<!-- Collision deferred beyond solution horizon. -->

### 14.6 Optimization instability
<!-- Gradient or optimizer failure. -->

---

## 15. Limitations

### 15.1 Local non-convex optimization
<!-- No guarantee a failed solve means no valid solution exists. -->

### 15.2 Learned-prior dependence
<!-- M-01 constrains planner solution space. -->

### 15.3 Collision approximation
<!-- Differentiable losses vs final validation. -->

### 15.4 Finite horizon
<!-- Extended but still bounded. -->

### 15.5 Planner interpretation
<!-- Solution is a learned-model trajectory, not necessarily executable by a real planner/controller. -->

---

## 16. Safety & Interpretation

### 16.1 Meaning of solution success
<!-- Existence of a model-generated collision-free response, not proof of planner safety. -->

### 16.2 Counterfactual interpretation
<!-- Solution is a counterfactual trajectory under STRIVE assumptions. -->

### 16.3 Use in planner diagnosis
<!-- Helps distinguish unavoidable scenarios from planner-specific failures. -->

### 16.4 Research-use boundary
<!-- Offline analysis, not direct operational control. -->

---

## 17. Reproducibility

### 17.1 Source files
<!-- `src/utils/sol_optim.py`, `src/losses/adv_gen_nusc.py`, `src/adv_scenario_gen.py`. -->

### 17.2 Configuration files
<!-- Rule-based/replay adversarial configs. -->

### 17.3 Companion metadata
<!-- `metadata/components/solution_optimization.yaml` -->

### 17.4 Quantitative profiler
<!-- `tools/profile_solution_optimization.py` -->

### 17.5 Required dependencies
<!-- C-02 success, M-01 checkpoint, map environment, PyTorch. -->

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

<!-- STRIVE paper -->
<!-- STRIVE GitHub repository -->
<!-- `src/utils/sol_optim.py` -->
<!-- `src/losses/adv_gen_nusc.py` -->
<!-- `src/adv_scenario_gen.py` -->
<!-- relevant configuration files -->
<!-- C-02, C-01, and M-01 cards -->

---

## 20. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial C-03 skeleton |
