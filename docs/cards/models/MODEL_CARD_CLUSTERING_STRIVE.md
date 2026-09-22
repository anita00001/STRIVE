# M-03 — STRIVE Scenario Clustering Model Card

> **Card ID:** M-03  
> **Card type:** Model Card  
> **Status:** Skeleton  
> **Model:** STRIVE Generated-Scenario Clustering  
> **Upstream:** D-02 — Generated Scenarios Data Card  
> **Downstream:** M-04 — Accident Classifier

---

## 1. Model Details

### 1.1 Model summary
<!-- What does STRIVE clustering do, and what scenarios does it operate on? -->

### 1.2 Model type
<!-- K-means clustering over collision-relative features. -->

### 1.3 Model artifact
<!-- `cluster.pkl` and associated label file. -->

### 1.4 Primary implementation
<!-- `src/cluster_scenarios.py`. -->

### 1.5 Authors, date, and license
<!-- STRIVE authors, CVPR 2022 release, code/artifact licensing. -->

---

## 2. Purpose & Role in STRIVE

### 2.1 Primary purpose
<!-- Group generated collision scenarios into collision-type clusters. -->

### 2.2 Role in analysis
<!-- Characterize the distribution of generated scenario types. -->

### 2.3 Relationship to D-02
<!-- Uses generated collision scenarios from D-02. -->

### 2.4 Relationship to M-04
<!-- Provides cluster assignments / semantic labels used by classification. -->

---

## 3. Intended Use

### 3.1 Intended uses
<!-- Scenario taxonomy, exploratory analysis, labeling newly generated scenarios. -->

### 3.2 Intended users
<!-- Researchers analyzing generated traffic collisions. -->

### 3.3 Out-of-scope uses
<!-- Real-world crash taxonomy, calibrated safety risk, causal conclusions. -->

---

## 4. Input Data

### 4.1 Scenario partitions used
<!-- `adv_sol_success` and `sol_failed` in public examples. -->

### 4.2 Required scenario fields
<!-- vehicle dimensions, adversarial trajectories, dt. -->

### 4.3 Collision-only requirement
<!-- Clustering is defined for generated scenarios where adversarial collision occurred. -->

### 4.4 Data provenance
<!-- D-02 plus planner/config/source split provenance. -->

---

## 5. Feature Extraction

### 5.1 Earliest collision selection
<!-- How the first planner collision is selected after interpolation. -->

### 5.2 Temporal interpolation
<!-- Interpolation scale and effective collision-time resolution. -->

### 5.3 Relative collision direction
<!-- Attacker position relative to planner at collision. -->

### 5.4 Relative attacker heading
<!-- Heading of attacker in planner-local frame. -->

### 5.5 Feature vector
<!-- Concatenated normalized direction and heading vectors. -->

### 5.6 Excluded information
<!-- What the clustering intentionally does not use. -->

---

## 6. Model Architecture / Algorithm

### 6.1 Algorithm
<!-- scikit-learn KMeans. -->

### 6.2 Number of clusters
<!-- Default `k=10`. -->

### 6.3 Initialization/randomness
<!-- `random_state=0`; other sklearn defaults for release environment. -->

### 6.4 Distance metric
<!-- Euclidean distance implicit in KMeans. -->

### 6.5 Fitted state
<!-- centroids, labels, model pickle. -->

---

## 7. Training / Fitting Procedure

### 7.1 Training script
<!-- `src/cluster_scenarios.py`. -->

### 7.2 Training command
<!-- Example using adv_sol_success + sol_failed. -->

### 7.3 Scenario loading
<!-- `datasets.utils.read_adv_scenes`. -->

### 7.4 Feature assembly
<!-- `[angvec_x, angvec_y, hvec_x, hvec_y]`. -->

### 7.5 K-means fit
<!-- Fitting process and saved artifact. -->

### 7.6 Visualization option
<!-- Optional cluster visualization/videos. -->

---

## 8. Public Precomputed Clustering

### 8.1 Artifact location
<!-- `data/clustering/cluster.pkl`. -->

### 8.2 Label file
<!-- `data/clustering/cluster_labels.txt`. -->

### 8.3 Source scenario set
<!-- README statement: over 400 scenarios, multiple nuScenes subsets and planner versions. -->

### 8.4 Reuse on new scenarios
<!-- `eval_adv_gen.py` prediction/assignment workflow. -->

---

## 9. Outputs

### 9.1 Cluster model
<!-- `cluster.pkl`. -->

### 9.2 Cluster assignments
<!-- Integer cluster indices. -->

### 9.3 Semantic labels
<!-- External label mapping from `cluster_labels.txt`. -->

### 9.4 Visualization artifacts
<!-- Cluster image and optional per-cluster videos. -->

### 9.5 Downstream labels
<!-- CSV assignments used by evaluation/classification. -->

