# M-04 — STRIVE Accident Classifier Model Card

> **Card ID:** M-04  
> **Card type:** Model Card  
> **Status:** Skeleton  
> **Model:** STRIVE Accident / Scenario Classifier  
> **Upstream:** D-02 — Generated Scenarios Data Card, M-03 — Scenario Clustering  
> **Downstream:** F-01 — Planner Tuning

---

## 1. Model Details

### 1.1 Model summary
<!-- What constitutes the STRIVE accident/scenario classifier in the public release? -->

### 1.2 Model type
<!-- Clarify whether this is cluster-based classification, a learned classifier, or another released mechanism. -->

### 1.3 Primary implementation
<!-- Identify exact public source file(s) and artifact(s). -->

### 1.4 Model artifacts
<!-- Clustering model, labels, classifier-specific artifacts if any. -->

### 1.5 Authors, date, and license
<!-- STRIVE authors, CVPR 2022 release, code/artifact licensing. -->

---

## 2. Purpose & Role in STRIVE

### 2.1 Primary purpose
<!-- Assign generated collision scenarios to interpretable accident/scenario categories. -->

### 2.2 Role in evaluation
<!-- Describe how classification supports scenario distribution analysis. -->

### 2.3 Relationship to D-02
<!-- Consumes generated scenario trajectories and metadata. -->

### 2.4 Relationship to M-03
<!-- Uses clustering-derived representations / labels if applicable. -->

### 2.5 Relationship to F-01
<!-- How classified scenarios inform planner tuning or downstream analysis. -->

---

## 3. Intended Use

### 3.1 Intended uses
<!-- Categorize generated accident-prone scenarios for analysis and planner evaluation. -->

### 3.2 Intended users
<!-- Researchers evaluating planner failure modes. -->

### 3.3 Out-of-scope uses
<!-- Real-world crash diagnosis, legal fault, severity prediction, calibrated risk. -->

---

## 4. Input Data

### 4.1 Input scenario partitions
<!-- Which D-02 partitions can be classified. -->

### 4.2 Required fields
<!-- `fut_adv`, `lw`, `dt`, and any other required fields. -->

### 4.3 Collision requirement
<!-- Whether classification requires a planner-agent collision. -->

### 4.4 Input provenance
<!-- D-02 planner/config/source data dependencies. -->

---

## 5. Feature Extraction

### 5.1 Collision feature extraction
<!-- Reused M-03 collision-direction / heading features if applicable. -->

### 5.2 Temporal interpolation
<!-- Collision-time interpolation and resolution. -->

### 5.3 Planner-relative coordinate frame
<!-- Transform into planner-local frame. -->

### 5.4 Feature vector schema
<!-- Exact classifier input dimensions/ordering. -->

### 5.5 Optional auxiliary features
<!-- Relative speed or other evaluation-only features, if relevant. -->

---

## 6. Classification Mechanism

### 6.1 Classifier type
<!-- Precomputed clustering prediction / explicit classifier implementation. -->

### 6.2 Decision rule
<!-- How class assignment is produced. -->

### 6.3 Number of classes
<!-- Expected class count. -->

### 6.4 Class ordering
<!-- Mapping from numeric IDs to labels. -->

### 6.5 Confidence or distance
<!-- Whether the public release exposes confidence, distance, or only hard labels. -->

---

## 7. Classes & Label Semantics

### 7.1 Released class names
<!-- Exact ordered label set. -->

### 7.2 Cluster/class index mapping
<!-- Relationship between M-03 indices and M-04 semantic labels. -->

### 7.3 Human-authored labels
<!-- Clarify post-hoc semantic naming. -->

### 7.4 Label ambiguity
<!-- Boundaries between similar collision geometries. -->

### 7.5 Versioning
<!-- Model artifact and label file must remain paired. -->

---

## 8. Training / Fitting Data

### 8.1 Source generated scenarios
<!-- D-02 / M-03 training source. -->

### 8.2 Scenario count
<!-- Exact local count vs public "over 400" statement. -->

### 8.3 Planner mix
<!-- Multiple rule-based planner versions if inherited from M-03. -->

### 8.4 nuScenes subsets
<!-- Source subset mixture. -->

### 8.5 Selection bias
<!-- Collision-only and generation feasibility filtering. -->

---

## 9. Training / Construction Procedure

### 9.1 Artifact construction
<!-- How the classification mechanism is constructed from M-03. -->

### 9.2 Model fitting
<!-- If no separate training exists, document reuse of M-03 fit. -->

### 9.3 Semantic label assignment
<!-- Human mapping from model IDs to class names. -->

### 9.4 Serialization
<!-- Saved artifact formats and paths. -->

---

## 10. Inference Procedure

### 10.1 Scenario loading
<!-- Input JSON loading flow. -->

### 10.2 Feature computation
<!-- Collision feature generation. -->

### 10.3 Class prediction
<!-- Model call / nearest centroid / `predict`. -->

### 10.4 Semantic label lookup
<!-- Map numeric class to human-readable name. -->

