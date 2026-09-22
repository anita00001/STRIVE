# A1-D-01 — STRIVE Learned Traffic Model Verification Data Card

> **Card ID:** A1-D-01  
> **Card type:** Formal-Assurance Data Card  
> **Status:** Complete specification; verification corpus not yet materialized  
> **Assurance approach:** Verify STRIVE's Learned Traffic Model  
> **Target:** M-01 — STRIVE Main Traffic Model  
> **System:** S-01 — STRIVE  
> **Primary evidence sources:** STRIVE source code, nuScenes observations/maps, exact M-01 artifact/configuration, formal property specifications, and verification-generated counterexamples

---

## 1. Dataset Summary

### 1.1 Dataset / evidence-set name

**STRIVE Learned Traffic Model Verification Evidence Set**

This card specifies the data and evidence required to formally analyze M-01, STRIVE's learned traffic prior.

It is not a claim that a completed formal-verification corpus already ships with STRIVE. The public repository provides the model implementation, nuScenes data pipeline, checkpoints/configuration conventions, and empirical collision/plausibility metrics; the assurance-specific case set and formal property registry must still be instantiated for the project.

### 1.2 Assurance purpose

The evidence set supports the question:

> For a precisely bounded family of STRIVE traffic-model inputs and latent variables, do M-01 outputs satisfy explicitly stated motion and interaction properties?

The initial project concept identifies candidate properties involving:

- acceleration limits;
- unrealistic speed;
- sharp turning;
- vehicle collisions.

The evidence set makes those concepts reproducible by recording the exact model artifact, source scene/domain, property version, verifier result, and any counterexample.

### 1.3 Verification target

Primary target:

```text
M-01 — STRIVE Main Traffic Model
src/models/traffic_model.py::TrafficModel
```

Documented repository revision:

```text
b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d
```

Default released architecture relevant to this card:

```text
past steps:        4
future steps:      12
dt:                0.5 s
state size:        6
latent size:       32
bicycle output:    enabled
raw decoder size:  2
future output:     x, y, heading_x, heading_y
```

### 1.4 Dataset role

This evidence set is intended to serve four roles:

1. **domain definition** — enumerate or parameterize admissible verification inputs;
2. **property evaluation** — provide reference trajectories/maps and derived physical signals;
3. **formal-result recording** — preserve SAT/UNSAT/unknown/timeout-style verifier outcomes without conflating them with empirical testing;
4. **counterexample regression** — retain violating inputs so future model/checkpoint changes can be retested.

### 1.5 Dataset status

```text
card/specification: complete
verification corpus: not yet materialized
formal verifier: not yet selected
formal thresholds: not yet frozen
```

This status matches the project concept: source code and nuScenes are available, but the verification tool and exact verification scope still need to be selected.

---

## 2. Assurance Claim Context

### 2.1 Top-level assurance claim

The intended claim pattern is:

```text
For every model input and latent value within verification domain D,
the selected M-01 output property φ holds over the stated future horizon.
```

The claim is meaningful only when all of the following are fixed:

```text
model/checkpoint
input domain D
latent domain
preprocessing
future horizon
property φ
numeric tolerances
verifier/model abstraction
```

### 2.2 Candidate verified properties

The concept document motivates checking whether predicted traffic remains within safe and realistic limits, especially:

```text
P-A     acceleration within [a_min, a_max]
P-S     speed within [s_min, s_max]
P-H     bounded heading-rate / turning behavior
P-COLL  no prohibited vehicle-vehicle collision
P-ROAD  no prohibited departure from drivable area
```

These are candidate assurance properties. Except for implementation clamps described below, the public STRIVE release and project concept do not supply final formal thresholds for all properties.

### 2.3 Supported subclaims

Depending on the selected verifier and abstraction, A1-D-01 can support claims such as:

- a local input region around one recorded scene is property-safe;
- a bounded latent region for one fixed scene is property-safe;
- a property is violated by a concrete M-01 counterexample;
- a post-dynamics invariant follows from implementation clamping;
- a bounded subnetwork has a verified output range.

### 2.4 Unsupported claims

This evidence set does not, by itself, establish:

- universal real-world traffic safety;
- safety outside the defined verification domain;
- planner safety;
- C-02/C-03 correctness;
- calibrated crash probability;
- that a STRIVE-generated scenario is formally “solvable”;
- that empirical absence of violations is a proof.

### 2.5 Evidence interpretation

Use the following separation:

```text
formal proof / verified:
    property established over the encoded mathematical domain

formal counterexample:
    a concrete in-domain input satisfying the verifier model but violating φ

empirical pass:
    sampled case did not violate φ; not a universal proof

empirical violation:
    replayed M-01 output violates φ; useful counterexample evidence

unknown / timeout:
    verifier did not establish either result
```

---

## 3. Verification Scope

### 3.1 Model boundary

The project should explicitly choose one of these scopes:

**Scope A — full M-01 inference path**

```text
map CNN
+ past motion encoder
+ prior GNN/MLP
+ latent z
+ autoregressive interaction decoder
+ GRU memory
+ bicycle dynamics
```

**Scope B — decoder-centered verification**

```text
fixed encoded scene features
+ bounded z
+ decoder GNN/MLP
+ GRU memory
+ bicycle dynamics
```

**Scope C — smaller network/property slice**

Examples:

```text
one decoded step
one/few agents
fixed graph topology
fixed map encoding
selected output channel
```

The project concept explicitly leaves open whether to verify the complete GNN-based learned component or a smaller analyzable subset.

### 3.2 Neural components in scope

M-01 contains:

- local map encoder: CNN;
- past motion encoder: MLP by default, GRU alternative;
- future motion encoder: MLP by default, GRU alternative;
- prior interaction network: GNN + MLP;
- posterior interaction network: GNN + MLP;
- autoregressive interaction decoder: GNN + MLP;
- decoder motion memory: GRU.

Only components actually included in the selected verification boundary should be represented in A1-D-01 cases.

### 3.3 Kinematic dynamics in scope

With released bicycle output enabled, the decoder produces two normalized channels that are unnormalized as:

```text
a_out   = decoder_a   × 1.045530 + 0.409074
ddh_out = decoder_ddh × 0.075032 + 0.000046
```

The implementation passes these into `car_dynamics()`.

Important implementation distinction:

- `a_out` is acceleration input and is **not directly clamped**;
- `ddh_out` updates heading-rate (`hdot`);
- resulting speed is clamped to `[0, 50] m/s`;
- resulting `hdot` is clamped to `[-2π, 2π]`.

Therefore “verify acceleration bounds” targets learned raw control behavior more directly than merely proving the post-dynamics speed clamp.

### 3.4 Input-space boundary

Every verification result must state bounds for all variable inputs, including as applicable:

- number of agents;
- graph topology;
- semantic categories;
- past trajectory state;
- visibility masks;
- vehicle dimensions;
- map crop / map encoding;
- latent variable `z`;
- initial speed and heading-rate;
- any fixed/external-agent future.

Unbounded “for all inputs” language is not acceptable unless the verifier actually encodes an unbounded domain and the network/property permits it.

### 3.5 Output-space boundary

Potential evidence signals include:

```text
raw decoder control:
    acceleration a
    heading-rate acceleration ddh

post-dynamics state:
    x
    y
    heading_x
    heading_y
    speed
    heading-rate

derived:
    acceleration magnitude
    turn/curvature proxy
    pairwise separation
    collision status
    drivable-area status
```

### 3.6 Temporal scope

Released M-01 defaults:

```text
dt = 0.5 s
12 future steps
6 s default prediction horizon
```

The evidence record must state whether a property applies:

- one step;
- every step through 6 seconds;
- another explicitly configured `nfuture`.

