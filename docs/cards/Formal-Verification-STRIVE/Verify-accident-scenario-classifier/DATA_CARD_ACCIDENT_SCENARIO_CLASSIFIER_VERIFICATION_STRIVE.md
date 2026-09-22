# A2-D-01 — STRIVE Accident Scenario Classifier Verification Data Card

> **Card ID:** A2-D-01  
> **Card type:** Formal-Assurance Data Card  
> **Status:** Skeleton  
> **Assurance approach:** Verify the Accident Scenario Classifier  
> **Target:** STRIVE learned binary accident-mode classifier  
> **System:** S-01 — STRIVE  
> **Primary assurance question:** Does the classifier reliably distinguish regular from accident-prone traffic situations over a clearly defined input domain?

---

## 1. Dataset Summary

### 1.1 Dataset / evidence-set name
<!-- Canonical name for the classifier-verification evidence set. -->

### 1.2 Assurance purpose
<!-- Define how the dataset supports formal assurance of the learned classifier. -->

### 1.3 Verification target
<!-- Exact classifier implementation/checkpoint/configuration, if available. -->

### 1.4 Dataset role
<!-- Natural scenes, generated accident-prone scenes, bounded perturbation domains, counterexamples. -->

### 1.5 Dataset status
<!-- Proposed / generated / frozen / validated. -->

---

## 2. Assurance Claim Context

### 2.1 Top-level assurance claim
<!-- Example: within domain D, classifier output is stable/correct with respect to specified regular/accident-prone labels or robustness properties. -->

### 2.2 Safety relevance
<!-- Classifier output determines regular vs accident-handling planner mode. -->

### 2.3 Supported subclaims
<!-- Classification robustness, mode-selection consistency, boundary behavior. -->

### 2.4 Unsupported claims
<!-- No direct claim of full planner/system safety. -->

### 2.5 Evidence interpretation
<!-- Verified / counterexample / empirical correctness / unknown. -->

---

## 3. Target Classifier Scope

### 3.1 Classifier described in the STRIVE paper/supplement
<!-- Learned binary classifier: regular vs accident-prone. -->

### 3.2 Distinction from public M-04
<!-- Public M-04 is cluster-based scenario labeling, not this binary classifier. -->

### 3.3 Model availability
<!-- Whether classifier source/checkpoint is publicly available. -->

### 3.4 Verification boundary
<!-- Full classifier vs fixed encoder + final MLP vs reduced subnetwork. -->

### 3.5 Planner-mode decision boundary
<!-- Relationship between classifier output and regular/accident-handling mode. -->

---

## 4. Data Sources

### 4.1 nuScenes regular traffic scenes
<!-- Source of regular examples. -->

### 4.2 STRIVE-generated collision scenarios
<!-- Source of accident-prone examples. -->

### 4.3 D-01 relationship
<!-- nuScenes input representation and provenance. -->

### 4.4 D-02 relationship
<!-- Generated scenario representation and partitions. -->

### 4.5 Paper/supplement training-data description
<!-- Exact training/evaluation composition once verified. -->

### 4.6 Verification-generated cases
<!-- Perturbations, adversarial robustness cases, solver counterexamples. -->

---

## 5. Ground Truth & Label Semantics

### 5.1 Regular label
<!-- Definition and provenance. -->

### 5.2 Accident-prone label
<!-- Definition and provenance. -->

### 5.3 Generated collision label provenance
<!-- How generated accident-prone cases acquire their class. -->

### 5.4 Label noise / ambiguity
<!-- Difficult or borderline traffic situations. -->

### 5.5 Formal label vs operational label
<!-- Separate classifier training labels from formal safety truth. -->

### 5.6 Missing real-world formal ground truth
<!-- No universal label proving a scene is formally accident-prone. -->

---

## 6. Classifier Input Schema

### 6.1 Past trajectory history
<!-- Past two seconds of trajectories for all agents. -->

### 6.2 Agent state representation
<!-- Exact trajectory/state fields. -->

### 6.3 Agent attributes
<!-- length/width if used. -->

### 6.4 Semantic class
<!-- Agent category representation. -->

### 6.5 Local map input
<!-- Map crop / map feature representation. -->

### 6.6 Scene graph
<!-- Agent interactions / edge structure. -->

### 6.7 Visibility / masks
<!-- Missing observations. -->

---

## 7. Classifier Output Schema

### 7.1 Binary class
<!-- regular / accident-prone. -->

### 7.2 Logit / probability
<!-- If available from implementation. -->

