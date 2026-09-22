# A1-M-01 — STRIVE Learned Traffic Model Verification Model Card

> **Card ID:** A1-M-01  
> **Card type:** Formal-Assurance Model Card  
> **Status:** Complete verification specification; no formal result claimed yet  
> **Assurance approach:** Verify STRIVE's Learned Traffic Model  
> **Target model:** M-01 — STRIVE Main Traffic Model  
> **Companion data card:** A1-D-01 — STRIVE Learned Traffic Model Verification Data Card  
> **System:** S-01 — STRIVE  
> **Inspected STRIVE revision:** `b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d`

---

## 1. Verification Model Details

### 1.1 Assurance model summary

A1-M-01 specifies how formal assurance should be applied to STRIVE's learned traffic model, M-01.

The target is a graph-conditioned conditional variational traffic model that predicts multi-agent futures. Under the released bicycle-output configuration, the neural decoder predicts longitudinal acceleration and a heading-rate-change quantity, and deterministic kinematic dynamics roll those learned outputs into future vehicle states.

The assurance objective is not merely to test whether sampled trajectories look plausible. It is to state explicit properties and determine, over a precisely bounded input/latent domain, whether:

```text
M-01 always satisfies the property,
a concrete counterexample exists,
or the verifier is inconclusive.
```

### 1.2 Target implementation

Primary implementation:

```text
src/models/traffic_model.py::TrafficModel
```

Supporting learned interaction implementation:

```text
src/models/interaction_net.py::SceneInteractionNet
src/models/interaction_net.py::AgentInteractionConv
```

Deterministic vehicle dynamics:

```text
src/models/common.py::car_dynamics
```

Data/dynamics constants:

```text
src/datasets/utils.py::NUSC_BIKE_PARAMS
```

### 1.3 Target artifact identity

Every assurance result must bind to:

```text
STRIVE repository revision
M-01 checkpoint SHA-256
effective model configuration
normalization constants
bicycle dynamics constants
formal property version
verification-domain version
verifier/tool version
```

A filename such as `traffic_model.pth` is not sufficient artifact identity.

### 1.4 Assurance status

Current status:

```text
verification specification: complete
evidence schema:            complete via A1-D-01
formal property thresholds: not yet frozen
formal verifier:            not yet selected
full formal encoding:       not yet implemented
formal verification runs:   not yet run
verified claims:            none yet
formal counterexamples:     none yet
```

This card therefore defines a defensible verification plan and reporting structure without claiming results that have not been produced.

### 1.5 Verification tool

The project concept leaves the verifier/tool undecided.

A1-M-01 is deliberately verifier-neutral. A future implementation may use an SMT-, MILP-, abstract-interpretation-, reachability-, or neural-network-verification workflow, provided its soundness/completeness limitations are documented.

---

## 2. Purpose & Assurance Role

### 2.1 Primary assurance objective

The primary objective is:

> Establish or falsify selected motion/interaction properties of M-01 for explicitly bounded admissible inputs and latent variables.

The project concept motivates candidate properties including:

- acceleration limits;
- unrealistic speed;
- sharp turning;
- collision-producing trajectories.

### 2.2 Safety relevance

M-01 is safety-relevant within STRIVE because it supplies the learned traffic prior used to:

- generate future traffic;
- constrain C-01/C-02/C-03 latent optimization;
- make adversarial traffic appear plausible under the learned model.

If M-01 can produce extreme or inconsistent motion inside a region treated as plausible by STRIVE, downstream scenario-generation conclusions can be affected.

### 2.3 Relationship to STRIVE

M-01 participates in:

```text
D-01 → M-01 → C-01 → C-02 → C-03 → D-02
```

It provides both:

- learned prior/posterior latent distributions;
- the autoregressive traffic decoder used during scenario optimization.

A1-M-01 verifies only the selected M-01 boundary, not the complete STRIVE pipeline.

### 2.4 Relationship to A1-D-01

A1-D-01 defines:

- source/natural anchors;
- bounded verification domains;
- property registry;
- model/checkpoint provenance;
- counterexample records;
- regression evidence.

A1-M-01 defines:

- the formal model boundary;
- formal properties;
- verifier translation;
- verification workflow;
- result interpretation.

### 2.5 Out-of-scope assurance claims

A1-M-01 alone does not establish:

- M-02 planner safety;
- C-02 adversarial-optimizer correctness;
- C-03 solution correctness;
- real-world autonomous-driving safety;
- that D-02 scenarios have real-world accident probabilities;
- that every physically plausible traffic behavior is represented by M-01.

---

## 3. Verification Target Boundary

### 3.1 Full-model verification option

The most complete boundary is:

```text
past trajectory input
+ vehicle attributes
+ semantic class
+ local map raster
+ graph structure
        │
        ▼
map CNN
past motion encoder
prior SceneInteractionNet
latent z
autoregressive decoder SceneInteractionNet
decoder GRU memory
dynamic map recropping/encoding
kinematic bicycle dynamics
        │
        ▼
future multi-agent trajectory
```

This is closest to the executable inference model but is likely the most difficult formal target.

### 3.2 Decoder-centered verification option

A more tractable assurance boundary freezes the scene encoding:

```text
fixed past feature
fixed map feature
fixed semantics
fixed graph topology
bounded z
        │
        ▼
decoder GNN/MLP
GRU memory
bicycle dynamics
```

This directly studies whether bounded latent variation can cause unsafe learned future controls/trajectories while avoiding verification of the map CNN and prior encoder.

### 3.3 Reduced-subnetwork verification option

A course-scale reduced target may fix:

```text
one/few agents
fixed graph topology
fixed map feature
one decoder step or short unroll
bounded hidden state
bounded z
```

and verify one property such as raw acceleration.

This is acceptable only if the card/result states that the proof applies to the reduced model boundary, not full M-01.

### 3.4 Selected boundary

Not yet finalized.

The project concept explicitly asks whether the complete GNN-based learned component should be verified or whether a smaller component should be analyzed.

Recommended reporting rule:

```text
No verification result may be labeled "M-01 verified"
without naming the exact included/excluded modules.
```

### 3.5 Excluded components

Typical exclusions that must be explicitly recorded include:

- posterior/future encoder when verifying prior-time inference only;
- map CNN when map features are frozen;
- prior network when `z` is treated directly as a bounded input;
- dynamic map recropping for a one-step proof;
- other agents when verifying a single-agent decoder slice;
- PyTorch floating-point semantics when using real arithmetic.

---

## 4. Target Architecture

### 4.1 Local map encoder

M-01's default map encoder is:

```text
Conv2d + GroupNorm + ReLU
```

repeated over six convolutional stages, followed by a linear projection to:

```text
map feature size = 64
```

Released default convolution settings:

```text
kernels: [7, 5, 5, 3, 3, 3]
strides: [2, 2, 2, 2, 2, 2]
filters: [16, 32, 64, 64, 128, 128]
```

### 4.2 Past motion encoder

Default trajectory encoder:

```text
MLP
```

with layers:

```text
input → 128 → 128 → 128 → 64
```

The code also supports a four-layer GRU alternative.

### 4.3 Future motion encoder

The posterior path uses an analogous future-motion encoder.

It is needed during training/reconstruction but not required for prior-only future sampling if the verification boundary starts from the prior or from bounded `z`.

### 4.4 Prior interaction network

The prior is a `SceneInteractionNet`.

It consumes:

```text
past feature
map feature
semantic one-hot
relative graph geometry
```

and outputs:

```text
2 × latent_size
```

split into mean and log-variance, with variance:

```text
exp(logvar)
```

Default latent size:

```text
32
```

### 4.5 Posterior interaction network

The posterior adds the future-motion feature and also returns mean/log-variance.

This network matters for posterior-mean reconstruction or domains centered on posterior latents.

### 4.6 Autoregressive interaction decoder

The decoder is another `SceneInteractionNet`.

Input per node includes:

```text
current motion-memory feature
current map feature
semantic class
latent z
vehicle length/width
```

Default interaction-network behavior includes:

```text
one message-passing round
max aggregation
MLP message/update functions
relative x,y,heading-vector edge features
```

### 4.7 Decoder motion memory

Between future steps, the decoder uses:

```text
3-layer GRU
input size: 4
hidden size: 64
```

The GRU consumes the latest local-frame:

```text
x, y, heading_x, heading_y
```

prediction.

### 4.8 Kinematic bicycle dynamics

With `output_bicycle=True`, the decoder produces two learned channels.

They are unnormalized using:

```text
a mean/std:   0.409074 / 1.045530
ddh mean/std: 0.000046 / 0.075032
```

and passed to `car_dynamics()`.

Released dynamics constants:

```text
dt:      0.5 s
maxs:    50 m/s
maxhdot: 2π rad/s
```

---

## 5. Inputs to the Formal Model

### 5.1 Past agent state

Canonical D-01/M-01 past state:

```text
x
y
heading_x
heading_y
speed
heading_change_rate
```

Default history:

```text
4 steps = 2 s
```

### 5.2 Agent attributes

```text
length
width
```

### 5.3 Semantic class

The main released model is trained on:

```text
car
truck
```

unless another checkpoint/configuration is explicitly selected.

### 5.4 Scene graph

A full formal model may require fixed:

```text
number of agents
edge_index
semantic classes
relative geometry
```

`AgentInteractionConv` transforms source-agent pose into the target agent's local frame before message computation.

### 5.5 Local map input

Default map input is a four-channel local raster crop.

A full verification encodes the raster/CNN.

A reduced verification may freeze the map feature, but that excludes the map encoder from the verified boundary.

### 5.6 Latent variable

Default:

```text
z ∈ R^32 per agent
```

The learned prior is Gaussian and therefore has unbounded support.

Formal verification must replace vague language such as “all plausible z” with an explicit bounded domain, for example:

```text
axis-aligned box
norm ball
bounded Mahalanobis region
fixed prior mean
```

### 5.7 Initial dynamic state

The bicycle rollout starts from the final past state after unnormalization.

The initial values relevant to dynamics are:

```text
x
y
heading
speed
heading-rate
vehicle length
```

---

## 6. Outputs of the Formal Model

### 6.1 Raw decoder outputs

When bicycle output is active:

```text
decoder_out[...,0] = normalized acceleration channel
decoder_out[...,1] = normalized ddh channel
```

These are the learned outputs most directly relevant to learned-control range verification.

### 6.2 Unnormalized dynamic controls

The executable model computes:

```text
a_out   = decoder_a   × 1.045530 + 0.409074
ddh_out = decoder_ddh × 0.075032 + 0.000046
```

Neither learned channel is directly clamped before entering `car_dynamics()`.

### 6.3 Post-dynamics state

`car_dynamics()` updates:

```text
heading-rate
heading
speed
x
y
```

### 6.4 Public future trajectory

The public decoder returns:

```text
x
y
heading_x
heading_y
```

for each agent/future step.

Speed and heading-rate remain internal to bicycle-state rollout rather than part of the returned four-channel trajectory.

### 6.5 Derived safety signals

Formal properties may derive:

- acceleration;
- speed;
- heading-rate;
- displacement;
- curvature/turn proxy;
- vehicle overlap;
- minimum vehicle separation;
- drivable-area occupancy.

The derivation must be part of the formal specification.

---

## 7. Formal Properties

### 7.1 P-A — Acceleration bounds

Project-concept form:

```text
a_min <= a_t(z) <= a_max
```

for every allowed input, latent, selected agent, and verified timestep.

This is a strong candidate for the first verification property because raw `a_out` is learned and is not directly clamped.

**Current threshold status:**

```text
TBD
```

The normalization mean/std are not acceptable substitutes for safety bounds.

### 7.2 P-S — Speed bounds

General form:

```text
s_min <= s_t <= s_max_spec
```

The released implementation already enforces:

```text
0 <= s_t <= 50 m/s
```

by construction.

A proof of exactly this broad interval mostly checks that the formal translation preserves the deterministic clamp. A tighter realism/safety requirement requires an independently defined `s_max_spec`.

### 7.3 P-H — Heading-rate / turning bounds

General form:

```text
|hdot_t| <= hdot_max_spec
```

The released implementation enforces:

```text
|hdot_t| <= 2π rad/s
```

by construction.

A more informative learned-behavior property may instead constrain:

```text
raw ddh_out
```

or a tighter heading-rate/curvature specification.

### 7.4 P-COLL — Vehicle-vehicle collision freedom

General form:

```text
for all i != j and all verified t:
    overlap(B_i(t), B_j(t)) = false
```

The property must freeze one collision semantics.

Possible choices include:

- exact oriented rectangle/polygon overlap;
- STRIVE's five-circle approximation;
- a conservative separation lower bound.

### 7.5 P-ROAD — Drivable-area constraint

General form:

```text
for all verified agents/t:
    vehicle footprint satisfies declared drivable-region predicate
```

This property is more difficult for formal verification because the public model uses raster map crops and dynamically recrops map input as predicted positions change.

### 7.6 P-HEAD — Heading-vector consistency

For the bicycle representation:

```text
heading_x = cos(heading)
heading_y = sin(heading)
```

so:

```text
heading_x^2 + heading_y^2 ≈ 1
```

This is primarily a consistency property of deterministic dynamics/transforms.

### 7.7 Combined properties

Combined claims may use:

```text
P-A ∧ P-S ∧ P-H
```

or:

```text
P-A ∧ P-COLL
```

but individual property outcomes must remain reportable.

### 7.8 Property versioning

Each property requires:

```text
property_id
version
signal
quantifier
lower/upper threshold if applicable
units
temporal scope
agent scope
numeric tolerance
geometry definition if applicable
source/rationale
```

---

## 8. Built-In Dynamics Constraints

### 8.1 Speed clamp

Released `car_dynamics()` computes:

```text
news = clamp(previous_speed + acceleration × dt, 0, max_s)
```

with:

```text
max_s = 50 m/s
```

### 8.2 Heading-rate clamp

Released dynamics computes:

```text
new_hdot = clamp(previous_hdot + ddh × dt, -max_hdot, max_hdot)
```

with:

```text
max_hdot = 2π rad/s
```

### 8.3 Raw acceleration behavior

`a_out` is not clamped.

Its only deterministic influence on speed is filtered by the subsequent speed clamp.

Therefore:

```text
post-state speed bounded
```

does not imply:

```text
learned acceleration bounded
```

### 8.4 Raw ddh behavior

Likewise, raw `ddh_out` is not directly clamped.

Only the resulting heading-rate state is clamped.

### 8.5 Assurance interpretation of construction invariants

The formal result must distinguish:

**construction invariant**

```text
speed <= 50 because code clamps speed
```

from:

**learned-model guarantee**

```text
the neural network never outputs acceleration above a specified bound
```

These support different assurance claims.

---

## 9. Verification Domain

### 9.1 Agent-count bounds

A practical verifier should begin with fixed `N`.

Examples:

```text
N = 1
N = 2
small fixed multi-agent scene
```

Any result is limited to that stated `N` unless a variable-size proof is actually implemented.

### 9.2 Graph-topology assumptions

For fixed-graph verification, store exact:

```text
edge_index
agent ordering
semantic labels
```

A proof for one topology does not quantify over all scene graphs.

### 9.3 State bounds

Every variable state must have explicit physical bounds.

Examples of fields:

```text
past x/y perturbation
speed
heading vector or heading angle
heading-rate
visibility
```

Bounds should come from A1-D-01 domain records.

### 9.4 Vehicle-dimension bounds

If vehicle dimensions are variable, define:

```text
length ∈ [l_min, l_max]
width  ∈ [w_min, w_max]
```

Otherwise freeze them to the natural anchor.

### 9.5 Map-domain assumptions

