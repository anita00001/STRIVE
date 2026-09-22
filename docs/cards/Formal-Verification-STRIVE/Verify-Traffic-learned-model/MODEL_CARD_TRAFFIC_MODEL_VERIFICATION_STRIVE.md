# A1-M-01 — STRIVE Learned Traffic Model Verification Model Card

> **Card ID:** A1-M-01  
> **Card type:** Formal-Assurance Model Card  
> **Status:** Skeleton  
> **Assurance approach:** Verify STRIVE's Learned Traffic Model  
> **Target model:** M-01 — STRIVE Main Traffic Model  
> **Companion data card:** A1-D-01 — STRIVE Learned Traffic Model Verification Data Card  
> **System:** S-01 — STRIVE

---

## 1. Verification Model Details

### 1.1 Assurance model summary
<!-- What is being formally verified and why? -->

### 1.2 Target implementation
<!-- `src/models/traffic_model.py::TrafficModel`. -->

### 1.3 Target artifact identity
<!-- Checkpoint, source revision, configuration. -->

### 1.4 Assurance status
<!-- Proposed / encoded / partially verified / verified / falsified. -->

### 1.5 Verification tool
<!-- Tool/verifier not yet selected in concept PDF; record once chosen. -->

---

## 2. Purpose & Assurance Role

### 2.1 Primary assurance objective
<!-- Establish selected behavioral properties for M-01 over a bounded verification domain. -->

### 2.2 Safety relevance
<!-- M-01 predictions constrain/generated traffic used by STRIVE. -->

### 2.3 Relationship to STRIVE
<!-- Role of M-01 in adversarial generation and solution search. -->

### 2.4 Relationship to A1-D-01
<!-- Verification model vs evidence/domain data. -->

### 2.5 Out-of-scope assurance claims
<!-- Does not prove whole-system/planner safety. -->

---

## 3. Verification Target Boundary

### 3.1 Full-model verification option
<!-- CNN + MLP/GRU + GNN prior + latent + decoder + bicycle dynamics. -->

### 3.2 Decoder-centered verification option
<!-- Fixed encoded scene + bounded latent + decoder + dynamics. -->

### 3.3 Reduced-subnetwork verification option
<!-- One/few step, fixed graph/map, selected network slice. -->

### 3.4 Selected boundary
<!-- To be finalized. -->

### 3.5 Excluded components
<!-- Explicitly state what is outside the formal model. -->

---

## 4. Target Architecture

### 4.1 Local map encoder
<!-- CNN. -->

### 4.2 Past motion encoder
<!-- MLP default / GRU alternative. -->

### 4.3 Future motion encoder
<!-- Posterior-only path; MLP default / GRU alternative. -->

### 4.4 Prior interaction network
<!-- GNN + MLP. -->

### 4.5 Posterior interaction network
<!-- GNN + MLP. -->

### 4.6 Autoregressive interaction decoder
<!-- GNN + MLP. -->

### 4.7 Decoder motion memory
<!-- GRU. -->

### 4.8 Kinematic bicycle dynamics
<!-- Learned acceleration/yaw-related outputs rolled into future state. -->

---

## 5. Inputs to the Formal Model

### 5.1 Past agent state
<!-- x, y, heading vector, speed, heading-change rate. -->

### 5.2 Agent attributes
<!-- length, width. -->

### 5.3 Semantic class
<!-- car/truck or explicitly chosen categories. -->

### 5.4 Scene graph
<!-- Nodes, edges, graph topology. -->

### 5.5 Local map input
<!-- Raster or fixed map embedding. -->

### 5.6 Latent variable
<!-- z dimension and bounded verification domain. -->

### 5.7 Initial dynamic state
<!-- State supplied to bicycle rollout. -->

---

## 6. Outputs of the Formal Model

### 6.1 Raw decoder outputs
<!-- Normalized acceleration + ddh channels when bicycle output enabled. -->

### 6.2 Unnormalized dynamic controls
<!-- a_out, ddh_out. -->

### 6.3 Post-dynamics state
<!-- x, y, heading, speed, heading-rate. -->

### 6.4 Public future trajectory
<!-- x, y, heading_x, heading_y. -->

### 6.5 Derived safety signals
<!-- Speed, acceleration, turn behavior, separation, map occupancy. -->

---

## 7. Formal Properties

### 7.1 P-A — Acceleration bounds

```text
a_min <= a_t(z) <= a_max
```

<!-- Exact property definition and bounds. -->

### 7.2 P-S — Speed bounds
<!-- Formal speed requirement. -->

### 7.3 P-H — Heading-rate / turning bounds
<!-- Formal turning requirement. -->

### 7.4 P-COLL — Vehicle-vehicle collision freedom
<!-- Exact geometry and temporal quantification. -->

