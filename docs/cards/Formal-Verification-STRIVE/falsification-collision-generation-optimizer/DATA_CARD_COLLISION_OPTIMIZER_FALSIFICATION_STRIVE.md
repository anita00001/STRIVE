# A3-D-01 — STRIVE Collision-Generation Optimizer Falsification Data Card

> **Card ID:** A3-D-01  
> **Card type:** Formal-Assurance Data Card  
> **Status:** Complete falsification-evidence specification; falsification corpus not yet materialized  
> **Assurance approach:** Specification-Driven Falsification of the Collision-Generation Optimizer  
> **Target:** STRIVE adversarial collision-generation pipeline / optimizer  
> **Primary STRIVE components:** C-01 Initialization Optimization, C-02 Adversarial Optimization, C-03 Solution Optimization  
> **System:** S-01 — STRIVE  
> **Inspected STRIVE revision:** `b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d`

---

## 1. Dataset Summary

### 1.1 Dataset / evidence-set name

**STRIVE Specification-Driven Collision-Optimizer Falsification Evidence Set**

This card specifies the evidence required to use STRIVE as a search engine for concrete violations of explicit autonomous-vehicle safety requirements.

The central assurance pattern is:

```text
natural seed scene
+ attacked planner
+ STRIVE traffic/scenario optimizer
+ formalized safety requirement φ
        │
        ▼
generated trajectory
        │
        ▼
independent specification evaluator
        │
        ├── satisfies φ
        └── violates φ → concrete counterexample
```

### 1.2 Assurance purpose

The project concept proposes connecting STRIVE to formal assurance by expressing safety requirements explicitly and then using STRIVE to search for violating trajectories.

Example requirements in the concept include:

```text
TTC > 1.5 s
minimum vehicle separation > d_min
```

The exact temporal operator, threshold semantics, vehicle geometry, and continuous/discrete-time interpretation must be fixed before a result is called a specification violation.

### 1.3 Falsification target

Primary target:

```text
STRIVE adversarial scenario-generation pipeline
```

with component-level roles:

```text
D-01 → M-01 → C-01 → C-02 → C-03 → D-02
```

For the released rule-based planner path:

```text
D-01 → M-01 → C-01 → M-02 → C-02 → C-03 → D-02
```

For replay:

```text
M-02 is bypassed
```

### 1.4 Dataset role

A3-D-01 is intended to provide:

1. **seed-scene evidence** — nuScenes scenes used to initialize falsification;
2. **specification evidence** — versioned safety predicates and thresholds;
3. **search-run provenance** — model/planner/optimizer configuration and budget;
4. **candidate traces** — trajectories generated during or after optimization;
5. **counterexample evidence** — independently re-evaluated violating traces;
6. **regression evidence** — persistent known violations for future optimizer/planner changes.

### 1.5 Dataset status

```text
card/specification:         complete
specification registry:     not yet frozen
falsification tool/wrapper: not yet selected
falsification corpus:       not yet materialized
counterexamples:            none claimed yet
```

---

## 2. Assurance Claim Context

### 2.1 Top-level assurance objective

The top-level objective is **falsification**, not proof:

> Search the declared STRIVE/planner/scenario domain for a concrete execution that violates a versioned safety specification.

### 2.2 Falsification semantics

For a specification `φ`:

```text
candidate trajectory τ
```

is a counterexample if:

```text
τ violates φ
```

under the exact evaluator, geometry, horizon, interpolation, and tolerance defined by that specification version.

### 2.3 Supported claims

A successful run can support statements such as:

> STRIVE found a replay-confirmed trajectory for planner/configuration P that violates specification φ over the declared seed/search domain.

A collection of runs can support empirical statements such as:

- counterexample frequency under a fixed search budget;
- search efficiency;
- severity of discovered violations;
- comparison across planners/specifications.

### 2.4 Unsupported claims

A failed falsification run does **not** establish:

```text
the planner is safe
```

or:

```text
φ holds for all admissible traffic
```

It means only:

```text
no confirmed violation was found under this search method/domain/budget
```

### 2.5 Evidence interpretation

Recommended run outcomes:

```text
counterexample
no_counterexample_found
invalid_candidate
timeout
error
```

These should remain distinct from STRIVE's native generation partitions:

```text
adv_failed
sol_failed
adv_sol_success
```

---

## 3. STRIVE Falsification Target

### 3.1 Initialization Optimization — C-01

C-01 fits M-01 latent variables to reproduce the source traffic.

Released behavior includes:

```text
initial fit:
    posterior-mean initialization
    75 iterations
    hardcoded lr = 0.1
```

For the rule-based path, M-02 is rolled out after the first fit, its ego future replaces the initialization target, and C-01 performs a second fit before C-02.

### 3.2 Adversarial Optimization — C-02

C-02 is the principal native collision-generation search stage.

Released behavior:

- separately optimizes target/planner and other-agent latent variables;
- repeatedly decodes traffic through M-01;
- in the hardcode path, reruns M-02 against current non-ego traffic;
- searches for a planner collision while regularizing plausibility;
- uses no early stopping in the released loop;
- declares native adversarial success using collision geometry rather than TTC/minimum-separation specifications.

Typical released iteration counts:

```text
rule-based planner: 200
replay planner:     300
```

with released adversarial learning rate:

```text
0.05
```

### 3.3 Solution Optimization — C-03

C-03 attempts to find a collision-free planner response after adversarial generation.

Its success is an **operational STRIVE criterion**, not a formal proof that the adversarial scene is solvable.

A3-D-01 therefore records C-03 outcome as contextual evidence rather than formal satisfiability evidence.

### 3.4 Planner under attack

Two principal public paths:

```text
Replay:
    ego follows recorded future

Rule-based:
    M-02 HardcodeNuscPlanner replans against current generated traffic
```

The planner identity/configuration is part of every falsification result.

### 3.5 Learned traffic prior — M-01

M-01 constrains/generated trajectories through the learned traffic prior and decoder.

Therefore A3 counterexamples are not arbitrary trajectories: they are search results within STRIVE's learned latent/optimization mechanism.

This is useful for plausibility-oriented falsification, but it also means search coverage inherits M-01 bias and blind spots.

### 3.6 Generated-scenario output — D-02

D-02 provides the natural serialization target for successful/failed generation traces.

Core fields include:

```text
N
dt
map
lw
sem
past
fut_init
fut_adv
```

Conditional fields may include:

```text
fut_internal_ego
fut_sol
attack_agt
attack_t
z_adv
z_sol
z_prior
attack_bike_prof
```

A3-D-01 should preserve the original D-02 artifact hash alongside its independent specification-evaluation record.

---

## 4. Safety Specifications

### 4.1 Specification registry

Every safety requirement must be represented as a versioned specification record, for example:

```yaml
property_id: TTC-01
version: 1.0.0
signal: time_to_collision
threshold:
  operator: ">"
  value: 1.5
  units: s
temporal_semantics: TBD
agent_scope: ego_vs_each_non_ego
interpolation: TBD
tolerance: TBD
```

### 4.2 TTC specification

The concept document proposes:

```text
TTC > 1.5 s
```

as an example safety requirement.

A formalized version must define:

- TTC formula;
- whether TTC is longitudinal, radial, projected, or geometry-aware;
- how non-closing vehicles are handled;
- how TTC is handled at zero relative speed;
- pairwise agent scope;
- whether the requirement holds at every sampled/continuous time;
- interpolation policy.

Until those choices are fixed, `1.5 s` is a project-concept threshold, not a fully specified executable property.

### 4.3 Minimum-separation specification

Conceptual requirement:

```text
d_ego > d_min
```

A formalized version must define `d_ego` as one of:

- center-to-center distance;
- oriented-box boundary distance;
- circle-approximation distance;
- another explicit geometry.

`d_min` must be independently selected and versioned.

### 4.4 Collision-freedom specification

A natural additional property is:

```text
no ego/non-ego geometric overlap
```

This can align more directly with STRIVE's collision objective, but the property must still fix the exact collision geometry.

### 4.5 Optional dynamic specifications

Possible future project extensions:

```text
speed bound
acceleration bound
heading-rate bound
drivable-area constraint
combined TTC + separation constraint
```