Permitted options include:

- fixed raster;
- bounded raster perturbation;
- fixed map feature;
- symbolic local road region.

Each option yields a different claim.

### 9.6 Latent-space bounds

Because the Gaussian prior has unbounded support, formal verification must specify a finite domain.

Examples:

```text
z = prior mean
z_i ∈ [μ_i-kσ_i, μ_i+kσ_i]
||diag(σ)^-1 (z-μ)||_2 <= r
```

The last two require tool support and a documented rationale for `k` or `r`.

### 9.7 Temporal horizon

Recommended staged scope:

```text
Stage 1: one decoded/dynamics step
Stage 2: short K-step autoregressive unroll
Stage 3: full 12-step / 6-second rollout if tractable
```

Each result must state its horizon.

---

## 10. Formal Encoding

### 10.1 Neural-network translation

The formal model may need to encode:

- affine layers;
- ReLU;
- LayerNorm;
- GroupNorm;
- convolution;
- max graph aggregation;
- exponential variance transform if prior is included;
- GRU sigmoid/tanh gates;
- trigonometric dynamics/transforms.

This mix makes full exact encoding substantially harder than a feed-forward ReLU network.

### 10.2 Graph encoding

`SceneInteractionNet` uses PyTorch Geometric message passing with:

```text
source-to-target flow
max aggregation
relative local-frame transformation
```

For a fixed graph, message paths can be unrolled into a fixed computation graph.

For variable graph topology, the formal problem is materially more complex.

### 10.3 Recurrent-state encoding

The autoregressive decoder includes a three-layer GRU.

Possible approaches:

- exact bounded unrolling for a fixed number of steps;
- sound nonlinear relaxation;
- freeze the hidden state for a one-step study;
- verify a simplified decoder slice.

The chosen approach must be documented rather than silently replacing the recurrence.

### 10.4 Bicycle-dynamics encoding

Dynamics include:

- addition/multiplication;
- absolute value;
- division by vehicle length;
- clamp/min/max;
- sine/cosine.

A tool that handles only piecewise-linear networks may require:

- verified approximations;
- interval/reachability treatment;
- or moving the property boundary to raw controls.

### 10.5 Map encoding

Full encoding includes six convolution blocks with GroupNorm/ReLU.

A decoder-centered proof may instead treat the 64-D map feature as fixed.

### 10.6 Floating-point abstraction

Potential arithmetic models include:

```text
real arithmetic
interval floating-point abstraction
native float semantics
mixed neural-bound + executable replay
```

If real arithmetic is used, the proof is about the real-valued abstraction unless additional reasoning connects it to float32 execution.

---

## 11. Verification Method

### 11.1 Verification paradigm

Not yet selected.

The selected paradigm must be described as one of, or comparable to:

- exact decision procedure for the encoded fragment;
- sound over-approximate reachability;
- complete/incomplete neural-network verification;
- optimization-based counterexample search;
- falsification only.

### 11.2 Soundness expectations

Every run must declare whether:

```text
verified
```

means a mathematically sound proof over the encoded domain, or merely “no counterexample found.”

Those meanings must never be merged.

### 11.3 Solver / backend

```text
TBD
```

The project concept explicitly requests guidance on choosing a suitable verification/falsification tool.

### 11.4 Timeout / resource policy

A future experiment should fix:

```text
timeout per domain
CPU/GPU allocation
memory limit
solver parallelism
random seed if relevant
```

before final evaluation.

### 11.5 Proof obligations

For each property/domain:

```text
domain constraints
∧ formal M-01 transition/model constraints
∧ negation(property)
```

should be checked according to the selected formal method.

Conceptually:

- infeasibility of the negated property supports verification;
- satisfiability yields a counterexample;
- timeout/unknown yields no conclusion.

### 11.6 Counterexample extraction

Counterexamples must preserve:

- physical input;
- normalized input;
- graph/map context;
- latent value;
- raw outputs;
- rolled trajectory;
- violated timestep;
- verifier numeric output.

---

## 12. Verification Workflow

