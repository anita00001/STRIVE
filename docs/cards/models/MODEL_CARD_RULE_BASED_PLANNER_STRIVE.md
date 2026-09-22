# M-02 — STRIVE Rule-Based Planner Model Card

> **Card ID:** M-02  
> **Card type:** Model Card  
> **Status:** Complete for the public STRIVE release  
> **Model:** STRIVE Rule-Based Planner (`HardcodeNuscPlanner`)  
> **Primary implementation:** `src/planners/hardcode_goalcond_nusc.py`  
> **Upstream context:** D-01 — nuScenes Data; D-02 — Generated Scenarios for evaluation  
> **Downstream:** C-02 — Adversarial Optimization; Planner Evaluation; F-01 — Planner Tuning

---

## 1. Model Details

### 1.1 Model summary

`HardcodeNuscPlanner` is STRIVE's released rule-based, lane-graph-based ego planner.

It repeatedly:

1. converts the current scene into an internal world-state representation;
2. associates vehicles with nearby lane-graph edges;
3. constructs lane-following splines;
4. predicts nearby non-ego agents under several longitudinal speed hypotheses;
5. generates candidate ego speed profiles;
6. scores candidate trajectories using approximate geometric collision risk;
7. selects a candidate that is sufficiently collision-free while preferring progress;
8. advances the ego by one planning step.

The planner is intentionally simple and serves primarily as a research target for STRIVE adversarial scenario generation and planner-improvement experiments.

### 1.2 Model type

```text
Rule-based reactive trajectory planner
```

Core characteristics:

- no learned weights;
- lane-graph-based path generation;
- finite-horizon longitudinal candidate search;
- hand-designed surrounding-agent prediction hypotheses;
- hand-designed collision scoring;
- receding-horizon replanning.

### 1.3 Primary implementation

```text
src/planners/hardcode_goalcond_nusc.py
```

Planner configuration wrapper:

```text
src/planners/planner.py::PlannerConfig
```

Primary consumers:

```text
src/adv_scenario_gen.py
src/eval_planner.py
```

### 1.4 Configuration interface

The planner source exposes:

```text
DEF_CONFIG
TUNED_VAL_FINAL_1
CONFIG_DICT
```

with public configuration keys:

```text
default
final_tuned_val_1
```

### 1.5 Authors, release, and license

The planner is part of the STRIVE CVPR 2022 release by Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, and Or Litany.

Repository source code is MIT licensed.

---

## 2. Purpose & Role in STRIVE

### 2.1 Primary purpose

The planner produces an ego future trajectory conditioned on:

- current scene state;
- externally supplied future trajectories for surrounding agents;
- nuScenes lane-graph geometry;
- a planner hyperparameter configuration.

### 2.2 Role in adversarial scenario generation

When:

```text
planner = hardcode
```

C-02 attacks this planner.

STRIVE repeatedly reruns the actual rule-based planner against the current generated surrounding-agent trajectories during adversarial optimization.

This is the principal closed-loop planner target in the released rule-based generation workflow.

### 2.3 Role in planner evaluation

`src/eval_planner.py` evaluates the rule-based planner on:

- D-02 generated adversarial scenarios;
- corresponding regular/source nuScenes scenarios.

### 2.4 Role in planner tuning

F-01 tunes this planner's hyperparameters.

The source exposes:

```text
default
final_tuned_val_1
```

and documents the tuned configuration as large-scale tuned on generated validation scenarios.

### 2.5 Relationship to replay planner

STRIVE also supports:

```text
planner = ego
```

which uses the observed nuScenes ego future as a replay planner.

Unlike `HardcodeNuscPlanner`, replay does not compute a reactive ego trajectory from surrounding traffic.

---

## 3. Intended Use

### 3.1 Intended uses

Appropriate uses include:

- STRIVE adversarial planner stress testing;
- evaluation on generated and regular nuScenes-derived scenarios;
- planner-failure analysis;
- hyperparameter tuning research;
- reproducing STRIVE rule-based-planner experiments.

### 3.2 Intended users

The implementation is intended for researchers studying:

- autonomous-driving planner robustness;
- synthetic failure generation;
- trajectory planning;
- planner tuning.

### 3.3 Out-of-scope uses

