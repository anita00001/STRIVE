# F-01 — STRIVE Planner Tuning Fitted-Config Card

> **Card ID:** F-01  
> **Card type:** Fitted-Config Card  
> **Status:** Skeleton  
> **Configuration:** STRIVE Rule-Based Planner Tuning  
> **Upstream:** M-04 — Accident Classifier / Scenario Classification  
> **Applies to:** STRIVE Rule-Based Planner

---

## 1. Configuration Summary

### 1.1 Purpose
<!-- What is being tuned, and why does STRIVE provide tuned planner configurations? -->

### 1.2 Role in the STRIVE pipeline
<!-- Explain how planner configuration affects scenario generation and evaluation. -->

### 1.3 Configuration identity
<!-- Default configuration vs tuned configuration name(s), e.g. `final_tuned_val_1` if verified. -->

### 1.4 Primary implementation
<!-- Planner source, configuration dictionary, evaluation/tuning code. -->

---

## 2. Target Component

### 2.1 Planner
<!-- STRIVE rule-based planner implementation. -->

### 2.2 Planner state and action interface
<!-- Inputs, internal rollout state, output trajectory/control representation. -->

### 2.3 Traffic inputs
<!-- Generated/scenario traffic supplied to the planner. -->

### 2.4 Map dependency
<!-- Semantic map information used by the planner. -->

---

## 3. Motivation for Tuning

### 3.1 Tuning objective
<!-- What planner behavior is intended to improve? -->

### 3.2 Evaluation criteria
<!-- Collision, acceleration, comfort, progress, or other metrics. -->

### 3.3 Relationship to generated scenarios
<!-- Use of D-02 challenging scenarios and regular/source scenarios. -->

### 3.4 Relationship to M-04
<!-- Whether scenario classes directly drive tuning or are used only for analysis/stratification. -->

---

## 4. Tuned Parameters

### 4.1 Planning timestep
<!-- `planner_dt`. -->

### 4.2 Prediction timestep
<!-- `planner_preddt`. -->

### 4.3 Planning horizon
<!-- `planner_nsteps`. -->

### 4.4 Goal / distance thresholds
<!-- `planner_xydistmax`, `planner_cdistang`, etc. -->

### 4.5 Speed and acceleration limits
<!-- `planner_smax`, `planner_accmax`. -->

### 4.6 Prediction scale factors
<!-- `planner_predsfacs`, `planner_predafacs`. -->

### 4.7 Interaction distance
<!-- `planner_interacdist`. -->

### 4.8 Plan acceleration factors
<!-- `planner_planaccfacs`. -->

### 4.9 Candidate speed count
<!-- `planner_plannspeeds`. -->

### 4.10 Collision probability / scoring parameters
<!-- `planner_col_plim`, `planner_score_wmin`, `planner_score_wfac`. -->

---

## 5. Baseline Configuration

### 5.1 Default parameter set
<!-- Values of the released default planner configuration. -->

### 5.2 Baseline provenance
<!-- Source file / config dictionary. -->

### 5.3 Baseline evaluation setting
<!-- Dataset/scenario set used for baseline comparison. -->

---

## 6. Tuned Configuration

### 6.1 Tuned parameter set
<!-- Exact released tuned values, if present. -->

### 6.2 Configuration name
<!-- e.g. `final_tuned_val_1`, subject to verification. -->

### 6.3 Source location
<!-- Exact implementation/config dictionary path. -->

### 6.4 Differences from default
<!-- Parameter-by-parameter delta. -->

---

## 7. Tuning Data

### 7.1 Source scenarios
<!-- Which nuScenes/generated scenario sets were used. -->

### 7.2 Data split
<!-- Train/validation/test or held-out set used for tuning. -->

### 7.3 Generated-scenario partitions
<!-- Which D-02 partitions are relevant. -->

### 7.4 Regular scenarios
<!-- Corresponding source/initialization scenes. -->

### 7.5 Scenario classes
<!-- Whether M-04 labels were used directly, indirectly, or not at all. -->

---

## 8. Tuning Procedure

### 8.1 Search method
<!-- Grid search, manual search, hyperparameter optimization, or other verified method. -->

### 8.2 Search space
<!-- Parameter ranges / candidate values. -->

### 8.3 Objective function
<!-- Metric(s) optimized. -->

### 8.4 Trial evaluation
<!-- How each candidate planner configuration was evaluated. -->

### 8.5 Selection rule
<!-- How the final configuration was chosen. -->

### 8.6 Randomness
<!-- Seeds / randomized validation split / nondeterminism. -->

---

## 9. Evaluation Procedure

### 9.1 Planner evaluation script
<!-- `src/eval_planner.py`. -->

### 9.2 Generated challenging scenarios
<!-- Evaluation on D-02 adversarial scenarios. -->

### 9.3 Regular scenarios
<!-- Evaluation on matched source scenarios. -->

### 9.4 Collision metrics
<!-- Collision rate and relative collision velocity. -->

### 9.5 Comfort metrics
<!-- Mean/forward/lateral acceleration. -->