---

## 4. Data Sources

### 4.1 STRIVE source code

Source code is normative for the verified implementation.

Primary files:

```text
src/models/traffic_model.py
src/models/common.py
src/models/interaction_net.py
src/datasets/utils.py
src/datasets/nuscenes_dataset.py
src/losses/traffic_model.py
src/utils/transforms.py
```

### 4.2 nuScenes dataset

nuScenes contributes observed:

- vehicle trajectories;
- dimensions;
- semantic categories;
- maps.

These observations anchor physically meaningful model inputs and permit comparison between model futures and recorded futures.

### 4.3 D-01 relationship

A1-D-01 derives its natural-scene representation from D-01.

Primary released M-01 data configuration:

```text
categories: car, truck
past:       4 × 0.5 s = 2 s
future:     12 × 0.5 s = 6 s
```

Canonical state:

```text
x, y, heading_x, heading_y, speed, heading_change_rate
```

Attributes:

```text
length, width
```

### 4.4 M-01 configuration/checkpoint

Every verification case set must bind to:

```text
checkpoint SHA-256
model/config SHA-256
repository revision
normalization constants
bicycle parameters
```

A result without this binding is not sufficient assurance provenance.

### 4.5 Verification-generated samples

Formal tools or falsifiers may create new inputs that are not observed nuScenes scenes.

Such inputs must be tagged as one of:

```text
bounded_perturbation
solver_counterexample
falsifier_counterexample
boundary_case
regression_case
synthetic_domain_sample
```

and preserve their parent case/domain if one exists.

---

## 5. Ground Truth & Reference Evidence

### 5.1 Recorded trajectory ground truth

nuScenes trajectories are observational ground truth for what happened in recorded scenes.

They can support:

- reconstruction error checks;
- empirical ranges;
- local-domain anchoring;
- plausibility comparison.

They do not define all safe possible futures.

### 5.2 Map ground truth

nuScenes maps provide recorded/map-semantic evidence for:

- local drivable area;
- road/lane context;
- map crop construction.

Map-based assurance must state the exact representation used by the property checker.

### 5.3 Physical / specification bounds

Formal thresholds should be treated as a separate artifact from observed-data statistics.

Examples:

```text
a_min / a_max
speed bound
heading-rate bound
minimum separation
drivable-area tolerance
```

They may come from:

- project safety requirements;
- vehicle physical limits;
- domain-expert requirements;
- intentionally conservative research assumptions.

### 5.4 Missing formal ground truth

There is no nuScenes label stating:

```text
this M-01-generated future is formally safe
```

or:

```text
this STRIVE-generated scenario is formally solvable
```

The project concept explicitly identifies this as partial ground truth.

### 5.5 Operational labels vs formal labels

Do not treat STRIVE's existing empirical thresholds as automatically equivalent to formal safety requirements.

For example, the traffic-model evaluation code contains operational collision constants:

```text
VEH_COLL_THRESH = 0.02
ENV_COLL_THRESH = 0.05
```

Those values may be reused only if the assurance specification explicitly adopts and justifies them.

---

## 6. Verification Input Schema

Each evidence record should contain at least the following logical fields.

### 6.1 Identity and provenance

```yaml
case_id: string
case_kind: natural | bounded_perturbation | boundary_case | counterexample | regression
source_dataset: nuscenes | synthetic
source_split: train | val | test | null
source_scene_id: string | null
source_sample_id: string | null
parent_case_id: string | null
```

For synthetic/counterexample cases, `source_scene_id` may be null if no natural parent exists.

### 6.2 Model identity

```yaml
repository_revision: string
checkpoint_sha256: string
config_sha256: string
model_output_bicycle: true
latent_size: 32
```

### 6.3 Scene structure

```yaml
num_agents: integer
map_name: string
agent_categories: [string, ...]
edge_index: optional graph representation
batch_or_scene_index: optional
```