It should not be treated as:

- production AV planning software;
- a deployable safety controller;
- a certified collision-avoidance system;
- a general lane-changing planner;
- a calibrated collision-probability estimator.

---

## 4. Inputs

### 4.1 Initial planner state

Before rollout, `reset()` receives unnormalized graph state:

```text
x
y
heading_x
heading_y
speed
heading_change_rate
```

The planner converts heading vector to scalar angle and keeps:

```text
x
y
heading
speed
length
width
```

in its internal world state.

### 4.2 Surrounding-agent trajectories

`rollout()` receives future trajectories for non-ego agents:

```text
[NA-B, T, 4]
```

with state:

```text
x
y
heading_x
heading_y
```

These trajectories are treated as externally specified traffic motion.

### 4.3 Agent attributes

Vehicle attributes are unnormalized:

```text
length
width
```

### 4.4 Map environment

The planner requires a `NuScenesMapEnv` with loaded lane graphs.

`eval_planner.py` constructs this with:

```text
load_lanegraph = true
lanegraph_res_meters = 1.0
```

### 4.5 Planner timestamps

`rollout()` receives:

```text
agent_t
planner_t
```

The surrounding-agent observations are interpolated over `agent_t`, and the final planner rollout is interpolated to requested `planner_t`.

### 4.6 Batch metadata

The planner stores:

```text
batch_mask
batch_size
map_idx
agent_ptr
```

to process multiple variable-agent scenes in one rollout.

---

## 5. Outputs

### 5.1 Planner future trajectory

Returned shape:

```text
[B, T, 4]
```

with:

```text
x
y
heading_x
heading_y
```

### 5.2 Internal world state

Each world-state object stores:

```text
x
y
heading
speed
length
width
```

and, during planning:

```text
lane matches
prediction splines
control
```

### 5.3 Control update

`compute_action()` chooses the next ego:

```text
x
y
heading
```

for one planner update.

### 5.4 Visualization outputs

Optional debug/planner visualization can render:

- world state;
- lane graph;
- vehicle boxes;
- candidate collision behavior;
- planner rollout video.

---

## 6. World-State Representation

### 6.1 Agent representation

`state_conv()` converts each graph-network state into:

```text
{x, y, h, s, l, w}
```

where:

- `h = atan2(heading_y, heading_x)`;
- `s` is signed speed;
- `l,w` are vehicle dimensions.

### 6.2 Ego identity

By default:

```text
ego_idx = 0
```

The controlled object is named:

```text
ego
```

and other agents are keyed by zero-padded integer strings.

### 6.3 Surrounding-agent representation

`create_other_agents()` prepends the current non-ego state to supplied future observations and creates SciPy linear interpolators.

Interpolation stops at the first NaN observation.

If an agent has only its initial valid state, it is retained with a one-entry trajectory but without future interpolation.

### 6.4 Time update

`update_wstate()`:

- advances planner-controlled agents to their selected control state;
- advances uncontrolled agents by interpolation if their supplied trajectory covers the next time.

Agents outside the supplied trajectory's valid time range are not carried into the new world state.

---

## 7. Map & Lane Processing

### 7.1 Lane graph

The planner accesses:

```text
map_env.lane_graphs
```

for each scene's nuScenes map.

### 7.2 Lane-match filtering

`get_lane_matches()` filters lane edges by:

1. heading compatibility;
2. Euclidean distance.

Released defaults:

```text
cdistang = 20 degrees
xydistmax = 2.0 m
```

Heading threshold is converted internally using:

```text
1 - cos(cdistang)
```

### 7.3 Connected-lane clustering

`cluster_matches_combine()` groups connected lane-edge matches using graph traversal in forward and backward directions.

For each connected cluster, it retains the match closest to the current vehicle position.

### 7.4 Local spline construction

`get_prediction_splines()`:

- expands lane connectivity forward/backward;
- extends terminal lanes if needed;
- finds a locally closest lane point;
- samples lane geometry;
- smoothly warps the lane toward the ego position;
- forces the spline through the current ego heading.

Hard-coded spline settings in `rollout()`:

```text
lane_ds  = 0.4 m
lane_sig = 3.5 m
sbuffer  = 4.0 m
```

