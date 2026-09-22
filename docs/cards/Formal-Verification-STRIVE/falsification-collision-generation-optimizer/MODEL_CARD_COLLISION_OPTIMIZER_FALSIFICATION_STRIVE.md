# A3-M-01 — STRIVE Collision-Generation Optimizer Falsification Model Card

> **Card ID:** A3-M-01  
> **Card type:** Formal-Assurance Model Card  
> **Status:** Skeleton  
> **Assurance approach:** Specification-Driven Falsification of the Collision-Generation Optimizer  
> **Target model/process:** STRIVE adversarial collision-generation pipeline  
> **Primary STRIVE components:** C-01 Initialization Optimization, C-02 Adversarial Optimization, C-03 Solution Optimization  
> **Companion data card:** A3-D-01 — STRIVE Collision-Generation Optimizer Falsification Data Card  
> **System:** S-01 — STRIVE

---

## 1. Falsification Model Details

### 1.1 Assurance model summary
<!-- What is being falsified and why? -->

### 1.2 Target pipeline
<!-- C-01 -> C-02 -> C-03 with M-01 and optional M-02. -->

### 1.3 Target artifact identity
<!-- STRIVE revision, M-01 checkpoint, planner/config, optimizer config. -->

### 1.4 Assurance status
<!-- Proposed / encoded / running / counterexample found / inconclusive. -->

### 1.5 Falsification tool / framework
<!-- Tool not yet selected. -->

---

## 2. Purpose & Assurance Role

### 2.1 Primary assurance objective
<!-- Search for concrete trajectories violating explicit AV safety specifications. -->

### 2.2 Why STRIVE is useful for falsification
<!-- Learned traffic prior + optimization searches realistic/challenging traffic. -->

### 2.3 Relationship to planner safety
<!-- Counterexamples expose violations for a specified planner/configuration. -->

### 2.4 Relationship to A3-D-01
<!-- Model method vs seed/specification/result evidence. -->

### 2.5 Out-of-scope claims
<!-- Failure to find a violation is not proof of safety. -->

---

## 3. Falsification Target Boundary

### 3.1 Full STRIVE generation path
<!-- D-01 -> M-01 -> C-01 -> C-02 -> C-03 -> D-02. -->

### 3.2 Replay-planner path
<!-- M-02 bypassed. -->

### 3.3 Rule-based-planner path
<!-- M-02 incorporated before/inside C-02. -->

### 3.4 Selected falsification boundary
<!-- Which components are treated as part of the search system? -->

### 3.5 Excluded components
<!-- Anything held fixed or evaluated externally. -->

---

## 4. STRIVE Search Components

### 4.1 M-01 — Learned traffic model
<!-- Learned prior/decoder defining traffic search space. -->

### 4.2 C-01 — Initialization Optimization
<!-- Fit source/planner initialization. -->

### 4.3 C-02 — Adversarial Optimization
<!-- Primary native collision search stage. -->

### 4.4 C-03 — Solution Optimization
<!-- Operational search for collision-free response. -->

### 4.5 M-02 — Rule-Based Planner
<!-- Required for hardcode path only. -->

### 4.6 D-02 — Generated scenario artifact
<!-- Serialized candidate/counterexample output. -->

---

## 5. Safety Specification Interface

### 5.1 Specification registry
<!-- Versioned property definitions. -->

### 5.2 TTC requirement

```text
φ_TTC = G(TTC > 1.5 s)
```

<!-- Exact TTC definition and temporal semantics. -->

### 5.3 Minimum-separation requirement

```text
φ_sep = G(d_ego > d_min)
```

<!-- Exact geometry and threshold semantics. -->

### 5.4 Collision-freedom requirement
<!-- Exact overlap/IoU/geometry rule. -->

### 5.5 Additional optional specifications
<!-- Speed, acceleration, drivable area, combined formulas. -->

### 5.6 Specification provenance
<!-- Project requirement / standard / research assumption. -->

---

## 6. Formal Falsification Semantics

