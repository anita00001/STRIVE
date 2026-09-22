# C-01 — Initialization Optimization Component Card

> **Card ID:** C-01  
> **Card type:** Component Card  
> **Status:** Skeleton  
> **Component:** STRIVE Initialization Optimization  
> **Upstream:** M-01 — Main Traffic Model  
> **Downstream:** C-02 — Adversarial Optimization

---

## 1. Component Summary

### 1.1 Purpose
<!-- What is initialization optimization and why does STRIVE need it? -->

### 1.2 Role in the STRIVE pipeline
<!-- Explain how this stage prepares latent variables / trajectories before adversarial optimization. -->

### 1.3 Primary implementation
<!-- `src/utils/init_optim.py` and call sites. -->

---

## 2. Inputs

### 2.1 Scene representation
<!-- Required scene graph fields and map context. -->

### 2.2 Traffic-model inputs
<!-- Embeddings, prior/posterior outputs, latent variables. -->

### 2.3 Initial future trajectory
<!-- What trajectory is being matched and where it comes from. -->

### 2.4 Configuration inputs
<!-- Iterations, learning rate, objective weights, horizon, etc. -->

---

## 3. Outputs

### 3.1 Optimized latent variables
<!-- What latent state is returned. -->

### 3.2 Decoded trajectories
<!-- What trajectory representation is produced. -->

### 3.3 Optimization diagnostics
<!-- Losses, convergence information, success/failure data if exposed. -->

### 3.4 Downstream interface
<!-- What C-02 consumes. -->

---

## 4. Optimization Objective

### 4.1 Trajectory matching objective
<!-- Match decoded trajectory to the observed/initial future. -->

### 4.2 Motion-prior regularization
<!-- Keep optimized latent values plausible under M-01. -->

### 4.3 Weighted total objective
<!-- Mathematical form and release-configured weights. -->

### 4.4 Valid-timestep masking
<!-- How missing/invalid future frames are handled. -->

---

## 5. Optimization Procedure

### 5.1 Initialization
<!-- Initial latent values and embedding state. -->

### 5.2 Optimizer
<!-- Adam and relevant hyperparameters. -->

### 5.3 Iteration count
<!-- Default/release-configured iterations. -->

### 5.4 Differentiable decoding
<!-- How gradients propagate through M-01. -->

### 5.5 Termination
<!-- Fixed iteration vs convergence criterion. -->

---

## 6. Configuration

### 6.1 Relevant configuration file
<!-- Identify config(s) containing initialization-stage values. -->

### 6.2 Core hyperparameters
<!-- lr, num_iters, motion-prior weight, match weight. -->

### 6.3 Model and data dependencies
<!-- D-01/M-01 versions, horizon, categories. -->

### 6.4 Planner dependency
<!-- Clarify whether a planner is used at this stage. -->

---

## 7. Quantitative Analysis

### 7.1 Release-configured values
<!-- Exact hyperparameter values from config. -->

### 7.2 Input/output tensor dimensions
<!-- Symbolic shapes. -->

### 7.3 Optimization trace statistics
<!-- Initial/final loss, iterations, latent movement if profiled. -->

### 7.4 Runtime measurements
<!-- Optional profiler outputs. -->

### 7.5 Profiler
<!-- `tools/profile_initialization_optimization.py` -->

---

## 8. Validation

### 8.1 Functional validation
<!-- Confirm initialization reproduces/matches the reference future within expected tolerance. -->

### 8.2 Numerical validation
<!-- NaNs, exploding latent values, gradient issues. -->

### 8.3 Interface validation
<!-- Compatibility with M-01 and C-02. -->

### 8.4 Reproducibility checks
<!-- Config and repository revision. -->

---

## 9. Failure Modes

### 9.1 Poor trajectory match
<!-- Reasons optimized latent may fail to reproduce initialization. -->

### 9.2 Out-of-prior latent solution
<!-- Excessive deviation from traffic prior. -->

### 9.3 Missing trajectory observations
<!-- Sparse/invalid future data. -->

### 9.4 Optimization instability
<!-- Learning-rate or gradient issues. -->

---

## 10. Limitations

### 10.1 Local optimization
<!-- Non-convexity and sensitivity to initialization. -->

### 10.2 Model dependence
<!-- Limited by M-01 decoder and latent representation. -->

### 10.3 Horizon dependence
<!-- Finite future horizon. -->

### 10.4 Dataset dependence
<!-- Inherited limitations from D-01 and M-01. -->

---

## 11. Safety & Interpretation

### 11.1 Meaning of a successful initialization
<!-- Success means optimization fit, not real-world safety/plausibility guarantee. -->

### 11.2 Downstream risk
<!-- Errors here propagate into adversarial scenario generation. -->

### 11.3 Plausibility interpretation
<!-- Prior regularization is model-relative. -->

---

## 12. Reproducibility

### 12.1 Source files
<!-- `src/utils/init_optim.py` and relevant callers. -->

### 12.2 Configuration files
<!-- Relevant adversarial/refinement configs. -->

### 12.3 Companion metadata
<!-- `metadata/components/initialization_optimization.yaml` -->

### 12.4 Quantitative profiler
<!-- `tools/profile_initialization_optimization.py` -->

### 12.5 Required dependencies
<!-- M-01 checkpoint, D-01-compatible inputs, PyTorch environment. -->

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

<!-- STRIVE paper -->
<!-- STRIVE GitHub repository -->
<!-- `src/utils/init_optim.py` -->
<!-- relevant configuration files -->
<!-- M-01 model card -->
<!-- D-01 data card -->

---

## 15. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial C-01 skeleton |
