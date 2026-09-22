# A1-D-01 — STRIVE Learned Traffic Model Verification Data Card

> **Card ID:** A1-D-01  
> **Card type:** Formal-Assurance Data Card  
> **Status:** Skeleton  
> **Assurance approach:** Verify STRIVE's Learned Traffic Model  
> **Target:** M-01 — STRIVE Main Traffic Model  
> **System:** S-01 — STRIVE  
> **Primary evidence sources:** STRIVE source code + nuScenes + verification-generated test cases/counterexamples

---

## 1. Dataset Summary

### 1.1 Dataset / evidence-set name
<!-- Canonical name for the assurance dataset. -->

### 1.2 Assurance purpose
<!-- Define how this dataset supports formal assurance of M-01. -->

### 1.3 Verification target
<!-- Exact M-01 checkpoint/configuration/revision under verification. -->

### 1.4 Dataset role
<!-- Verification inputs, property-evaluation evidence, counterexample seeds, boundary cases. -->

### 1.5 Dataset status
<!-- Proposed / generated / frozen / validated. -->

---

## 2. Assurance Claim Context

### 2.1 Top-level assurance claim
<!-- Example: within a defined input domain, M-01 outputs satisfy selected motion-safety / realism properties. -->

### 2.2 Candidate verified properties
<!-- Acceleration bounds, speed bounds, heading/yaw-rate bounds, collision freedom or collision-related constraints. -->

### 2.3 Supported subclaims
<!-- Which properties can be evaluated directly using this dataset? -->

### 2.4 Unsupported claims
<!-- No claim of universal real-world safety unless formally established over a complete domain. -->

### 2.5 Evidence interpretation
<!-- What constitutes satisfaction, violation, or inconclusive evidence. -->

---

## 3. Verification Scope

### 3.1 Model boundary
<!-- Full M-01 vs selected encoder/decoder/dynamics subnetwork. -->

### 3.2 Neural components in scope
<!-- Map CNN, motion encoders, interaction GNNs, decoder GNN/MLP, decoder GRU. -->

### 3.3 Kinematic dynamics in scope
<!-- Acceleration / yaw-rate output and bicycle-model rollout. -->

### 3.4 Input-space boundary
<!-- Agent count, categories, history, maps, state ranges, latent range. -->

### 3.5 Output-space boundary
<!-- Predicted acceleration, yaw-rate, speed, heading, position, pairwise geometry. -->

### 3.6 Temporal scope
<!-- Verification horizon and timestep. -->

---

## 4. Data Sources

### 4.1 STRIVE source code
<!-- Relevant implementation files used to define transformations and properties. -->

### 4.2 nuScenes dataset
<!-- Recorded vehicle trajectories, attributes, semantics, and maps. -->

### 4.3 D-01 relationship
<!-- Reuse/derive from the documented STRIVE nuScenes data representation. -->

### 4.4 M-01 configuration/checkpoint
<!-- Exact model artifact associated with each verification record. -->

### 4.5 Verification-generated samples
<!-- Solver-generated, abstracted, perturbed, boundary, or counterexample inputs. -->

---

## 5. Ground Truth & Reference Evidence

### 5.1 Recorded trajectory ground truth
<!-- Observed nuScenes trajectories. -->

### 5.2 Map ground truth
<!-- nuScenes map information used to evaluate drivable-area / geometry properties. -->

### 5.3 Physical / specification bounds
<!-- Which bounds are externally specified rather than learned from data. -->

### 5.4 Missing formal ground truth
<!-- No real-world label saying a generated future is formally safe/unsafe. -->

### 5.5 Operational labels vs formal labels
<!-- Separate empirical plausibility/collision outcomes from formally specified properties. -->

---

## 6. Verification Input Schema

### 6.1 Scene identifier
<!-- Source scene/sample token or synthetic verification-case ID. -->

### 6.2 Agent state history
<!-- x, y, heading_x, heading_y, speed, heading-rate. -->

### 6.3 Agent attributes
<!-- length, width. -->

### 6.4 Semantic category
<!-- car/truck or expanded categories if explicitly in scope. -->

### 6.5 Map representation
<!-- Local raster/map crop and/or symbolic map constraints. -->

### 6.6 Graph structure
<!-- Scene-graph connectivity/batch representation. -->

### 6.7 Latent variable
<!-- z or bounded latent domain if verification operates in latent space. -->