These are not required by the concept PDF.

### 4.6 Specification source

Each threshold should identify one of:

```text
course/project requirement
published standard/reference
vehicle/platform constraint
domain-expert requirement
research assumption
```

Do not present a research assumption as an externally mandated safety standard.

---

## 5. Seed Data Sources

### 5.1 nuScenes source scenes

The public STRIVE pipeline starts from nuScenes scenes and traffic histories.

These are the primary natural seed scenes for A3.

### 5.2 D-01 relationship

Use D-01 for:

- split provenance;
- agent/state schema;
- map crop;
- semantic categories;
- history/future horizon;
- missing-data handling.

### 5.3 Planner-specific eligibility

Some source scenes may be rejected or unsuitable for a particular planner path.

For the rule-based path, STRIVE explicitly rejects scenes in which the planner already collides after initialization.

A3-D-01 should preserve the reason a seed is:

```text
accepted
rejected_before_search
invalid
```

### 5.4 Map context

Record:

```text
map name
source scene/sample
map crop/configuration
```

and enough information to reproduce any map-dependent specification.

### 5.5 Initial traffic trajectories

Preserve both:

```text
recorded/source future
```

and:

```text
C-01 initialized future
```

when relevant.

This permits distinguishing a pre-existing near-violation from one created by optimization.

---

## 6. Falsification Input Schema

### 6.1 Run identity

Recommended fields:

```yaml
run_id: string
seed_case_id: string
planner_type: replay | rule_based
property_id: string
property_version: string
random_seed: integer
```

### 6.2 STRIVE artifact identity

Required:

```yaml
strive_revision: string
traffic_model_checkpoint_sha256: string
traffic_model_config_sha256: string
optimizer_config_sha256: string
planner_config_sha256: string | null
```

### 6.3 Seed scene provenance

Recommended:

```yaml
source_dataset: nuscenes
source_version: string
source_split: train | val | test
source_scene_id: string
source_sample_id: string
map_name: string
```

### 6.4 Optimization configuration

Record resolved settings for:

```text
C-01
C-02
C-03
```

including:

- iteration counts;
- learning rates;
- loss weights;
- collision buffer/threshold settings;
- feasibility settings;
- future horizon.

### 6.5 Planner configuration

For rule-based:

```text
M-02 config name
resolved planner parameters
```

For replay:

```text
recorded ego future identity/hash
```

### 6.6 Specification

Each run must embed/reference:

```text
property ID
version
thresholds
geometry
temporal semantics
interpolation
numeric tolerance
```

### 6.7 Search budget

Record:

```text
optimizer iterations
wall-clock timeout
number of restarts
random seeds
candidate-agent strategy
```

---

## 7. Falsification Output Schema

### 7.1 Generated trajectory artifact

Preserve:

```text
original D-02 JSON
SHA-256
partition
planner/non-ego trajectories
latents
attack metadata
```

### 7.2 Specification trace

For each checked timestep/pair, preserve derived signals such as:

```text
TTC
separation
collision status
robustness score
```

where applicable.

### 7.3 Violation result

Recommended:

```yaml
falsification_status: counterexample | no_counterexample_found | invalid_candidate | timeout | error
violated: true | false | null
first_violation_time_s: float | null
worst_time_s: float | null
worst_value: float | null
robustness: float | null
```

### 7.4 Violating agent(s)

Record:

```text
ego index
other agent index
stable source identifier if available
```

### 7.5 Native STRIVE outcome

Record separately:

```text
adv_failed
sol_failed
adv_sol_success
```

where the run follows the original STRIVE partitioning.

### 7.6 Independent evaluation

A final counterexample should include:

```text
independent_property_replay = true
```

after recomputing the property from the saved trajectory artifact rather than trusting only optimizer-internal quantities.

---

## 8. Counterexample Definition

### 8.1 Formal/project counterexample

For A3:

> A counterexample is a concrete saved STRIVE-generated trajectory that violates the exact versioned safety specification under independent re-evaluation.

### 8.2 Native STRIVE adversarial success is not enough

C-02 native success means a collision was detected under STRIVE's released success test.

That does not automatically establish violation of a different property such as:

```text
TTC > 1.5 s
```

unless the independent specification evaluator confirms it.

### 8.3 TTC/separation violation without native collision

Conversely, a candidate may violate:

```text
TTC threshold
minimum separation threshold
```

without satisfying STRIVE's native collision criterion.

Such a trace may still be a valid A3 counterexample.

### 8.4 Replay-confirmed counterexample

A counterexample is strongest when the saved trajectory:

1. reloads successfully;
2. reproduces the same property trace;
3. violates the same property/version within tolerance;
4. preserves attacked planner/scenario provenance.

### 8.5 Invalid candidate

Examples:

- NaN/invalid trajectory;
- inconsistent timestep;
- missing agent geometry required by property;
- property evaluator error;
- artifact mismatch;
- trajectory transformed in the wrong coordinate frame.

---

## 9. Specification Signals

### 9.1 Time-to-Collision

A TTC evaluator must define its formula precisely.

A common constant-relative-velocity TTC is only one option and may not be appropriate for turning multi-agent trajectories.

The chosen evaluator is part of the specification.

### 9.2 Minimum vehicle separation

Recommended hierarchy:

```text
preferred:
    oriented vehicle-footprint boundary distance

acceptable if explicitly specified:
    STRIVE-compatible circle approximation
    center distance with documented limitation
```

### 9.3 Collision indicator

Possible semantics:

- polygon IoU / overlap;
- oriented-box intersection;
- circle approximation.

The same property version must use one consistent semantics.

### 9.4 Relative speed

Optional contextual signal:

```text
closing speed
relative velocity magnitude
```

### 9.5 Ego acceleration

Optional specification/context signal derived from the planner trajectory.

### 9.6 Drivable-area status

Optional map property requiring a documented raster/polygon interpretation.

---

## 10. Temporal Semantics

### 10.1 Native STRIVE timebases

Relevant released timebases include:

```text
M-01 / nuScenes traffic prediction:
    dt = 0.5 s

M-02 rule-based planner internal rollout:
    dt = 0.2 s
```

Generated/evaluated trajectories may therefore require interpolation before a common specification check.

### 10.2 Horizon

The property record must specify:

```text
start time
end time
inclusive/exclusive endpoints
```

and whether it covers:

- adversarial future only;
- full 6-second M-01 future;
- planner's native horizon;
- another explicit interval.

### 10.3 Temporal operator semantics

The concept document gives informal temporal formulas around TTC and separation.

Before execution, define whether the property is intended as:

```text
always over horizon
eventually
until
pointwise threshold
```

No operator should be inferred from typography alone.

### 10.4 First violation

Store:

```text
earliest timestamp at which the executable property is false
```

under the specified discretization/interpolation.

### 10.5 Continuous-time approximation

Because collision/TTC events can occur between samples, specify one of:

- no interpolation;
- linear interpolation;
- higher-order interpolation;
- dense resampling;
- analytic segment check.

The approximation affects the counterexample claim.

---

## 11. Search-Space Definition

### 11.1 STRIVE latent variables

C-02 optimizes M-01 latent variables for:

- the target/planner-related branch;
- other traffic agents.

These are the primary native search variables.

### 11.2 Attack-agent selection

C-02 selects/candidates non-ego agents according to its released feasibility and attack-selection logic.

A3-D-01 should record:

```text
candidate agents
selected attacker
actual violating agent
```

because D-02's stored `attack_agt` need not equal the independently observed colliding/violating agent.

### 11.3 Fixed scene context

Typically fixed across one search run:

```text
map
vehicle dimensions
semantic categories
source scene history
```

unless the A3 method explicitly extends the search space.

### 11.4 Planner response

Replay:

```text
ego trajectory fixed to recorded future
```

Rule-based:

```text
M-02 replans against current generated non-ego trajectories
```

This distinction materially changes the falsification system.

### 11.5 Search bounds

The released optimizer is not a generic bounded formal search procedure.

If A3 introduces explicit:

```text
latent boxes
norm bounds
trajectory bounds
```

those are new assurance-search constraints and must be stored separately from native STRIVE configuration.

### 11.6 Restarts