### 7.3 Mode-selection output
<!-- Which planner mode is selected. -->

### 7.4 Verification status
<!-- verified / counterexample / unknown / timeout. -->

### 7.5 Counterexample payload
<!-- Input, predicted class, expected/spec class, margin/logit. -->

---

## 8. Candidate Assurance Properties

### 8.1 Label robustness
<!-- Output class remains invariant under bounded input perturbations. -->

### 8.2 Margin robustness
<!-- Classification margin stays above/below threshold. -->

### 8.3 Accident-prone non-demotion
<!-- Accident-prone cases should not become regular under allowed perturbations. -->

### 8.4 Regular-case stability
<!-- Regular cases should not spuriously switch modes under small perturbations. -->

### 8.5 Map-perturbation robustness
<!-- Stability to bounded map-input variation. -->

### 8.6 Agent-trajectory perturbation robustness
<!-- Position/speed/history perturbation robustness. -->

### 8.7 Combined scene robustness
<!-- Joint multi-agent perturbations. -->

---

## 9. Assurance-Oriented Label Policy

### 9.1 False-negative significance
<!-- Accident-prone -> regular error may suppress accident-handling mode. -->

### 9.2 False-positive significance
<!-- Regular -> accident-prone may cause unnecessary mode switching. -->

### 9.3 Asymmetric assurance priority
<!-- Whether false negatives should receive stronger requirements. -->

### 9.4 Borderline / abstain region
<!-- Optional uncertainty/abstention handling if included. -->

### 9.5 Threshold selection
<!-- Classification threshold and versioning. -->

---

## 10. Verification Domain

### 10.1 Natural anchor scenes
<!-- Recorded/generated source scenes used to center domains. -->

### 10.2 Number of agents
<!-- Fixed or bounded. -->

### 10.3 History bounds
<!-- Position/speed/heading perturbations. -->

### 10.4 Map bounds
<!-- Fixed raster / bounded pixels / fixed map feature. -->

### 10.5 Graph-topology assumptions
<!-- Fixed adjacency or variable graph. -->

### 10.6 Class-specific domains
<!-- Regular-anchor vs accident-anchor domains. -->

---

## 11. Sampling & Case Construction

### 11.1 Natural regular cases
<!-- nuScenes-derived. -->

### 11.2 Natural/generated accident-prone cases
<!-- STRIVE-generated collision cases. -->

### 11.3 Boundary cases
<!-- Classifier-logit/margin near decision threshold. -->

### 11.4 Perturbed cases
<!-- Controlled trajectory/map perturbations. -->

### 11.5 Counterexample-directed cases
<!-- Cases found by verifier/falsifier. -->

### 11.6 Hard-negative / hard-positive cases
<!-- Near-boundary misclassification cases. -->

---

## 12. Partitioning

### 12.1 Training provenance partition
<!-- Data reportedly used to train classifier. -->

### 12.2 Development assurance partition
<!-- Property/encoding development. -->

### 12.3 Frozen verification partition
<!-- Final reported assurance domains. -->

### 12.4 Regression partition
<!-- Counterexamples and prior failures. -->

### 12.5 Leakage controls
<!-- Keep final assurance evidence independent from tuning where possible. -->

---

## 13. Data Transformations

### 13.1 Trajectory normalization
<!-- Exact preprocessing. -->

### 13.2 Coordinate-frame transformation
<!-- Global/local frame behavior. -->

### 13.3 Map preprocessing
<!-- Crop/raster/encoder. -->

### 13.4 Graph construction
<!-- Nodes/edges/order. -->

### 13.5 Fixed-length history
<!-- Two-second input representation. -->

### 13.6 Verifier-specific abstraction
<!-- Fixed graph/map encoding, network simplification, etc. -->

---

## 14. Quantitative Dataset Profile

### 14.1 Total cases
<!-- To be measured. -->

### 14.2 Regular vs accident-prone balance
<!-- To be measured. -->

### 14.3 Source distribution
<!-- nuScenes vs generated scenarios. -->

### 14.4 Agent-count distribution
<!-- To be measured. -->

### 14.5 Map / scene distribution
<!-- To be measured. -->

### 14.6 Classifier-margin distribution
<!-- If logits/probabilities available. -->

### 14.7 Counterexample distribution
<!-- By class/property/perturbation type. -->

---

## 15. Coverage Strategy

### 15.1 Class coverage
<!-- Regular and accident-prone. -->

### 15.2 Scenario-type coverage
<!-- Generated collision modes / map contexts / interaction geometries. -->

