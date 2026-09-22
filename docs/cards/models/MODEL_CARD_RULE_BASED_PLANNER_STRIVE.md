# M-02 — STRIVE Rule-Based Planner Model Card

> **Card ID:** M-02  
> **Card type:** Model Card  
> **Status:** Skeleton  
> **Model:** STRIVE Rule-Based Planner (`HardcodeNuscPlanner`)  
> **Upstream:** D-01 — nuScenes Data, D-02 — Generated Scenarios  
> **Downstream:** C-02 — Adversarial Optimization, Planner Evaluation, F-01 — Planner Tuning

---

## 1. Model Details

### 1.1 Model summary
<!-- What is `HardcodeNuscPlanner`, and what role does it play in STRIVE? -->

### 1.2 Model type
<!-- Rule-based / lane-graph / trajectory-selection planner. -->

### 1.3 Primary implementation
<!-- `src/planners/hardcode_goalcond_nusc.py`. -->

### 1.4 Configuration interface
<!-- `PlannerConfig`, `DEF_CONFIG`, `TUNED_VAL_FINAL_1`, `CONFIG_DICT`. -->

### 1.5 Authors, release, and license
<!-- STRIVE authors, CVPR 2022, MIT source license. -->

---

## 2. Purpose & Role in STRIVE

### 2.1 Primary purpose
<!-- Produce an ego/planner trajectory conditioned on surrounding-agent motion and map context. -->

### 2.2 Role in adversarial scenario generation
<!-- C-02 attacks the planner while repeatedly rerunning it on generated traffic. -->

### 2.3 Role in planner evaluation
<!-- `src/eval_planner.py`. -->

### 2.4 Role in planner tuning
<!-- F-01 default/tuned configurations. -->

### 2.5 Relationship to replay planner
<!-- Distinguish `hardcode` planner from `ego`/replay planner. -->

---

## 3. Intended Use

### 3.1 Intended uses
<!-- STRIVE research, planner robustness, generated-scenario evaluation. -->

### 3.2 Intended users
<!-- Researchers evaluating planner behavior in nuScenes-derived scenarios. -->

### 3.3 Out-of-scope uses
<!-- Production AV control, deployment, safety certification. -->

---

## 4. Inputs

### 4.1 Initial planner state
<!-- x, y, heading, speed, dimensions. -->

### 4.2 Surrounding-agent trajectories
<!-- Non-ego future trajectories supplied to rollout. -->

### 4.3 Agent attributes
<!-- length, width. -->

### 4.4 Map environment
<!-- nuScenes lane graph and map index. -->

### 4.5 Planner timestamps
<!-- Requested planner output times and agent-observation times. -->

### 4.6 Batch metadata
<!-- Batch mask / agent pointers / map indices. -->

---

## 5. Outputs

### 5.1 Planner future trajectory
<!-- `[B, T, 4]`: x, y, heading_x, heading_y. -->

### 5.2 Internal world state
<!-- Ego and surrounding-agent state representation. -->

### 5.3 Control update
<!-- Selected next x/y/heading state. -->

### 5.4 Visualization outputs
<!-- Optional planner rollout visualization/video. -->

---

## 6. World-State Representation

### 6.1 Agent representation
<!-- x, y, heading, speed, length, width. -->

### 6.2 Ego identity
<!-- Planner-controlled vehicle index and `ego` key. -->

### 6.3 Surrounding-agent representation
<!-- Interpolated external trajectories. -->

### 6.4 Time update
<!-- `update_wstate`. -->

---

## 7. Map & Lane Processing

### 7.1 Lane graph
<!-- `map_env.lane_graphs`. -->

### 7.2 Lane-match filtering
<!-- Heading and positional thresholds. -->

### 7.3 Connected-lane clustering
<!-- `cluster_matches_combine` and BFS. -->

### 7.4 Local spline construction
<!-- Forward/backward lane expansion and ego-aligned splines. -->