### 6.1 Satisfaction
<!-- What does it mean for trajectory τ to satisfy φ? -->

### 6.2 Violation
<!-- What does it mean for τ to violate φ? -->

### 6.3 Counterexample
<!-- Concrete saved STRIVE trajectory violating φ. -->

### 6.4 Quantitative robustness
<!-- Optional robustness score if formalism supports it. -->

### 6.5 Unknown / inconclusive
<!-- Timeout/search exhaustion/etc. -->

---

## 7. Inputs to the Falsification Model

### 7.1 Seed scene
<!-- nuScenes source scene. -->

### 7.2 Traffic-model checkpoint
<!-- Exact M-01 checkpoint/hash. -->

### 7.3 Planner
<!-- Replay or Rule-based. -->

### 7.4 Planner configuration
<!-- Exact config/version/hash. -->

### 7.5 Optimizer configuration
<!-- C-01/C-02/C-03 hyperparameters. -->

### 7.6 Specification
<!-- Property ID/version/thresholds. -->

### 7.7 Search budget
<!-- Iterations/restarts/timeout/random seed. -->

---

## 8. Search Variables

### 8.1 Target/planner latent variables
<!-- C-02 target branch variables. -->

### 8.2 Other-agent latent variables
<!-- C-02 non-ego branch variables. -->

### 8.3 Attack-agent selection
<!-- Candidate vs selected attacker. -->

### 8.4 Planner trajectory
<!-- Fixed in replay; recomputed in rule-based path. -->

### 8.5 Optional externally introduced search bounds
<!-- Latent boxes/norm constraints/etc. -->

---

## 9. Native STRIVE Objective vs Safety Specification

### 9.1 Native collision objective
<!-- What C-02 optimizes. -->

### 9.2 Native adversarial success
<!-- STRIVE collision success criterion. -->

### 9.3 External falsification property
<!-- TTC/separation/etc. -->

### 9.4 Non-equivalence
<!-- Native success != automatically formal property violation. -->

### 9.5 Valid external counterexample without native success
<!-- TTC/separation violation can occur without native collision. -->

---

## 10. Planner-Specific Falsification

### 10.1 Replay planner
<!-- Fixed recorded ego future. -->

### 10.2 Rule-based planner
<!-- M-02 replans against generated traffic. -->

### 10.3 Planner configuration dependence
<!-- Counterexamples are planner/config specific. -->

### 10.4 Multi-configuration comparison
<!-- Optional default/tuned planner comparisons. -->

---

## 11. Temporal Semantics

### 11.1 Evaluation horizon
<!-- Start/end time. -->

### 11.2 STRIVE timebases
<!-- M-01 0.5 s, M-02 0.2 s. -->

### 11.3 Interpolation
<!-- How trajectories are aligned for property evaluation. -->

### 11.4 Discrete vs continuous time
<!-- Approximation assumptions. -->

### 11.5 First-violation semantics
<!-- Earliest violating time. -->

---

## 12. Vehicle Geometry & Signals

### 12.1 TTC definition
<!-- Exact computation. -->

### 12.2 Separation definition
<!-- Center/polygon/circle distance. -->

### 12.3 Collision definition
<!-- IoU/overlap/geometry. -->

### 12.4 Relative velocity
<!-- Optional supporting signal. -->

### 12.5 Vehicle dimensions
<!-- length/width. -->

### 12.6 Map/drivable-area geometry
<!-- Optional map-based property. -->

---

## 13. Falsification Workflow

### 13.1 Freeze system artifacts
<!-- STRIVE revision/checkpoints/configs. -->

### 13.2 Freeze specification
<!-- Property/version/evaluator. -->

### 13.3 Select seed scene
<!-- From A3-D-01. -->

### 13.4 Run C-01 initialization
<!-- Establish source/planner initialization. -->

### 13.5 Run C-02 adversarial search
<!-- Generate candidate violating trajectory. -->

### 13.6 Optionally run C-03
<!-- Operational solution search. -->