### 15.3 Decision-boundary coverage
<!-- Focus on low-margin examples. -->

### 15.4 Perturbation coverage
<!-- Position/speed/heading/map perturbations. -->

### 15.5 Agent-count coverage
<!-- Small to dense scenes. -->

### 15.6 Failure-mode coverage
<!-- False negatives / false positives / unstable modes. -->

---

## 16. Validation & Quality Assurance

### 16.1 Schema validation
<!-- Required fields and tensor shapes. -->

### 16.2 Label validation
<!-- Check regular/accident-prone provenance. -->

### 16.3 Input reproduction
<!-- Reproduce exact classifier input preprocessing. -->

### 16.4 Classifier replay
<!-- Re-run original classifier on every concrete case. -->

### 16.5 Counterexample replay
<!-- Verify formal counterexamples against executable classifier. -->

### 16.6 Numeric tolerance
<!-- Formal model vs runtime differences. -->

---

## 17. Known Limitations

### 17.1 Classifier public-release availability
<!-- Learned binary classifier may not be present in public repository. -->

### 17.2 Label ambiguity
<!-- Accident-prone is an operational class, not universal formal truth. -->

### 17.3 Generated-data dependence
<!-- Accident-prone examples inherit STRIVE generation assumptions. -->

### 17.4 Class imbalance
<!-- Potential training/evaluation imbalance. -->

### 17.5 Distribution shift
<!-- nuScenes/generated data vs deployment. -->

### 17.6 Formal-domain restriction
<!-- Proof applies only to bounded domains. -->

### 17.7 Full-network tractability
<!-- GNN/map encoder/MLP complexity. -->

---

## 18. Safety & Assurance Interpretation

### 18.1 Meaning of a verified robustness property
<!-- Scope-qualified stability claim. -->

### 18.2 Meaning of a counterexample
<!-- Concrete bounded perturbation causing unsafe/misclassified mode. -->

### 18.3 False-negative interpretation
<!-- Accident-prone input classified regular. -->

### 18.4 False-positive interpretation
<!-- Regular input classified accident-prone. -->

### 18.5 System-level inference limits
<!-- Classifier assurance does not prove planner safety. -->

---

## 19. Reproducibility & Provenance

### 19.1 Classifier artifact identity
<!-- Checkpoint/source hash. -->

### 19.2 STRIVE revision
<!-- Source revision. -->

### 19.3 Training-data provenance
<!-- Natural/generated data versions. -->

### 19.4 Verification dataset manifest
<!-- Case IDs/domains/properties. -->

### 19.5 Property specification version
<!-- Robustness/label/margin properties. -->

### 19.6 Verifier/tool version
<!-- Once selected. -->

### 19.7 Random seeds
<!-- Sampling/falsification. -->

### 19.8 Generated-case lineage
<!-- Parent scene / STRIVE scenario / perturbation. -->

---

## 20. Relationships

### 20.1 Upstream evidence

```text
D-01 — STRIVE nuScenes Data
D-02 — STRIVE Generated Scenarios
```

### 20.2 Assurance approach

```text
Approach 2 — Verify the Accident Scenario Classifier
```

### 20.3 Companion assurance model card
<!-- Future A2-M-01 model card. -->

### 20.4 Relationship to M-04
<!-- Explicitly distinguish public cluster classifier from paper-level learned binary accident-mode classifier. -->

### 20.5 Planner-tuning relationship
<!-- Binary classifier determines regular vs accident-handling planner mode in paper-level workflow. -->

---

## 21. Terms of Art

### 21.1 Regular
<!-- Operational classifier class. -->

### 21.2 Accident-prone
<!-- Operational classifier class. -->

### 21.3 Mode selector
<!-- Classifier output controls planner operating mode. -->

### 21.4 Robustness domain
<!-- Allowed bounded perturbation set. -->

### 21.5 Classification margin
<!-- Logit/probability distance from threshold. -->

### 21.6 Counterexample
<!-- In-domain input violating the specified classification/robustness property. -->

---

## 22. References

<!-- Formal Assurance in STRIVE project concept PDF -->
<!-- STRIVE paper and supplementary material -->
<!-- D-01 nuScenes Data Card -->
<!-- D-02 Generated Scenarios Data Card -->
<!-- M-04 public Scenario Classifier card, with distinction caveat -->
<!-- F-01 Planner Tuning card -->
<!-- selected verifier/tool references once decided -->

---

## 23. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial Approach-2 accident-scenario-classifier verification data-card skeleton |