### 7.5 Constant-heading fallback
<!-- Behavior when no lane match is available. -->

---

## 8. Surrounding-Agent Prediction

### 8.1 Interaction radius
<!-- `interacdist`. -->

### 8.2 Speed hypotheses
<!-- `predsfacs`. -->

### 8.3 Acceleration hypotheses
<!-- `predafacs`. -->

### 8.4 Prediction horizon
<!-- `nsteps × preddt`. -->

### 8.5 Predicted trajectory construction
<!-- Lane splines + speed profiles. -->

---

## 9. Ego Candidate Generation

### 9.1 Candidate speed profiles
<!-- `gen_sprofiles`. -->

### 9.2 Two-stage speed targets
<!-- `s1` and `s2`. -->

### 9.3 Acceleration factors
<!-- `planaccfacs`. -->

### 9.4 Candidate speed count
<!-- `plannspeeds`; candidate-grid size. -->

### 9.5 Speed and acceleration constraints
<!-- `smax`, `accmax`. -->

---

## 10. Collision Scoring

### 10.1 Vehicle approximation
<!-- Bounding boxes / circle approximation used in planner scoring. -->

### 10.2 Distance computation
<!-- Approximate bounding-box separation. -->

### 10.3 Time-dependent score weights
<!-- `score_wmin`, `score_wfac`. -->

### 10.4 Collision-probability-like score
<!-- `1 + tanh(-distance * weight)`. -->

### 10.5 Candidate acceptance threshold
<!-- `col_plim`. -->

---

## 11. Action Selection

### 11.1 Valid candidate set
<!-- Candidate trajectories below `col_plim`. -->

### 11.2 Progress preference
<!-- Select longest-distance candidate when valid. -->

### 11.3 Stop preference
<!-- Behavior when no lane match exists. -->

### 11.4 Fallback behavior
<!-- Minimum-score candidate when none meet threshold. -->

### 11.5 First-step control
<!-- Convert selected profile to next ego state. -->

---

## 12. Rollout Procedure

### 12.1 Reset
<!-- Initialize planner world state. -->

### 12.2 Per-step planning
<!-- Recompute splines, predictions, candidates, score, action. -->

### 12.3 Surrounding-agent update
<!-- Follow supplied external trajectories. -->

### 12.4 Output interpolation
<!-- Interpolate internal planner-rate rollout to requested timestamps. -->

### 12.5 Batched rollout
<!-- Multi-scene batching behavior. -->

---

## 13. Configuration

### 13.1 Default configuration
<!-- `DEF_CONFIG`. -->

### 13.2 Released tuned configuration
<!-- `TUNED_VAL_FINAL_1`. -->

### 13.3 Configuration dictionary
<!-- `CONFIG_DICT`. -->

### 13.4 Scenario-generation selection
<!-- `planner_cfg` in `adv_scenario_gen.py`. -->

### 13.5 Evaluation configuration
<!-- `planner_*` arguments in `eval_planner.py`. -->

---

## 14. Evaluation

### 14.1 Evaluation script
<!-- `src/eval_planner.py`. -->

### 14.2 Regular scenarios
<!-- nuScenes/source initialization scenarios. -->

### 14.3 Adversarial scenarios
<!-- D-02 generated scenarios. -->

### 14.4 Collision rate
<!-- Planner collision frequency. -->

### 14.5 Collision velocity
<!-- Relative speed at collision. -->

### 14.6 Comfort metrics
<!-- Mean, forward, lateral acceleration. -->

### 14.7 Per-scenario reporting
<!-- CSV outputs. -->

---

## 15. Quantitative Analysis

### 15.1 Planning horizon
<!-- Derive from nsteps/preddt. -->

### 15.2 Candidate-count analysis
<!-- Number of ego speed profiles per lane/acceleration factor. -->

### 15.3 Interaction-distance statistics
<!-- `interacdist`. -->

### 15.4 Default vs tuned configuration delta
<!-- Parameters changed in F-01. -->