A3 may use multiple random/latent restarts.

Record each restart separately or preserve a parent run with child-search IDs.

---

## 12. Case Construction

### 12.1 Natural seed scenes

Use nuScenes anchors with full D-01 provenance.

### 12.2 Replay-planner cases

Replay is useful for:

- deterministic ego-reference comparison;
- isolating non-ego traffic search;
- reproducing STRIVE's replay attack path.

### 12.3 Rule-based-planner cases

Rule-based cases exercise M-02's receding-horizon reaction to generated traffic.

These are often more representative of planner-in-the-loop falsification.

### 12.4 Boundary cases

Prioritize seeds whose initial or early optimized traces are near:

```text
TTC threshold
separation threshold
collision boundary
```

### 12.5 Counterexample-directed cases

Use prior counterexamples to create:

- nearby seeds;
- alternative planner configurations;
- specification-threshold sensitivity studies.

### 12.6 Regression cases

All replay-confirmed counterexamples should enter a persistent regression partition.

---

## 13. Partitioning

### 13.1 Development

Used for:

- specification evaluator debugging;
- objective integration;
- threshold exploration;
- search-budget tuning.

### 13.2 Falsification evaluation

Frozen before final reporting:

```text
seed IDs
planner configs
property versions
search budgets
optimizer configs
```

### 13.3 Regression

Contains confirmed violations.

### 13.4 Planner-specific partitions

Report replay and rule-based results separately before any aggregate.

### 13.5 Leakage controls

Do not tune:

```text
thresholds
search budgets
loss weights
restart counts
```

on final evaluation outcomes and then present those same outcomes as untouched final evidence.

---

## 14. Data Transformations

### 14.1 STRIVE normalization

Preserve the original normalized optimization representation and the unnormalized physical trajectory used for specification evaluation.

### 14.2 Coordinate frames

Specification evaluation should use one documented physical frame.

For saved D-02 trajectories, confirm whether positions/headings are already in the expected scene/global frame before computing TTC/separation.

### 14.3 Trajectory interpolation

Record:

```text
input dt
output evaluation dt
interpolation method
scale factor
```

Existing STRIVE evaluation code uses interpolation for some collision checks; A3 property interpolation is a separate specification choice.

### 14.4 Vehicle geometry

Keep:

```text
length
width
heading
```

with each trajectory if the specification uses footprint geometry.

### 14.5 Map transformations

For map-based properties, preserve the exact map coordinate convention.

### 14.6 Specification-evaluator preprocessing

Hash/version the evaluator code and configuration.

A counterexample should be reproducible from:

```text
trajectory artifact + specification registry + evaluator revision
```

---

## 15. Quantitative Dataset Profile

The A3 corpus does not yet exist, so no falsification-rate claims are populated.

### 15.1 Required seed statistics

Report:

```text
number of unique seed scenes
source split distribution
map distribution
agent-count distribution
planner distribution
```

### 15.2 Search-run statistics

Report:

```text
total runs
restarts
iterations
timeouts
errors
```

### 15.3 Specification statistics

Report:

```text
runs by property/version
runs by threshold
runs by combined specification
```

### 15.4 Outcome statistics

Report separately:

```text
counterexample
no_counterexample_found
invalid_candidate
timeout
error
```

### 15.5 Severity statistics

Per property:

```text
minimum TTC
minimum separation
worst robustness score
first violation time
```

### 15.6 STRIVE partition cross-tabulation

Cross-tabulate formal/project falsification outcome with:

```text
adv_failed
sol_failed
adv_sol_success
```

This reveals whether native STRIVE success aligns with the external safety specification.

---

## 16. Coverage Strategy

### 16.1 Scene coverage

Cover:

- multiple maps;
- varying traffic density;
- intersection/merge/following geometries;
- differing agent counts.

### 16.2 Planner coverage

At minimum:

```text
Replay
Rule-based default
```

and, if relevant:

```text
Rule-based tuned configuration
```

### 16.3 Specification coverage

Start with:

```text
TTC threshold
minimum-separation threshold
```

then add combined properties if justified.

### 16.4 Boundary coverage

Intentionally include near-threshold seed/generated trajectories.

