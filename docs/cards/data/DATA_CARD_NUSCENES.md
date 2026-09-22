# D-01 — nuScenes Data Card for STRIVE

> **Card ID:** D-01  
> **Card type:** Data Card  
> **Status:** Skeleton  
> **Dataset:** nuScenes as used by STRIVE  
> **Primary downstream artifact:** M-01 Main Traffic Model Card

---

## 1. Summary

### 1.1 Dataset summary
<!-- What is this dataset, in one concise paragraph? -->

### 1.2 Why this dataset matters to STRIVE
<!-- What role does nuScenes play in STRIVE? -->

### 1.3 Key facts
<!-- Short table: dataset version, modalities actually used by STRIVE, sampling rate, categories, temporal window, map inputs. -->

---

## 2. Authorship

### 2.1 Dataset publisher
<!-- Who publishes nuScenes? -->

### 2.2 STRIVE data integration authors
<!-- Who created the STRIVE-specific processing/integration? -->

### 2.3 Dataset owners and maintainers
<!-- Upstream owner, downstream maintainer, contact if known. -->

### 2.4 Funding and institutional context
<!-- Relevant upstream and STRIVE project affiliations/funding, when documented. -->

---

## 3. Dataset Overview

### 3.1 Dataset version
<!-- nuScenes version(s) supported/used by STRIVE. -->

### 3.2 Dataset scope
<!-- What parts of nuScenes are in scope for this card? Clarify metadata/maps vs raw sensor data. -->

### 3.3 Unit of data
<!-- Scene, sample, annotation, agent trajectory, graph example, etc. -->

### 3.4 Data modalities used by STRIVE
<!-- Trajectories, semantic categories, vehicle dimensions, raster map layers, split metadata, etc. -->

### 3.5 Sensitive or restricted data
<!-- Note whether STRIVE uses raw imagery/sensor data or only metadata/annotations/maps. -->

### 3.6 Dataset maintenance
<!-- Upstream maintenance vs STRIVE-side assumptions. -->

---

## 4. Example of Data Points

### 4.1 STRIVE scene example
<!-- Describe one processed multi-agent scene/graph example. -->

### 4.2 Agent state representation
<!-- e.g. x, y, heading vector, speed, heading-change rate. -->

### 4.3 Vehicle attributes
<!-- e.g. length, width, semantic category. -->

### 4.4 Temporal structure
<!-- Past and future horizon represented in one training/evaluation item. -->

### 4.5 Map context
<!-- Local raster crop and semantic map layers. -->

---

## 5. Motivations & Intentions

### 5.1 Motivation for using nuScenes
<!-- Why was nuScenes selected for STRIVE? -->

### 5.2 Intended uses in STRIVE
<!-- Training traffic model, initialization, scenario generation, evaluation, planner tuning. -->

### 5.3 Out-of-scope uses
<!-- What conclusions or applications should not be made from this STRIVE-specific view of nuScenes? -->

### 5.4 Intended users
<!-- Researchers, engineers, evaluators, etc. -->

---

## 6. Access, Retention & Wipeout

### 6.1 Access requirements
<!-- How is nuScenes obtained? What is downloaded locally? -->

### 6.2 Expected local directory structure
<!-- STRIVE's expected `data/nuscenes/...` layout. -->

### 6.3 Redistribution constraints
<!-- Refer to upstream licensing/terms. -->

### 6.4 Retention
<!-- Whether STRIVE defines a retention policy; otherwise state not specified. -->

### 6.5 Deletion / wipeout
<!-- How local copies can be removed; distinguish from upstream account/data policies. -->

---

## 7. Provenance

### 7.1 Upstream source
<!-- Official nuScenes source and release. -->

### 7.2 Relationship to source
<!-- What STRIVE consumes unchanged and what it derives/transforms. -->

### 7.3 Collection process
<!-- Summarize upstream collection only to the extent needed for STRIVE context. -->

### 7.4 Geographic coverage
<!-- Locations represented by nuScenes and implications for STRIVE. -->

### 7.5 Temporal coverage
<!-- Scene duration, sample/annotation cadence relevant to STRIVE. -->

### 7.6 Versioning
<!-- Upstream dataset version and STRIVE repository/config assumptions. -->

---

## 8. Collection & Selection Criteria

### 8.1 Scene selection
<!-- Which split(s) and scene subsets does STRIVE use? -->

### 8.2 Agent selection
<!-- Main-paper categories and optional categories supported by code. -->

### 8.3 Trajectory eligibility
<!-- Valid-history/future requirements, missing values, filtering. -->

### 8.4 Map eligibility
<!-- Required maps/map expansion. -->

### 8.5 Scenario-generation selection
<!-- Validation/test subset selection, sequence interval, feasibility-related upstream selection where relevant. -->

---

## 9. Processing, Transformation & Labeling

### 9.1 Trajectory preprocessing
<!-- State conversion, velocities, heading-rate, normalization. -->

### 9.2 Coordinate transformations
<!-- Local frames, Singapore flip, other transformations. -->

### 9.3 Map preprocessing
<!-- Raster layers, crop bounds, resolution/size. -->

### 9.4 Category mapping
<!-- Mapping nuScenes taxonomy to STRIVE categories. -->

### 9.5 Filtering
<!-- Non-drivable overlap filtering and other documented filters. -->

### 9.6 Noise or augmentation
<!-- Training-time input noise and other augmentation. -->

