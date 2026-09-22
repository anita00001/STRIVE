# F-01 — STRIVE Planner Tuning Fitted-Config Card

> **Card ID:** F-01  
> **Card type:** Fitted-Config Card  
> **Status:** Complete for the public STRIVE release  
> **Configuration:** STRIVE Rule-Based Planner Tuning  
> **Upstream:** M-04 — Accident Classifier / Accident-Mode Classifier  
> **Applies to:** STRIVE Rule-Based Planner  
> **Released tuned configuration:** `final_tuned_val_1`

---

## 1. Configuration Summary

### 1.1 Purpose

F-01 documents the fitted hyperparameters used to improve STRIVE's rule-based planner after evaluating it on regular and generated challenging scenarios.

The STRIVE paper uses generated accident-prone scenarios to "close the loop": planner failures are not only measured, but are used to identify and tune parameters that reduce collision failures. The paper also introduces a multi-mode planner that can switch between regular and accident-mode parameter sets.

### 1.2 Role in the STRIVE pipeline

```text
D-02 generated scenarios
  │
  ▼
M-03 collision clustering / analysis
  │
  ▼
M-04 accident-mode classification / failure analysis
  │
  ▼
F-01 planner hyperparameter tuning
  │
  ▼
improved rule-based planner evaluation
```

There are two distinct levels to keep separate:

1. **Public repository configuration:** the code exposes the default planner parameters and one named tuned parameter set, `final_tuned_val_1`.
2. **Paper tuning experiment:** the paper/supplement describes a larger 432-combination sweep, tuning on regular and generated collision scenarios, and a learned binary accident-mode classifier.

The public repository does not include the complete hyperparameter-sweep or learned accident-mode-classifier training implementation.

### 1.3 Configuration identity

Planner implementation:

```text
src/planners/hardcode_goalcond_nusc.py
```

Released configuration dictionary:

```python
CONFIG_DICT = {
    "default": DEF_CONFIG,
    "final_tuned_val_1": TUNED_VAL_FINAL_1
}
```

The tuned dictionary is documented in source as:

```text
large-scale tuned on generated scenarios from validation set
```

The public source does not explicitly state which individual Table 3 experimental row should be equated one-to-one with `final_tuned_val_1`; this card therefore reports the code artifact and the paper's tuning experiment separately rather than inferring that mapping.

### 1.4 Primary implementation

Planner:

```text
src/planners/hardcode_goalcond_nusc.py
```

Planner configuration wrapper:

```text
src/planners/planner.py::PlannerConfig
```

Scenario-generation selection of planner config:

```text
src/adv_scenario_gen.py
```

Planner evaluation:

```text
src/eval_planner.py
configs/eval_planner.cfg
```

---

## 2. Target Component

### 2.1 Planner

The fitted parameters apply to:

```text
HardcodeNuscPlanner
```

The planner is lane-graph-based and reactive. It:

- associates agents with lane-graph splines;
- predicts possible future motion for nearby non-ego agents;
- generates candidate ego speed profiles;
- estimates collision probability;
- chooses a low-collision candidate that otherwise makes progress.

### 2.2 Planner state and action interface

Input agent state follows:

```text
x, y, heading, speed, length, width
```

The planner ultimately returns a kinematic ego trajectory:

```text
x, y, heading_x, heading_y
```

at requested output timestamps.

### 2.3 Traffic inputs

At rollout time, non-ego trajectories are supplied externally.

For STRIVE adversarial generation, these are generated traffic trajectories from M-01/C-02.

For log-replay evaluation, surrounding traffic follows recorded trajectories.

### 2.4 Map dependency

The rule-based planner uses nuScenes lane graphs.

It matches vehicles to lane-graph edges using position and heading constraints and generates lane-following splines.

A known limitation is that the released planner cannot robustly change lanes; STRIVE-generated failures expose this limitation.

---

## 3. Motivation for Tuning

### 3.1 Tuning objective

The supplement states that each hyperparameter setting is ranked by:

1. **lowest collision rate**;
2. ties broken by **lowest acceleration**.

Thus collision avoidance is the primary tuning objective and driving comfort is the secondary criterion.

### 3.2 Evaluation criteria

Relevant reported metrics include:

- collision rate;
- relative velocity at collision;
- planner acceleration;
- regular-scenario performance;
- generated collision-scenario performance.

### 3.3 Relationship to generated scenarios

The paper first tunes on regular nuScenes driving and then generates challenging scenarios against planners with default and regular-tuned parameters.

Those challenging scenarios are then used to guide additional tuning.

The supplement states that `Behind` collision scenarios are removed when tuning on challenging scenarios because the authors considered many of them unrealistic or not meaningfully avoidable by the planner.

### 3.4 Relationship to M-04

The paper's multi-mode planner uses a **binary learned classifier** to choose between:

```text
regular mode
accident-prone mode
```

based on a moving 2-second traffic-history window.

The supplement describes this classifier as a neural network similar to the traffic-model encoder, using:

- past 2-second trajectories of all agents;
- local map crops;
- scene-graph message passing;
- a 64-dimensional ego feature;
- a 2-layer MLP binary classifier.

It is trained with weighted binary cross-entropy on:

- regular nuScenes training scenarios; and
- a diverse set of over 1,000 generated collision scenarios from train/validation scenes using Replay and Rule-based planner variants.

This paper-level accident-mode classifier is not implemented in the inspected public repository. Therefore F-01 can document its role, but the released code only exposes single-mode planner configurations.

---

## 4. Tuned Parameters

### 4.1 Planning timestep — `dt`

Default:

```text
0.2 s
```

Released tuned value:

```text
0.2 s
```

Unchanged.

### 4.2 Prediction timestep — `preddt`

Default:

```text
0.2 s
```

Released tuned value:

```text
0.2 s
```

Unchanged.

### 4.3 Planning horizon — `nsteps`

Default/tuned:

```text
25
```

With `preddt = 0.2 s`:

```text
prediction horizon = 5.0 s
```

### 4.4 Lane-match thresholds

`cdistang`:

```text
20 degrees
```

`xydistmax`:

```text
2.0 m
```

Both are unchanged in the released tuned configuration.

### 4.5 Maximum speed — `smax`

Default:

```text
15.0 m/s
```

Released tuned:

```text
20.0 m/s
```

Change:

```text
+5.0 m/s
+33.3%
```

### 4.6 Maximum acceleration — `accmax`

Default:

```text
3.0 m/s²
```

Released tuned:

```text
4.0 m/s²
```

Change:

```text
+1.0 m/s²
+33.3%
```

### 4.7 Other-agent prediction speed factors — `predsfacs`

Default/tuned:

```text
[0.5, 1.0]
```

The planner predicts nearby traffic using target speeds scaled from current speed.

### 4.8 Other-agent prediction acceleration factors — `predafacs`

Default/tuned:

```text
[0.5]
```

The factor is multiplied by `accmax` when forming other-agent speed-profile predictions.

### 4.9 Interaction distance — `interacdist`

Default/tuned:

```text
70.0 m
```

Agents farther than this are excluded from the planner's interaction prediction.

### 4.10 Planner acceleration factors — `planaccfacs`

Default/tuned:

```text
[1.0]
```

### 4.11 Candidate speed count — `plannspeeds`

Default/tuned:

```text
5
```

`gen_sprofiles()` chooses five intermediate target speeds and five second-stage target speeds for each acceleration factor, yielding up to:

```text
5 × 5 = 25
```

two-stage speed profiles per applicable lane spline / acceleration factor.

### 4.12 Maximum accepted collision probability — `col_plim`

Default/tuned:

```text
0.1
```

This is the threshold used to decide whether a candidate trajectory has sufficiently low estimated collision probability.

The supplement refers to this tuning dimension as `p_max` and states that tuning searches:

```text
[0.05, 0.2]
```

