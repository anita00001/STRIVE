# A3-M-01 — STRIVE Collision-Generation Optimizer Falsification Model Card

> **Card ID:** A3-M-01  
> **Card type:** Formal-Assurance Model Card  
> **Status:** Complete falsification specification; no falsification result claimed yet  
> **Assurance approach:** Specification-Driven Falsification of the Collision-Generation Optimizer  
> **Target model/process:** STRIVE adversarial collision-generation pipeline  
> **Primary STRIVE components:** C-01 Initialization Optimization, C-02 Adversarial Optimization, C-03 Solution Optimization  
> **Companion data card:** A3-D-01 — STRIVE Collision-Generation Optimizer Falsification Data Card  
> **System:** S-01 — STRIVE  
> **Inspected STRIVE revision:** `b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d`

---

## 1. Falsification Model Details

### 1.1 Assurance model summary

A3-M-01 specifies how STRIVE can be used as a **specification-driven falsifier** for autonomous-vehicle planner safety requirements.

The central assurance workflow is:

```text
explicit safety requirement φ
+ seed traffic scene
+ attacked planner/configuration
+ STRIVE collision-generation optimizer
        │
        ▼
candidate generated trajectory
        │
        ▼
independent specification evaluator
        │
        ├── satisfies φ
        └── violates φ → concrete counterexample
```

The objective is to **find violations**, not to prove universal safety.

### 1.2 Target pipeline

Primary public STRIVE path:

```text
D-01 nuScenes
   │
   ▼
M-01 learned traffic model
   │
   ▼
C-01 initialization optimization
   │
   ▼
C-02 adversarial optimization
   │
   ▼
C-03 solution optimization
   │
   ▼
D-02 generated scenarios
```

Rule-based planner path:

```text
D-01 → M-01 → C-01 → M-02 → C-02 → C-03 → D-02
```

Replay path:

```text
M-02 is bypassed
```

### 1.3 Target artifact identity

Every falsification result must bind to:

```text
STRIVE source revision
M-01 checkpoint SHA-256
M-01 effective configuration
planner implementation/configuration
C-01/C-02/C-03 configuration
safety-specification ID/version
specification-evaluator revision/hash
seed-scene identity
search budget
random seed(s)
```

### 1.4 Assurance status

Current status:

```text
falsification model specification: complete
companion data specification:     complete
safety-specification registry:    not yet frozen
external evaluator:               not yet implemented/frozen
falsification tool/wrapper:       not yet selected
falsification runs:               not yet run
confirmed counterexamples:        none claimed
```

### 1.5 Falsification tool / framework

The project concept leaves the exact tool open.

Possible integrations include:

- direct STRIVE optimization plus executable property evaluator;
- optimization driven by quantitative temporal-logic robustness;
- an external falsification framework wrapping STRIVE;
- hybrid gradient/random-restart search.

The selected method must state whether it merely **searches** for violations or provides any stronger guarantee.

---

## 2. Purpose & Assurance Role

### 2.1 Primary assurance objective

The primary objective is:

> Given a planner, seed scene, safety specification, and finite search budget, use STRIVE to search for a concrete generated traffic trajectory that violates the specification.

### 2.2 Why STRIVE is useful for falsification

STRIVE already provides:

- natural nuScenes initialization;
- a learned traffic prior;
- differentiable latent traffic generation;
- collision-oriented adversarial optimization;
- planner-in-the-loop behavior for the rule-based path;
- serialized generated scenarios.

This makes it a natural search engine for **plausibility-constrained safety falsification**.

### 2.3 Relationship to planner safety

A confirmed counterexample establishes that:

```text
the specified planner/configuration
```

admits at least one generated traffic execution violating the exact property under the stated assumptions.

It does not estimate how frequently that execution would occur in the real world.

### 2.4 Relationship to A3-D-01

A3-D-01 defines:

- seed scenes;
- specification records;
- search-run provenance;
- generated trajectory artifacts;
- property traces;
- counterexample records.

A3-M-01 defines:

- the falsification process;
- search target/boundary;
- specification semantics;
- optimizer/specification relationship;
- result interpretation.

### 2.5 Out-of-scope claims

A3-M-01 does not establish:

- universal planner safety;
- absence of violations after unsuccessful search;
- real-world crash probability;
- complete M-01 correctness;
- formal solvability from C-03 success/failure;
- safety outside the declared seed/search/specification domain.