### 9.7 Derived labels
<!-- Clarify what labels come from nuScenes vs are derived by STRIVE. -->

---

## 10. Dataset Structure & Schema

### 10.1 Raw upstream files used
<!-- Relevant nuScenes JSON/map files. -->

### 10.2 STRIVE loader
<!-- `src/datasets/nuscenes_dataset.py` -->

### 10.3 Scene graph schema
<!-- Node, edge/batch, trajectory, semantic, dimensions, map index. -->

### 10.4 Core tensor shapes
<!-- Document symbolic shapes rather than hard-coded dataset counts. -->

### 10.5 Missing-data representation
<!-- NaNs, visibility masks, truncated trajectories, etc. -->

---

## 11. Quantitative Analysis

### 11.1 Upstream dataset counts
<!-- Official scene/sample/annotation counts relevant to the selected version. -->

### 11.2 STRIVE-effective counts
<!-- Counts after STRIVE category/split/filter rules. Generated by profiler where possible. -->

### 11.3 Distribution by agent category
<!-- Cars, trucks, and optional categories. -->

### 11.4 Distribution by location
<!-- Boston/Singapore locations or map names. -->

### 11.5 Scene and trajectory statistics
<!-- Agents per scene, valid history/future coverage, timestep distribution. -->

### 11.6 Data-quality checks
<!-- Broken scene chains, missing metadata, malformed annotations, missing maps. -->

### 11.7 Profiler
<!-- `tools/profile_nuscenes_strive.py` and the facts it writes to companion metadata/output. -->

---

## 12. Validation & Quality Assurance

### 12.1 Structural validation
<!-- Required files and expected schema. -->

### 12.2 Semantic validation
<!-- Category mappings, trajectory validity, map consistency. -->

### 12.3 Leakage considerations
<!-- Train/validation/test split handling and scenario-derived data boundaries. -->

### 12.4 Reproducibility checks
<!-- Version, config, repository commit, profiler output. -->

---

## 13. Known Applications & Benchmarks

### 13.1 STRIVE traffic-model training
<!-- Link to M-01 when available. -->

### 13.2 Traffic-model evaluation
<!-- Reconstruction, sampling, displacement/collision metrics. -->

### 13.3 Scenario generation
<!-- Initialization and adversarial/solution optimization. -->

### 13.4 Planner evaluation and tuning
<!-- Downstream generated scenarios and planner experiments. -->

---

## 14. Known Limitations

### 14.1 Geographic limitations
<!-- Domain coverage. -->

### 14.2 Agent-class limitations
<!-- Main-paper car/truck emphasis. -->

### 14.3 Sampling and temporal limitations
<!-- 2 Hz annotation trajectory representation and finite horizon. -->

### 14.4 Behavior coverage
<!-- Rare events, unusual maneuvers, vulnerable road users, etc. -->

### 14.5 Map and annotation limitations
<!-- Dependence on nuScenes maps/boxes and derived trajectory quantities. -->

### 14.6 STRIVE-specific limitations
<!-- Bias introduced by selection, filtering, preprocessing, and downstream use. -->

---

## 15. Ethical, Safety & Societal Considerations

### 15.1 Privacy considerations
<!-- Distinguish metadata/map use from raw sensor content. -->

### 15.2 Safety considerations
<!-- Dataset/model outputs are research artifacts, not safety guarantees. -->

### 15.3 Bias and representativeness
<!-- Geographic, behavioral, class, collection biases. -->

### 15.4 Misuse risks
<!-- Inappropriate use as real-world accident prevalence or safety-certification evidence. -->

---

## 16. Licensing & Terms

### 16.1 nuScenes license / terms
<!-- Link and summarize only what is needed; do not restate legal terms inaccurately. -->

### 16.2 STRIVE code license
<!-- Repository license. -->

### 16.3 Derived-artifact licensing
<!-- Pretrained weights/generated scenarios if relevant to downstream relationship. -->

---

## 17. Reproducibility & Maintenance

### 17.1 Required versions
<!-- nuScenes version, devkit version, STRIVE revision. -->

### 17.2 Required configuration
<!-- Dataset/model config values needed to reproduce the documented view. -->

### 17.3 Companion metadata
<!-- `metadata/data/nuscenes_strive.yaml` -->

### 17.4 Quantitative profiler
<!-- `tools/profile_nuscenes_strive.py` -->

### 17.5 Update policy
<!-- What facts should be revisited when code/config/data versions change? -->

---

## 18. Relationships

### 18.1 Upstream
<!-- nuScenes -->

### 18.2 Downstream
<!-- M-01 Main Traffic Model -->

### 18.3 Dependency chain

```text
D-01  nuScenes Data Card
  │
  ▼
M-01  Main Traffic Model Card
```

---

## 19. Terms of Art

### 19.1 Scene
<!-- Definition and STRIVE interpretation. -->

### 19.2 Sample
<!-- Definition and STRIVE interpretation. -->

### 19.3 Agent
<!-- Definition and STRIVE interpretation. -->

### 19.4 Scene graph
<!-- Definition and STRIVE interpretation. -->

### 19.5 Past / future trajectory
<!-- Definition and STRIVE interpretation. -->

### 19.6 Map crop
<!-- Definition and STRIVE interpretation. -->

---

## 20. References

<!-- STRIVE paper -->
<!-- STRIVE GitHub repository -->
<!-- Official nuScenes documentation -->
<!-- Data Cards Playbook -->

---

## 21. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial D-01 skeleton |