as its overall range.

### 4.13 Collision-score minimum weight — `score_wmin`

Default:

```text
0.7
```

Released tuned:

```text
0.3
```

Change:

```text
-0.4
```

### 4.14 Collision-score time factor — `score_wfac`

Default:

```text
0.05
```

Released tuned:

```text
0.02
```

Change:

```text
-0.03
```

The planner forms time-dependent weights as:

```text
w[t] = score_wmin + t × score_wfac
```

and converts estimated separation distances into collision-like scores using:

```text
1 + tanh(-distance × w[t])
```

with overlapping boxes assigned probability 1.

---

## 5. Baseline Configuration

### 5.1 Default parameter set

The public source defines:

```yaml
dt: 0.2
preddt: 0.2
nsteps: 25
cdistang: 20.0
xydistmax: 2.0
smax: 15.0
accmax: 3.0
predsfacs: [0.5, 1.0]
predafacs: [0.5]
interacdist: 70.0
planaccfacs: [1.0]
plannspeeds: 5
col_plim: 0.1
score_wmin: 0.7
score_wfac: 0.05
```

### 5.2 Baseline provenance

Source:

```text
src/planners/hardcode_goalcond_nusc.py::DEF_CONFIG
```

The supplement states that these initial default parameters were set by observing planner rollouts on a small nuScenes subset rather than by large-scale tuning.

### 5.3 Baseline use in scenario generation

The released:

```text
configs/adv_gen_rule_based.cfg
```

uses:

```yaml
planner_cfg: default
```

and comments that:

```text
final_tuned_val_1
```

can be used after hyperparameter tuning.

Therefore the repository's default adversarial-generation config reproduces the original default-planner attack setting rather than automatically selecting the tuned config.

---

## 6. Tuned Configuration

### 6.1 Released tuned parameter set

The public source defines:

```yaml
dt: 0.2
preddt: 0.2
nsteps: 25
cdistang: 20.0
xydistmax: 2.0
smax: 20.0
accmax: 4.0
predsfacs: [0.5, 1.0]
predafacs: [0.5]
interacdist: 70.0
planaccfacs: [1.0]
plannspeeds: 5
col_plim: 0.1
score_wmin: 0.3
score_wfac: 0.02
```

### 6.2 Configuration name

Canonical released key:

```text
final_tuned_val_1
```

Python symbol:

```text
TUNED_VAL_FINAL_1
```

### 6.3 Source location

```text
src/planners/hardcode_goalcond_nusc.py
```

### 6.4 Differences from default

| Parameter | Default | `final_tuned_val_1` | Change |
|---|---:|---:|---:|
| `smax` | 15.0 | 20.0 | +5.0 |
| `accmax` | 3.0 | 4.0 | +1.0 |
| `score_wmin` | 0.7 | 0.3 | -0.4 |
| `score_wfac` | 0.05 | 0.02 | -0.03 |

All other released dictionary entries are unchanged.

### 6.5 Interpretation caution

The source comment describes `TUNED_VAL_FINAL_1` as:

```text
large-scale tuned on generated scenarios from validation set
```

The paper contains several tuning stages and parameter sets:

- regular-tuned;
- regular + challenging-data tuned;
- extra learned accident mode;
- extra oracle accident mode.

The public source does not explicitly annotate `TUNED_VAL_FINAL_1` with a specific Table 3 row, so this card does not infer an exact one-to-one mapping.

---

## 7. Tuning Data

### 7.1 Initial regular tuning set

The supplement states that initial large-scale planner tuning uses:

```text
800
```

regular:

```text
8-second nuScenes scenarios
```

from train/validation splits.

This produces the initial optimal hyperparameters for regular driving.

### 7.2 Generated challenging scenarios

STRIVE adversarial optimization is then run against planners with:

- default parameters; and
- regular-tuned parameters.

The resulting generated collision scenarios guide further planner improvements.

### 7.3 Challenging-scenario filtering

When tuning on challenging scenarios, the supplement states that:

```text
Behind
```

collisions are removed because the authors found these often reflected unrealistic or effectively unavoidable rear impacts rather than useful planner weaknesses.

### 7.4 Held-out evaluation

Table 3 results are reported on scenarios from the held-out nuScenes test set.

For collision-scenario metrics, scenarios where **every** evaluated hyperparameter setting collides are treated as impossible and discarded from the Coll evaluation subset.

### 7.5 Scenario classes

Collision labels help diagnose failure modes and determine which scenarios are useful for planner improvement.

The paper additionally uses a learned binary accident-mode classifier for multi-mode operation, but the exact classifier implementation and training scripts are not present in the public repository.

---

## 8. Tuning Procedure

### 8.1 Search method

The supplement describes an exhaustive hyperparameter sweep:

```text
432 hyperparameter combinations
```

No corresponding public sweep script was identified in the inspected STRIVE repository.

### 8.2 Search space

The supplement explicitly states tuning over:

```text
p_max:       0.05 to 0.2
max speed:   12.5 to 20.0 m/s
max accel:   3.0 to 4.5 m/s²
```

plus parameters controlling:

```text
p_col(trajectory)
```

The repository implementation shows that collision-scoring behavior is parameterized by:

```text
col_plim
score_wmin
score_wfac
```

The supplement text inspected for this card gives the overall ranges above and the total combination count, but not the complete discrete grid values for every dimension.

### 8.3 Objective function

Selection rule:

```text
minimize collision rate
```

Tie-breaker:

```text
minimize acceleration
```

### 8.4 Trial evaluation

Each candidate parameter set is rolled out over the selected scenario collection and evaluated using planner metrics such as:

- collision occurrence;
- relative collision velocity;
- acceleration.

### 8.5 Selection sequence

Paper procedure:

```text
default manually set config
        │
        ▼
tune on 800 regular scenarios
        │
        ▼
regular-tuned planner
        │
        ├── generate challenging scenarios
        │
        ▼
tune using challenging data
        │
        ▼
analyze single-mode tradeoff
        │
        ▼
introduce regular + accident-mode parameter sets
```

### 8.6 Randomness

The public planner itself is predominantly deterministic for fixed trajectories/configuration.

Reproducibility of the overall tuning experiment still depends on:

- exact scenario list;
- source split selection;
- generated D-02 scenarios;
- filtering of impossible/Behind cases;
- code revision;
- numeric environment.

---

## 9. Evaluation Procedure

### 9.1 Planner evaluation script

Public evaluation:

```text
src/eval_planner.py
```

Default config:

```text
configs/eval_planner.cfg
```

### 9.2 Generated challenging scenarios

The default evaluation config points to:

```text
./out/adv_gen_rule_based_out/scenario_results/adv_sol_success
```

for adversarial scenarios.

### 9.3 Regular scenarios

By default:

```yaml
skip_regular: false
filter_regular: true
```

The evaluator therefore also evaluates matched regular nuScenes scenarios corresponding to the generated accident scenarios.

The config notes that split and sequence interval must agree with scenario generation for matching to work as intended.

### 9.4 Collision metrics

Planner evaluation computes:

- collision occurrence;
- relative collision speed.

Collision trajectories are temporally interpolated by a factor of 3 for metric calculation.

### 9.5 Comfort metrics

Planner evaluation reports:

- mean acceleration magnitude;
- forward acceleration;
- lateral acceleration.

The paper's rule-based-planner table emphasizes forward acceleration because the released planner cannot change lanes.

### 9.6 Aggregate metrics

The README states that planner evaluation reports metrics for:

```text
regular
adversarial
total
```

and writes per-scenario CSV output.

---

## 10. Quantitative Results

### 10.1 Paper Table 3

Held-out evaluation reported in the paper:

| Improvement | Collision % Reg / Coll | Collision velocity m/s Reg / Coll | Acceleration m/s² Reg / Coll |
|---|---:|---:|---:|
| None (regular-tuned) | 4.6 / 68.6 | 4.59 / 10.48 | 1.96 / 2.26 |
| + Challenging data | 6.0 / 51.4 | 5.48 / 13.88 | 2.29 / 2.50 |
| + Extra learned mode | 4.6 / 54.3 | 4.60 / 10.86 | 2.02 / 2.55 |
| + Extra oracle mode | 4.6 / 54.3 | 4.59 / 10.40 | 1.96 / 2.39 |

These are experimental results from the paper, not measurements produced by the repository profiler.

### 10.2 Regular-tuned baseline

The regular-tuned planner has:

```text
4.6% collision rate on regular scenarios
68.6% on the selected challenging collision scenarios
```

The supplement notes that a per-scenario oracle over all tested hyperparameter sets can only reduce the regular collision rate to:

```text
3.2%
```

because log replay creates some unavoidable failures.

### 10.3 Tuning on challenging data

Adding challenging scenarios to a single-mode tuning set reduces challenging collision rate:

```text
68.6% → 51.4%
```

but increases regular collision rate:

```text
4.6% → 6.0%
```

and produces more aggressive velocity/acceleration behavior.

This is the tradeoff that motivates multi-mode operation.

### 10.4 Learned accident mode

With a learned accident-mode classifier, the reported challenging collision rate is:

```text
54.3%
```

while regular collision performance stays:

```text
4.6%
```

Compared with the regular-tuned baseline, this is a:

```text
14.3 percentage-point
```

reduction in challenging collision rate without increasing the reported regular collision rate.

### 10.5 Oracle mode

The oracle accident-mode version also reports:

```text
54.3%
```

challenging collision rate, with somewhat lower collision velocity/acceleration than the learned version.

### 10.6 Profiler

Run:

```bash
python tools/profile_planner_tuning.py \
  --repo-root . \
  --output ./out/planner_tuning_profile.yaml
```

or merge into metadata:

```bash
python tools/profile_planner_tuning.py \
  --repo-root . \
  --metadata ./metadata/fitted_configs/planner_tuning.yaml
```

The profiler statically extracts the released dictionaries and verifies the exact default-to-tuned delta.

---

## 11. Configuration Schema

### 11.1 Canonical parameters

```text
dt
preddt
nsteps
cdistang
xydistmax
smax
accmax
predsfacs
predafacs
interacdist
planaccfacs
plannspeeds
col_plim
score_wmin
score_wfac
```

### 11.2 Types

| Parameter | Type |
|---|---|
| `dt` | float |
| `preddt` | float |
| `nsteps` | int |
| `cdistang` | float |
| `xydistmax` | float |
| `smax` | float |
| `accmax` | float |
| `predsfacs` | list[float] |
| `predafacs` | list[float] |
| `interacdist` | float |
| `planaccfacs` | list[float] |
| `plannspeeds` | int |
| `col_plim` | float |
| `score_wmin` | float |
| `score_wfac` | float |

### 11.3 Units

| Parameter | Unit / interpretation |
|---|---|
| `dt` | seconds |
| `preddt` | seconds |
| `nsteps` | prediction steps |
| `cdistang` | degrees |
| `xydistmax` | meters |
| `smax` | meters/second |
| `accmax` | meters/second² |
| `interacdist` | meters |
| `col_plim` | dimensionless probability-like threshold |
| `score_wmin` | distance-score scale |
| `score_wfac` | per-prediction-step score-weight increment |

### 11.4 Runtime assertions / effective constraints

Examples in planner code include:

```text
smax > 0
```

and positive timestep/horizon values are operationally required.

The code does not centrally enforce a complete formal parameter schema.

### 11.5 Coupled parameters

Important couplings include:

```text
prediction horizon = nsteps × preddt
```

and:

```text
other-agent acceleration hypothesis =
    accmax × predafac
```

while collision scoring jointly depends on:

```text
col_plim
score_wmin
score_wfac
```

---

## 12. Validation