---

## 3. Falsification Target Boundary

### 3.1 Full STRIVE generation path

A full falsification run includes:

```text
natural source scene
M-01 latent model/decoder
C-01 initialization
planner behavior
C-02 adversarial search
optional C-03 solution search
D-02 serialization
external specification evaluation
```

### 3.2 Replay-planner path

Replay uses the recorded ego future as the planner trajectory.

The adversarial optimizer changes non-ego traffic through M-01 while the ego reference is fixed.

This path is useful for isolating traffic-side falsification.

### 3.3 Rule-based-planner path

The rule-based path includes M-02.

Important released workflow:

1. C-01 first fits the source traffic;
2. M-02 rolls out the ego;
3. C-01 refits with the M-02 ego target;
4. during C-02, M-02 is repeatedly rerun against the current generated non-ego trajectories.

Thus the planner responds to the evolving falsification candidate.

### 3.4 Selected falsification boundary

The recommended A3 boundary is:

```text
STRIVE candidate generation
        +
external versioned safety evaluator
```

The external evaluator should remain logically separate from C-02's native loss/success logic unless the project explicitly replaces or augments the native objective.

### 3.5 Excluded components

Unless separately included, A3 does not formally verify:

- M-01's neural correctness;
- M-02's implementation;
- C-02 global optimality;
- C-03 completeness;
- nuScenes sensor truth;
- deployment dynamics.

---

## 4. STRIVE Search Components

### 4.1 M-01 — Learned traffic model

M-01 supplies the learned latent traffic prior and autoregressive decoder.

In A3, it functions as a **search-space prior**: C-01/C-02/C-03 manipulate latent variables rather than arbitrary future trajectories.

This helps keep search results near the learned distribution but also limits coverage to what M-01 can represent.

### 4.2 C-01 — Initialization Optimization

C-01 fits latent variables so generated traffic initially matches the source scene.

Released first fit:

```text
initial z: posterior mean
iterations: 75
learning rate: 0.1
```

Rule-based mode performs a second fit after M-02 provides the ego target:

```text
iterations: 100
configured learning rate: 0.05
```

A3 should treat this initialization as part of search provenance because it can materially affect the local optimum reached by C-02.

### 4.3 C-02 — Adversarial Optimization

C-02 is the principal native adversarial-search stage.

Released behavior includes:

- optimizing target/planner-related and other-agent latent variables separately;
- detaching the opposing branch during each optimization update;
- differentiable crash-distance objective;
- prior regularization;
- vehicle/environment collision regularization;
- target/non-target latent initialization terms;
- no early stopping in the released loop;
- rule-based planner recomputation during hardcode-mode optimization.

Typical released optimization settings:

```text
learning rate: 0.05
rule-based iterations: 200
replay iterations:     300
```

### 4.4 C-02 native collision objective

The adversarial loss is collision-oriented and includes a soft minimum crash-distance term.

This objective is not identical to:

```text
TTC > 1.5 s
```

or:

```text
minimum separation > d_min
```

unless the A3 method explicitly rewrites the objective around those specifications.

### 4.5 C-02 native success test

Released final adversarial success is based on geometric planner/other-agent collision, with collision counted when final overlap exceeds the implementation threshold.

Documented operational threshold:

```text
polygon IoU > 0.02
```

This is a native STRIVE success criterion, not a generic formal-safety specification.

### 4.6 C-03 — Solution Optimization

C-03 attempts to find a collision-free planner response after adversarial generation.

Released success requires no:

```text
planner-vs-other collision
planner-vs-environment collision
```

under its operational criteria.

A3 interpretation:

```text
C-03 success:
    STRIVE found one operational collision-free response

C-03 failure:
    STRIVE did not find such a response under its optimizer/configuration
```

Neither result is a complete formal solvability theorem.

### 4.7 M-02 — Rule-Based Planner

M-02 is included only in the rule-based falsification path.

It is a receding-horizon planner whose rollout is repeatedly recomputed against generated traffic in C-02.

The exact planner configuration must be frozen for every result.

### 4.8 D-02 — Generated scenario artifact

D-02 stores the generated scenario and relevant latent/provenance fields.

A3 uses the D-02 trajectory as the candidate trace for independent specification evaluation.

---

## 5. Safety Specification Interface

### 5.1 Specification registry