### 16.5 Attack-agent coverage

Measure whether violations involve:

- selected attack agent;
- a different non-ego agent;
- multiple agents.

### 16.6 Scenario-taxonomy coverage

M-03/M-04 labels may be used after generation to stratify collision geometry, but they are not required for falsification validity.

---

## 17. Validation & Quality Assurance

### 17.1 Schema validation

Require:

```text
run ID
seed ID
STRIVE revision
model checkpoint hash
planner identity
property ID/version
search budget
trajectory artifact/hash
falsification outcome
```

### 17.2 Specification-evaluator unit tests

Each property implementation needs tests for:

- clearly safe trace;
- threshold equality;
- clearly violating trace;
- zero/negative relative speed where applicable;
- missing/invalid trajectory;
- geometry edge cases.

### 17.3 Optimizer replay

Where practical, replay generation with fixed seeds/configuration.

Gradient/GPU nondeterminism should be documented if exact bitwise reproduction is unavailable.

### 17.4 Counterexample re-evaluation

Final counterexamples must be checked independently from optimizer loss values.

### 17.5 Geometry consistency

Do not report:

```text
minimum separation
```

using one geometry and:

```text
collision
```

using another without stating the difference.

### 17.6 Numerical tolerance

Record tolerances for:

- threshold comparison;
- interpolation;
- polygon/circle geometry;
- floating-point equality.

---

## 18. Falsification Metrics

### 18.1 Falsification success rate

For a fixed protocol:

```text
confirmed counterexamples / valid completed searches
```

Report denominator explicitly.

### 18.2 Time to first violation

Record:

```text
wall-clock time
optimizer iteration
restart index
```

where available.

### 18.3 Quantitative robustness

If the chosen temporal-logic/falsification framework defines a robustness score:

```text
ρ < 0 → violation
ρ > 0 → satisfaction
```

only use this convention if the selected tool/specification actually defines it that way.

### 18.4 Minimum TTC

For TTC properties, store:

```text
min_TTC
time_of_min_TTC
agent_pair
```

### 18.5 Minimum separation

Store:

```text
min_distance
time_of_min_distance
agent_pair
geometry
```

### 18.6 Unique counterexamples

Deduplicate by a documented rule, for example:

- seed + violating agent + time window;
- trajectory hash;
- feature-space clustering.

Raw count and unique count should both be available.

---

## 19. Known Limitations

### 19.1 Falsification is not verification

The central limitation:

```text
no counterexample found != property proved
```

### 19.2 Optimizer local search

C-02 uses gradient optimization and may fail because of:

- local minima;
- initialization;
- nonconvex learned decoder;
- planner discontinuities/heuristics;
- insufficient search budget.

### 19.3 Learned traffic-prior bias

STRIVE searches through M-01's learned representation.

Unsafe behaviors outside that representation may never be explored.

### 19.4 Planner dependence

A counterexample is specific to:

```text
planner implementation
planner configuration
planner timebase
```

### 19.5 Specification incompleteness

TTC and minimum separation do not capture all aspects of driving safety.

### 19.6 Discrete-time approximation

A property checked only at sampled timesteps can miss between-sample events.

### 19.7 Synthetic evidence

Generated counterexamples are synthetic stress tests.

They do not imply empirical real-world event frequency.

### 19.8 C-03 interpretation

C-03 failure does not prove that no collision-free solution exists.

C-03 success demonstrates an operationally found solution under STRIVE's method, not a universal proof of solvability.

---

## 20. Safety & Assurance Interpretation

### 20.1 Meaning of a found violation

A replay-confirmed violation establishes:

> The specified planner/system execution admits at least one concrete STRIVE-generated trajectory violating the exact property under the declared assumptions.

### 20.2 Meaning of no violation found

Only:

> This falsification process did not find a confirmed violation under its domain, configuration, initialization, and budget.

### 20.3 Meaning of STRIVE adversarial success

STRIVE native adversarial success is evidence of a collision according to STRIVE's released success test.

It should be treated as a **candidate safety counterexample** until the A3 specification evaluator confirms violation of the relevant property.

### 20.4 Meaning of C-03 solution success