### 6.4 Physical agent input

Canonical unnormalized form:

```text
past_state[N,4,6]
past_visibility[N,4]
length_width[N,2]
semantics[N,C]
```

The unnormalized representation should be retained even when the verifier consumes normalized tensors.

### 6.5 Map representation

Record either:

- exact model raster input;
- source map identifier plus reproducible crop parameters;
- fixed encoded map feature, if Scope B/C verifies only downstream components.

### 6.6 Latent variable / latent domain

Depending on assurance scope:

```yaml
z:
  mode: concrete | interval | norm_ball | fixed_prior_mean | sampled
  center: ...
  lower: ...
  upper: ...
  radius: ...
```

Latent-domain choice is part of the claim, not a sampling convenience.

### 6.7 Numeric domain

Every variable input must include or reference:

```text
lower bound
upper bound
units
normalization state
precision
```

---

## 7. Verification Output Schema

### 7.1 Raw neural outputs

When possible, capture raw decoder outputs before dynamics:

```text
decoder_out[...,0] → normalized acceleration channel
decoder_out[...,1] → normalized ddh channel
```

and the unnormalized:

```text
a_out
ddh_out
```

These signals are important because downstream clamps can hide extreme learned outputs.

### 7.2 Rolled-out vehicle state

Store or derive:

```text
future_xyh[N,T,4]
speed[N,T]
heading_rate[N,T]
```

for the exact verified/model-replayed future.

### 7.3 Derived verification signals

Examples:

```text
min/max acceleration
min/max speed
max absolute heading-rate
minimum pairwise vehicle separation
vehicle-collision flag
environment-collision flag
heading-vector norm error
```

### 7.4 Formal result

Recommended fields:

```yaml
property_id: string
property_version: string
verifier: string
verifier_version: string
status: verified | counterexample | unknown | timeout | error
runtime_seconds: float
numeric_tolerance: float
```

Use the vocabulary supported by the eventual verifier while preserving these semantics.

### 7.5 Counterexample payload

A counterexample record should preserve:

```text
full bounded-domain definition
concrete violating input
concrete z
model raw controls if available
rolled-out trajectory
violated timestep
violated agents
property expression/version
replay result in original PyTorch M-01
```

A counterexample that cannot be replayed against the original implementation should be marked as an abstraction-only counterexample until reconciled.

---

## 8. Candidate Formal Properties

### 8.1 P-A — Acceleration bounds

Conceptual property:

```text
for all allowed inputs and z:
    a_min <= a_t(z) <= a_max
```

for every verified agent/timestep.

The project concept explicitly proposes this form.

**Threshold status:** not yet fixed.

Do not use M-01's acceleration normalization mean/std as safety bounds. They are normalization statistics, not specifications.

### 8.2 P-S — Speed bounds

Possible post-dynamics property:

```text
s_min <= s_t <= s_max
```

The released bicycle dynamics already clamps:

```text
0 <= s_t <= 50 m/s
```

Thus verifying exactly that range mainly verifies implementation translation/correctness rather than learned behavioral realism.

A tighter safety/realism speed property requires independently justified bounds.

### 8.3 P-H — Heading-rate / turn bounds

Possible property:

```text
|hdot_t| <= hdot_max_spec
```

The released bicycle dynamics clamps `hdot` to:

```text
[-2π, 2π]
```

Again, that implementation bound is not necessarily an appropriate realism bound.

An assurance project may instead verify:

- a tighter `hdot` requirement;
- raw `ddh_out`;
- derived curvature/lateral behavior.

### 8.4 P-COLL — Vehicle-vehicle collision

Possible property:

```text
for all distinct agents i,j and all t:
    overlap(vehicle_i(t), vehicle_j(t)) = false
```

The exact geometry must be fixed in the property specification.

Options include:

- STRIVE's differentiable five-circle approximation;
- final oriented-box/polygon overlap;
- conservative minimum-separation bound.