### 9.6 Aggregate metrics
<!-- Regular, adversarial, total reporting. -->

---

## 10. Quantitative Results

### 10.1 Default configuration results
<!-- Exact released metrics if available. -->

### 10.2 Tuned configuration results
<!-- Exact released metrics if available. -->

### 10.3 Delta vs baseline
<!-- Improvement/regression by metric. -->

### 10.4 Results by scenario class
<!-- Optional M-04-stratified analysis if available. -->

### 10.5 Results by partition
<!-- Generated vs regular scenarios. -->

### 10.6 Profiler
<!-- `tools/profile_planner_tuning.py` -->

---

## 11. Configuration Schema

### 11.1 Parameter names
<!-- Canonical parameter names. -->

### 11.2 Types
<!-- float/int/list types. -->

### 11.3 Units
<!-- seconds, meters, radians/degrees, speeds, etc. -->

### 11.4 Allowed ranges
<!-- If enforced. -->

### 11.5 Coupled parameters
<!-- Parameters whose interpretation depends on other settings. -->

---

## 12. Validation

### 12.1 Configuration completeness
<!-- All required planner parameters present. -->

### 12.2 Type/range validation
<!-- Expected numeric/list types and legal values. -->

### 12.3 Source consistency
<!-- Card/YAML matches implementation dictionary/config. -->

### 12.4 Reproduction check
<!-- Re-run planner evaluation with fitted values. -->

### 12.5 Regression check
<!-- Compare against default configuration. -->

---

## 13. Sensitivity & Robustness

### 13.1 Parameter sensitivity
<!-- Which settings most affect planner behavior. -->

### 13.2 Scenario sensitivity
<!-- Performance across different generated accident classes. -->

### 13.3 Planner-version sensitivity
<!-- Dependence on source code revision. -->

### 13.4 Distribution shift
<!-- Behavior outside nuScenes/STRIVE generated scenarios. -->

---

## 14. Limitations

### 14.1 Tuning-set overfitting
<!-- Tuned values may overfit the selected validation/generated scenarios. -->

### 14.2 Simulator/model dependence
<!-- Results depend on STRIVE trajectory and collision representations. -->

### 14.3 Metric tradeoffs
<!-- Collision reduction vs comfort/progress tradeoffs. -->

### 14.4 Finite evaluation set
<!-- Limited scenario coverage. -->

### 14.5 Scenario-class coverage
<!-- Possible imbalance across M-04 collision classes. -->

---

## 15. Safety & Interpretation

### 15.1 Meaning of improved metrics
<!-- Better STRIVE evaluation metrics do not constitute real-world safety certification. -->

### 15.2 Tuning vs validation separation
<!-- Avoid evaluating only on the same data used to select parameters. -->

### 15.3 Generated-scenario interpretation
<!-- Stress-test performance is conditional on D-02 generation assumptions. -->

### 15.4 Deployment boundary
<!-- Fitted values are research configuration, not production calibration. -->

---

## 16. Reproducibility

### 16.1 Source files
<!-- Planner implementation, configuration dictionary, tuning/evaluation scripts. -->

### 16.2 Input data
<!-- D-02 scenarios and corresponding regular scenes. -->

### 16.3 Fitted artifact
<!-- Exact serialized/config representation of the tuned planner parameters. -->

### 16.4 Companion metadata
<!-- `metadata/fitted_configs/planner_tuning.yaml` -->

### 16.5 Quantitative profiler
<!-- `tools/profile_planner_tuning.py` -->

### 16.6 Dependency versions
<!-- STRIVE revision and runtime dependencies. -->

---

## 17. Relationships

### 17.1 Upstream

```text
D-02 — Generated Scenarios
  │
  ▼
M-03 — Scenario Clustering
  │
  ▼
M-04 — Accident Classifier
```

### 17.2 Applied component

```text
STRIVE Rule-Based Planner
```

### 17.3 Dependency chain

```text
D-02  Generated Scenarios
  │
  ▼
M-03  Scenario Clustering
  │
  ▼
M-04  Accident Classifier
  │
  ▼
F-01  Planner Tuning
```

---

## 18. Terms of Art

### 18.1 Default configuration
<!-- Baseline released planner parameter set. -->

### 18.2 Tuned configuration
<!-- Planner parameter set selected through tuning. -->

### 18.3 Regular scenario
<!-- Source/initialization scenario corresponding to a generated adversarial case. -->

### 18.4 Adversarial scenario
<!-- D-02 generated challenging scenario. -->

### 18.5 Fitted configuration
<!-- Non-model parameter artifact selected using empirical evaluation. -->

---

## 19. References

<!-- STRIVE paper -->
<!-- STRIVE GitHub repository -->
<!-- planner implementation -->
<!-- planner configuration dictionary -->
<!-- `src/eval_planner.py` -->
<!-- tuning source/script if present -->
<!-- `configs/eval_planner.cfg` -->
<!-- D-02, M-03, M-04 cards -->

---

## 20. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial F-01 skeleton |