### 6.8 Masks / missing observations
<!-- Visibility and NaN handling. -->

---

## 7. Verification Output Schema

### 7.1 Raw neural outputs
<!-- Acceleration, yaw-rate or direct waypoint outputs depending on configuration. -->

### 7.2 Rolled-out vehicle state
<!-- Position, heading, speed across future timesteps. -->

### 7.3 Derived verification signals
<!-- Acceleration, speed, yaw-rate, curvature, pairwise distance, map occupancy. -->

### 7.4 Property result
<!-- SAT / violated / unknown / timeout, depending on verifier. -->

### 7.5 Counterexample payload
<!-- Input state, latent, output trajectory, violated property, timestep. -->

---

## 8. Candidate Formal Properties

### 8.1 Acceleration bounds

```text
a_min <= a_t(z) <= a_max
```

<!-- Define bounds, units, scope, and whether longitudinal or total acceleration. -->

### 8.2 Speed bounds
<!-- Define min/max speed specification. -->

### 8.3 Yaw-rate / turning bounds
<!-- Prevent unrealistically sharp turning. -->

### 8.4 Heading-change / curvature bounds
<!-- Optional derived trajectory constraint. -->

### 8.5 Vehicle-vehicle separation
<!-- Pairwise minimum-distance or collision property. -->

### 8.6 Environment / drivable-area constraint
<!-- Optional map-consistency property. -->

### 8.7 Combined properties
<!-- Conjunctions and temporal versions of the above. -->

---

## 9. Property Parameterization

### 9.1 Source of bounds
<!-- Physics, STRIVE configuration, empirical quantiles, domain expert specification. -->

### 9.2 Units
<!-- m/s, m/s^2, rad/s, meters, etc. -->

### 9.3 Fixed vs context-dependent thresholds
<!-- Global thresholds vs speed/map/vehicle-dependent bounds. -->

### 9.4 Conservative margins
<!-- Numerical/abstraction margins if used. -->

### 9.5 Versioning of specifications
<!-- Property ID and version. -->

---

## 10. Sampling & Case Construction

### 10.1 Natural nuScenes cases
<!-- Held-out recorded contexts used as anchors. -->

### 10.2 Boundary-value cases
<!-- Inputs near allowed state/property limits. -->

### 10.3 Perturbed cases
<!-- Controlled perturbations around recorded scenes. -->

### 10.4 Latent-space cases
<!-- z samples / bounded z regions if verification is performed over latent inputs. -->

### 10.5 Counterexample-directed cases
<!-- Cases generated iteratively from solver/falsifier outputs. -->

### 10.6 Rare / safety-critical cases
<!-- Dense traffic, high speed, sharp turns, small separation. -->

---

## 11. Partitioning

### 11.1 Development partition
<!-- Used to formulate/adjust properties and verifier encodings. -->

### 11.2 Verification partition
<!-- Frozen set/domain used for reported results. -->

### 11.3 Regression partition
<!-- Persisted counterexamples and previously difficult cases. -->

### 11.4 Independence from M-01 training
<!-- Prevent training/verification leakage where relevant. -->

---

## 12. Data Transformations

### 12.1 STRIVE normalization
<!-- State and attribute normalization used before M-01. -->

### 12.2 Coordinate frames
<!-- Global/local frame transformations. -->

### 12.3 Map preprocessing
<!-- Raster crop and channel handling. -->

### 12.4 Graph construction
<!-- Agent nodes / edges / batching. -->

### 12.5 Verifier-specific abstraction
<!-- Network simplification, interval bounds, fixed graph size, linearization, etc. -->

### 12.6 Precision / datatype
<!-- float32 / float64 / verifier rationalization or interval representation. -->

---

## 13. Quantitative Dataset Profile

### 13.1 Number of source scenes
<!-- To be measured. -->

### 13.2 Number of verification cases
<!-- To be measured. -->

### 13.3 Agent-count distribution
<!-- To be measured. -->

### 13.4 Speed / acceleration distribution
<!-- To be measured. -->

### 13.5 Map-context distribution
<!-- To be measured. -->

### 13.6 Property coverage
<!-- Number of cases/domains per property. -->

### 13.7 Counterexample counts
<!-- By property / model / verification tool. -->

---

## 14. Coverage Strategy

### 14.1 Input-domain coverage
<!-- How representative and boundary coverage are measured. -->