Do not mix geometries within one reported property.

### 8.5 P-ROAD — Drivable-area constraint

Possible property:

```text
vehicle footprint remains within the allowed drivable region
```

or a stated tolerated overlap threshold.

Formalization requires either:

- symbolic/polygonal map constraints;
- a sound abstraction of the raster map;
- a locally fixed drivable region.

### 8.6 P-HEAD — Heading-vector validity

For rolled-out bicycle output:

```text
heading_x^2 + heading_y^2 = 1
```

up to numeric tolerance.

Because the vector is produced from angle representation, this is primarily an implementation consistency property.

### 8.7 Combined properties

A final assurance claim may combine properties:

```text
P-A ∧ P-S ∧ P-H
```

or:

```text
P-A ∧ P-COLL
```

but the verifier result should still preserve per-property diagnostics.

---

## 9. Property Parameterization

### 9.1 Property registry

Each property should live in a versioned YAML or JSON registry such as:

```yaml
property_id: P-A
version: 1.0.0
signal: raw_acceleration
quantifier: forall
temporal_scope: all_verified_steps
lower: TBD
upper: TBD
units: m/s^2
tolerance: TBD
source: course/project safety specification
```

### 9.2 Source of bounds

Every non-code-derived threshold must document its source.

Allowed source categories:

```text
formal project requirement
physical platform constraint
domain-expert requirement
published standard/reference
empirical design choice
```

Empirical design choices must not be presented as externally established safety limits.

### 9.3 Units

Canonical physical units:

```text
position:       m
speed:          m/s
acceleration:   m/s²
heading-rate:   rad/s
ddh:            rad/s² under the released dynamics interpretation
time:           s
distance:       m
```

### 9.4 Fixed vs context-dependent thresholds

If thresholds depend on:

- vehicle class;
- current speed;
- road geometry;
- timestep;
- relative traffic state;

the property record must capture the rule, not only the evaluated numeric result.

### 9.5 Conservative margins

Any margin used for floating-point/verifier mismatch must be explicit:

```yaml
verification_margin:
replay_tolerance:
geometry_margin:
```

---

## 10. Sampling & Case Construction

### 10.1 Natural nuScenes anchors

Use recorded nuScenes scenes as physically meaningful centers for bounded domains.

Recommended assurance anchors should come from a split not used to fit M-01 whenever the checkpoint/training provenance permits this.

### 10.2 Boundary-value cases

Prioritize scenes near the property boundaries:

- high observed speed;
- high acceleration/deceleration;
- large heading-rate;
- close vehicle separation;
- map-edge proximity;
- dense multi-agent interaction.

### 10.3 Perturbed cases

For local verification, define explicit perturbation boxes or norm balls around natural inputs.

Example conceptual form:

```text
x' ∈ [x-εx, x+εx]
speed' ∈ [s-εs, s+εs]
z ∈ [z0-εz, z0+εz]
```

The exact bounds are part of the formal claim and must be stored.

### 10.4 Latent-space cases

Reasonable starting modes include:

```text
prior mean
sampled z
posterior mean for reconstruction anchors
bounded neighborhood around prior/posterior mean
```

A Gaussian prior has unbounded support, so “verify all z from the Gaussian” is not equivalent to a finite box proof. A bounded latent assurance region must be defined explicitly.

### 10.5 Counterexample-directed cases

After a violation is found:

1. replay it in original M-01;
2. store it in the regression partition;
3. optionally create nearby cases to characterize the violation region;
4. keep the original property/specification version immutable.

### 10.6 Rare / safety-critical cases

The corpus should intentionally include:

- close-following traffic;
- crossing trajectories;
- head-on geometry where available;
- fast approach;
- sharp-turn contexts;
- dense intersections;
- road-boundary cases.

This is coverage engineering, not evidence that such cases match real-world frequency.

---