### 7.5 Constant-heading fallback

If no lane match exists, the planner uses:

```text
constant_heading_spline(...)
```

through the current vehicle pose.

This fallback also changes candidate selection to prefer stopping/shorter progress when a low-collision candidate exists.

---

## 8. Surrounding-Agent Prediction

### 8.1 Interaction radius

Default:

```text
interacdist = 70.0 m
```

Agents beyond this ego-relative distance are ignored by prediction/collision scoring.

### 8.2 Speed hypotheses

Default:

```text
predsfacs = [0.5, 1.0]
```

For each nearby other vehicle, the planner predicts motion toward target speed:

```text
current_speed × speed_factor
```

### 8.3 Acceleration hypotheses

Default:

```text
predafacs = [0.5]
```

Maximum acceleration for those hypotheses is:

```text
accmax × predafac
```

### 8.4 Prediction horizon

Default:

```text
nsteps = 25
preddt = 0.2 s
```

so:

```text
prediction horizon = 5.0 s
```

### 8.5 Predicted trajectory construction

For each nearby agent, the planner combines:

```text
speed hypothesis
× acceleration hypothesis
× lane spline
```

to form possible future boxes:

```text
x, y, heading, length, width
```

These candidate other-agent trajectories are used for ego collision scoring.

---

## 9. Ego Candidate Generation

### 9.1 Candidate speed profiles

`gen_sprofiles()` builds piecewise longitudinal profiles over the planning horizon.

The horizon is divided into:

```text
n1 = nsteps // 2
n2 = nsteps - n1
```

### 9.2 Two-stage speed targets

For each planner acceleration factor, it selects:

```text
s1
s2
```

from evenly spaced feasible speed ranges.

The first stage accelerates/decelerates toward `s1`, and the second toward `s2`.

### 9.3 Acceleration factors

Default:

```text
planaccfacs = [1.0]
```

Candidate acceleration magnitude is:

```text
factor × accmax
```

### 9.4 Candidate speed count

Default:

```text
plannspeeds = 5
```

The nested `s1 × s2` grid produces:

```text
5 × 5 = 25
```

speed profiles per planner acceleration factor.

With the released single acceleration factor, that is 25 profiles for the selected ego spline.

### 9.5 Speed and acceleration constraints

Default:

```text
smax   = 15.0 m/s
accmax = 3.0 m/s²
```

Released tuned F-01 config:

```text
smax   = 20.0 m/s
accmax = 4.0 m/s²
```

Candidate speed targets are clipped to:

```text
[0, smax]
```

---

## 10. Collision Scoring

### 10.1 Vehicle approximation

Planner collision scoring uses `boxes2circles()`.

Each oriented vehicle box is approximated by:

```text
5 circles
```

comprising:

- four smaller circles around the box footprint;
- one central circle.

The code swaps effective length/width orientation when `length < width`.

### 10.2 Distance computation

`approx_bbox_distance()` computes pairwise circle-to-circle separations and takes the minimum over the circle/other-object dimensions.

Negative distance indicates geometric overlap under the approximation.

### 10.3 Time-dependent score weights

For distance sequence `d[t]`:

```text
w[t] = score_wmin + t × score_wfac
```

Default:

```text
score_wmin = 0.7
score_wfac = 0.05
```

Tuned:

```text
score_wmin = 0.3
score_wfac = 0.02
```

### 10.4 Collision-probability-like score

Per-step score:

```text
p[t] = 1 + tanh(-d[t] × w[t])
```

If:

```text
d[t] < 0
```

the code sets:

```text
p[t] = 1
```

The trajectory score is then:

```text
P = 1 - product_t(1 - p[t])
```

This is a heuristic collision-like score, not a calibrated physical probability.

### 10.5 Candidate acceptance threshold

Default/tuned:

```text
col_plim = 0.1
```

Candidates with:

```text
P < col_plim
```

are considered acceptable.

---

## 11. Action Selection

### 11.1 No surrounding predictions

If no other-agent prediction trajectory is present, the planner picks the ego candidate with maximum final travel distance.

### 11.2 Valid candidate set

When predictions exist:

```text
valid = candidates with collision score < col_plim
```

### 11.3 Progress preference