Every A3 property should be represented as a versioned executable specification.

Required fields:

```text
property_id
version
signal definitions
agent scope
threshold(s)
units
temporal semantics
time horizon
interpolation
vehicle geometry
numeric tolerance
evaluator revision/hash
source/rationale
```

### 5.2 TTC requirement

The project concept provides an example requiring:

```text
TTC > 1.5 s
```

The concept notation does not by itself fully define:

- TTC computation;
- closing-direction assumptions;
- pair selection;
- continuous vs sampled time;
- behavior at zero/negative closing speed;
- temporal quantification.

A3 must make those choices explicit before execution.

### 5.3 Minimum-separation requirement

The project concept also proposes a requirement of the form:

```text
d_ego > d_min
```

A3 must define `d_ego` exactly, for example:

```text
oriented-box boundary distance
```

or another declared geometry.

`d_min` remains a project-specified parameter unless an external requirement defines it.

### 5.4 Collision-freedom requirement

A direct property may be:

```text
for all checked times and non-ego agents:
    ego footprint does not overlap non-ego footprint
```

This is closer to STRIVE's native objective but still requires a frozen geometry/evaluator.

### 5.5 Additional optional specifications

Possible extensions:

- maximum ego acceleration;
- maximum speed;
- lane/drivable-area containment;
- combined TTC and separation;
- temporal combinations.

These are extensions beyond the two examples in the concept document.

### 5.6 Specification provenance

Every non-code threshold must be labeled as:

```text
project requirement
published requirement/standard
vehicle/platform constraint
domain-expert requirement
research assumption
```

---

## 6. Formal Falsification Semantics

### 6.1 Satisfaction

For a saved trajectory `τ`:

```text
τ ⊨ φ
```

means the independent A3 evaluator declares the exact versioned property satisfied over its defined horizon and semantics.

### 6.2 Violation

```text
τ ⊭ φ
```

means at least one required condition fails according to that same evaluator.

### 6.3 Counterexample

A confirmed A3 counterexample is:

> a concrete, reloadable STRIVE-generated trajectory that violates the exact specification and reproduces that violation under independent re-evaluation.

### 6.4 Quantitative robustness

If the selected formalism defines a signed robustness score:

```text
ρ(τ, φ)
```

its semantics must be documented.

Do not assume a universal sign convention without the selected tool.

### 6.5 Inconclusive outcomes

Examples:

```text
search exhausted without violation
timeout
optimizer numerical failure
invalid generated trace
specification evaluator failure
```

These are not proofs of satisfaction.

---

## 7. Inputs to the Falsification Model

### 7.1 Seed scene

Each run begins from a frozen A3-D-01 seed with D-01/nuScenes provenance.

### 7.2 Traffic-model artifact

Required:

```text
M-01 checkpoint SHA-256
effective config
normalizers
repository revision
```

### 7.3 Planner

```text
replay
```

or:

```text
rule-based M-02
```

### 7.4 Planner configuration

Replay:

```text
exact source ego trajectory
```

Rule-based:

```text
resolved M-02 configuration/hash
```

### 7.5 Optimizer configuration

Required resolved parameters for:

```text
C-01
C-02
C-03
```

### 7.6 Specification

Required:

```text
property ID/version
registry hash
evaluator hash
```

### 7.7 Search budget

At minimum:

```text
iterations
restarts
timeout
random seed
candidate-agent policy
```

---

## 8. Search Variables

### 8.1 Target/planner latent branch

C-02 optimizes target/planner-related latent variables through the learned model.

### 8.2 Other-agent latent branch

C-02 also optimizes non-target traffic latents.

The two branches are updated separately with the opposing branch detached during each update.

### 8.3 Attack-agent selection

STRIVE distinguishes:

- candidate attack agents;
- selected attack agent;
- agent that ultimately collides/violates.

A3 should preserve all three concepts when available.

### 8.4 Planner trajectory

Replay:

```text
fixed recorded ego future
```

Rule-based:

```text
planner trajectory changes as generated traffic changes
```

### 8.5 Optional A3 search bounds

If A3 introduces additional:

```text
latent norm bounds
latent boxes
trajectory perturbation bounds
```

these are new assurance constraints and must be versioned separately from native STRIVE.

---

## 9. Native STRIVE Objective vs Safety Specification

### 9.1 Native collision objective

