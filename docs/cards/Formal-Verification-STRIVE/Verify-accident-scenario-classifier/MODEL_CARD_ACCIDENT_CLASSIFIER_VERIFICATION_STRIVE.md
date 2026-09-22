# A2-M-01 — STRIVE Accident Scenario Classifier Verification Model Card

> **Card ID:** A2-M-01  
> **Card type:** Formal-Assurance Model Card  
> **Status:** Skeleton  
> **Assurance approach:** Verify the Accident Scenario Classifier  
> **Target model:** STRIVE paper-level learned binary regular-vs-accident-prone classifier  
> **Companion data card:** A2-D-01 — STRIVE Accident Scenario Classifier Verification Data Card  
> **System:** S-01 — STRIVE  
> **Important distinction:** This target is not the public M-04 K-means/cluster-labeling workflow.

---

## 1. Verification Model Details

### 1.1 Assurance model summary
<!-- What is being formally verified and why? -->

### 1.2 Target classifier
<!-- Learned binary regular vs accident-prone classifier. -->

### 1.3 Target artifact identity
<!-- Source, checkpoint, configuration, threshold, revision. -->

### 1.4 Public availability
<!-- Whether original classifier implementation/checkpoint is available. -->

### 1.5 Assurance status
<!-- Proposed / reproduced / encoded / partially verified / verified / falsified. -->

### 1.6 Verification tool
<!-- Tool/verifier not yet selected. -->

---

## 2. Purpose & Assurance Role

### 2.1 Primary assurance objective
<!-- Verify robustness/correctness of the planner-mode classification decision over bounded domains. -->

### 2.2 Safety relevance
<!-- Output determines regular vs accident-handling planner mode. -->

### 2.3 Relationship to planner tuning
<!-- Paper-level multi-mode planner. -->

### 2.4 Relationship to A2-D-01
<!-- Model method vs assurance evidence/domain. -->

### 2.5 Out-of-scope claims
<!-- Does not prove planner or system safety. -->

---

## 3. Target Classifier Definition

### 3.1 Input history
<!-- Past two seconds of trajectories for all agents. -->

### 3.2 Local map input
<!-- Local map information/crops around agents. -->

### 3.3 Scene representation
<!-- Graph-based multi-agent representation. -->

### 3.4 Ego feature
<!-- 64-dimensional ego-node feature described in supplement. -->

### 3.5 Classification head
<!-- Two-layer MLP. -->

### 3.6 Binary output
<!-- regular / accident-prone. -->

---

## 4. Distinction from Public M-04

### 4.1 Public M-04
<!-- Collision feature -> KMeans.predict -> 10 cluster labels. -->

### 4.2 A2-M-01 target
<!-- Learned binary classifier used for planner-mode selection. -->

### 4.3 Non-equivalence
<!-- Do not treat M-04 as implementation of this classifier. -->

### 4.4 Possible analytical relationship
<!-- M-03/M-04 labels may be useful for stratified robustness analysis only. -->

---

## 5. Model Availability & Reproduction Status

### 5.1 Public source-code availability
<!-- Original binary classifier source not identified in inspected public repo. -->

### 5.2 Public checkpoint availability
<!-- Original classifier checkpoint not identified. -->

### 5.3 Published architecture information
<!-- What paper/supplement actually specifies. -->

### 5.4 Missing implementation details
<!-- Threshold, exact preprocessing, layer dimensions where unavailable, etc. -->

### 5.5 Reproduction policy
<!-- If reconstructed, label it as reproduction rather than original artifact. -->

---

## 6. Inputs to the Formal Model

### 6.1 Past multi-agent trajectories
<!-- Exact state representation once target artifact is available. -->

### 6.2 Agent semantics
<!-- Classes/one-hot representation. -->

### 6.3 Agent attributes
<!-- Length/width if used. -->

### 6.4 Local map representation
<!-- Raster or encoded feature. -->