If at least one valid candidate exists and a lane match is available, the planner chooses the valid candidate with:

```text
maximum final traveled distance
```

### 11.4 Stop preference

If no lane match is available, `prefer_stop=True`.

Among valid candidates, the planner then chooses:

```text
minimum final traveled distance
```

### 11.5 Fallback behavior

If no candidate satisfies `col_plim`, it chooses:

```text
argmin(collision_score)
```

### 11.6 First-step control

After selecting a speed profile, the planner:

1. computes one-step target speed toward `s1`;
2. evaluates the selected spline at `dt × target_speed`;
3. converts spline heading vector to angle;
4. calls `postprocess_act_for_speed()` to enforce the intended signed speed;
5. stores the resulting next `x,y,h`.

---

## 12. Rollout Procedure

### 12.1 Reset

Before rollout, the caller must run:

```text
planner.reset(...)
```

to supply:

- initial states;
- vehicle attributes;
- batch membership;
- map indices.

### 12.2 Per-step planning

For each planning step, the planner:

```text
compute splines
→ compute action
→ advance world state
→ recompute splines
→ compute action
→ ...
```

Thus planning is receding horizon.

### 12.3 Surrounding-agent update

Other agents follow the externally supplied trajectories via interpolation.

The planner does not cause those trajectories to react.

### 12.4 Output interpolation

The internally produced world states are stacked, then interpolated with SciPy to the caller-requested planner timestamps.

The final tensor is converted back to Torch.

### 12.5 Batched rollout

The planner supports multiple scenes by keeping per-scene:

```text
world state
map name/index
agent slice
```

and processing each scene independently within the batch.

### 12.6 Released alternate-initial-state issue

`rollout()` exposes:

```text
init_state=None
```

and contains a branch intended to rebuild the world state from an alternate `init_state`.

However, that branch calls:

```text
self.create_init_state(init_state, vehicle_atts, ...)
```

where `vehicle_atts` is not defined in the `rollout()` scope or signature.

Therefore the released `rollout(init_state=...)` path is not safely usable as written without correction. Standard STRIVE callers reset the planner and do not rely on this branch.

---

## 13. Configuration

### 13.1 Default configuration

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

### 13.2 Released tuned configuration

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

### 13.3 Configuration dictionary

```text
CONFIG_DICT["default"]
CONFIG_DICT["final_tuned_val_1"]
```

### 13.4 Scenario-generation selection

`adv_scenario_gen.py` verifies that:

```text
planner_cfg in CONFIG_DICT
```

and creates:

```text
HardcodeNuscPlanner(
  map_env,
  PlannerConfig(**CONFIG_DICT[planner_cfg])
)
```

The released `adv_gen_rule_based.cfg` uses:

```text
planner_cfg: default
```

by default.

### 13.5 Evaluation configuration

`eval_planner.py` exposes each planner field as a `planner_*` command-line/config option.

The released `configs/eval_planner.cfg` uses the default configuration, not `final_tuned_val_1`.

---

## 14. Evaluation

### 14.1 Evaluation script

```text
src/eval_planner.py
```

The evaluator runs on CPU in the public implementation.

### 14.2 Regular scenarios

Regular evaluation rolls out the planner on nuScenes future trajectories of surrounding agents.

With:

```text
filter_regular = true
```

it restricts regular evaluation to source windows corresponding to the given generated scenarios.

### 14.3 Adversarial scenarios

For D-02 input:

```text
planner initial state = final past state
non-ego future        = fut_adv[1:]
```

The rule-based planner recomputes its ego response.

### 14.4 Collision rate

Planner-other collision is detected after temporal interpolation.

Evaluator interpolation:

```text
scale factor = 3
```

### 14.5 Collision velocity

For a collision, the evaluator approximates planner and attacker velocity from neighboring trajectory samples and records relative speed magnitude.

### 14.6 Comfort metrics

Before collision/end of sequence it computes:

- acceleration magnitude;
- forward acceleration magnitude;
- lateral acceleration magnitude.

### 14.7 Per-scenario reporting

The evaluator writes:

```text
all_eval_results.csv
```

containing per-scenario metrics.

---

## 15. Quantitative Analysis

### 15.1 Planning horizon

Default/tuned:

```text
25 × 0.2 s = 5.0 s
```

### 15.2 Internal update rate

Default planner step:

```text
dt = 0.2 s
```

equivalent to:

```text
5 Hz
```

### 15.3 Candidate-count analysis

With:

```text
plannspeeds = 5
planaccfacs = [1.0]
```

the planner generates:

```text
25
```

ego longitudinal speed profiles for the selected ego spline at each planning call.

### 15.4 Other-agent hypothesis count

For each nearby agent/lane spline, default longitudinal hypotheses include:

```text
2 speed factors × 1 acceleration factor = 2
```

speed-profile hypotheses.

The total number of other-agent predicted trajectories also scales with that agent's number of candidate lane splines.

### 15.5 Geometric approximation

Every box is represented by:

```text
5 circles
```

for planner collision scoring.

### 15.6 Default vs tuned configuration delta

Only four parameters change:

| Parameter | Default | Tuned |
|---|---:|---:|
| `smax` | 15.0 | 20.0 |
| `accmax` | 3.0 | 4.0 |
| `score_wmin` | 0.7 | 0.3 |
| `score_wfac` | 0.05 | 0.02 |

### 15.7 Profiler

Run:

```bash
python tools/profile_rule_based_planner.py \
  --repo-root . \
  --output ./out/rule_based_planner_profile.yaml
```

The profiler extracts the released dictionaries directly from source and validates key implementation patterns.

---

## 16. Factors

### 16.1 Map quality

Planner behavior depends on lane-graph coverage and topology.

Poor or missing lane matches cause constant-heading fallback.

### 16.2 Surrounding-trajectory quality

The planner assumes supplied other-agent futures are the trajectories it should plan against.

Errors, NaNs, or physically unrealistic trajectories can materially alter behavior.

### 16.3 Initial-state dependence

Lane matching, available speed profiles, and future spline geometry depend on current:

```text
position
heading
speed
```

### 16.4 Configuration dependence

Planner behavior is sensitive to:

- speed/acceleration limits;
- collision-scoring weights;
- collision-score threshold;
- interaction radius;
- candidate-grid resolution.

### 16.5 Agent-density dependence

More nearby vehicles and more lane hypotheses create more predicted trajectories and more restrictive collision scoring.

---

## 17. Limitations

### 17.1 Lane-following bias

The planner chooses:

```text
obj["splines"][0]
```

for ego action generation.

It does not perform a general discrete route/lane decision search over all lane options.

### 17.2 Lane-change limitation

The STRIVE paper identifies inability to change lanes as a significant limitation of the rule-based planner and a source of some generated failures.

### 17.3 Fixed surrounding-agent futures

Surrounding traffic follows supplied trajectories and does not react to the planner within this implementation.

### 17.4 Heuristic collision scoring

The collision score:

```text
1 - product(1 - p[t])
```

is a hand-designed quantity derived from approximate box separation.

It is not empirically calibrated as a probability.

### 17.5 Five-circle geometry approximation

Collision scoring uses circles rather than exact polygon geometry.

This can differ from final evaluation collision definitions.

### 17.6 Finite planning horizon

The default planner looks ahead:

```text
5 s
```

at each receding-horizon step.

### 17.7 Limited route selection

The implementation does not expose a high-level goal/route planner that reasons broadly over alternative maneuvers.

### 17.8 Released alternate-init bug

The optional `rollout(init_state=...)` branch references undefined `vehicle_atts` and should not be considered functional without a code fix.

### 17.9 Research-only implementation

The planner lacks the sensing, uncertainty handling, redundancy, formal validation, and systems integration expected of production autonomous-driving planning software.

---

## 18. Safety & Interpretation

### 18.1 Research planner status

M-02 is a research stress-test target.

It should be interpreted as a deliberately understandable rule-based baseline, not a production planner.

### 18.2 Collision metric interpretation

A planner collision in STRIVE is conditional on:

- supplied traffic trajectories;
- map data;
- finite horizon;
- approximate collision metrics;
- log-replay assumptions.

### 18.3 Tuned configuration interpretation

`final_tuned_val_1` is an empirically selected research configuration.

Improvement under STRIVE evaluation does not imply general road-safety improvement.

### 18.4 Failure interpretation