### 12.1 Freeze target

Record:

```text
repository revision
checkpoint hash
resolved config
normalizers
NUSC_BIKE_PARAMS
```

### 12.2 Choose boundary

Select:

```text
full
decoder-centered
reduced
```

and record excluded modules.

### 12.3 Freeze property

Choose a versioned property from the A1-D-01 registry.

No threshold should be changed after seeing final verification outcomes without incrementing the property version.

### 12.4 Instantiate domain

Select a natural or synthetic A1-D-01 domain.

Record all fixed/variable dimensions.

### 12.5 Validate executable reference

Before formal verification, run the original PyTorch implementation on the domain center/concrete test points to validate preprocessing.

### 12.6 Encode model and property

Build the tool-specific formal representation.

### 12.7 Equivalence-check the encoding

Compare formal-model outputs against PyTorch on concrete points before trusting proof results.

### 12.8 Run verifier

Record:

```text
verified
counterexample
unknown
timeout
error
```

### 12.9 Replay counterexample

If a counterexample exists, execute it in original M-01 whenever technically possible.

### 12.10 Persist assurance evidence

Write the result into A1-D-01-compatible evidence storage and, for confirmed violations, into the regression partition.

---

## 13. Counterexample Handling

### 13.1 Counterexample definition

A valid formal counterexample is:

> a concrete input/latent satisfying all verification-domain assumptions for which the encoded M-01 model violates the exact property.

### 13.2 PyTorch replay

Replay should use:

- same checkpoint;
- same source revision;
- same normalization;
- same graph/map;
- same latent;
- same horizon.

### 13.3 Numeric reconciliation

If solver and PyTorch values differ, report:

```text
formal value
PyTorch value
absolute/relative error
property margin
```

Near-boundary discrepancies should not be silently classified as confirmed violations.

### 13.4 Abstraction-only counterexamples

A violation that appears only in an over-approximate abstraction but cannot be concretized/replayed should be labeled:

```text
spurious / abstraction-only candidate
```

according to the verifier's semantics.

### 13.5 Regression retention

Replay-confirmed violations should be permanent regression cases unless intentionally retired with documented rationale.

---

## 14. Validation of the Formal Model

### 14.1 Model-equivalence checks

Before interpreting proof results, compare the formal model against executable M-01 on concrete points sampled inside each domain.

### 14.2 Layer-level equivalence

Where feasible, validate:

```text
MLP output
GNN message/update output
GRU step
dynamics step
```

separately.

### 14.3 Interaction-network equivalence

Important implementation semantics to preserve include:

```text
max aggregation
source-to-target message flow
relative pose transformed into target frame
zero replacement for NaN relative transforms
```

### 14.4 Dynamics equivalence

Check formal vs PyTorch:

```text
a unnormalization
ddh unnormalization
hdot clamp
heading update
speed clamp
x/y integration
```

### 14.5 Preprocessing equivalence

Check:

- normalization;
- last-past local frame;
- visibility masking;
- semantic encoding;
- vehicle attributes;
- map crop/feature;
- graph topology.

### 14.6 Property-evaluator equivalence

The executable checker used for counterexample replay must implement the same property semantics as the formal formula.

---

## 15. Quantitative Analysis

No formal verification results are populated yet.

The final report should include at minimum:

### 15.1 Domain counts

```text
domains by property
domains by scope
domains by agent count
domains by horizon
```

### 15.2 Outcome counts

```text
verified
counterexample
unknown
timeout
error
```

### 15.3 Runtime

Report:

```text
median
mean
max
timeouts
```

by property/scope.

### 15.4 Domain size

Report:

- number of symbolic scalar variables;
- latent dimension varied;
- interval widths/norm radii;
- number of graph edges;
- rollout steps.

### 15.5 Counterexample replay

Report:

```text
formal counterexamples
replayed
replay-confirmed
spurious/abstraction-only
```

### 15.6 Scalability

Measure how runtime/outcome changes with:

```text
agent count
edge count
latent dimensions
horizon
domain width
```