### 6.5 Scene graph
<!-- Node/edge construction. -->

### 6.6 Ego-node designation
<!-- Which graph node feeds the final classifier head. -->

### 6.7 Visibility / missing data
<!-- Observation masks and handling. -->

---

## 7. Outputs of the Formal Model

### 7.1 Binary class
<!-- regular / accident-prone. -->

### 7.2 Logits / score
<!-- Exact output convention if available. -->

### 7.3 Decision threshold
<!-- Exact threshold/version. -->

### 7.4 Classification margin
<!-- Distance from decision boundary. -->

### 7.5 Planner-mode decision
<!-- regular mode / accident-handling mode. -->

---

## 8. Candidate Formal Properties

### 8.1 C-FN — Accident-prone non-demotion

```text
forall x' in D(x):
    classifier(x') = accident-prone
```

<!-- Accident-prone anchor remains accident-prone under allowed perturbations. -->

### 8.2 C-FP — Regular-case stability

```text
forall x' in D(x):
    classifier(x') = regular
```

<!-- Regular anchor remains regular under allowed perturbations. -->

### 8.3 C-MARGIN — Margin robustness
<!-- Score remains on correct side of threshold with a safety margin. -->

### 8.4 C-TRAJ — Trajectory perturbation robustness
<!-- Bounded position/speed/heading/history perturbations. -->

### 8.5 C-MAP — Map perturbation robustness
<!-- Bounded map uncertainty. -->

### 8.6 C-JOINT — Joint multi-agent robustness
<!-- Multiple agents perturbed simultaneously. -->

### 8.7 C-DROP — Observation robustness
<!-- Optional missing-track/history robustness if supported. -->

---

## 9. Verification Domain

### 9.1 Anchor class
<!-- regular or accident-prone. -->

### 9.2 Agent-count bounds
<!-- Fixed N or bounded N. -->

### 9.3 Trajectory-state bounds
<!-- Perturbation set around past trajectories. -->

### 9.4 Map-domain assumptions
<!-- Fixed map / bounded map / fixed map feature. -->

### 9.5 Graph-topology assumptions
<!-- Fixed adjacency or variable graph. -->

### 9.6 Ego-node assumptions
<!-- Fixed ego identity. -->

### 9.7 Class-specific domains
<!-- Separate regular and accident-prone verification domains. -->

---

## 10. Formal Encoding

### 10.1 Trajectory encoder encoding
<!-- MLP/GRU details if original/reproduction target available. -->

### 10.2 Map encoder encoding
<!-- CNN or fixed map feature. -->

### 10.3 Graph message-passing encoding
<!-- Relative-agent interactions. -->

### 10.4 Ego-feature extraction
<!-- 64-D ego feature. -->

### 10.5 Two-layer MLP encoding
<!-- Final binary head. -->

### 10.6 Decision rule encoding
<!-- Logit/threshold/class mapping. -->

### 10.7 Floating-point abstraction
<!-- Real arithmetic vs runtime floating point. -->

---

## 11. Verification Method

### 11.1 Verification paradigm
<!-- SMT / MILP / abstract interpretation / neural verification / robustness verification. -->

### 11.2 Soundness expectations
<!-- Formal proof vs incomplete search. -->

### 11.3 Solver / backend
<!-- TBD. -->

### 11.4 Timeout / resource policy
<!-- Fixed resource settings. -->

### 11.5 Proof obligation
<!-- Domain + model + negated robustness/class property. -->

### 11.6 Counterexample extraction
<!-- Perturbed scene causing class/mode flip. -->

---

## 12. Verification Workflow

### 12.1 Obtain/freeze classifier artifact
<!-- Original artifact or explicitly named reproduction. -->

### 12.2 Freeze preprocessing
<!-- Trajectory/map/graph transformations. -->

### 12.3 Select A2-D-01 anchor
<!-- Regular or accident-prone evidence case. -->

