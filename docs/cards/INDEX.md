# STRIVE Documentation Card Index

> **Documentation set:** STRIVE  
> **Repository:** `nv-tlabs/STRIVE`  
> **Inspected revision:** `b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d`  
> **Cards:** 11 total, including the S-01 system card

This index is the entry point for the STRIVE documentation-card set. It separates the core scenario-generation path from downstream analysis, planner evaluation, and planner tuning.

---

## Card Inventory

| ID | Type | Card | Markdown | Metadata | Profiler |
|---|---|---|---|---|---|
| S-01 | System | STRIVE System | `docs/cards/system/SYSTEM_CARD_STRIVE.md` | `metadata/system/strive_system.yaml` | `tools/profile_strive_system.py` |
| D-01 | Data | nuScenes Data | `docs/cards/data/DATA_CARD_NUSCENES_STRIVE.md` | `metadata/data/nuscenes_strive.yaml` | `tools/profile_nuscenes_strive.py` |
| M-01 | Model | Main Traffic Model | `docs/cards/models/MODEL_CARD_TRAFFIC.md` | `metadata/models/traffic_model.yaml` | `tools/profile_traffic_model.py` |
| M-02 | Model | Rule-Based Planner | `docs/cards/models/MODEL_CARD_RULE_BASED_PLANNER_STRIVE.md` | `metadata/models/rule_based_planner.yaml` | `tools/profile_rule_based_planner.py` |
| C-01 | Component | Initialization Optimization | `docs/cards/components/COMPONENT_CARD_INITIALIZATION_OPTIMIZATION.md` | `metadata/components/initialization_optimization.yaml` | `tools/profile_initialization_optimization.py` |
| C-02 | Component | Adversarial Optimization | `docs/cards/components/COMPONENT_CARD_ADVERSARIAL_OPTIMIZATION.md` | `metadata/components/adversarial_optimization.yaml` | `tools/profile_adversarial_optimization.py` |
| C-03 | Component | Solution Optimization | `docs/cards/components/COMPONENT_CARD_SOLUTION_OPTIMIZATION.md` | `metadata/components/solution_optimization.yaml` | `tools/profile_solution_optimization.py` |
| D-02 | Data | Generated Scenarios | `docs/cards/data/DATA_CARD_GENERATED_SCENARIOS_STRIVE.md` | `metadata/data/generated_scenarios.yaml` | `tools/profile_generated_scenarios.py` |
| M-03 | Model | Scenario Clustering | `docs/cards/models/MODEL_CARD_CLUSTERING_STRIVE.md` | `metadata/models/clustering.yaml` | `tools/profile_clustering.py` |
| M-04 | Model | Accident / Scenario Classifier | `docs/cards/models/MODEL_CARD_ACCIDENT_CLASSIFIER_STRIVE.md` | `metadata/models/accident_classifier.yaml` | `tools/profile_accident_classifier.py` |
| F-01 | Fitted Config | Planner Tuning | `docs/cards/fitted_configs/FITTED_CONFIG_CARD_PLANNER_TUNING_STRIVE.md` | `metadata/fitted_configs/planner_tuning.yaml` | `tools/profile_planner_tuning.py` |

---

## Core Generation Path

The common learned-traffic portion is:

```text
D-01  nuScenes Data
  │
  ▼
M-01  Main Traffic Model
  │
  ▼
C-01  Initialization Optimization
```

From C-01, the execution path depends on the attacked planner.

### Rule-Based (`hardcode`) Path

```text
D-01
  │
  ▼
M-01
  │
  ▼
C-01
  │
  ▼
M-02  Rule-Based Planner
  │
  ▼
C-02  Adversarial Optimization
  │
  ▼
C-03  Solution Optimization
  │
  ▼
D-02  Generated Scenarios
```

For this path, C-02 depends on both:

```text
M-01 — differentiable learned traffic/target model
M-02 — actual rule-based planner rollout
```

M-02 is also used during the hardcode initialization stage: after the first C-01 fit, the planner is rolled out, its ego future replaces the initialization target, and C-01 performs a second fit before C-02 begins.

### Replay (`ego`) Path

The replay planner uses the observed nuScenes ego trajectory and bypasses M-02:

```text
D-01
  │
  ▼
M-01
  │
  ▼
C-01
  │
  ▼
C-02
  │
  ▼
C-03
  │
  ▼
D-02
```

---

## Downstream Analysis

Generated scenarios feed the collision-analysis taxonomy:

```text
D-02
  │
  ▼
M-03  Scenario Clustering
  │
  ▼
M-04  Accident / Scenario Classifier
```

In the public repository:

- M-03 fits or loads the 10-cluster K-means collision taxonomy.
- M-04 is the cluster-assignment/class-labeling workflow built on M-03.
- M-04 is **not** a separately trained supervised classifier in the public release.

The paper's learned binary accident-mode classifier used in multi-mode planner tuning is a separate paper-level component and was not identified in the inspected public repository.

---

## Planner Evaluation & Tuning

M-02 is also directly connected to planner evaluation and F-01:

```text
D-02 ───────────────► Planner Evaluation
                         ▲
                         │
                       M-02
                         │
                         ▼
                       F-01
```

More explicitly:

```text
M-02 Rule-Based Planner
  ├──► C-02 Adversarial Optimization
  ├──► Planner Evaluation
  └──► F-01 Planner Tuning
```

F-01 documents the released:

```text
default
final_tuned_val_1
```

planner configurations and the paper-level tuning procedure.

The public `final_tuned_val_1` configuration changes four M-02 parameters:

```text
smax:        15.0 → 20.0
accmax:       3.0 → 4.0
score_wmin:   0.7 → 0.3
score_wfac:  0.05 → 0.02
```

---

## Full Documentation Graph

```text
                           ┌──────────────────┐
                           │ S-01 System Card │
                           └────────┬─────────┘
                                    │
                                    ▼
                              D-01 nuScenes
                                    │
                                    ▼
                           M-01 Traffic Model
                                    │
                                    ▼
                         C-01 Initialization
                             │             │
                  hardcode   │             │ replay
                             ▼             │
                    M-02 Rule Planner      │
                             │             │
                             └──────┬──────┘
                                    ▼
                         C-02 Adversarial
                                    │
                                    ▼
                          C-03 Solution
                                    │
                                    ▼
                      D-02 Generated Scenarios
                           │               │
                           │               └────────► Planner Evaluation
                           ▼                              ▲
                      M-03 Clustering                     │
                           │                              │
                           ▼                              │
                    M-04 Classification                  M-02
                                                          │
                                                          ▼
                                                        F-01
```

---

## Card Responsibilities

### S-01 — System Card

Use S-01 for:

- end-to-end architecture;
- system-wide data flow;
- runtime environment;
- licensing boundaries;
- cross-component limitations;
- public-release gaps;
- dependency validation.

### D-01 — nuScenes Data

Use D-01 for:

- source-data scope;
- splits and horizons;
- state/schema definitions;
- map crops;
- filtering;
- data provenance.

### M-01 — Main Traffic Model

Use M-01 for:

- graph CVAE architecture;
- latent prior/posterior;
- map and trajectory encoders;
- decoder/dynamics;
- training objective;
- traffic-model checkpoint profiling.

### M-02 — Rule-Based Planner

Use M-02 for:

- `HardcodeNuscPlanner`;
- lane matching and splines;
- surrounding-agent prediction hypotheses;
- 25-profile default ego speed search;
- five-circle collision scoring;
- candidate selection;
- planner rollout;
- default and tuned configurations;
- the released `rollout(init_state=...)` undefined-`vehicle_atts` issue.

### C-01 — Initialization Optimization

Use C-01 for:

- latent fitting to source trajectories;
- hardcode planner initialization/refit;
- initialization iteration counts;
- released `TgtMatchingLoss` behavior.

### C-02 — Adversarial Optimization

Use C-02 for:

- planner-target attack objective;
- latent optimization;
- feasibility filtering;
- actual-planner vs differentiable-proxy behavior;
- adversarial success criteria.

### C-03 — Solution Optimization

Use C-03 for:

- collision-free counterfactual search;
- solution horizon;
- solution success criteria;
- returned non-planner trajectory behavior.

### D-02 — Generated Scenarios

Use D-02 for:

- JSON serialization;
- result partitions;
- trajectory/latent fields;
- generated-scenario provenance;
- downstream scenario dataset usage.

### M-03 — Scenario Clustering

Use M-03 for:

- four-dimensional collision features;
- K-means fitting;
- 10 public clusters;
- precomputed `cluster.pkl`;
- scikit-learn reproducibility considerations.

### M-04 — Accident / Scenario Classifier

Use M-04 for:

- public cluster-based scenario classification;
- class-index-to-label mapping;
- classification CSV outputs;
- distinction from the paper's unreleased learned accident-mode classifier.

### F-01 — Planner Tuning

Use F-01 for:

- `DEF_CONFIG`;
- `final_tuned_val_1`;
- default-to-tuned parameter differences;
- paper-level 432-combination tuning procedure;
- planner tuning/evaluation results;
- public-release tuning gaps.

---

## Important Cross-Card Distinctions

### Public M-04 vs Paper Accident-Mode Classifier

Do not conflate:

```text
Public M-04
= M-03 KMeans.predict + semantic label lookup
```

with:

```text
Paper accident-mode classifier
= learned binary regular/accident-prone mode selector
```

The latter is described in the paper/supplement but was not identified in the public source release.

### M-02 vs M-01 in C-02

For rule-based attacks:

```text
M-01
```

provides the differentiable traffic prior/target-node model, while:

```text
M-02
```

provides the actual rule-based planner rollout used by STRIVE.

Both matter to C-02, but they serve different functions.

### Generated Scenario Success Partitions

```text
adv_failed
```

means adversarial optimization did not produce the required collision.

```text
sol_failed
```

means adversarial generation succeeded but C-03 did not find a collision-free solution.

```text
adv_sol_success
```

means both C-02 and C-03 succeeded.

---

## Recommended Reading Order

For the complete system:

```text
S-01
→ D-01
→ M-01
→ M-02
→ C-01
→ C-02
→ C-03
→ D-02
→ M-03
→ M-04
→ F-01
```

For scenario generation only:

```text
D-01 → M-01 → C-01 → M-02 → C-02 → C-03 → D-02
```

with M-02 omitted when studying the replay-planner path.

For generated-scenario analysis only:

```text
D-02 → M-03 → M-04
```

For planner evaluation/tuning:

```text
M-02 → D-02 → Planner Evaluation → F-01
```

---

## Source Baseline

Documentation in this set was grounded against:

```text
Repository: nv-tlabs/STRIVE
Revision:   b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d
Paper:      CVPR 2022
```

The subordinate cards should be treated as the detailed source of truth for component-specific implementation behavior. S-01 and this index provide system-level navigation and dependency context.

---

## Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.1 | 2026-09-21 | Added M-02 Rule-Based Planner, updated card count to 11, and corrected hardcode/replay generation, planner-evaluation, and F-01 relationships. |