### 13.7 Independently evaluate specification
<!-- Do not trust optimizer objective alone. -->

### 13.8 Confirm and save counterexample
<!-- Persist D-02 + property trace + hashes. -->

---

## 14. Counterexample Handling

### 14.1 Candidate counterexample
<!-- Generated trajectory suspected of violating φ. -->

### 14.2 Confirmed counterexample
<!-- Independent evaluator confirms violation. -->

### 14.3 Invalid counterexample
<!-- NaN/schema/evaluator/geometry mismatch. -->

### 14.4 Replay confirmation
<!-- Reload and re-evaluate saved trace. -->

### 14.5 Counterexample minimization
<!-- Optional search for smaller perturbation / earlier violation. -->

### 14.6 Regression retention
<!-- Preserve known violations. -->

---

## 15. Quantitative Falsification Metrics

### 15.1 Falsification success rate
<!-- Confirmed counterexamples / valid searches. -->

### 15.2 Search time
<!-- Wall-clock and iterations. -->

### 15.3 Time to first violation
<!-- Earliest violation and search iteration. -->

### 15.4 Minimum TTC
<!-- Severity. -->

### 15.5 Minimum separation
<!-- Severity. -->

### 15.6 Robustness score
<!-- If used by selected formalism. -->

### 15.7 Unique counterexample count
<!-- Deduplication semantics. -->

---

## 16. Search Robustness & Sensitivity

### 16.1 Initialization sensitivity
<!-- Dependence on latent initialization. -->

### 16.2 Random-seed sensitivity
<!-- Multiple restarts/seeds. -->

### 16.3 Search-budget sensitivity
<!-- Iteration/timeout effects. -->

### 16.4 Planner sensitivity
<!-- Replay vs rule-based. -->

### 16.5 Specification-threshold sensitivity
<!-- TTC/d_min changes. -->

### 16.6 Learned-prior sensitivity
<!-- Different M-01 checkpoints/models. -->

---

## 17. Validation of the Falsification Model

### 17.1 Reproduce native STRIVE results
<!-- Verify unmodified optimizer behavior first. -->

### 17.2 Specification-evaluator unit tests
<!-- Safe/boundary/violating traces. -->

### 17.3 Geometry validation
<!-- Independent collision/distance checker. -->

### 17.4 Timebase validation
<!-- Interpolation and horizon. -->

### 17.5 Saved-artifact replay
<!-- Counterexample reproducibility. -->

### 17.6 Cross-check native vs external outcome
<!-- Native success partition vs safety-spec result. -->

---

## 18. Failure Modes

### 18.1 Search local minimum
<!-- Violation exists but optimizer misses it. -->

### 18.2 Unrealistic learned-prior region
<!-- Optimizer exploits M-01 artifact. -->

### 18.3 Planner-model mismatch
<!-- Counterexample depends on planner approximation/config. -->

### 18.4 Specification mismatch
<!-- TTC/separation definition differs from intended requirement. -->

### 18.5 Temporal aliasing
<!-- Violation between discrete samples. -->

### 18.6 Geometry mismatch
<!-- Different collision/distance definitions. -->

### 18.7 C-03 interpretation error
<!-- Treating solution success/failure as formal solvability proof. -->

---

## 19. Known Limitations

### 19.1 Falsification incompleteness
<!-- No violation found != proof. -->

### 19.2 Nonconvex optimization
<!-- C-02 search limitations. -->

### 19.3 Learned traffic prior bias
<!-- M-01 constrains explored behavior. -->

### 19.4 Planner dependence
<!-- Counterexample specific to planner/config. -->

### 19.5 Specification incompleteness
<!-- TTC/separation are partial safety requirements. -->

### 19.6 Discrete-time approximation
<!-- Continuous-time gap. -->

### 19.7 Synthetic counterexamples
<!-- Not observed real-world crash frequency. -->

---

## 20. Safety & Assurance Interpretation

### 20.1 Meaning of “falsified”
<!-- A confirmed trajectory violates exact φ. -->