C-02 optimizes a differentiable loss designed to create a planner collision while preserving learned-prior plausibility and avoiding invalid traffic behavior.

### 9.2 Native adversarial success

Native final success is a geometric collision result.

This is useful candidate evidence for a collision-freedom property.

### 9.3 External falsification property

A3 properties may instead measure:

```text
TTC
minimum separation
collision geometry
other safety predicates
```

with independent semantics.

### 9.4 Non-equivalence

Therefore:

```text
native STRIVE success
    does not imply every A3 property is violated
```

and:

```text
A3 violation
    does not require native STRIVE collision success
```

### 9.5 Example

A generated near-miss could satisfy:

```text
no polygon collision
```

while violating:

```text
TTC > 1.5 s
```

or:

```text
d_ego > d_min
```

Such a trajectory may be a valid A3 counterexample despite native `adv_failed`.

### 9.6 Objective integration option

A future A3 implementation may replace/augment the crash-distance loss with a differentiable robustness objective:

```text
minimize ρ(τ, φ)
```

if the selected property formalism supports this.

If so, that modified optimizer becomes a distinct A3 search configuration and must not be described as unmodified C-02.

---

## 10. Planner-Specific Falsification

### 10.1 Replay planner

Advantages:

- deterministic ego trajectory;
- simpler search system;
- isolates traffic-side changes;
- easier to reproduce.

Limitation:

- ego does not react to adversarial traffic.

### 10.2 Rule-based planner

Advantages:

- planner responds to changing generated traffic;
- closer to planner-in-the-loop falsification.

Limitations:

- planning logic adds nondifferentiable/heuristic behavior;
- released planner behavior depends on exact configuration and receding-horizon state.

### 10.3 Planner configuration dependence

Every counterexample is scoped to:

```text
planner implementation
planner configuration
planning horizon/update rate
```

### 10.4 Multi-configuration comparison

A3 may compare:

```text
Replay
M-02 default
M-02 tuned
```

but each is a distinct falsification target.

---

## 11. Temporal Semantics

### 11.1 Evaluation horizon

Every specification must define:

```text
t_start
t_end
```

### 11.2 STRIVE timebases

Relevant public timebases:

```text
M-01 / nuScenes prediction:
    0.5 s

M-02 rule-based planner:
    0.2 s
```

### 11.3 Interpolation

A3 must define how trajectories on different timebases are aligned.

Possible policies:

```text
linear interpolation
dense resampling
native-step-only evaluation
analytic segment evaluation
```

### 11.4 Discrete vs continuous time

A sampled property establishes only sampled-time behavior unless the interpolation/continuous-time semantics provide stronger coverage.

### 11.5 First-violation semantics

Record:

```text
earliest evaluator time at which φ becomes false
```

under the chosen time representation.

---

## 12. Vehicle Geometry & Signals

### 12.1 TTC definition

TTC must be explicitly defined.

A simplistic relative-speed formula may be insufficient for turning vehicles.

The exact A3 evaluator is authoritative.

### 12.2 Separation definition

Preferred formal quantity:

```text
minimum distance between vehicle footprints
```

If center distance or circle approximation is used instead, record that choice.

### 12.3 Collision definition

Possible exact A3 choices:

```text
oriented-rectangle intersection
polygon overlap/IoU
five-circle approximation
```

Use one geometry per property version.

### 12.4 Native STRIVE collision approximations

STRIVE uses different collision-related mechanisms in different places, including:

- differentiable circle-based penalties;
- final polygon/IoU-based success tests.

A3 must not silently mix them.

### 12.5 Relative velocity

Optional TTC-support signal:

```text
relative position
relative velocity
closing component
```

### 12.6 Vehicle dimensions

Use D-01/D-02:

```text
length
width
```

for footprint geometry.

### 12.7 Map/drivable-area geometry

Optional map-based specifications need a fixed raster/polygon interpretation and coordinate transform.

---

## 13. Falsification Workflow

### 13.1 Freeze system artifacts

Record:

```text
STRIVE revision
M-01 checkpoint
planner config
C-01/C-02/C-03 config
```

### 13.2 Freeze specification

Record:

```text
property ID/version
thresholds
geometry
time semantics
evaluator hash
```

### 13.3 Select seed scene

Choose a frozen A3-D-01 seed.

### 13.4 Run C-01 initialization

