# D-02 — Generated Scenarios Data Card for STRIVE

> **Card ID:** D-02  
> **Card type:** Data Card  
> **Status:** Skeleton  
> **Dataset:** STRIVE Generated Scenarios  
> **Upstream:** C-02 — Adversarial Optimization, C-03 — Solution Optimization  
> **Downstream:** M-03 — Clustering, M-04 — Accident Classifier

---

## 1. Summary

### 1.1 Dataset summary
<!-- What are STRIVE generated scenarios? -->

### 1.2 Role in the STRIVE pipeline
<!-- Explain how generated scenarios become downstream analysis/training data. -->

### 1.3 Dataset unit
<!-- One saved scenario JSON and its associated trajectories/metadata. -->

### 1.4 Scenario result partitions
<!-- `adv_failed`, `sol_failed`, `adv_sol_success`. -->

---

## 2. Authorship

### 2.1 Dataset creators
<!-- STRIVE authors / public repository. -->

### 2.2 Upstream dataset dependency
<!-- nuScenes / D-01. -->

### 2.3 Generation-system dependency
<!-- M-01, C-01, C-02, C-03. -->

### 2.4 Maintenance
<!-- Who maintains the public generated-scenario release and local derived copy. -->

---

## 3. Dataset Overview

### 3.1 Dataset source
<!-- Generated rather than directly collected. -->

### 3.2 Generation pipeline
<!-- D-01 → M-01 → C-01 → C-02 → C-03 → D-02. -->

### 3.3 Planner variants
<!-- Rule-based and replay planner generation outputs. -->

### 3.4 Agent-category variants
<!-- Cars/trucks vs supplementary category configurations if applicable. -->

### 3.5 Temporal resolution
<!-- `dt`, past/future trajectory horizons. -->

---

## 4. Example of Data Points

### 4.1 Scenario JSON structure
<!-- Example conceptual schema of one saved generated scenario. -->

### 4.2 Initialization trajectory
<!-- `fut_init`. -->

### 4.3 Adversarial trajectory
<!-- `fut_adv`. -->

### 4.4 Solution trajectory
<!-- `fut_sol` when available. -->

### 4.5 Latent fields
<!-- `z_adv`, `z_sol`, `z_prior`. -->

### 4.6 Attack metadata
<!-- `attack_agt`, `attack_t`. -->

### 4.7 Agent metadata
<!-- N, dt, map, dimensions, semantics, past trajectory. -->

---

## 5. Motivations & Intentions

### 5.1 Why the dataset is generated
<!-- Stress-test planners using plausible accident-prone scenarios. -->

### 5.2 Intended research uses
<!-- Robustness analysis, scenario taxonomy, classifier training, clustering. -->

### 5.3 Downstream use by M-03
<!-- Clustering generated accidents/scenarios. -->

### 5.4 Downstream use by M-04
<!-- Accident classifier training/evaluation. -->

### 5.5 Out-of-scope uses
<!-- Real-world accident statistics, safety certification, causal claims. -->

---

## 6. Access, Retention & Distribution

### 6.1 Public release
<!-- Download path / release mechanism. -->

### 6.2 Local output path
<!-- STRIVE generation output directories. -->

### 6.3 Redistribution
<!-- Licensing and nuScenes-derived constraints. -->

### 6.4 Retention
<!-- Local/generated artifact retention policy. -->

### 6.5 Deletion
<!-- How to remove generated artifacts locally. -->

---

## 7. Provenance

### 7.1 Source dataset
<!-- D-01 nuScenes. -->

### 7.2 Source model
<!-- M-01 traffic model checkpoint. -->

### 7.3 Generation components
<!-- C-01, C-02, C-03. -->

### 7.4 Planner provenance
<!-- Planner name/config used to generate each scenario set. -->

### 7.5 Configuration provenance
<!-- Exact adversarial-generation config. -->

### 7.6 Code revision
<!-- STRIVE commit/release. -->

---

## 8. Generation & Selection Criteria

