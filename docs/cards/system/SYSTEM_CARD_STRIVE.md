# S-01 — STRIVE System Card

> **Card ID:** S-01  
> **Card type:** System Card  
> **Status:** Skeleton  
> **System:** STRIVE — Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior  
> **Primary repository:** `nv-tlabs/STRIVE`

---

## 1. System Summary

### 1.1 System purpose
<!-- What problem does STRIVE solve? -->

### 1.2 Core idea
<!-- Learned traffic prior + latent-space optimization + planner-in-the-loop scenario generation. -->

### 1.3 System outputs
<!-- Generated adversarial scenarios, collision-free solutions, cluster/classification outputs, planner-tuning artifacts. -->

### 1.4 Primary research context
<!-- CVPR 2022 paper and intended research setting. -->

---

## 2. System Scope

### 2.1 In-scope functionality
<!-- Traffic-prior training, scenario generation, solution search, evaluation, clustering, planner evaluation/tuning. -->

### 2.2 Out-of-scope functionality
<!-- Production AV control, real-world crash prediction, safety certification, causal accident analysis. -->

### 2.3 Supported planners
<!-- Replay/ego and rule-based planner. -->

### 2.4 Supported datasets
<!-- nuScenes trainval/mini and generated STRIVE scenarios. -->

---

## 3. System Architecture

### 3.1 High-level architecture
<!-- Overall data/model/component flow. -->

### 3.2 Primary dependency chain

```text
D-01  nuScenes Data
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
  ├── M-03 Scenario Clustering
  │       │
  │       ▼
  │     M-04 Accident / Scenario Classifier
  │       │
  │       ▼
  │     F-01 Planner Tuning
  │
  └── Planner Evaluation
```

### 3.3 Runtime subsystems
<!-- Dataset loader, map environment, traffic model, optimizer stack, planner, evaluator. -->

### 3.4 Offline vs runtime behavior
<!-- Training/fitting vs scenario-generation/evaluation stages. -->

---

## 4. System Components

### 4.1 D-01 — nuScenes Data Card
<!-- Source metadata, maps, trajectories, semantics. -->

### 4.2 M-01 — Main Traffic Model
<!-- Learned multi-agent traffic prior / graph CVAE. -->

### 4.3 C-01 — Initialization Optimization
<!-- Fit latent representation to source/planner initialization. -->

### 4.4 C-02 — Adversarial Optimization
<!-- Generate collision-inducing surrounding traffic. -->

### 4.5 C-03 — Solution Optimization
<!-- Search for collision-free planner counterfactual. -->

### 4.6 D-02 — Generated Scenarios
<!-- Serialized JSON scenario artifacts and partitions. -->

### 4.7 M-03 — Scenario Clustering
<!-- K-means over collision geometry. -->

### 4.8 M-04 — Accident / Scenario Classifier
<!-- Cluster-based classification in public release; paper-level accident-mode classifier distinction. -->

### 4.9 F-01 — Planner Tuning
<!-- Released fitted rule-based planner configuration and paper tuning workflow. -->

---

## 5. Data Flow

### 5.1 Source-scene ingestion
<!-- nuScenes scene/sample/annotation/map loading. -->

### 5.2 Scene-graph construction
<!-- Agent states, masks, semantics, attributes, map crop. -->

### 5.3 Learned-prior embedding
<!-- M-01 prior/posterior representation. -->

### 5.4 Scenario generation
<!-- C-01 → C-02 → C-03. -->

### 5.5 Scenario serialization
<!-- D-02 JSON structure and result directories. -->

### 5.6 Downstream analysis
<!-- Evaluation, clustering, classification, planner tuning. -->

---

## 6. Inputs

### 6.1 nuScenes metadata
<!-- Required upstream metadata and map expansion. -->

### 6.2 Traffic-model checkpoint
<!-- M-01 checkpoint dependency. -->

### 6.3 Planner configuration
<!-- Replay or rule-based planner and config key. -->

### 6.4 Scenario-generation configuration
<!-- Split, feasibility, optimizer, loss, save/viz settings. -->

### 6.5 Optional downstream artifacts
<!-- cluster.pkl, cluster_labels.txt, tuned planner config. -->

---

## 7. Outputs

### 7.1 Traffic-model artifacts
<!-- M-01 checkpoint and evaluation outputs. -->

### 7.2 Generated scenario JSON
<!-- `adv_failed`, `sol_failed`, `adv_sol_success`. -->