Reproduce the appropriate replay/rule-based initialization procedure.

### 13.5 Run C-02 adversarial search

Generate the primary candidate trace.

A3 may:

- use unmodified C-02;
- add restarts;
- add explicit bounds;
- replace/augment the objective.

The chosen variant must be named.

### 13.6 Optionally run C-03

C-03 provides contextual information about whether STRIVE can find an operational collision-free response.

It is not necessary for every falsification property.

### 13.7 Independently evaluate specification

Compute the A3 property from the saved physical trajectory.

Do not classify a run solely from C-02 loss values.

### 13.8 Confirm and save counterexample

A confirmed counterexample must preserve:

```text
scenario artifact
property trace
evaluator version/hash
violation time/value
planner/model/optimizer provenance
```

---

## 14. Counterexample Handling

### 14.1 Candidate counterexample

Any generated trajectory with:

- native STRIVE collision success;
- negative/violating robustness;
- sampled threshold violation;

is a candidate until independent replay confirms it.

### 14.2 Confirmed counterexample

Requirements:

1. valid serialized trajectory;
2. exact property/version available;
3. independent evaluator completes;
4. property violation reproduced;
5. provenance complete.

### 14.3 Invalid counterexample

Examples:

- nonfinite state;
- missing dimensions required by evaluator;
- inconsistent agent ordering;
- trajectory/hash mismatch;
- map-frame mismatch;
- evaluator exception.

### 14.4 Replay confirmation

Reload the saved D-02/A3 artifact and rerun the property evaluator independently of the optimizer process.

### 14.5 Counterexample minimization

Optional postprocessing can search for:

- smaller latent displacement;
- larger TTC/separation margin violation;
- fewer modified agents;
- earlier violation.

A minimized trace should retain a link to its original counterexample.

### 14.6 Regression retention

Confirmed counterexamples should become persistent regression cases for later:

- planner changes;
- traffic-model changes;
- optimizer changes;
- specification-evaluator changes.

---

## 15. Quantitative Falsification Metrics

### 15.1 Falsification success rate

For a frozen protocol:

```text
confirmed counterexamples
-------------------------
valid completed searches
```

The denominator must exclude or separately report invalid/error runs.

### 15.2 Search time

Record:

```text
wall-clock seconds
optimizer iterations
restart number
```

### 15.3 Time to first violation

Two different quantities may be useful:

```text
search time until a violating candidate is found
trajectory time of first safety violation
```

Do not conflate them.

### 15.4 Minimum TTC

Report with:

```text
value
timestamp
agent pair
TTC definition/version
```

### 15.5 Minimum separation

Report with:

```text
distance
timestamp
agent pair
geometry/version
```

### 15.6 Robustness score

Only report a formal robustness value if the selected specification formalism defines one.

### 15.7 Unique counterexample count

Deduplication policy must be explicit.

Possible keys:

```text
trajectory SHA-256
seed + property + violating agent/time
feature-space clustering
```

---

## 16. Search Robustness & Sensitivity

### 16.1 Initialization sensitivity

Repeat searches from different latent initializations where supported.

### 16.2 Random-seed sensitivity

Use multiple random seeds/restarts and report outcome variance.

### 16.3 Search-budget sensitivity

Compare:

```text
iterations
wall-clock budget
restart count
```

### 16.4 Planner sensitivity

Compare the same property/seed under:

```text
Replay
Rule-based default
Rule-based tuned
```

where appropriate.

### 16.5 Specification-threshold sensitivity

Threshold sweeps can characterize severity/margin, but the primary requirement must be fixed before final evaluation.

### 16.6 Learned-prior sensitivity

Different M-01 checkpoints may expose different falsification regions.

Results are checkpoint-specific.

---

## 17. Validation of the Falsification Model

### 17.1 Reproduce native STRIVE behavior

Before adding A3-specific logic, reproduce native generation on known configs.

### 17.2 Specification-evaluator unit tests

Every evaluator should include:

- clearly satisfying trace;
- exact-boundary trace;
- clearly violating trace;
- zero-relative-speed TTC case;
- non-closing TTC case;
- between-sample geometry case;
- malformed trace.

### 17.3 Geometry validation

Cross-check collision/distance computations on synthetic vehicle poses with known outcomes.

### 17.4 Timebase validation

Verify that:

```text
0.5-s traffic trajectories
0.2-s planner trajectories
```