### 8.1 Source scene selection
<!-- Split, val_size, seq_interval, agent categories. -->

### 8.2 Feasibility filtering
<!-- Distance, time, in-front, map-separation, motion criteria. -->

### 8.3 Adversarial success filtering
<!-- Definition from C-02. -->

### 8.4 Solution success filtering
<!-- Definition from C-03. -->

### 8.5 Result partition assignment
<!-- Logic for adv_failed / sol_failed / adv_sol_success. -->

### 8.6 Saved vs discarded cases
<!-- Which candidate scenes are skipped before serialization. -->

---

## 9. Processing & Transformation

### 9.1 Trajectory normalization/unnormalization
<!-- How outputs are converted for JSON storage. -->

### 9.2 Planner trajectory replacement
<!-- Actual planner trajectory vs internal model planner prediction. -->

### 9.3 Non-planner solution preservation
<!-- C-03 restoration of C-02 adversarial trajectories. -->

### 9.4 Latent serialization
<!-- How tensors become JSON lists. -->

### 9.5 Semantic encoding
<!-- Saved semantic vectors and category decoding. -->

### 9.6 Map identifier
<!-- Stored map/location field. -->

---

## 10. Dataset Structure & Schema

### 10.1 Directory structure
<!-- `scenario_results/{adv_failed,sol_failed,adv_sol_success}/`. -->

### 10.2 Filename convention
<!-- `scene_XXXX.json`. -->

### 10.3 Required fields
<!-- N, dt, map, lw, sem, past, fut_init, fut_adv. -->

### 10.4 Conditional fields
<!-- fut_sol, z_adv, z_sol, z_prior, attack metadata, internal ego trajectory. -->

### 10.5 Field shapes
<!-- Symbolic dimensions for each array. -->

### 10.6 Data types
<!-- JSON numeric/list/string representations. -->

---

## 11. Quantitative Analysis

### 11.1 Scenario counts
<!-- Counts by result partition. -->

### 11.2 Agent-count distribution
<!-- Distribution of N. -->

### 11.3 Map/location distribution
<!-- Counts by stored map. -->

### 11.4 Attack-agent category distribution
<!-- Car/truck/etc. -->

### 11.5 Attack-time distribution
<!-- `attack_t`. -->

### 11.6 Success rates
<!-- Adversarial and solution success rates with denominators clearly defined. -->

### 11.7 Collision statistics
<!-- Planner/attacker/other/environment collision metrics. -->

### 11.8 Kinematic statistics
<!-- Velocity, acceleration, heading-rate distributions. -->

### 11.9 Latent statistics
<!-- Prior likelihood / Mahalanobis / latent displacement if available. -->

### 11.10 Profiler
<!-- `tools/profile_generated_scenarios.py` -->

---

## 12. Validation & Quality Assurance

### 12.1 Schema validation
<!-- Required/conditional field checks. -->

### 12.2 Shape validation
<!-- Consistent agent/time dimensions. -->

### 12.3 Finite-value checks
<!-- NaN/Inf handling. -->

### 12.4 Collision validation
<!-- Recompute success labels from trajectories when possible. -->

### 12.5 Partition consistency
<!-- Ensure folder agrees with adversarial/solution outcome. -->

### 12.6 Map/category consistency
<!-- Validate map names and semantic vectors. -->

### 12.7 Provenance validation
<!-- Config/checkpoint/code hashes. -->

---

## 13. Known Applications & Benchmarks

### 13.1 Planner stress testing
<!-- Primary STRIVE application. -->

### 13.2 Scenario clustering
<!-- M-03. -->

### 13.3 Accident classification
<!-- M-04. -->

### 13.4 Planner tuning
<!-- Indirect downstream relationship through M-04/F-01 if applicable. -->

### 13.5 Visualization and qualitative analysis
<!-- Scenario videos/images. -->

---

## 14. Known Limitations

### 14.1 Synthetic/optimized nature
<!-- Generated scenarios are model-based, not observed accidents. -->

