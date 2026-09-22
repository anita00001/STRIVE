# A3-D-01 — STRIVE Collision-Generation Optimizer Falsification Data Card

> **Card ID:** A3-D-01  
> **Card type:** Formal-Assurance Data Card  
> **Status:** Skeleton  
> **Assurance approach:** Specification-Driven Falsification of the Collision-Generation Optimizer  
> **Target:** STRIVE adversarial collision-generation pipeline / optimizer  
> **Primary STRIVE components:** C-01 Initialization Optimization, C-02 Adversarial Optimization, C-03 Solution Optimization  
> **System:** S-01 — STRIVE  
> **Primary assurance question:** Can STRIVE generate concrete trajectories that violate explicitly stated AV safety specifications?

---

## 1. Dataset Summary

### 1.1 Dataset / evidence-set name
<!-- Canonical name for falsification evidence. -->

### 1.2 Assurance purpose
<!-- Define how the data supports specification-driven falsification. -->

### 1.3 Falsification target
<!-- Exact STRIVE optimizer/pipeline/configuration being exercised. -->

### 1.4 Dataset role
<!-- Seed scenes, specifications, generated candidates, counterexamples, regression cases. -->

### 1.5 Dataset status
<!-- Proposed / generated / frozen / validated. -->

---

## 2. Assurance Claim Context

### 2.1 Top-level assurance objective
<!-- Search for violations of explicit AV safety requirements. -->

### 2.2 Falsification semantics
<!-- A violating trajectory is a concrete counterexample to the specification. -->

### 2.3 Supported claims
<!-- STRIVE can/cannot find violations within the defined search domain and budget. -->

### 2.4 Unsupported claims
<!-- Failure to find a violation is not proof of safety. -->

### 2.5 Evidence interpretation
<!-- Counterexample / no counterexample found / invalid candidate / inconclusive. -->

---

## 3. STRIVE Falsification Target

### 3.1 Collision-generation pipeline
<!-- C-01 -> C-02 -> C-03 relationship. -->

### 3.2 Planner under attack
<!-- Replay vs Rule-based / exact configuration. -->

### 3.3 Learned traffic prior
<!-- M-01 role in constraining realistic traffic. -->

### 3.4 Adversarial optimizer
<!-- C-02 role in inducing planner collision. -->

### 3.5 Solution optimizer
<!-- C-03 role in finding a collision-free response. -->

### 3.6 Generated-scenario output
<!-- D-02 relationship. -->

---

## 4. Safety Specifications

### 4.1 Specification registry
<!-- Versioned list of formal requirements. -->

### 4.2 TTC specification

```text
φ_TTC = G(TTC > 1.5 s)
```

<!-- Exact temporal semantics and TTC definition. -->

### 4.3 Minimum-separation specification

```text
φ_sep = G(d_ego > d_min)
```

<!-- Exact distance geometry, threshold, and temporal semantics. -->

### 4.4 Additional candidate specifications
<!-- Collision freedom, speed, acceleration, drivable area, etc. -->

### 4.5 Specification source
<!-- Project requirement / standard / research assumption. -->

### 4.6 Specification versioning
<!-- IDs, versions, units, threshold provenance. -->

---

## 5. Seed Data Sources

### 5.1 nuScenes source scenes
<!-- Natural traffic seeds. -->

### 5.2 D-01 relationship
<!-- STRIVE nuScenes representation. -->

### 5.3 Planner-specific seed filtering
<!-- Scenes eligible for replay/rule-based planner attack. -->

### 5.4 Map context
<!-- nuScenes map metadata/raster. -->

### 5.5 Initial traffic trajectories
<!-- Ground-truth / C-01 fitted initialization. -->

---

## 6. Falsification Input Schema

### 6.1 Source scene identity
<!-- nuScenes scene/sample token or run-local ID. -->

### 6.2 Planner identity
<!-- Planner type/configuration/hash. -->

### 6.3 Traffic-model identity
<!-- M-01 checkpoint/config/hash. -->

### 6.4 Optimization configuration
<!-- C-01/C-02/C-03 settings. -->

### 6.5 Initial latent state
<!-- z initialization / prior/posterior origin. -->

### 6.6 Safety specification
<!-- Property ID/version/parameters. -->

### 6.7 Search budget
<!-- Iterations, restarts, timeout, seeds. -->

---

## 7. Falsification Output Schema

### 7.1 Generated trajectory
<!-- Planner and non-ego futures. -->

### 7.2 Specification trace
<!-- TTC / distance / other predicate values over time. -->

### 7.3 Robustness / violation score
<!-- If temporal-logic robustness or equivalent is used. -->

### 7.4 Violation status
<!-- Counterexample / no violation found / invalid. -->

### 7.5 Violating timestep
<!-- Earliest or worst violation. -->

### 7.6 Violating agent(s)
<!-- Ego and interacting agent IDs. -->