### 15.5 Profiler
<!-- `tools/profile_rule_based_planner.py`. -->

---

## 16. Factors

### 16.1 Map quality
<!-- Dependence on lane graph quality. -->

### 16.2 Surrounding-trajectory quality
<!-- Planner reacts to externally provided future trajectories. -->

### 16.3 Initial-state dependence
<!-- Starting position/heading/speed. -->

### 16.4 Configuration dependence
<!-- Default vs tuned behavior. -->

### 16.5 Agent-density dependence
<!-- Candidate scoring complexity / interactions. -->

---

## 17. Limitations

### 17.1 Lane-following bias
<!-- Planner primarily follows lane splines. -->

### 17.2 Lane-change limitation
<!-- Known structural limitation. -->

### 17.3 Fixed surrounding-agent futures
<!-- No fully interactive traffic response in rollout. -->

### 17.4 Heuristic collision scoring
<!-- Approximate score rather than calibrated probability. -->

### 17.5 Finite planning horizon
<!-- Limited lookahead. -->

### 17.6 Research-only implementation
<!-- Not production planner software. -->

---

## 18. Safety & Interpretation

### 18.1 Research planner status
<!-- Stress-test target, not production controller. -->

### 18.2 Collision metric interpretation
<!-- Simulation/log-replay collision only. -->

### 18.3 Tuned configuration interpretation
<!-- Research parameter selection, not production calibration. -->

### 18.4 Failure interpretation
<!-- Planner failure is conditional on STRIVE environment and assumptions. -->

---

## 19. Reproducibility

### 19.1 Source files
<!-- planner implementation and supporting utilities. -->

### 19.2 Required map/data inputs
<!-- nuScenes maps + D-01/D-02 inputs. -->

### 19.3 Configuration provenance
<!-- default/tuned config and calling script. -->

### 19.4 Companion metadata
<!-- `metadata/models/rule_based_planner.yaml`. -->

### 19.5 Quantitative profiler
<!-- `tools/profile_rule_based_planner.py`. -->

### 19.6 Runtime dependencies
<!-- NumPy, SciPy, Torch, matplotlib, STRIVE revision. -->

---

## 20. Relationships

### 20.1 Upstream

```text
D-01 — nuScenes Data
D-02 — Generated Scenarios
```

### 20.2 Downstream

```text
C-02 — Adversarial Optimization
Planner Evaluation
F-01 — Planner Tuning
```

### 20.3 System position

```text
D-01 / D-02
    │
    ▼
M-02  Rule-Based Planner
    │
    ├──► C-02 Adversarial Optimization
    ├──► Planner Evaluation
    └──► F-01 Planner Tuning
```

---

## 21. Terms of Art

### 21.1 Lane match
<!-- Candidate lane-graph edge compatible with ego position/heading. -->

### 21.2 Prediction spline
<!-- Lane-aligned path used for ego/other-agent prediction. -->

### 21.3 Speed profile
<!-- Candidate longitudinal speed plan over the planning horizon. -->

### 21.4 Collision score
<!-- Planner's heuristic collision-probability-like value. -->

### 21.5 Default configuration
<!-- `DEF_CONFIG`. -->

### 21.6 Tuned configuration
<!-- `TUNED_VAL_FINAL_1`. -->

---

## 22. References

<!-- STRIVE paper -->
<!-- STRIVE supplementary material -->
<!-- STRIVE GitHub repository -->
<!-- `src/planners/hardcode_goalcond_nusc.py` -->
<!-- `src/planners/planner.py` -->
<!-- `src/adv_scenario_gen.py` -->
<!-- `src/eval_planner.py` -->
<!-- `configs/eval_planner.cfg` -->
<!-- `configs/adv_gen_rule_based.cfg` -->
<!-- D-01, D-02, C-02, F-01 cards -->

---

## 23. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial M-02 rule-based planner model-card skeleton |