### 7.3 Visualizations
<!-- Optimization and evaluation videos/images. -->

### 7.4 Evaluation reports
<!-- Scenario metrics, planner metrics, classification CSVs. -->

### 7.5 Clustering artifacts
<!-- cluster.pkl, cluster labels, distribution plots. -->

### 7.6 Fitted planner configurations
<!-- default and `final_tuned_val_1`. -->

---

## 8. End-to-End Scenario Generation

### 8.1 Candidate scene selection
<!-- Source split, windowing, category filtering. -->

### 8.2 Feasibility sampling/filtering
<!-- M-01 sampling and attack feasibility checks. -->

### 8.3 Initialization fitting
<!-- C-01 behavior. -->

### 8.4 Adversarial search
<!-- C-02 behavior. -->

### 8.5 Adversarial success check
<!-- Selected-attacker collision criterion. -->

### 8.6 Solution search
<!-- C-03 behavior. -->

### 8.7 Solution success check
<!-- Vehicle/environment collision-free criterion. -->

### 8.8 Result partitioning
<!-- adv_failed / sol_failed / adv_sol_success. -->

---

## 9. Traffic Model

### 9.1 Model family
<!-- Graph-conditioned CVAE / learned traffic prior. -->

### 9.2 State representation
<!-- x, y, heading vector, speed, heading-rate. -->

### 9.3 Latent representation
<!-- Default dimension and prior/posterior roles. -->

### 9.4 Map representation
<!-- Rasterized local map crop. -->

### 9.5 Interaction modeling
<!-- SceneInteractionNet / message passing. -->

### 9.6 Decoder / vehicle dynamics
<!-- Autoregressive decoder and bicycle-style dynamics. -->

---

## 10. Planner Integration

### 10.1 Replay planner
<!-- Ground-truth ego future. -->

### 10.2 Rule-based planner
<!-- `HardcodeNuscPlanner`. -->

### 10.3 Closed-loop adversarial interaction
<!-- Actual planner rerun during C-02. -->

### 10.4 Internal differentiable proxy
<!-- M-01 target-node prediction used for crash gradient where applicable. -->

### 10.5 Planner evaluation
<!-- Regular vs adversarial scenario evaluation. -->

---

## 11. Optimization Stack

### 11.1 Shared latent-space formulation
<!-- Optimize M-01 latent variables rather than raw trajectories. -->

### 11.2 C-01 objectives
<!-- Initial trajectory matching and release-specific loss behavior. -->

### 11.3 C-02 objectives
<!-- Crash, prior, collision, initialization regularization. -->

### 11.4 C-03 objectives
<!-- Planner collision avoidance and non-planner preservation. -->

### 11.5 Optimizers and stopping
<!-- Adam, fixed iteration budgets, learning rates. -->

### 11.6 Known release-specific objective discrepancies
<!-- TgtMatchingLoss motion-prior term behavior. -->

---

## 12. Evaluation

### 12.1 Traffic-model evaluation
<!-- ADE/FDE/angle/collision/prior-related metrics. -->

### 12.2 Adversarial-generation evaluation
<!-- Success rates, collisions, plausibility, planner matching. -->

### 12.3 Solution evaluation
<!-- Collision-free success and kinematic plausibility. -->

### 12.4 Scenario clustering/classification
<!-- Collision-mode distribution. -->

### 12.5 Planner evaluation
<!-- Collision rate, collision velocity, acceleration. -->

### 12.6 Paper-level tuning results
<!-- Table 3 and related improvement analysis. -->

---

## 13. Configuration

### 13.1 Data configuration
<!-- data_dir, version, split, categories, horizons. -->

### 13.2 M-01 training configuration
<!-- Epochs, lr, loss weights. -->

### 13.3 Adversarial-generation configuration
<!-- Feasibility, optimizer settings, C-01/C-02/C-03 loss weights. -->

### 13.4 Planner configuration
<!-- default and tuned values. -->

### 13.5 Evaluation configuration
<!-- Traffic, generated-scenario, planner evaluation. -->

---

## 14. Reproducibility

### 14.1 Public repository revision
<!-- Commit hash used for this documentation set. -->

### 14.2 Runtime environment
<!-- Ubuntu/Python/PyTorch/CUDA and dependency versions. -->

### 14.3 Required external data
<!-- nuScenes metadata/map expansion. -->