### 7.7 STRIVE success partition
<!-- adv_failed / sol_failed / adv_sol_success if retained. -->

---

## 8. Counterexample Definition

### 8.1 Formal counterexample
<!-- Generated trajectory violating φ. -->

### 8.2 STRIVE collision success vs specification violation
<!-- Keep these concepts distinct. -->

### 8.3 Replay-confirmed counterexample
<!-- Re-evaluate exact specification on saved trajectory. -->

### 8.4 Invalid counterexample
<!-- NaN, preprocessing mismatch, unsupported geometry, etc. -->

### 8.5 Minimality / severity
<!-- Optional metrics such as robustness margin or earliest violation. -->

---

## 9. Specification Signals

### 9.1 Time-to-Collision
<!-- Definition, relative state, edge cases. -->

### 9.2 Minimum vehicle separation
<!-- Center distance / polygon distance / circle approximation. -->

### 9.3 Collision indicator
<!-- Exact geometry / IoU / overlap. -->

### 9.4 Relative speed
<!-- Optional derived signal. -->

### 9.5 Ego acceleration
<!-- Optional comfort/safety specification. -->

### 9.6 Drivable-area status
<!-- Optional map specification. -->

---

## 10. Temporal Semantics

### 10.1 Horizon
<!-- Which STRIVE future horizon is checked. -->

### 10.2 Sampling rate
<!-- Native model/planner dt vs interpolated checking. -->

### 10.3 Always / eventually operators
<!-- Exact interpretation of G/F if temporal logic is used. -->

### 10.4 First-violation time
<!-- How earliest violation is computed. -->

### 10.5 Continuous-time approximation
<!-- Interpolation policy between discrete samples. -->

---

## 11. Search-Space Definition

### 11.1 Latent variables
<!-- Target and non-ego latent variables optimized by STRIVE. -->

### 11.2 Agent selection
<!-- Attack-agent candidate logic. -->

### 11.3 Scene constraints
<!-- Fixed map, vehicle attributes, semantics. -->

### 11.4 Planner response
<!-- Fixed/recomputed planner trajectory depending on attack mode. -->

### 11.5 Search bounds
<!-- Any explicit latent/state/trajectory bounds. -->

### 11.6 Restarts / random seeds
<!-- Multiple-search strategy. -->

---

## 12. Case Construction

### 12.1 Natural seed scenes
<!-- nuScenes anchors. -->

### 12.2 Replay-planner falsification cases
<!-- Ego replay variant. -->

### 12.3 Rule-based-planner falsification cases
<!-- Hardcode/M-02 variant. -->

### 12.4 Boundary cases
<!-- Seeds close to TTC/separation threshold. -->

### 12.5 Counterexample-directed cases
<!-- Seeds refined from prior violations. -->

### 12.6 Regression cases
<!-- Persisted known violations. -->

---

## 13. Partitioning

### 13.1 Development partition
<!-- Specification/debugging/tuning. -->

### 13.2 Falsification evaluation partition
<!-- Frozen final seeds. -->

### 13.3 Regression partition
<!-- Known counterexamples. -->

### 13.4 Planner-specific partitions
<!-- Replay vs Rule-based. -->

### 13.5 Leakage controls
<!-- Keep specification tuning separate from final evaluation. -->

---

## 14. Data Transformations

### 14.1 STRIVE normalization
<!-- Input/output normalization. -->

### 14.2 Coordinate frames
<!-- Local/global transforms. -->

### 14.3 Trajectory interpolation
<!-- For TTC/collision checking. -->

### 14.4 Vehicle geometry
<!-- Rectangle / circle / point approximation. -->

### 14.5 Map transformations
<!-- Raster/global map relation. -->

### 14.6 Specification evaluator preprocessing
<!-- Any transformation before property evaluation. -->

---

## 15. Quantitative Dataset Profile

### 15.1 Number of seed scenes
<!-- To be measured. -->

### 15.2 Number of optimization runs
<!-- To be measured. -->

### 15.3 Planner distribution
<!-- Replay vs Rule-based. -->

### 15.4 Specification distribution
<!-- TTC / separation / combined. -->

### 15.5 Counterexample count
<!-- Per property/planner. -->

### 15.6 Violation severity
<!-- Min TTC, min separation, robustness score. -->

### 15.7 Runtime / iteration statistics
<!-- To be measured. -->

---

## 16. Coverage Strategy

### 16.1 Scene coverage
<!-- Maps, traffic density, interaction geometry. -->

### 16.2 Planner coverage
<!-- Replay / Rule-based / configurations. -->

### 16.3 Specification coverage
<!-- Different properties and thresholds. -->

### 16.4 Boundary coverage
<!-- Near-threshold seeds. -->

### 16.5 Attack-agent coverage
<!-- Different non-ego agents. -->

### 16.6 Failure-mode coverage
<!-- Collision, near miss, TTC violation, distance violation. -->

---

## 17. Validation & Quality Assurance