## 11. Partitioning

### 11.1 Development partition

Used for:

- encoding the network;
- debugging preprocessing equivalence;
- selecting tractable domains;
- calibrating solver settings;
- validating property evaluators.

No headline assurance result should rely only on development cases.

### 11.2 Verification partition

A frozen set of scenes/domains used for final reported results.

Recommended properties:

```text
immutable case IDs
immutable property versions
checkpoint hash fixed
no threshold tuning after observing final outcomes
```

### 11.3 Regression partition

Contains:

- formal counterexamples;
- empirically replayed violations;
- previously difficult/timeout domains.

Regression evidence is especially useful after any model or property-encoding change.

### 11.4 Independence from M-01 training

Where possible, source natural anchors from the held-out STRIVE test split rather than training scenes.

If train/validation scenes are used for tractability or debugging, tag them explicitly; do not describe them as independent held-out verification evidence.

---

## 12. Data Transformations

### 12.1 STRIVE normalization

The canonical assurance record should preserve physical unnormalized values.

A generated verifier input may additionally store exact normalized tensors produced with the M-01/D-01 normalizers.

### 12.2 Coordinate frames

M-01 transforms past/future trajectories into the local frame of the last past state for motion encoding.

Formal encoding must document whether it verifies:

- the original global input plus frame transform;
- already-transformed local tensors;
- fixed encoded motion features.

### 12.3 Map preprocessing

M-01 extracts a local raster crop and passes it through the map CNN.

For tractability, a reduced-scope proof may freeze:

```text
map crop
or
map feature vector
```

but must say that the excluded map encoder is not verified.

### 12.4 Graph construction

If graph topology is fixed for a local verification case, store:

```text
agent ordering
edge_index
semantic labels
batch mapping
```

A result on a fixed graph does not automatically cover arbitrary numbers/topologies of agents.

### 12.5 Verifier-specific abstraction

If the chosen tool cannot directly encode the full CNN/GNN/GRU stack, record all abstractions such as:

```text
fixed map feature
fixed graph
one-step decoder
bounded hidden state
piecewise-linear relaxation
floating-point to real-number abstraction
```

### 12.6 Precision / datatype

Record:

```text
original PyTorch dtype
verification numeric type
solver precision
replay dtype
```

Formal results under real arithmetic and float32 execution are related but not identical claims.

---

## 13. Quantitative Dataset Profile

The following quantities are intentionally **not populated yet**, because the assurance corpus has not been materialized.

### 13.1 Required corpus statistics

The profiler should report:

```text
total cases
cases by partition
cases by kind
natural vs synthetic/counterexample
unique source scenes
agent-count distribution
map distribution
category distribution
property counts
verification status counts
counterexample counts
runtime distribution
```

### 13.2 Motion-domain statistics

For physical unnormalized inputs/outputs:

```text
speed min/max/quantiles
acceleration min/max/quantiles
heading-rate min/max/quantiles
pairwise separation min
```

### 13.3 Domain-width statistics

For bounded verification cases:

```text
interval width by state variable
latent interval/norm radius
number of variable dimensions
fixed vs symbolic dimensions
```

### 13.4 Counterexample replay rate

Report:

```text
formal counterexamples found
counterexamples replayed in PyTorch
replay-confirmed violations
abstraction-only violations
```

These categories must remain distinct.

---

## 14. Coverage Strategy

### 14.1 Input-domain coverage

Coverage should be reported across:

- speed;
- heading-rate;
- number of agents;
- relative distances;
- map locations;
- scene density;
- semantic category.

### 14.2 Latent-space coverage

If `z` is variable, report:

- chosen latent-domain construction;
- radius/interval widths;
- distance from prior mean;
- whether the region is centered at mean/sample/posterior.

Do not convert Gaussian likelihood into a formal coverage percentage without an explicit probabilistic argument.

### 14.3 Temporal coverage

Report which future steps each property covers.

