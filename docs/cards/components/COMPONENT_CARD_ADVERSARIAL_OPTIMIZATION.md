# C-02 — Adversarial Optimization Component Card

> **Card ID:** C-02  
> **Card type:** Component Card  
> **Status:** Skeleton  
> **Component:** STRIVE Adversarial Optimization  
> **Upstream:** C-01 — Initialization Optimization, M-01 — Main Traffic Model  
> **Downstream:** C-03 — Solution Optimization

---

## 1. Component Summary

### 1.1 Purpose
<!-- What does adversarial optimization do in STRIVE? -->

### 1.2 Role in the STRIVE pipeline
<!-- Explain how it transforms an initialized scene into an accident-prone scenario. -->

### 1.3 Primary implementation
<!-- `src/utils/adv_gen_optim.py`, `src/adv_scenario_gen.py`, and relevant loss code. -->

---

## 2. Inputs

### 2.1 Initialized latent variables
<!-- Output of C-01 and how it seeds adversarial optimization. -->

### 2.2 Scene graph
<!-- Required agent, map, and graph fields. -->

### 2.3 Traffic-model embeddings
<!-- M-01 prior/map/past embeddings. -->

### 2.4 Planner trajectory
<!-- Rule-based or replay planner target trajectory. -->

### 2.5 Attack-agent information
<!-- Feasible attacker set, selected attacker/time if fixed. -->

### 2.6 Configuration inputs
<!-- LR, iterations, loss weights, collision settings, feasibility constraints. -->

---

## 3. Outputs

### 3.1 Adversarial latent variables
<!-- `z_adv` or equivalent. -->

### 3.2 Adversarial trajectories
<!-- Decoded multi-agent trajectories after optimization. -->

### 3.3 Selected attacker
<!-- Attacking-agent index. -->

### 3.4 Attack time
<!-- Collision/attack timestep. -->

### 3.5 Optimization diagnostics
<!-- Losses, minimum distances, prior likelihoods, collision metrics. -->

### 3.6 Downstream interface
<!-- Inputs passed into C-03. -->

---

## 4. Attack Objective

### 4.1 Planner-crash objective
<!-- Encourage an attacker trajectory to approach/collide with the planner. -->

### 4.2 Soft minimum over agents and time
<!-- How STRIVE differentiably selects likely attacker/time. -->

### 4.3 Attacker restrictions
<!-- Fixed attacker, in-front constraint, category restriction. -->

### 4.4 Crash-loss weighting
<!-- Release-configured value. -->

---

## 5. Plausibility & Regularization Objectives

### 5.1 Motion-prior loss
<!-- Keep non-attacker trajectories likely under M-01. -->

### 5.2 Attacker motion-prior loss
<!-- Separate reduced weight for the attacking vehicle. -->

### 5.3 Initialization-latent loss
<!-- Stay near C-01 latent initialization. -->

### 5.4 Attacker initialization loss
<!-- Separate attacker weight. -->

### 5.5 External trajectory matching
<!-- Preserve externally controlled/planner trajectories where applicable. -->

---

## 6. Collision Regularization

### 6.1 Non-planner vehicle collisions
<!-- Penalize unwanted agent-agent collisions. -->

### 6.2 Planner collision weighting
<!-- Distinguish desired attacker-planner collision from unwanted planner interactions. -->

### 6.3 Environment collisions
<!-- Penalize non-drivable-area violations. -->

### 6.4 Trajectory interpolation
<!-- Higher-resolution interpolation used for collision penalties. -->

---

## 7. Optimization Procedure

### 7.1 Latent initialization
<!-- Start from C-01 optimized latents. -->

### 7.2 Optimized variables
<!-- Which agents' latent variables are optimized. -->

### 7.3 Optimizer
<!-- Adam. -->

### 7.4 Iteration count
<!-- Release-configured `num_iters`. -->

### 7.5 Learning rate
<!-- Release-configured `lr`. -->

### 7.6 Planner-in-the-loop behavior
<!-- Rule-based closed-loop rollout vs replay planner. -->

### 7.7 Attack-agent/time determination
<!-- Dynamic selection and final extraction. -->

### 7.8 Termination
<!-- Fixed iterations and final evaluation. -->

---

## 8. Planner Integration

### 8.1 Supported planner types
<!-- Rule-based / replay. -->

### 8.2 Rule-based planner
<!-- How planner rollout is recomputed against generated traffic. -->

### 8.3 Replay planner
<!-- How observed ego/planner future is treated. -->

### 8.4 Planner configuration
<!-- Default vs tuned configuration. -->

---

## 9. Feasibility Filtering

### 9.1 Seed feasibility
<!-- Distance-based feasibility before adversarial optimization. -->

### 9.2 Minimum time
<!-- Earliest timestep eligible for attack if configured. -->