### 10.5 CSV/report output
<!-- Per-scenario classification output. -->

---

## 11. Evaluation Metrics

### 11.1 Classification distribution
<!-- Count/fraction per class. -->

### 11.2 Agreement with cluster semantics
<!-- Manual inspection / qualitative consistency. -->

### 11.3 Stability
<!-- Sensitivity to model artifact, feature extraction, and dataset composition. -->

### 11.4 Coverage
<!-- Fraction of generated collision scenarios that can be classified. -->

### 11.5 Optional confidence diagnostics
<!-- Centroid distance or margin if computed locally. -->

---

## 12. Quantitative Analysis

### 12.1 Class distribution
<!-- Counts and percentages by class. -->

### 12.2 Distribution by scenario partition
<!-- `adv_sol_success` vs `sol_failed`. -->

### 12.3 Distribution by planner/configuration
<!-- If multiple D-02 sources are combined. -->

### 12.4 Feature-to-centroid distance
<!-- Optional local analysis. -->

### 12.5 Unassigned/invalid cases
<!-- Missing collision, malformed fields, invalid artifact. -->

### 12.6 Profiler
<!-- `tools/profile_accident_classifier.py` -->

---

## 13. Validation

### 13.1 Artifact compatibility
<!-- Classifier artifact and label-file consistency. -->

### 13.2 Feature compatibility
<!-- Exact match with M-03 feature ordering. -->

### 13.3 Label-count validation
<!-- Number of labels equals number of model classes. -->

### 13.4 Scenario validation
<!-- Collision exists and feature extraction succeeds. -->

### 13.5 Reproducibility validation
<!-- Code revision, model hash, label hash, dependency versions. -->

---

## 14. Factors

### 14.1 Planner dependence
<!-- Generated collision geometry depends on planner. -->

### 14.2 Agent-category dependence
<!-- Class assignment behavior across category sets. -->

### 14.3 Geographic dependence
<!-- nuScenes geography / D-02 distribution. -->

### 14.4 Collision-detection dependence
<!-- Class features depend on STRIVE collision checker. -->

### 14.5 Model-version dependence
<!-- Different M-03 fits may permute or alter class boundaries. -->

---

## 15. Limitations

### 15.1 Cluster-derived classes
<!-- Classes may inherit limitations of unsupervised M-03 clustering. -->

### 15.2 Hard assignment
<!-- No uncertainty if public workflow outputs only a single class. -->

### 15.3 Synthetic-data dependence
<!-- Categories characterize generated collisions, not real-world crash populations. -->

### 15.4 Limited feature space
<!-- Classification may ignore speed, map context, and other relevant dimensions. -->

### 15.5 Semantic-label subjectivity
<!-- Human names are interpretations of geometric clusters. -->

### 15.6 Version-coupling
<!-- Model and label artifacts must stay synchronized. -->

---

## 16. Ethical & Safety Considerations

### 16.1 Interpretation
<!-- Class labels describe synthetic generated collision geometry. -->

### 16.2 Bias
<!-- Inherited from D-02 and M-03. -->

### 16.3 Misuse
<!-- Do not use class assignment as real-world fault/severity/risk determination. -->

### 16.4 Reporting
<!-- Clearly state generated/synthetic source and classifier provenance. -->

---

## 17. Reproducibility

### 17.1 Source files
<!-- `src/eval_adv_gen.py`, M-03 clustering source, scenario loader. -->

### 17.2 Input artifacts
<!-- `cluster.pkl`, `cluster_labels.txt`, D-02 scenarios. -->

### 17.3 Output artifacts
<!-- `*_labels.csv`, distribution plots/reports. -->

### 17.4 Companion metadata
<!-- `metadata/models/accident_classifier.yaml` -->

### 17.5 Quantitative profiler
<!-- `tools/profile_accident_classifier.py` -->

### 17.6 Required dependency versions
<!-- Python, NumPy, scikit-learn, STRIVE revision. -->

---

## 18. Relationships

### 18.1 Upstream

```text
D-02 — Generated Scenarios
  │
  ▼
M-03 — Scenario Clustering
```

### 18.2 Downstream

```text
F-01 — Planner Tuning
```

### 18.3 Dependency chain

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

## 19. Terms of Art

### 19.1 Accident class
<!-- Human-readable collision/scenario category. -->

### 19.2 Class index
<!-- Numeric model output. -->

### 19.3 Cluster label
<!-- Semantic name inherited from M-03 label mapping. -->

### 19.4 Classification
<!-- Assignment of a generated collision scenario to one category. -->

---

## 20. References

<!-- STRIVE paper -->
<!-- STRIVE GitHub repository -->
<!-- `src/eval_adv_gen.py` -->
<!-- `src/cluster_scenarios.py` -->
<!-- `data/clustering/cluster.pkl` -->
<!-- `data/clustering/cluster_labels.txt` -->
<!-- D-02 data card -->
<!-- M-03 model card -->

---

## 21. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial M-04 skeleton |