### 17.1 Schema validation
<!-- Required IDs/configs/property fields. -->

### 17.2 Specification evaluator tests
<!-- Unit tests for TTC/separation/etc. -->

### 17.3 Optimizer replay
<!-- Re-run or replay saved STRIVE output. -->

### 17.4 Counterexample re-evaluation
<!-- Independent property evaluation on saved trajectories. -->

### 17.5 Geometry consistency
<!-- Ensure one collision/separation semantics per property. -->

### 17.6 Numerical tolerance
<!-- Discrete interpolation / floating-point tolerance. -->

---

## 18. Falsification Metrics

### 18.1 Falsification success rate
<!-- Fraction of runs/seeds yielding a violation. -->

### 18.2 Time / iterations to first violation
<!-- Search efficiency. -->

### 18.3 Robustness margin
<!-- If quantitative semantics used. -->

### 18.4 Minimum TTC
<!-- Severity. -->

### 18.5 Minimum separation
<!-- Severity. -->

### 18.6 Unique counterexample count
<!-- Avoid duplicate trajectories/scenes. -->

---

## 19. Known Limitations

### 19.1 Falsification is not verification
<!-- No counterexample found != proof of safety. -->

### 19.2 Optimizer local minima
<!-- Gradient/local search limitations. -->

### 19.3 Traffic-prior bias
<!-- Search constrained by M-01. -->

### 19.4 Planner-model dependence
<!-- Counterexamples depend on attacked planner/config. -->

### 19.5 Specification incompleteness
<!-- TTC/separation do not capture all safety requirements. -->

### 19.6 Discrete-time approximation
<!-- Violations may occur between samples. -->

### 19.7 Ground-truth limits
<!-- Generated counterexamples are synthetic, not observed crashes. -->

---

## 20. Safety & Assurance Interpretation

### 20.1 Meaning of a found violation
<!-- Concrete counterexample to the exact specification. -->

### 20.2 Meaning of no violation found
<!-- Search failure only; no proof. -->

### 20.3 Meaning of STRIVE adversarial success
<!-- Distinct from formal spec violation unless property confirms it. -->

### 20.4 Meaning of C-03 solution success
<!-- Operational usefulness, not formal solvability proof. -->

### 20.5 System-level inference limits
<!-- Counterexample says requirement is violated by this planner/scenario; not universal deployment frequency. -->

---

## 21. Reproducibility & Provenance

### 21.1 STRIVE revision
<!-- Exact repository revision. -->

### 21.2 Model checkpoint
<!-- M-01 hash. -->

### 21.3 Planner configuration
<!-- M-02/replay config. -->

### 21.4 Optimizer configuration
<!-- C-01/C-02/C-03 parameters. -->

### 21.5 Specification version
<!-- Property registry hash/version. -->

### 21.6 Seed scene identity
<!-- nuScenes provenance. -->

### 21.7 Random seeds
<!-- Search reproducibility. -->

### 21.8 Generated counterexample artifact
<!-- JSON/hash/path. -->

---

## 22. Relationships

### 22.1 Upstream

```text
D-01 — STRIVE nuScenes Data
M-01 — STRIVE Main Traffic Model
M-02 — STRIVE Rule-Based Planner (hardcode path)
C-01 — Initialization Optimization
C-02 — Adversarial Optimization
C-03 — Solution Optimization
```

### 22.2 Downstream

```text
D-02 — STRIVE Generated Scenarios
```

### 22.3 Assurance approach

```text
Approach 3 — Specification-Driven Falsification
```

### 22.4 Companion assurance model card
<!-- Future A3-M-01 model card. -->

### 22.5 Relationship to planner evaluation
<!-- Counterexamples can be replayed/evaluated against attacked planner. -->

---

## 23. Terms of Art

### 23.1 Safety specification
<!-- Formal requirement over a trajectory. -->

### 23.2 Falsification
<!-- Search for a violating execution. -->

### 23.3 Counterexample
<!-- Concrete trajectory violating the specification. -->

### 23.4 Robustness score
<!-- Quantitative distance to satisfaction/violation if used. -->

### 23.5 Seed scene
<!-- Natural STRIVE/nuScenes starting scenario. -->

### 23.6 Search budget
<!-- Iterations/restarts/time allowed. -->

### 23.7 Specification evaluator
<!-- Executable/formal function deciding satisfaction. -->

---

## 24. References

<!-- Formal Assurance in STRIVE project concept PDF -->
<!-- STRIVE paper -->
<!-- D-01 nuScenes Data Card -->
<!-- D-02 Generated Scenarios Data Card -->
<!-- C-01 Initialization Optimization Card -->
<!-- C-02 Adversarial Optimization Card -->
<!-- C-03 Solution Optimization Card -->
<!-- M-02 Rule-Based Planner Card -->
<!-- selected falsification / temporal-logic tool references once chosen -->

---

## 25. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial Approach-3 specification-driven collision-optimizer falsification data-card skeleton |