are aligned exactly as specified.

### 17.5 Saved-artifact replay

Every final counterexample should reproduce after serialization/reload.

### 17.6 Native-vs-external cross-check

Report a cross table:

```text
native STRIVE partition
×
A3 specification outcome
```

This is important evidence because the two notions are intentionally distinct.

---

## 18. Failure Modes

### 18.1 Search local minimum

A real violation may exist but C-02 fails to find it.

### 18.2 Unrealistic learned-prior region

Optimization may exploit imperfections in M-01 and produce a trajectory that is mathematically valid in-model but behaviorally questionable.

### 18.3 Planner-model/configuration mismatch

A counterexample may disappear when:

- planner config changes;
- planner update frequency changes;
- another planner is used.

### 18.4 Specification mismatch

An incorrectly defined TTC or distance metric can generate misleading “violations.”

### 18.5 Temporal aliasing

Checking only discrete samples can miss a collision/near-miss between samples.

### 18.6 Geometry mismatch

Circle approximation, box overlap, polygon IoU, and center distance can disagree near boundaries.

### 18.7 Attack-agent mismatch

The agent selected as the intended attacker may differ from the agent causing the independently measured violation.

### 18.8 C-03 interpretation error

Treating:

```text
sol_failed
```

as proof of no safe response is invalid.

---

## 19. Known Limitations

### 19.1 Falsification incompleteness

The fundamental limitation:

```text
no violation found ≠ property proved
```

### 19.2 Nonconvex optimization

C-02 is gradient-based and nonconvex.

Search outcome can depend on initialization, optimizer settings, and budget.

### 19.3 Learned traffic prior bias

M-01 constrains the explored traffic manifold.

Counterexamples outside that learned manifold may remain undiscovered.

### 19.4 Planner dependence

A3 counterexamples are planner/configuration-specific.

### 19.5 Specification incompleteness

TTC and minimum separation are partial safety requirements.

### 19.6 Discrete-time approximation

Without appropriate interpolation/continuous reasoning, short-duration violations may be missed.

### 19.7 Synthetic counterexamples

STRIVE-generated trajectories are stress tests, not observed accident frequencies.

### 19.8 C-03 incompleteness

C-03's optimizer does not provide a global solvability proof.

---

## 20. Safety & Assurance Interpretation

### 20.1 Meaning of “falsified”

Acceptable wording:

> Specification TTC-01 v1.0.0 is falsified for planner/configuration P by replay-confirmed STRIVE trajectory T generated from seed S.

This means the universal requirement does not hold over the declared system/domain if the counterexample is in scope.

### 20.2 Meaning of “no counterexample found”

Acceptable wording:

> No confirmed violation was found under search configuration Q and budget B.

Do not convert this into a proof statement.

### 20.3 Meaning of native STRIVE success

Native C-02 success is:

```text
collision according to STRIVE's released collision-success semantics
```

It is a strong candidate for a collision-freedom counterexample but not automatically for TTC/separation specifications.

### 20.4 Meaning of C-03 solution success

C-03 success shows that STRIVE found one operationally acceptable alternative under its own criteria.

### 20.5 Scope of a counterexample

Every counterexample is scoped by:

```text
planner
planner config
traffic-model checkpoint
seed
optimizer variant/config
specification/evaluator
time/geometry semantics
```

### 20.6 System-level inference limits

One valid counterexample can refute a universal property over its stated domain.

It does not establish:

- deployment likelihood;
- fleet risk;
- frequency/severity distribution;
- behavior under other planners/configurations.

---

## 21. Reproducibility

### 21.1 STRIVE revision

Required:

```text
repository revision
```

Baseline documented here:

```text
b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d
```

### 21.2 M-01 checkpoint hash

Required:

```text
SHA-256
```

### 21.3 Planner identity/configuration

Replay:

```text
source ego trajectory hash/provenance
```

Rule-based:

```text
M-02 config name + resolved values + hash
```

### 21.4 Optimizer configuration

Store resolved:

```text
C-01
C-02
C-03
```

configuration.

### 21.5 A3-D-01 manifest

Required for final experiments.

### 21.6 Specification registry

Required:

```text
registry hash
property ID/version
```

### 21.7 Evaluator revision

Required:

```text
source revision/hash
runtime configuration
```

### 21.8 Random seeds