### 14.4 Required downloadable artifacts
<!-- Traffic-model checkpoint, generated scenarios, clustering artifact. -->

### 14.5 Randomness and nondeterminism
<!-- Sampling, validation split choices, GPU behavior, clustering. -->

### 14.6 Companion cards and metadata
<!-- Link all subordinate documentation artifacts. -->

---

## 15. Quantitative System Profile

### 15.1 Source-code inventory
<!-- Relevant source/config/artifact counts and hashes. -->

### 15.2 Component configuration summary
<!-- Consolidated defaults/release settings. -->

### 15.3 Dependency validation
<!-- Card/component relationships resolve correctly. -->

### 15.4 Public artifact availability
<!-- Checkpoints, scenarios, clustering labels/model. -->

### 15.5 Profiler
<!-- `tools/profile_strive_system.py` -->

---

## 16. Known Limitations

### 16.1 Simulation/log-replay limitations
<!-- Surrounding traffic behavior and reaction assumptions. -->

### 16.2 Learned-prior limitations
<!-- M-01 approximation/bias. -->

### 16.3 Planner limitations
<!-- Rule-based planner, lane-change constraints, replay planner. -->

### 16.4 Optimization limitations
<!-- Local non-convex search; no global guarantees. -->

### 16.5 Collision-model limitations
<!-- Differentiable vs final geometry checks. -->

### 16.6 Finite-horizon limitations
<!-- 6s default, 8s C-03 optimization horizon. -->

### 16.7 Dataset limitations
<!-- nuScenes geography/categories and selected generated scenarios. -->

### 16.8 Public-release gaps
<!-- Missing full tuning sweep, paper-level accident-mode classifier implementation, dependency pinning gaps. -->

---

## 17. Failure Modes

### 17.1 No feasible attacker
<!-- Scenario skipped before optimization. -->

### 17.2 Initialization fit failure
<!-- C-01 mismatch/instability. -->

### 17.3 Adversarial optimization failure
<!-- No selected-attacker collision. -->

### 17.4 Solution optimization failure
<!-- No returned collision-free counterfactual. -->

### 17.5 Planner/map failures
<!-- Invalid map association, planner collision, impossible log-replay cases. -->

### 17.6 Downstream artifact mismatch
<!-- cluster.pkl/labels mismatch, config/card drift. -->

---

## 18. Safety, Ethics & Interpretation

### 18.1 Intended safety use
<!-- Offline robustness analysis and planner improvement. -->

### 18.2 Synthetic scenario interpretation
<!-- Generated accidents are not observed crash probabilities. -->

### 18.3 Planner-failure interpretation
<!-- Failure is conditional on planner/model/system assumptions. -->

### 18.4 Counterfactual solution interpretation
<!-- C-03 solution does not prove real planner controllability. -->

### 18.5 Misuse boundaries
<!-- Avoid real-world harmful operationalization, legal/fault conclusions, unsupported certification. -->

### 18.6 Bias and representativeness
<!-- Inherited from nuScenes and generated-data selection. -->

---

## 19. Licensing & Distribution

### 19.1 Source-code license
<!-- MIT. -->

### 19.2 Model/scenario artifact license
<!-- CC-BY-NC-SA-4.0 statement from README. -->

### 19.3 Upstream dataset terms
<!-- nuScenes terms. -->

### 19.4 Redistribution considerations
<!-- Preserve provenance and applicable licenses. -->

---

## 20. Relationships

### 20.1 Card inventory

```text
S-01  STRIVE System Card
│
├── D-01  nuScenes Data Card
├── M-01  Main Traffic Model Card
├── C-01  Initialization Optimization Component Card
├── C-02  Adversarial Optimization Component Card
├── C-03  Solution Optimization Component Card
├── D-02  Generated Scenarios Data Card
├── M-03  Scenario Clustering Model Card
├── M-04  Accident / Scenario Classifier Model Card
└── F-01  Planner Tuning Fitted-Config Card
```

### 20.2 End-to-end dependency graph

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
  │
  ├──► M-03 ───► M-04 ───► F-01
  │
  └──► Planner Evaluation
```

---

## 21. References

<!-- STRIVE paper -->
<!-- STRIVE supplementary material -->
<!-- STRIVE GitHub repository -->
<!-- nuScenes -->
<!-- Data Cards Playbook -->
<!-- subordinate STRIVE cards -->

---

## 22. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial S-01 STRIVE system-card skeleton |