### 12.4 Select property
<!-- C-FN, C-FP, C-MARGIN, etc. -->

### 12.5 Instantiate bounded domain
<!-- Perturbation dimensions and bounds. -->

### 12.6 Encode classifier and property
<!-- Verifier-specific representation. -->

### 12.7 Validate formal/executable equivalence
<!-- Concrete-point comparisons. -->

### 12.8 Run verifier
<!-- verified / counterexample / unknown / timeout. -->

### 12.9 Replay counterexample
<!-- Original executable classifier. -->

### 12.10 Store evidence
<!-- Persist into A2-D-01 regression/evidence set. -->

---

## 13. Counterexample Handling

### 13.1 Counterexample definition
<!-- In-domain class or margin violation. -->

### 13.2 False-negative counterexample
<!-- accident-prone -> regular. -->

### 13.3 False-positive counterexample
<!-- regular -> accident-prone. -->

### 13.4 Executable replay
<!-- Confirm against original/reproduced classifier. -->

### 13.5 Numeric reconciliation
<!-- Solver/runtime differences. -->

### 13.6 Regression retention
<!-- Persist validated counterexamples. -->

---

## 14. Validation of the Formal Model

### 14.1 Preprocessing equivalence
<!-- Exact trajectory/map tensors. -->

### 14.2 Encoder equivalence
<!-- Trajectory and map features. -->

### 14.3 Graph-layer equivalence
<!-- Message passing. -->

### 14.4 Ego-feature equivalence
<!-- 64-D feature match. -->

### 14.5 MLP-head equivalence
<!-- Final logits. -->

### 14.6 Decision-rule equivalence
<!-- Hard class/mode mapping. -->

---

## 15. Quantitative Analysis

### 15.1 Verification cases
<!-- Counts by class/property/domain. -->

### 15.2 Verification outcomes
<!-- Verified / counterexample / unknown / timeout. -->

### 15.3 False-negative robustness
<!-- Accident-prone anchors. -->

### 15.4 False-positive robustness
<!-- Regular anchors. -->

### 15.5 Runtime
<!-- Per domain/property. -->

### 15.6 Robustness radius / margin
<!-- If method supports it. -->

### 15.7 Counterexample replay rate
<!-- Reproduced vs abstraction-only. -->

---

## 16. Robustness & Sensitivity

### 16.1 Trajectory perturbation size
<!-- Robustness as epsilon increases. -->

### 16.2 Agent-count sensitivity
<!-- Scaling with scene size. -->

### 16.3 Map sensitivity
<!-- Fixed vs perturbed map context. -->

### 16.4 Graph sensitivity
<!-- Fixed vs changing topology. -->

### 16.5 Decision-margin sensitivity
<!-- Low-margin vs high-margin anchors. -->

### 16.6 Class asymmetry
<!-- Compare accident-prone vs regular robustness. -->

---

## 17. Failure Modes

### 17.1 Accident-prone demotion
<!-- Safety-relevant false negative. -->

### 17.2 Regular promotion
<!-- False positive / unnecessary accident mode. -->

### 17.3 Low-margin instability
<!-- Tiny perturbations cause mode changes. -->

### 17.4 Map-induced mode flip
<!-- Classification depends strongly on local map perturbation. -->

### 17.5 Multi-agent interaction instability
<!-- Small changes to another agent alter ego mode. -->

### 17.6 Reproduction mismatch
<!-- Reproduced model diverges from original classifier semantics. -->

---

## 18. Known Limitations

### 18.1 Original classifier unavailable
<!-- Major assurance limitation. -->

### 18.2 Exact preprocessing unavailable
<!-- Cannot claim original equivalence without implementation. -->

### 18.3 Exact decision threshold unavailable
<!-- Must be obtained or explicitly chosen for reproduction. -->

### 18.4 Operational labels
<!-- regular/accident-prone are not universal formal safety truth. -->