Store all random/search seeds that affect generation.

### 21.9 Execution environment

Record:

```text
OS
Python
PyTorch
CUDA
GPU
CPU
solver/falsifier version
```

### 21.10 Companion metadata

```text
metadata/assurance/models/collision_optimizer_falsification.yaml
```

### 21.11 Profiler

```text
tools/profile_collision_optimizer_falsification.py
```

The profiler validates source assumptions and summarizes result manifests. It does not itself perform falsification.

---

## 22. Assurance Evidence & Results

### 22.1 Claim-evidence matrix

Initial state:

| Property | Planner | Seed domain | Evidence | Status |
|---|---|---|---|---|
| TTC-01 | Replay | TBD | none yet | Not run |
| TTC-01 | Rule-based | TBD | none yet | Not run |
| SEP-01 | Replay | TBD | none yet | Not run |
| SEP-01 | Rule-based | TBD | none yet | Not run |
| COLL-01 | Replay | TBD | none yet | Not run |
| COLL-01 | Rule-based | TBD | none yet | Not run |

### 22.2 Confirmed counterexamples

```text
None yet.
```

### 22.3 No-counterexample runs

```text
None yet.
```

### 22.4 Invalid/inconclusive runs

```text
None yet.
```

### 22.5 Residual risk

Even after future falsification runs, residual risk includes:

- unsearched seeds;
- unseen maps/traffic regimes;
- different planner settings;
- unmodeled specifications;
- M-01 representational blind spots;
- search local minima;
- discretization/geometry mismatch.

---

## 23. Relationships

### 23.1 Companion data card

```text
A3-D-01 — STRIVE Collision-Generation Optimizer Falsification Data Card
```

### 23.2 STRIVE generation chain

```text
D-01 → M-01 → C-01 → C-02 → C-03 → D-02
```

### 23.3 Rule-based path

```text
D-01 → M-01 → C-01 → M-02 → C-02 → C-03 → D-02
```

### 23.4 Assurance overlay

```text
D-02 candidate trajectory
        │
        ▼
versioned external safety specification
        │
        ▼
independent evaluator
        │
        ├── satisfaction
        └── violation → A3 counterexample
```

### 23.5 Other assurance approaches

```text
A1 — Verify STRIVE's learned traffic model
A2 — Verify the accident scenario classifier
```

A3 differs because it is fundamentally **counterexample search**, not universal model verification.

---

## 24. Terms of Art

### 24.1 Safety specification

A versioned executable requirement over a trajectory/system trace.

### 24.2 Falsification

Search for a concrete execution that violates a safety specification.

### 24.3 Counterexample

A concrete saved trace that violates the exact versioned property.

### 24.4 Search budget

Finite computational resources allocated to falsification.

### 24.5 Quantitative robustness

A property-specific numerical satisfaction/violation measure defined by the selected formalism.

### 24.6 Native STRIVE success

C-02's released adversarial-collision success outcome.

### 24.7 External specification violation

Failure of the independent A3 safety property.

### 24.8 Replay-confirmed counterexample

A saved candidate whose violation reproduces when reloaded and independently evaluated.

### 24.9 Search completeness

Whether failure to find a violation implies none exists.

For the proposed STRIVE optimization workflow:

```text
search completeness is not established
```

---

## 25. References

1. **Formal Assurance in STRIVE** — project concept document. It proposes expressing AV safety requirements such as TTC and minimum vehicle separation and using STRIVE to search for trajectories that violate them; a violating trajectory serves as a concrete counterexample.

2. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.

3. STRIVE public repository:  
   `https://github.com/nv-tlabs/STRIVE`

4. Existing documentation:
   - A3-D-01 — STRIVE Collision-Generation Optimizer Falsification Data Card
   - D-01 — STRIVE nuScenes Data Card
   - M-01 — STRIVE Main Traffic Model Card
   - M-02 — STRIVE Rule-Based Planner Card
   - C-01 — Initialization Optimization Card
   - C-02 — Adversarial Optimization Card
   - C-03 — Solution Optimization Card
   - D-02 — STRIVE Generated Scenarios Data Card
   - S-01 — STRIVE System Card

---

## 26. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed Approach-3 falsification model-card specification, including STRIVE search boundary, external safety-specification interface, native-vs-external outcome separation, counterexample confirmation, planner-specific semantics, and falsification-result interpretation. |