### 9.3 Relative-position constraints
<!-- In-front filtering. -->

### 9.4 Velocity constraints
<!-- Minimum motion for candidate attackers. -->

### 9.5 Map-separation check
<!-- Non-drivable separation between planner and attacker. -->

### 9.6 Agent-category restriction
<!-- Optional `adv_attack_with`. -->

---

## 10. Configuration

### 10.1 Primary configuration
<!-- `configs/adv_gen_rule_based.cfg`. -->

### 10.2 Optimization parameters
<!-- num_iters, lr. -->

### 10.3 Adversarial loss weights
<!-- coll_veh, coll_veh_plan, coll_env, init_z, motion_prior, adv_crash, etc. -->

### 10.4 Feasibility parameters
<!-- Source/config defaults. -->

### 10.5 Planner parameters
<!-- planner, planner_cfg. -->

---

## 11. Quantitative Analysis

### 11.1 Release-configured values
<!-- Exact adversarial-stage weights and optimizer settings. -->

### 11.2 Latent dimensions
<!-- Symbolic and default shapes. -->

### 11.3 Collision-success metrics
<!-- `adv_success`, planner/attacker collision state, attack time. -->

### 11.4 Plausibility metrics
<!-- Latent likelihood and trajectory regularization. -->

### 11.5 Runtime / convergence metrics
<!-- Optional local measurements. -->

### 11.6 Profiler
<!-- `tools/profile_adversarial_optimization.py` -->

---

## 12. Success Criteria

### 12.1 Adversarial success
<!-- Definition used by STRIVE after optimization. -->

### 12.2 Target collision
<!-- Collision with the selected attacking agent. -->

### 12.3 Unwanted collisions
<!-- Other planner/agent/environment collisions. -->

### 12.4 Saved scenario status
<!-- How success/failure affects result partitioning. -->

---

## 13. Validation

### 13.1 Collision validation
<!-- Final collision check at evaluation resolution. -->

### 13.2 Planner consistency
<!-- Ensure reported collision uses actual planner rollout. -->

### 13.3 Plausibility validation
<!-- Prior likelihood, collision penalties, map constraints. -->

### 13.4 Numerical validation
<!-- NaNs, invalid latent values, unstable gradients. -->

### 13.5 Reproducibility validation
<!-- Config, checkpoint, planner version, source revision. -->

---

## 14. Failure Modes

### 14.1 No feasible attacker
<!-- Seed rejected before optimization. -->

### 14.2 Optimization fails to induce collision
<!-- `adv_failed`. -->

### 14.3 Unintended collision
<!-- Other-agent or environment collisions dominate. -->

### 14.4 Planner instability
<!-- Planner behavior changes discontinuously during optimization. -->

### 14.5 Implausible latent movement
<!-- Prior/initialization regularizers insufficient. -->

### 14.6 Map exploitation
<!-- Optimization exploits raster/map limitations. -->

---

## 15. Limitations

### 15.1 Local non-convex optimization
<!-- Dependence on initialization and local minima. -->

### 15.2 Planner-specific scenarios
<!-- Adversarial cases depend on planner implementation/config. -->

### 15.3 Learned-prior limitations
<!-- M-01 defines plausibility. -->

### 15.4 Collision-model approximations
<!-- Circle approximation/interpolation vs final IoU check. -->

### 15.5 Finite horizon
<!-- Only searches within modeled rollout. -->

---

## 16. Safety & Interpretation

### 16.1 Meaning of adversarial success
<!-- A generated failure case for a specified planner, not accident probability. -->

### 16.2 Research-use boundary
<!-- Scenario generation for analysis/testing, not operational attack guidance. -->

### 16.3 Dependence on model/planner
<!-- Results are conditional on M-01 and selected planner. -->

### 16.4 Human interpretation
<!-- Generated collisions need qualitative/quantitative review. -->

---

## 17. Reproducibility

### 17.1 Source files
<!-- `src/utils/adv_gen_optim.py`, `src/losses/adv_gen_nusc.py`, `src/adv_scenario_gen.py`. -->

### 17.2 Configuration files
<!-- Rule-based and replay adversarial configs. -->

### 17.3 Companion metadata
<!-- `metadata/components/adversarial_optimization.yaml` -->

### 17.4 Quantitative profiler
<!-- `tools/profile_adversarial_optimization.py` -->

### 17.5 Required dependencies
<!-- M-01 checkpoint, C-01 output, planner, maps, PyTorch. -->

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

<!-- STRIVE paper -->
<!-- STRIVE GitHub repository -->
<!-- `src/utils/adv_gen_optim.py` -->
<!-- `src/losses/adv_gen_nusc.py` -->
<!-- `src/adv_scenario_gen.py` -->
<!-- relevant adversarial config files -->
<!-- C-01 and M-01 cards -->

---

## 20. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial C-02 skeleton |