Example:

```text
one-step verification
12-step autoregressive verification
partial 1–K-step proof
```

### 14.4 Property-boundary coverage

Track how many domains are:

```text
far from threshold
near threshold
crossing threshold empirically
formal counterexample
```

### 14.5 Architectural coverage

State which components are actually inside the verifier:

```text
map CNN
past MLP/GRU
GNN prior
latent input
decoder GNN
decoder GRU
bicycle dynamics
```

---

## 15. Validation & Quality Assurance

### 15.1 Schema validation

Reject records with:

- duplicate `case_id`;
- invalid partition/kind;
- missing model hash;
- missing property ID/version;
- inconsistent array shapes;
- unknown units.

### 15.2 Physical range sanity

Before verification, flag impossible or suspicious source values.

These are data-quality checks, not formal proof.

### 15.3 Reproduction of M-01 inputs

For every natural anchor, reproduce the exact M-01 input tensors from the original STRIVE pipeline and compare them with the serialized verification representation.

### 15.4 Property-evaluator validation

Property calculators should have unit tests with:

- obvious safe cases;
- boundary-equality cases;
- obvious violations;
- geometry edge cases.

### 15.5 Counterexample replay

Every formal counterexample should be replayed against the original PyTorch model whenever technically possible.

Record:

```text
replay_matches
replay_violates
numeric_difference
```

### 15.6 Clamp-awareness validation

The assurance pipeline must distinguish:

```text
raw network output
post-dynamics state
```

so a post-clamp property cannot be mistaken for a neural-output guarantee.

---

## 16. Known Limitations

### 16.1 Partial ground truth

Recorded trajectories and maps are observations, not formal labels of all safe behavior.

### 16.2 Finite data vs universal verification

A finite collection of sampled cases is testing evidence.

A formal claim requires proof over an explicitly bounded domain.

The data card supports both workflows but must not merge their conclusions.

### 16.3 Full-model tractability

The complete M-01 stack includes CNNs, GNNs, MLPs, GRU recurrence, dynamic map recropping, multi-agent autoregression, and kinematic dynamics.

A practical course project may need to verify a reduced component/domain.

### 16.4 Dynamic map dependence

In autoregressive decoding, M-01 recrops/re-encodes the map around predicted positions between future steps.

Freezing map features changes the verified model boundary.

### 16.5 Variable graph structure

Scene size and graph topology vary across nuScenes cases.

Many neural verifiers require fixed tensor shapes/topology, so each verified domain may cover one fixed graph.

### 16.6 Gaussian latent support

The learned prior has unbounded Gaussian support.

Any finite latent box/norm-ball proof covers only the stated latent region.

### 16.7 Clamp-dominated properties

The released dynamics enforce broad speed and heading-rate clamps.

Proving those exact bounds may add limited assurance about the learned network itself.

### 16.8 Property incompleteness

Even successful verification of acceleration/speed/turn/collision properties does not imply total behavioral safety.

---

## 17. Safety & Assurance Interpretation

### 17.1 Meaning of a verified property

A successful proof supports only:

```text
specified model abstraction
+ specified checkpoint
+ specified input/latent domain
+ specified property
+ specified arithmetic/solver assumptions
```

### 17.2 Meaning of a counterexample

A counterexample is strong evidence when:

1. it lies within the declared domain;
2. it violates the exact property;
3. it replays against the original M-01 implementation.

### 17.3 Meaning of unknown / timeout

Unknown or timeout means:

```text
no conclusion
```

It must not be counted as verified or unsafe.

### 17.4 Empirical vs formal evidence

Keep separate fields and summaries for:

```text
formal verification status
empirical replay status
observational ground truth
```

### 17.5 System-level inference limits

M-01 verification does not verify:

- M-02;
- C-01/C-02/C-03;
- D-02 scenario usefulness;
- planner safety;
- S-01 end-to-end safety.

---