C-03 success can support the operational STRIVE notion that another planner response was found.

It is not a formal proof of solvability.

### 20.5 System-level inference limits

One counterexample disproves the corresponding universal safety requirement for the declared domain/system configuration.

It does not by itself determine:

- real-world probability;
- severity frequency;
- behavior of different planners/configurations;
- behavior outside the seed/search domain.

---

## 21. Reproducibility & Provenance

### 21.1 STRIVE revision

Required:

```text
b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d
```

or the exact revision actually used.

### 21.2 M-01 checkpoint

Required:

```text
SHA-256
```

### 21.3 Planner configuration

Replay:

```text
recorded ego artifact/provenance
```

Rule-based:

```text
M-02 configuration name + resolved values + hash
```

### 21.4 Optimizer configuration

Hash/store resolved:

```text
C-01
C-02
C-03
```

settings.

### 21.5 Specification version

Required:

```text
property ID
property version
specification registry hash
evaluator code hash/revision
```

### 21.6 Seed scene identity

Preserve nuScenes provenance plus an A3 seed ID.

### 21.7 Random seeds

Record all sampling/search seeds available.

### 21.8 Counterexample artifact

For every confirmed counterexample:

```text
D-02/generated JSON hash
A3 evaluation record hash
property trace
independent replay status
```

---

## 22. Relationships

### 22.1 Upstream

```text
D-01 — STRIVE nuScenes Data
M-01 — STRIVE Main Traffic Model
C-01 — Initialization Optimization
C-02 — Adversarial Optimization
C-03 — Solution Optimization
M-02 — Rule-Based Planner (hardcode path)
```

### 22.2 Downstream

```text
D-02 — STRIVE Generated Scenarios
```

A3 adds a separate assurance layer:

```text
D-02 candidate trajectory
        │
        ▼
versioned specification evaluator
        │
        └──► A3 counterexample evidence
```

### 22.3 Assurance approach

```text
Approach 3
Specification-Driven Falsification of the Collision-Generation Optimizer
```

### 22.4 Companion assurance model card

Planned:

```text
A3-M-01 — STRIVE Collision-Generation Optimizer Falsification Model Card
```

### 22.5 Relationship to planner evaluation

Confirmed A3 counterexamples can be replayed through the same planner-evaluation infrastructure, but A3's safety-property result must remain independently computed and versioned.

---

## 23. Terms of Art

### 23.1 Safety specification

A versioned predicate over a trajectory/system trace.

### 23.2 Falsification

Search for a concrete execution that violates a specification, without proving that no violations exist when the search fails.

### 23.3 Counterexample

A concrete saved trace that violates the exact specification.

### 23.4 Specification robustness

A quantitative satisfaction/violation measure, only when defined by the selected specification formalism/tool.

### 23.5 Seed scene

A natural source scene from which STRIVE optimization begins.

### 23.6 Search budget

The finite optimization resources allocated to a falsification attempt.

### 23.7 Specification evaluator

The independently versioned implementation that maps a saved trajectory to property signals and satisfaction/violation.

### 23.8 Native STRIVE success

The original repository's adversarial-generation success criterion; not automatically identical to an A3 specification violation.

---

## 24. References

1. **Formal Assurance in STRIVE** — project concept document. It proposes specification-driven falsification by expressing AV safety requirements, including example TTC and minimum-separation constraints, and using STRIVE-generated violating trajectories as concrete counterexamples.

2. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.

3. STRIVE public repository:  
   `https://github.com/nv-tlabs/STRIVE`

4. Existing documentation:
   - D-01 — STRIVE nuScenes Data Card
   - M-01 — STRIVE Main Traffic Model Card
   - M-02 — STRIVE Rule-Based Planner Card
   - C-01 — Initialization Optimization Card
   - C-02 — Adversarial Optimization Card
   - C-03 — Solution Optimization Card
   - D-02 — STRIVE Generated Scenarios Data Card
   - S-01 — STRIVE System Card

---

## 25. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed Approach-3 falsification data specification, including versioned TTC/separation requirements, STRIVE-vs-specification outcome separation, search provenance, independent counterexample replay, and falsification metrics. |