### 14.2 Learned-prior dependence
<!-- M-01 determines plausibility. -->

### 14.3 Planner dependence
<!-- Scenario outcome depends on attacked planner/config. -->

### 14.4 Selection bias
<!-- Only feasible/generated/saved scenes are represented. -->

### 14.5 Geographic/category bias
<!-- Inherited from D-01 and M-01. -->

### 14.6 Collision-model limitations
<!-- Optimization vs final collision checks. -->

### 14.7 Finite-horizon limitations
<!-- 6s saved horizons / longer solution search where applicable. -->

---

## 15. Ethical, Safety & Societal Considerations

### 15.1 Safety interpretation
<!-- Generated collisions are simulation stress tests, not real-world incident probability. -->

### 15.2 Misuse risk
<!-- Avoid operationalizing scenarios as instructions for causing real-world crashes. -->

### 15.3 Dataset bias
<!-- Inherited and generation-induced biases. -->

### 15.4 Reporting requirements
<!-- Clearly distinguish synthetic generated accidents from observed accidents. -->

---

## 16. Licensing & Terms

### 16.1 STRIVE generated scenario license
<!-- CC-BY-NC-SA-4.0 per repository README. -->

### 16.2 nuScenes-derived status
<!-- Upstream nuScenes terms also matter. -->

### 16.3 STRIVE source license
<!-- MIT for code, distinct from generated artifacts. -->

### 16.4 Redistribution considerations
<!-- Requirements for sharing local derived scenario sets. -->

---

## 17. Reproducibility & Maintenance

### 17.1 Required source versions
<!-- STRIVE commit, M-01 checkpoint, D-01 version. -->

### 17.2 Generation configuration
<!-- Rule-based/replay config and planner cfg. -->

### 17.3 Randomness
<!-- Any sampling/shuffling seeds or nondeterministic GPU behavior. -->

### 17.4 Companion metadata
<!-- `metadata/data/generated_scenarios.yaml` -->

### 17.5 Quantitative profiler
<!-- `tools/profile_generated_scenarios.py` -->

### 17.6 Update triggers
<!-- New checkpoint/config/planner/data version. -->

---

## 18. Relationships

### 18.1 Upstream

```text
D-01 — nuScenes Data Card
  │
  ▼
M-01 — Main Traffic Model
  │
  ▼
C-01 — Initialization Optimization
  │
  ▼
C-02 — Adversarial Optimization
  │
  ▼
C-03 — Solution Optimization
```

### 18.2 Downstream

```text
M-03 — Clustering
M-04 — Accident Classifier
```

### 18.3 Dependency chain

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
  │
  ▼
C-03  Solution Optimization
  │
  ▼
D-02  Generated Scenarios
  │
  ├── M-03 Clustering
  └── M-04 Accident Classifier
```

---

## 19. Terms of Art

### 19.1 Initialization scenario
<!-- C-01 fitted source-scene future. -->

### 19.2 Adversarial scenario
<!-- C-02 optimized collision scenario. -->

### 19.3 Solution scenario
<!-- C-03 collision-free counterfactual response. -->

### 19.4 Attacker
<!-- Selected non-planner agent associated with the adversarial collision. -->

### 19.5 Attack time
<!-- Selected collision/attack timestep. -->

### 19.6 `adv_failed`
<!-- Adversarial optimization did not create selected-attacker collision. -->

### 19.7 `sol_failed`
<!-- Adversarial success but no successful solution found. -->

### 19.8 `adv_sol_success`
<!-- Both adversarial and solution optimization succeeded. -->

---

## 20. References

<!-- STRIVE paper -->
<!-- STRIVE GitHub repository -->
<!-- generated-scenario release -->
<!-- `src/utils/scenario_gen.py` -->
<!-- `src/adv_scenario_gen.py` -->
<!-- C-02 and C-03 component cards -->
<!-- D-01 data card -->

---

## 21. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial D-02 skeleton |