A failure may indicate:

- true weakness in planner logic;
- limited maneuver vocabulary;
- data/map issues;
- unrealistic or non-reactive traffic;
- limitations in the collision approximation.

---

## 19. Reproducibility

### 19.1 Source files

Primary:

```text
src/planners/hardcode_goalcond_nusc.py
src/planners/planner.py
```

Integration/evaluation:

```text
src/adv_scenario_gen.py
src/eval_planner.py
```

### 19.2 Required map/data inputs

Core planner use requires:

- nuScenes lane graph/map environment;
- initial state;
- dimensions;
- surrounding-agent future trajectories.

### 19.3 Configuration provenance

Record:

```text
planner config name
full planner parameter dictionary
STRIVE source revision
```

For generated scenarios, also record the C-02/D-02 provenance.

### 19.4 Companion metadata

```text
metadata/models/rule_based_planner.yaml
```

### 19.5 Quantitative profiler

```text
tools/profile_rule_based_planner.py
```

The profiler reports:

- source hashes;
- extracted default/tuned configuration dictionaries;
- changed parameters;
- derived horizon/profile counts;
- collision-scoring implementation checks;
- lane-processing constants;
- integration checks;
- released alternate-init issue detection.

### 19.6 Runtime dependencies

Notable direct dependencies include:

```text
NumPy
SciPy
Torch
matplotlib
```

plus STRIVE map/dataset utilities.

The README-tested environment is primarily:

```text
Ubuntu 18.04
Python 3.6
PyTorch 1.9
CUDA 11.1
```

although `eval_planner.py` explicitly runs the planner on CPU.

---

## 20. Relationships

### 20.1 Upstream context

```text
D-01 — nuScenes Data / maps
D-02 — Generated Scenarios for downstream evaluation
```

M-02 does not depend on M-01 to compute its own planner action; M-01 is involved when the planner is embedded inside STRIVE C-02 scenario generation.

### 20.2 Downstream

```text
C-02 — Adversarial Optimization
Planner Evaluation
F-01 — Planner Tuning
```

### 20.3 System position

```text
D-01 maps / traffic state
          │
          ▼
M-02 Rule-Based Planner
   │        │         │
   │        │         └──► F-01 Planner Tuning
   │        └────────────► Planner Evaluation
   └─────────────────────► C-02 Adversarial Generation
```

### 20.4 Interaction with C-01

For hardcode generation, C-01 first fits the source traffic, then M-02 is rolled out and its trajectory replaces the ego initialization target before a second initialization fit.

Thus M-02 also participates immediately before C-02 in the hardcode scenario-generation path.

---

## 21. Terms of Art

### 21.1 Lane match

A lane-graph edge compatible with an agent's current heading and location.

### 21.2 Prediction spline

A continuous path derived from matched lane-graph geometry, locally warped to pass through the agent state.

### 21.3 Speed profile

A finite-horizon sequence of longitudinal speeds generated by bounded acceleration toward one or more target speeds.

### 21.4 Collision score

The planner's heuristic score formed from approximate vehicle separation over the horizon.

### 21.5 Default configuration

```text
DEF_CONFIG
```

### 21.6 Tuned configuration

```text
TUNED_VAL_FINAL_1
```

released through:

```text
CONFIG_DICT["final_tuned_val_1"]
```

---

## 22. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.

2. STRIVE public repository:  
   `https://github.com/nv-tlabs/STRIVE`

3. Primary implementation:
   - `src/planners/hardcode_goalcond_nusc.py`
   - `src/planners/planner.py`

4. Integration:
   - `src/adv_scenario_gen.py`
   - `configs/adv_gen_rule_based.cfg`

5. Evaluation:
   - `src/eval_planner.py`
   - `configs/eval_planner.cfg`

6. Related documentation:
   - D-01 — nuScenes Data Card
   - C-01 — Initialization Optimization Component Card
   - C-02 — Adversarial Optimization Component Card
   - D-02 — Generated Scenarios Data Card
   - F-01 — Planner Tuning Fitted-Config Card
   - S-01 — STRIVE System Card

---

## 23. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed M-02 with exact planner logic, configuration, collision scoring, evaluation behavior, and released alternate-initial-state issue. |