### 18.5 Generated positive-class bias
<!-- Accident data inherit STRIVE generator/planner assumptions. -->

### 18.6 Domain restriction
<!-- Local proofs only. -->

### 18.7 Full graph/CNN tractability
<!-- Formal verification complexity. -->

---

## 19. Safety & Assurance Interpretation

### 19.1 Meaning of “verified”
<!-- Scope-qualified robustness statement. -->

### 19.2 Meaning of “falsified”
<!-- Concrete replay-confirmed mode flip. -->

### 19.3 Meaning of unknown / timeout
<!-- No conclusion. -->

### 19.4 False-negative significance
<!-- Accident mode suppressed. -->

### 19.5 False-positive significance
<!-- Accident mode unnecessarily activated. -->

### 19.6 System-level limits
<!-- Classifier assurance does not prove planner safety. -->

---

## 20. Reproducibility

### 20.1 Classifier source revision
<!-- Required if obtained. -->

### 20.2 Checkpoint hash
<!-- SHA-256. -->

### 20.3 Effective configuration
<!-- Architecture/preprocessing/threshold. -->

### 20.4 A2-D-01 dataset manifest
<!-- Anchor/domain/evidence set. -->

### 20.5 Property registry
<!-- IDs, versions, bounds. -->

### 20.6 Verifier/toolchain
<!-- Tool/version/backend. -->

### 20.7 Execution environment
<!-- OS/Python/PyTorch/verifier. -->

### 20.8 Companion metadata
<!-- `metadata/assurance/models/accident_classifier_verification.yaml`. -->

### 20.9 Profiler
<!-- `tools/profile_accident_classifier_verification.py`. -->

---

## 21. Assurance Evidence & Results

### 21.1 Claim-evidence matrix
<!-- Property -> class -> domain -> result. -->

### 21.2 Verified claims
<!-- None until formal runs are executed. -->

### 21.3 Falsified claims
<!-- Replay-confirmed counterexamples. -->

### 21.4 Inconclusive claims
<!-- Unknown / timeout / unavailable artifact. -->

### 21.5 Residual risk
<!-- Unverified domains, labels, planner behavior. -->

---

## 22. Relationships

### 22.1 Companion data card

```text
A2-D-01 — STRIVE Accident Scenario Classifier Verification Data Card
```

### 22.2 Paper-level planner relationship

```text
binary accident classifier
        │
        ├──► regular planner mode
        └──► accident-handling planner mode
```

### 22.3 Relationship to F-01
<!-- Multi-mode planner-tuning experiment. -->

### 22.4 Relationship to M-04
<!-- Explicit non-equivalence with public 10-way cluster classifier. -->

### 22.5 Other assurance approaches
<!-- A1 traffic-model verification; A3 optimizer falsification. -->

---

## 23. Terms of Art

### 23.1 Regular
<!-- Operational binary class. -->

### 23.2 Accident-prone
<!-- Operational binary class. -->

### 23.3 Mode selector
<!-- Binary classifier selecting planner mode. -->

### 23.4 Robustness domain
<!-- Allowed perturbation set. -->

### 23.5 Classification margin
<!-- Distance from decision boundary. -->

### 23.6 Counterexample
<!-- In-domain violation/class flip. -->

### 23.7 Reproduction
<!-- Independently implemented approximation of unreleased classifier. -->

### 23.8 Equivalence gap
<!-- Difference between reproduced/formal classifier and original artifact. -->

---

## 24. References

<!-- Formal Assurance in STRIVE project concept PDF -->
<!-- STRIVE paper and supplementary material -->
<!-- A2-D-01 assurance data card -->
<!-- M-04 public classifier card, with non-equivalence note -->
<!-- F-01 planner tuning card -->
<!-- selected formal-verification tool references once decided -->

---

## 25. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial Approach-2 accident-scenario-classifier verification model-card skeleton |