### 14.2 Neural-path / activation coverage
<!-- Optional if used. -->

### 14.3 Latent-space coverage
<!-- If z is explicitly part of the assurance domain. -->

### 14.4 Scenario diversity
<!-- Map, speed, density, interaction geometry. -->

### 14.5 Property-boundary coverage
<!-- Emphasize cases near thresholds. -->

---

## 15. Validation & Quality Assurance

### 15.1 Schema validation
<!-- Shapes, dtypes, required fields. -->

### 15.2 Range validation
<!-- State/map/property input ranges. -->

### 15.3 Reproduction of M-01 inputs
<!-- Ensure verifier dataset matches actual model preprocessing. -->

### 15.4 Property-evaluator validation
<!-- Independently test property calculators. -->

### 15.5 Counterexample replay
<!-- Replay verifier/falsifier violations through original M-01 implementation. -->

### 15.6 Numerical tolerance checks
<!-- Solver/model precision mismatch. -->

---

## 16. Known Limitations

### 16.1 Partial ground truth
<!-- Recorded trajectories/maps are observations, not formal safety labels. -->

### 16.2 Finite data vs universal verification
<!-- Clarify distinction between dataset-based testing and formal domain proof. -->

### 16.3 Domain restriction
<!-- Any bounds on agents, latent variables, map types, categories. -->

### 16.4 Abstraction error
<!-- If only a subnetwork/simplified network is formally analyzed. -->

### 16.5 Distribution shift
<!-- nuScenes vs other environments. -->

### 16.6 Property incompleteness
<!-- Passing chosen properties is not equivalent to overall driving safety. -->

---

## 17. Safety & Assurance Interpretation

### 17.1 Meaning of a verified property
<!-- Exactly what can be claimed if verification succeeds. -->

### 17.2 Meaning of a counterexample
<!-- Concrete violating input/output within specified domain. -->

### 17.3 Meaning of unknown / timeout
<!-- Not evidence of safety or unsafety. -->

### 17.4 Empirical vs formal evidence
<!-- Keep testing evidence and proof evidence separate. -->

### 17.5 System-level inference limits
<!-- M-01 verification alone does not verify the whole STRIVE system/planner. -->

---

## 18. Reproducibility & Provenance

### 18.1 STRIVE repository revision
<!-- Exact source revision. -->

### 18.2 M-01 checkpoint hash
<!-- Required. -->

### 18.3 M-01 configuration hash
<!-- Required. -->

### 18.4 nuScenes version / split
<!-- Required. -->

### 18.5 Verification specification version
<!-- Required. -->

### 18.6 Verifier/tool version
<!-- Required once tool is selected. -->

### 18.7 Random seeds
<!-- For sampling/falsification where applicable. -->

### 18.8 Generated-case provenance
<!-- Parent scene, perturbation, solver run, property. -->

---

## 19. Relationships

### 19.1 Upstream

```text
D-01 — STRIVE nuScenes Data
M-01 — STRIVE Main Traffic Model
```

### 19.2 Assurance approach

```text
Approach 1 — Verify STRIVE's Learned Traffic Model
```

### 19.3 Companion model card
<!-- Future A1-M-01 formal-assurance model card. -->

### 19.4 System relationship

```text
S-01 STRIVE
  │
  └──► M-01 learned traffic model
          │
          └──► A1-D-01 verification data/evidence
```

---

## 20. Terms of Art

### 20.1 Verification domain
<!-- Bounded set of admissible model inputs over which a property is checked. -->

### 20.2 Safety property
<!-- Explicit predicate/specification over model inputs/outputs. -->

### 20.3 Counterexample
<!-- Input within scope that violates the property. -->

### 20.4 Ground truth
<!-- Recorded observation vs formal specification distinction. -->

### 20.5 Formal verification
<!-- Proof/check over a defined mathematical model and input domain. -->

### 20.6 Falsification
<!-- Search for a concrete property violation without proving absence of violations. -->

---

## 21. References

<!-- Formal Assurance in STRIVE project concept PDF -->
<!-- STRIVE paper -->
<!-- STRIVE repository -->
<!-- D-01 nuScenes Data Card -->
<!-- M-01 Main Traffic Model Card -->
<!-- selected formal-verification/falsification tool references once decided -->

---

## 22. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial Approach-1 learned-traffic-model verification data-card skeleton |