---

## 10. Evaluation & Analysis

### 10.1 Cluster counts
<!-- Scenario count per cluster. -->

### 10.2 Centroid analysis
<!-- Interpret collision direction / heading centroids. -->

### 10.3 Distribution by solution status
<!-- `adv_sol_success` vs `sol_failed`. -->

### 10.4 Stability analysis
<!-- Across seeds, k, datasets, planner versions. -->

### 10.5 Coverage analysis
<!-- Fraction of collision scenarios represented. -->

---

## 11. Quantitative Analysis

### 11.1 Training-set size
<!-- Measured local count; distinguish from README's over-400 paper clustering source. -->

### 11.2 Feature statistics
<!-- Mean/std/range of 4-D clustering features. -->

### 11.3 Cluster membership distribution
<!-- counts and fractions. -->

### 11.4 Centroid coordinates
<!-- Fitted cluster centers. -->

### 11.5 Inertia
<!-- KMeans inertia. -->

### 11.6 Silhouette or optional diagnostics
<!-- Optional local diagnostics; not necessarily part of public release. -->

### 11.7 Profiler
<!-- `tools/profile_clustering.py` -->

---

## 12. Label Semantics

### 12.1 Cluster index vs semantic name
<!-- Cluster IDs are arbitrary; names come from separate label file. -->

### 12.2 Label ordering
<!-- Labels must correspond to cluster indices. -->

### 12.3 Human interpretation
<!-- Semantic names are post-hoc descriptions of geometric clusters. -->

### 12.4 Relabeling risks
<!-- Model pickle and label file must stay paired. -->

---

## 13. Factors

### 13.1 Planner dependence
<!-- Collision geometry depends on planner used to generate D-02. -->

### 13.2 Agent-category dependence
<!-- Car/truck vs broader-category generated scenarios. -->

### 13.3 Geographic dependence
<!-- nuScenes / D-02 geography. -->

### 13.4 Collision-detection dependence
<!-- Feature extraction depends on STRIVE collision checker/interpolation. -->

### 13.5 Dataset-composition dependence
<!-- Different success partitions/configs alter clusters. -->

---

## 14. Limitations

### 14.1 Low-dimensional features
<!-- Only relative collision direction and heading drive clustering. -->

### 14.2 Fixed k
<!-- Default 10 clusters is a modeling choice. -->

### 14.3 K-means geometry
<!-- Assumes Euclidean, roughly centroid-based cluster structure. -->

### 14.4 Arbitrary cluster indices
<!-- Numeric IDs have no intrinsic ordering/meaning. -->

### 14.5 Training-set composition
<!-- Provided clustering mixes scenarios from multiple planner versions/subsets. -->

### 14.6 Synthetic-data dependence
<!-- Clusters describe STRIVE-generated collisions, not observed crash population. -->

---

## 15. Ethical & Safety Considerations

### 15.1 Interpretation
<!-- Cluster labels should not be treated as real-world accident prevalence. -->

### 15.2 Bias
<!-- Inherits generation and source-data biases. -->

### 15.3 Misuse
<!-- Avoid using cluster membership as a standalone safety score. -->

---

## 16. Reproducibility

### 16.1 Source files
<!-- `src/cluster_scenarios.py`, `src/eval_adv_gen.py`, `src/datasets/utils.py`. -->

### 16.2 Input data
<!-- D-02 scenario directories. -->

### 16.3 Configuration
<!-- scenario_dirs, k, viz. -->

### 16.4 Saved artifacts
<!-- cluster.pkl, cluster_labels.txt. -->

### 16.5 Companion metadata
<!-- `metadata/models/clustering.yaml` -->

### 16.6 Quantitative profiler
<!-- `tools/profile_clustering.py` -->

### 16.7 Dependency versions
<!-- scikit-learn and related environment versions. -->

---

## 17. Relationships

### 17.1 Upstream

```text
D-02 — Generated Scenarios Data Card
```

### 17.2 Downstream

```text
M-04 — Accident Classifier
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
```

---

## 18. Terms of Art

### 18.1 Collision direction
<!-- Planner-relative direction from planner to colliding agent. -->

### 18.2 Relative attacker heading
<!-- Attacker heading expressed in planner-local frame at collision. -->

### 18.3 Cluster index
<!-- Integer output of the fitted KMeans model. -->

### 18.4 Cluster label
<!-- Human-readable semantic description paired with a cluster index. -->

---

## 19. References

<!-- STRIVE paper -->
<!-- STRIVE GitHub repository -->
<!-- `src/cluster_scenarios.py` -->
<!-- `src/eval_adv_gen.py` -->
<!-- `data/clustering/cluster.pkl` -->
<!-- `data/clustering/cluster_labels.txt` -->
<!-- D-02 data card -->

---

## 20. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial M-03 skeleton |