### 7.5 P-ROAD — Drivable-area constraint
<!-- Map-dependent safety property. -->

### 7.6 Combined properties
<!-- Conjunctions / temporal specifications. -->

### 7.7 Property versioning
<!-- IDs, versions, units, tolerances. -->

---

## 8. Built-In Dynamics Constraints

### 8.1 Speed clamp
<!-- Released `car_dynamics()` clamp. -->

### 8.2 Heading-rate clamp
<!-- Released `car_dynamics()` clamp. -->

### 8.3 Raw acceleration behavior
<!-- Distinguish learned acceleration from post-dynamics speed clamp. -->

### 8.4 Raw ddh behavior
<!-- Distinguish learned ddh from clamped heading-rate state. -->

### 8.5 Assurance interpretation of construction invariants
<!-- Do not overclaim learned behavior from code-enforced clamps. -->

---

## 9. Verification Domain

### 9.1 Agent-count bounds
<!-- Fixed N or bounded N. -->

### 9.2 Graph-topology assumptions
<!-- Fixed graph or admissible topology family. -->

### 9.3 State bounds
<!-- Position, speed, heading, heading-rate. -->

### 9.4 Vehicle-dimension bounds
<!-- Length/width. -->

### 9.5 Map-domain assumptions
<!-- Fixed raster / fixed feature / bounded map input. -->

### 9.6 Latent-space bounds
<!-- Interval / norm ball / mean-centered region. -->

### 9.7 Temporal horizon
<!-- One-step, K-step, or full 12-step rollout. -->

---

## 10. Formal Encoding

### 10.1 Neural-network translation
<!-- How CNN/MLP/GNN/GRU operations are represented. -->

### 10.2 Graph encoding
<!-- Fixed adjacency or bounded graph structure. -->

### 10.3 Recurrent-state encoding
<!-- GRU unrolling or abstraction. -->

### 10.4 Bicycle-dynamics encoding
<!-- Exact / approximate / abstracted. -->

### 10.5 Map encoding
<!-- Full CNN vs frozen map feature. -->

### 10.6 Floating-point abstraction
<!-- Real arithmetic, float semantics, interval bounds, etc. -->

---

## 11. Verification Method

### 11.1 Verification paradigm
<!-- SMT/MILP/abstract interpretation/reachability/etc. -->

### 11.2 Soundness expectations
<!-- Exact proof vs over-approximation vs incomplete search. -->

### 11.3 Solver / backend
<!-- TBD. -->

### 11.4 Timeout / resource policy
<!-- CPU/GPU, memory, timeout. -->

### 11.5 Proof obligations
<!-- Per-property conditions. -->

### 11.6 Counterexample extraction
<!-- Concrete violating input and latent. -->

---

## 12. Verification Workflow

### 12.1 Select model/checkpoint
<!-- Freeze artifact. -->

### 12.2 Select verification boundary
<!-- Full/decoder/reduced. -->

### 12.3 Select property
<!-- P-A/P-S/P-H/P-COLL/P-ROAD. -->

### 12.4 Instantiate domain
<!-- A1-D-01 case/domain. -->

### 12.5 Encode model and property
<!-- Tool-specific representation. -->

### 12.6 Run verifier
<!-- Verified/counterexample/unknown/timeout. -->

### 12.7 Replay counterexample
<!-- Original PyTorch M-01 replay. -->

### 12.8 Store assurance evidence
<!-- Link result back to A1-D-01. -->

---

## 13. Counterexample Handling

### 13.1 Counterexample definition
<!-- In-domain violating input. -->

### 13.2 PyTorch replay
<!-- Required when technically possible. -->

### 13.3 Numeric reconciliation
<!-- Solver vs float32 differences. -->

### 13.4 Abstraction-only counterexamples
<!-- Mark separately. -->

### 13.5 Regression retention
<!-- Add validated violations to regression partition. -->

---

## 14. Validation of the Formal Model

### 14.1 Model-equivalence checks
<!-- Compare formal encoding against M-01 execution. -->

### 14.2 Layer-level equivalence
<!-- CNN/MLP/GNN/GRU unit comparisons. -->

### 14.3 Dynamics equivalence
<!-- Formal bicycle rollout vs original code. -->

### 14.4 Preprocessing equivalence
<!-- Normalization / coordinate frame / graph / map. -->

### 14.5 Property-evaluator equivalence
<!-- Formal vs executable predicate. -->

---

## 15. Quantitative Analysis

### 15.1 Verification cases
<!-- Counts by property/domain. -->

### 15.2 Verification outcomes
<!-- Verified / counterexample / timeout / unknown. -->

### 15.3 Runtime
<!-- Per property/domain. -->

### 15.4 Domain size
<!-- Variable dimensions / interval widths. -->

### 15.5 Counterexample replay rate
<!-- Confirmed vs abstraction-only. -->