### 12.1 Configuration completeness

Validate that both:

```text
DEF_CONFIG
TUNED_VAL_FINAL_1
```

contain the same key set.

### 12.2 Type/range validation

At minimum check:

- `dt > 0`;
- `preddt > 0`;
- `nsteps > 0`;
- `smax > 0`;
- `accmax > 0`;
- `plannspeeds > 0`;
- non-empty factor lists;
- `0 <= col_plim <= 1`.

### 12.3 Source consistency

`CONFIG_DICT` should map:

```text
default → DEF_CONFIG
final_tuned_val_1 → TUNED_VAL_FINAL_1
```

### 12.4 Evaluation-config consistency

The released `configs/eval_planner.cfg` reproduces the default `DEF_CONFIG`, not the tuned values.

To evaluate `final_tuned_val_1` with `eval_planner.py`, the corresponding command/config parameters must be changed to the tuned values.

### 12.5 Regression check

Recommended local evaluation compares:

```text
default
final_tuned_val_1
```

on exactly the same:

- regular scenarios;
- D-02 scenarios;
- planner-evaluation settings.

---

## 13. Sensitivity & Robustness

### 13.1 Parameter sensitivity

The released tuned artifact changes only four of fifteen configuration entries:

```text
smax
accmax
score_wmin
score_wfac
```

These affect:

- aggressiveness/speed envelope;
- acceleration envelope;
- time-dependent collision scoring.

### 13.2 Scenario sensitivity

Paper results show a strong tradeoff between regular and challenging scenarios when a single parameter set is used.

This is why the authors introduce an accident-specific operating mode.

### 13.3 Collision-class sensitivity

Generated scenario analysis exposes particularly difficult classes, including:

```text
Head On
Behind
Front from Right
```

Many such failures are linked to the structural inability to change lanes and cannot be solved by parameter tuning alone.

### 13.4 Distribution shift

A parameter set tuned on STRIVE/nuScenes log-replay scenarios is not guaranteed to generalize to:

- different cities;
- different map graph quality;
- different agent behavior;
- closed-loop reactive traffic;
- production perception/control stacks.

---

## 14. Limitations

### 14.1 Tuning-set overfitting

A fitted config can over-specialize to the selected regular/generated scenarios.

Held-out evaluation is required.

### 14.2 Missing public sweep implementation

The supplement documents the 432-combination search, but the inspected public repository does not expose the full tuning/sweep implementation.

Therefore exact reconstruction of:

- every discrete grid value;
- trial ordering;
- intermediate metrics;
- selected parameter set at each paper stage

requires more than the released code alone.

### 14.3 Metric tradeoffs

Naively tuning on challenging data improves collision rate on challenging scenarios but worsens regular driving and increases aggressive behavior.

### 14.4 Planner structural limitation

Hyperparameters cannot solve all planner failures.

The lane-following planner's inability to change lanes creates failure modes where every tested parameter setting collides.

### 14.5 Log-replay limitation

Regular traffic is pre-recorded and does not react to planner changes.

This creates some unavoidable collisions and limits interpretation of the measured collision rate.

### 14.6 Multi-mode implementation availability

The paper's learned binary accident-mode classifier and full multi-mode runtime are described in the supplement but are not present in the inspected public repository.

---

## 15. Safety & Interpretation

### 15.1 Meaning of improved metrics

Lower collision rate in STRIVE evaluation means better performance under the documented simulated/log-replay conditions.

It is not real-world safety certification.

### 15.2 Tuning vs validation separation

Parameter selection and final evaluation should use separate scenario sets.

The paper reports final Table 3 evaluation on a held-out nuScenes test set.

### 15.3 Generated-scenario interpretation

Challenging data is synthetic and optimization-generated.

Improvements measured on this data remain conditional on:

- M-01;
- C-02;
- C-03;
- D-02 selection;
- planner assumptions.

### 15.4 Deployment boundary

`final_tuned_val_1` is a research configuration for the STRIVE rule-based planner, not a production AV calibration.