---

## 16. Robustness & Sensitivity

### 16.1 Domain-width sensitivity

Start from small local domains and systematically widen them.

A transition from verified to counterexample/timeout is useful assurance evidence and should be recorded.

### 16.2 Agent-count sensitivity

Compare:

```text
single-agent
two-agent
small multi-agent
```

domains.

### 16.3 Horizon sensitivity

Compare:

```text
1 step
short K-step
12-step
```

where tractable.

### 16.4 Latent-radius sensitivity

For mean-centered regions, vary radius and report:

```text
largest verified radius
first counterexample radius
timeout boundary
```

only when the chosen method supports such interpretation.

### 16.5 Map-complexity sensitivity

Compare:

```text
fixed map feature
full map encoder
```

or multiple fixed map contexts.

### 16.6 Property-threshold sensitivity

Threshold sweeps may characterize margin, but the primary safety requirement must be frozen independently of the final outcome.

---

## 17. Known Limitations

### 17.1 Full-network tractability

M-01 contains:

```text
CNN
LayerNorm/GroupNorm
GNN max aggregation
GRU recurrence
exp
trigonometric transforms
dynamic map recropping
multi-agent autoregression
```

This is substantially harder than verifying a small feed-forward ReLU model.

### 17.2 Variable graph topology

Formal methods typically work most naturally on fixed computation graphs.

A fixed-topology proof is local to that topology.

### 17.3 Dynamic map recropping

After each predicted step, M-01 updates position and re-encodes a map crop around the new state.

Freezing map features changes the verified model.

### 17.4 Gaussian latent support

The prior distribution is unbounded.

Any finite latent-domain verification covers only its explicitly bounded region.

### 17.5 Arithmetic abstraction

Real-number verification is not automatically bit-exact float32 verification.

### 17.6 Property incompleteness

Passing selected acceleration/speed/turn/collision properties is not equivalent to proving all traffic behavior safe or realistic.

### 17.7 Partial ground truth

nuScenes provides observed trajectories and maps, not formal labels declaring arbitrary generated futures safe/unsafe/solvable.

### 17.8 Learned-prior semantics

A region of high learned prior probability is a learned distributional statement, not a formal physical-safety certificate.

---

## 18. Safety & Assurance Interpretation

### 18.1 Meaning of “verified”

Acceptable wording:

> Property P-A v1.0.0 is verified for checkpoint X over domain D, using formal encoding E and verifier V under arithmetic assumptions A.

Avoid:

```text
STRIVE traffic model is safe
```

unless an independently justified, comprehensive claim actually supports it.

### 18.2 Meaning of “falsified”

A replay-confirmed formal counterexample demonstrates that the stated property does not hold over the stated domain for the exact target artifact.

### 18.3 Meaning of unknown / timeout

```text
No conclusion.
```

Unknown/timeout is neither verified nor falsified.

### 18.4 Construction invariants vs learned guarantees

Code-level clamps may be formally proven, but they should be categorized separately from learned-output guarantees.

### 18.5 System-level limits

A1-M-01 does not prove the safety of:

- the rule-based planner;
- the accident-mode classifier;
- the collision-generation optimizer;
- the complete STRIVE system.

Those are separate assurance targets.

---

## 19. Reproducibility

### 19.1 STRIVE revision

Documented baseline:

```text
b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d
```

### 19.2 Checkpoint hash

Required for every result:

```text
SHA-256
```

### 19.3 Effective configuration

Record at least:

```text
past_len
future_len
map size/layers
feature sizes
latent size
trajectory encoder type
output_bicycle
bicycle parameters
agent categories
```

### 19.4 Verification specification

Record:

```text
property registry hash
property ID/version
domain manifest hash
```

### 19.5 Verification data

Companion:

```text
A1-D-01
```

### 19.6 Toolchain

Once selected:

```text
verifier
backend solver
versions
encoding scripts
numeric assumptions
```

### 19.7 Execution environment

Record:

```text
OS
CPU/GPU
RAM
Python
PyTorch
verifier runtime
```