### 20.2 Meaning of “no counterexample found”
<!-- Inconclusive with respect to universal safety. -->

### 20.3 Meaning of native STRIVE success
<!-- Candidate evidence only until property evaluation. -->

### 20.4 Meaning of C-03 solution success
<!-- Operational usefulness, not formal solvability proof. -->

### 20.5 Scope of counterexample
<!-- Specific planner/config/seed/specification. -->

### 20.6 System-level inference limits
<!-- Does not establish real-world probability/frequency. -->

---

## 21. Reproducibility

### 21.1 STRIVE revision
<!-- Exact source revision. -->

### 21.2 M-01 checkpoint hash
<!-- SHA-256. -->

### 21.3 Planner identity/configuration
<!-- Replay artifact or M-02 config/hash. -->

### 21.4 Optimizer configuration
<!-- C-01/C-02/C-03 resolved settings. -->

### 21.5 A3-D-01 manifest
<!-- Seed/run/counterexample evidence. -->

### 21.6 Specification registry
<!-- Property ID/version/hash. -->

### 21.7 Evaluator revision
<!-- Independent property-checker code hash. -->

### 21.8 Random seeds
<!-- Search reproducibility. -->

### 21.9 Execution environment
<!-- OS/Python/PyTorch/CUDA/etc. -->

### 21.10 Profiler
<!-- `tools/profile_collision_optimizer_falsification.py`. -->

---

## 22. Assurance Evidence & Results

### 22.1 Claim-evidence matrix
<!-- Property -> planner -> seed domain -> result. -->

### 22.2 Confirmed counterexamples
<!-- None until runs are performed. -->

### 22.3 No-counterexample runs
<!-- Search outcomes, not proofs. -->

### 22.4 Invalid/inconclusive runs
<!-- Timeout/error/evaluator failure. -->

### 22.5 Residual risk
<!-- Search blind spots and untested domains. -->

---

## 23. Relationships

### 23.1 Companion data card

```text
A3-D-01 — STRIVE Collision-Generation Optimizer Falsification Data Card
```

### 23.2 STRIVE generation chain

```text
D-01 → M-01 → C-01 → C-02 → C-03 → D-02
```

### 23.3 Rule-based path

```text
D-01 → M-01 → C-01 → M-02 → C-02 → C-03 → D-02
```

### 23.4 Assurance overlay

```text
D-02 candidate trajectory
        │
        ▼
versioned safety specification
        │
        ▼
independent evaluator
        │
        ├── satisfaction
        └── violation → A3 counterexample
```

### 23.5 Other assurance approaches
<!-- A1 traffic-model verification; A2 classifier verification. -->

---

## 24. Terms of Art

### 24.1 Safety specification
<!-- Formal requirement over a trajectory/system execution. -->

### 24.2 Falsification
<!-- Search for a concrete violating execution. -->

### 24.3 Counterexample
<!-- Saved trace violating the exact property. -->

### 24.4 Search budget
<!-- Finite optimizer resources. -->

### 24.5 Robustness score
<!-- Quantitative satisfaction/violation measure if defined. -->

### 24.6 Native STRIVE success
<!-- Original adversarial collision success criterion. -->

### 24.7 External specification violation
<!-- Independently evaluated A3 property failure. -->

### 24.8 Replay-confirmed counterexample
<!-- Saved trace re-evaluates as the same violation. -->

---

## 25. References

<!-- Formal Assurance in STRIVE project concept PDF -->
<!-- STRIVE paper -->
<!-- A3-D-01 assurance data card -->
<!-- C-01 Initialization Optimization Card -->
<!-- C-02 Adversarial Optimization Card -->
<!-- C-03 Solution Optimization Card -->
<!-- M-01 Main Traffic Model Card -->
<!-- M-02 Rule-Based Planner Card -->
<!-- D-02 Generated Scenarios Data Card -->
<!-- selected falsification / temporal-logic tool references once chosen -->

---

## 26. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial Approach-3 collision-optimizer falsification model-card skeleton |