---

## 16. Reproducibility

### 16.1 Source files

```text
src/planners/hardcode_goalcond_nusc.py
src/planners/planner.py
src/adv_scenario_gen.py
src/eval_planner.py
```

### 16.2 Config files

```text
configs/adv_gen_rule_based.cfg
configs/eval_planner.cfg
```

### 16.3 Paper/supplement facts needed for full tuning reproduction

Record:

```text
432 combinations
800 initial regular 8-second scenarios
lowest collision rate selection
lowest acceleration tie-break
challenging generated data
Behind-collision exclusion during challenging tuning
held-out nuScenes test evaluation
```

### 16.4 Fitted artifact

The released fitted configuration is a Python dictionary embedded in source:

```text
TUNED_VAL_FINAL_1
```

and exposed through:

```text
CONFIG_DICT["final_tuned_val_1"]
```

It is not a separate binary checkpoint.

### 16.5 Companion metadata

```text
metadata/fitted_configs/planner_tuning.yaml
```

### 16.6 Quantitative profiler

```text
tools/profile_planner_tuning.py
```

The profiler reports:

- source hashes;
- extracted default dictionary;
- extracted tuned dictionary;
- changed/unchanged parameters;
- horizon and speed-profile derivations;
- whether eval config matches defaults;
- whether adversarial config exposes the tuned config comment/key;
- static indicators for whether a public dedicated tuning sweep implementation is present.

---

## 17. Relationships

### 17.1 Upstream

Paper-level improvement path:

```text
D-02 — Generated Scenarios
  │
  ▼
M-03 — Collision Clustering / Failure Analysis
  │
  ▼
M-04 — Learned Accident-Mode Classifier
```

The public repository contains D-02/M-03 classification analysis but does not release the learned accident-mode classifier described in the supplement.

### 17.2 Applied component

```text
STRIVE Rule-Based Planner
```

### 17.3 Dependency chain

```text
D-02  Generated Scenarios
  │
  ▼
M-03  Scenario Clustering
  │
  ▼
M-04  Accident-Mode Classifier
  │
  ▼
F-01  Planner Tuning / Multi-Mode Improvement
```

---

## 18. Terms of Art

### 18.1 Default configuration

`DEF_CONFIG`: manually set planner parameters used before large-scale tuning.

### 18.2 Regular-tuned configuration

The parameter set selected by tuning on 800 regular 8-second nuScenes scenarios in the paper experiment.

The public repository does not separately name this artifact in `CONFIG_DICT`.

### 18.3 Released tuned configuration

`TUNED_VAL_FINAL_1`, exposed as:

```text
final_tuned_val_1
```

in the repository.

### 18.4 Challenging-data tuning

Planner tuning that incorporates generated collision scenarios in addition to regular scenarios.

### 18.5 Accident mode

A second planner-parameter mode used in the paper for accident-prone situations.

### 18.6 Learned accident-mode classifier

The paper-level binary network that switches between regular and accident modes based on the previous 2 seconds of traffic/map context.

### 18.7 Fitted configuration

A parameter artifact selected empirically through scenario evaluation rather than learned through gradient-based model training.

---

## 19. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.

2. STRIVE paper supplementary material, especially:
   - Appendix A.7 — rule-based planner details;
   - Appendix B.5 — improving the rule-based planner.

3. STRIVE public repository:
   - `src/planners/hardcode_goalcond_nusc.py`
   - `src/planners/planner.py`
   - `src/adv_scenario_gen.py`
   - `src/eval_planner.py`
   - `configs/eval_planner.cfg`
   - `configs/adv_gen_rule_based.cfg`

4. D-02 — Generated Scenarios Data Card.

5. M-03 — Scenario Clustering Model Card.

6. M-04 — Accident Classifier Model Card.

---

## 20. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed F-01 with exact released default/tuned dictionaries, 432-combination paper tuning procedure, held-out results, and public-release reproducibility gaps. |