## 18. Reproducibility & Provenance

### 18.1 Repository revision

Required:

```text
repository: nv-tlabs/STRIVE
revision: b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d
```

or the exact revision actually verified.

### 18.2 Checkpoint hash

Required:

```text
SHA-256 of traffic_model.pth
```

Do not identify a checkpoint only by filename.

### 18.3 Configuration hash

Hash the effective M-01 configuration or save the resolved configuration verbatim.

### 18.4 nuScenes provenance

Record:

```text
version
split
scene/sample identifiers
category filter
past/future lengths
map revision/files where practical
```

### 18.5 Property specification version

Every result must reference a versioned property.

Changing a threshold produces a new property version.

### 18.6 Verifier provenance

Once selected:

```text
tool
tool version
solver/backend
command/config
timeout
numeric mode
```

### 18.7 Randomness

Record seeds for:

- latent sampling;
- case sampling;
- falsification;
- any randomized verifier heuristic.

### 18.8 Generated-case lineage

For every non-natural case:

```text
parent case
transformation/generator
parameters
property targeted
run ID
```

---

## 19. Relationships

### 19.1 Upstream

```text
D-01 — STRIVE nuScenes Data
M-01 — STRIVE Main Traffic Model
S-01 — STRIVE System Card
```

### 19.2 Assurance approach

```text
Approach 1
Verify STRIVE's Learned Traffic Model
```

### 19.3 Companion assurance model card

Planned:

```text
A1-M-01 — STRIVE Learned Traffic Model Verification Model Card
```

A1-D-01 specifies the evidence/domain representation; A1-M-01 should specify the verification method, formal model boundary, properties, tool encoding, and assurance argument.

### 19.4 Relationship to existing D-01

D-01 documents the data actually consumed by STRIVE.

A1-D-01 documents the **assurance evidence derived from or anchored to D-01**, including bounded domains and counterexamples that do not exist in the original dataset.

---

## 20. Terms of Art

### 20.1 Verification domain

The mathematically defined set of admissible model inputs over which the property is quantified.

### 20.2 Property specification

A versioned predicate over model inputs, raw controls, trajectories, or derived geometry.

### 20.3 Counterexample

An in-domain input that causes the modeled system to violate the property.

### 20.4 Natural anchor

A recorded nuScenes case used as the center/reference for a verification domain.

### 20.5 Replay-confirmed counterexample

A counterexample from the formal model that also violates the same property when executed through the original PyTorch implementation within stated tolerance.

### 20.6 Construction invariant

A property enforced directly by deterministic implementation logic, such as a clamp, rather than learned behavior.

### 20.7 Formal verification

A proof/check over the explicitly encoded model and verification domain.

### 20.8 Falsification

A search for concrete property violations without proving that no other violations exist.

---

## 21. References

1. **Formal Assurance in STRIVE** — project concept document. It defines three assurance directions and, for Approach 1, motivates verifying acceleration limits, unsafe sharp turns, unrealistic speeds, and collision-producing traffic-model outputs. It also identifies STRIVE source code and nuScenes as available evidence while noting the absence of formal real-world safe/unsafe/solvable labels.

2. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.

3. STRIVE public repository:  
   `https://github.com/nv-tlabs/STRIVE`

4. Relevant implementation:
   - `src/models/traffic_model.py`
   - `src/models/common.py`
   - `src/models/interaction_net.py`
   - `src/datasets/utils.py`
   - `src/datasets/nuscenes_dataset.py`
   - `src/losses/traffic_model.py`

5. Existing documentation:
   - D-01 — STRIVE nuScenes Data Card
   - M-01 — STRIVE Main Traffic Model Card
   - S-01 — STRIVE System Card

---

## 22. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed Approach-1 assurance data-card specification with M-01 implementation-derived controls/dynamics, evidence schema, property registry requirements, counterexample lineage, and verifier-neutral profiling. |
