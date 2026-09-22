# STRIVE Documentation Registry

## Scope

This documentation covers learned, fitted, and optimization-based
artifacts described in the original STRIVE CVPR 2022 paper and
its supplementary material.

## Data Products

### D-01 — STRIVE nuScenes-Derived Dataset
Card:
data/DATA_CARD_NUSCENES_STRIVE.md

### D-02 — STRIVE Generated Scenario Dataset
Card:
data/DATA_CARD_GENERATED_SCENARIOS.md

## Learned Models

### M-01 — STRIVE Traffic Model: Car/Truck
Status: Public implementation available
Checkpoint: Released
Primary sources:
- Paper Section 3.1
- Appendix A.1
- src/models/traffic_model.py
- src/models/interaction_net.py

Card:
models/MODEL_CARD_TRAFFIC_MODEL_CAR_TRUCK.md


### M-02 — STRIVE Traffic Model: All Categories
Status: Public implementation/configuration available
Checkpoint: Released
Primary sources:
- Appendix C.7
- configs/train_traffic_all_cats.cfg

Card:
models/MODEL_CARD_TRAFFIC_MODEL_ALL_CATEGORIES.md


### M-03 — Collision-Type Clustering Model
Type: K-means
k: 10
Status: Public implementation and fitted cluster object available
Primary sources:
- Section 4.1
- Appendix B.4
- src/cluster_scenarios.py
- data/clustering/cluster.pkl

Card:
models/MODEL_CARD_COLLISION_CLUSTERING.md


### M-04 — Accident-Mode Classifier
Type: Binary neural classifier
Status: Paper-described; public implementation/checkpoint not located
Primary sources:
- Section 5.3
- Appendix B.5

Card:
models/MODEL_CARD_ACCIDENT_MODE_CLASSIFIER.md


## Fitted Configurations

### F-01 — Rule-Based Planner Hyperparameter Configuration
Method: Grid search
Search space: 432 configurations
Status: Tuned configuration present in source

Card:
fitted_configs/FITTED_CONFIG_RULE_BASED_PLANNER.md


## Optimization Components

### C-01 — Initialization Optimization
Card:
components/COMPONENT_CARD_INITIALIZATION_OPTIMIZATION.md

### C-02 — Adversarial Optimization
Card:
components/COMPONENT_CARD_ADVERSARIAL_OPTIMIZATION.md

### C-03 — Solution Optimization
Card:
components/COMPONENT_CARD_SOLUTION_OPTIMIZATION.md