### 15.6 Scalability
<!-- Agent count / horizon / graph complexity. -->

---

## 16. Robustness & Sensitivity

### 16.1 Domain-width sensitivity
<!-- Verification difficulty as bounds widen. -->

### 16.2 Agent-count sensitivity
<!-- Scaling with N. -->

### 16.3 Horizon sensitivity
<!-- One-step vs autoregressive multi-step. -->

### 16.4 Latent-radius sensitivity
<!-- Scaling with z domain. -->

### 16.5 Map-complexity sensitivity
<!-- Full map encoder vs fixed features. -->

### 16.6 Property-threshold sensitivity
<!-- Effect of tighter/looser specs. -->

---

## 17. Known Limitations

### 17.1 Full-network tractability
<!-- CNN/GNN/GRU/autoregressive complexity. -->

### 17.2 Variable graph topology
<!-- Formal-verifier limitations. -->

### 17.3 Dynamic map recropping
<!-- Position-dependent CNN re-evaluation. -->

### 17.4 Gaussian latent support
<!-- Unbounded prior vs bounded verification regions. -->

### 17.5 Arithmetic abstraction
<!-- Real vs float semantics. -->

### 17.6 Specification incompleteness
<!-- Selected properties do not equal overall safety. -->

### 17.7 Partial ground truth
<!-- nuScenes observations are not formal safety labels. -->

---

## 18. Safety & Assurance Interpretation

### 18.1 Meaning of “verified”
<!-- Exact scope-qualified statement. -->

### 18.2 Meaning of “falsified”
<!-- Concrete counterexample. -->

### 18.3 Meaning of unknown / timeout
<!-- No safety conclusion. -->

### 18.4 Construction invariants vs learned guarantees
<!-- Important speed/heading clamp distinction. -->

### 18.5 System-level limits
<!-- M-01 assurance does not establish STRIVE/planner assurance. -->

---

## 19. Reproducibility

### 19.1 STRIVE revision
<!-- Exact repository revision. -->

### 19.2 Checkpoint hash
<!-- SHA-256. -->

### 19.3 Effective configuration
<!-- Model/data/dynamics settings. -->

### 19.4 Verification specification
<!-- Property registry and version. -->

### 19.5 Verification data
<!-- A1-D-01 manifest/domain. -->

### 19.6 Toolchain
<!-- Verifier, backend, version, numeric mode. -->

### 19.7 Execution environment
<!-- OS/Python/PyTorch/verifier hardware. -->

### 19.8 Companion metadata
<!-- `metadata/assurance/models/traffic_model_verification.yaml`. -->

### 19.9 Profiler
<!-- `tools/profile_traffic_model_verification.py`. -->

---

## 20. Assurance Evidence & Results

### 20.1 Claim-evidence matrix
<!-- Property -> domain -> evidence -> status. -->

### 20.2 Verified claims
<!-- None until verification is actually run. -->

### 20.3 Falsified claims
<!-- Counterexamples. -->

### 20.4 Inconclusive claims
<!-- Timeout / unsupported / abstraction gap. -->

### 20.5 Residual risk
<!-- What remains outside verified scope. -->

---

## 21. Relationships

### 21.1 Target model

```text
M-01 — STRIVE Main Traffic Model
```

### 21.2 Companion assurance data card

```text
A1-D-01 — STRIVE Learned Traffic Model Verification Data Card
```

### 21.3 System relationship

```text
S-01 STRIVE
  │
  └──► M-01 Main Traffic Model
          │
          ├──► A1-D-01 verification evidence/domain
          └──► A1-M-01 formal verification model
```

### 21.4 Other assurance approaches
<!-- Accident classifier verification; specification-driven optimizer falsification. -->

---

## 22. Terms of Art

### 22.1 Verification target
<!-- Exact learned implementation/artifact being analyzed. -->

### 22.2 Formal model
<!-- Mathematical encoding used by verifier. -->

### 22.3 Verification domain
<!-- Bounded quantified input space. -->

### 22.4 Property
<!-- Predicate being established or falsified. -->

### 22.5 Construction invariant
<!-- Guarantee created by deterministic implementation logic. -->

### 22.6 Counterexample
<!-- In-domain property violation. -->

### 22.7 Replay-confirmed counterexample
<!-- Violation reproduced in original M-01 code. -->

### 22.8 Abstraction gap
<!-- Difference between formal encoding and executable model. -->

---

## 23. References

<!-- Formal Assurance in STRIVE project concept PDF -->
<!-- STRIVE paper -->
<!-- STRIVE repository -->
<!-- M-01 Main Traffic Model Card -->
<!-- A1-D-01 assurance data card -->
<!-- selected verifier/tool references once chosen -->

---

## 24. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial Approach-1 learned-traffic-model formal-verification model-card skeleton |