### 19.8 Companion metadata

```text
metadata/assurance/models/traffic_model_verification.yaml
```

### 19.9 Profiler

```text
tools/profile_traffic_model_verification.py
```

The profiler is intentionally static/result-oriented: it verifies M-01 source invariants and summarizes assurance-result JSONL if supplied. It does not itself perform formal verification.

---

## 20. Assurance Evidence & Results

### 20.1 Claim-evidence matrix

Initial state:

| Claim | Domain | Evidence | Status |
|---|---|---|---|
| P-A acceleration bounds | TBD | none yet | Not run |
| P-S speed bounds | TBD | construction clamp known; formal run not performed | Not run |
| P-H heading-rate / turn bounds | TBD | construction clamp known; formal run not performed | Not run |
| P-COLL collision freedom | TBD | none yet | Not run |
| P-ROAD drivable-area | TBD | none yet | Not run |

### 20.2 Verified claims

```text
None yet.
```

### 20.3 Falsified claims

```text
None yet.
```

### 20.4 Inconclusive claims

No formal runs have been performed, so the current state is:

```text
not evaluated
```

rather than verifier `unknown`.

### 20.5 Residual risk

Even after future verification, residual risk will include:

- unverified input regions;
- unverified graph topologies;
- latent regions outside bounds;
- properties not encoded;
- arithmetic/model abstraction gaps;
- downstream STRIVE components.

---

## 21. Relationships

### 21.1 Target model

```text
M-01 — STRIVE Main Traffic Model
```

### 21.2 Companion assurance data card

```text
A1-D-01 — STRIVE Learned Traffic Model Verification Data Card
```

### 21.3 System relationship

```text
S-01 STRIVE
  │
  └──► M-01 Main Traffic Model
          │
          ├──► A1-D-01 Verification Data / Evidence
          │
          └──► A1-M-01 Formal Verification Model
```

### 21.4 Other assurance approaches

The project concept defines two additional directions:

```text
Approach 2 — Verify the accident scenario classifier
Approach 3 — Specification-driven falsification of the collision-generation optimizer
```

Those assurance targets are separate from A1-M-01.

---

## 22. Terms of Art

### 22.1 Verification target

The exact executable artifact and source boundary being analyzed.

### 22.2 Formal model

The mathematical/tool encoding of the selected verification target.

### 22.3 Verification domain

The explicitly constrained set of inputs/latents quantified by the property.

### 22.4 Property

A versioned predicate over inputs, raw learned outputs, states, trajectories, or geometry.

### 22.5 Construction invariant

A bound established by deterministic code, such as a clamp, independently of what the neural network outputs.

### 22.6 Counterexample

A concrete in-domain assignment violating the property.

### 22.7 Replay-confirmed counterexample

A formal counterexample reproduced by the original M-01 PyTorch implementation under the stated tolerance.

### 22.8 Abstraction gap

Any semantic difference between formal encoding and original executable M-01.

---

## 23. References

1. **Formal Assurance in STRIVE** — project concept document. It proposes formal assurance of M-01 using properties such as bounded acceleration and checks for unsafe sharp turns, unrealistic speeds, and collisions. It also leaves the verifier and the choice between full-GNN and reduced-component verification open.

2. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.

3. STRIVE public repository:  
   `https://github.com/nv-tlabs/STRIVE`

4. Primary implementation:
   - `src/models/traffic_model.py`
   - `src/models/interaction_net.py`
   - `src/models/common.py`
   - `src/datasets/utils.py`
   - `src/losses/traffic_model.py`

5. Existing documentation:
   - M-01 — STRIVE Main Traffic Model Card
   - D-01 — STRIVE nuScenes Data Card
   - A1-D-01 — STRIVE Learned Traffic Model Verification Data Card
   - S-01 — STRIVE System Card

---

## 24. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed Approach-1 formal-assurance model-card specification, including M-01 verification boundaries, formal properties, construction invariants, encoding/equivalence requirements, counterexample replay, and claim-evidence reporting. |
