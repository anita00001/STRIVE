# A2-M-01 — STRIVE Accident Scenario Classifier Verification Model Card

> **Card ID:** A2-M-01  
> **Card type:** Formal-Assurance Model Card  
> **Status:** Complete verification specification; no formal result claimed yet  
> **Assurance approach:** Verify the Accident Scenario Classifier  
> **Target model:** STRIVE paper-level learned binary regular-vs-accident-prone classifier  
> **Companion data card:** A2-D-01 — STRIVE Accident Scenario Classifier Verification Data Card  
> **System:** S-01 — STRIVE  
> **Important distinction:** This target is not the public M-04 K-means/cluster-labeling workflow.  
> **Inspected STRIVE revision:** `b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d`

---

## 1. Verification Model Details

### 1.1 Assurance model summary

A2-M-01 specifies formal assurance for the learned binary classifier described in the STRIVE paper/supplement for multi-mode planner operation.

The target classifier maps recent multi-agent traffic history and local map context to one of two operational classes:

```text
regular
accident-prone
```

The classifier is safety-relevant because its decision selects whether the planner uses regular or accident-handling behavior.

The assurance objective is to determine whether the classification decision remains correct or stable over a declared bounded domain, rather than merely reporting average classification accuracy.

### 1.2 Target classifier

Published description:

```text
past two seconds of trajectories for all agents
+ local map information
        │
        ▼
traffic-model-like trajectory/map processing
        │
        ▼
graph-based scene interaction
        │
        ▼
ego-node representation
        │
        ▼
two-layer MLP
        │
        ▼
binary regular / accident-prone decision
```

The STRIVE supplement further describes a 64-dimensional ego representation before the final binary MLP.

### 1.3 Target artifact identity

A formal result must bind to an exact executable classifier artifact.

Required identity fields:

```text
source implementation/revision
checkpoint SHA-256
effective architecture/configuration
input preprocessing
class ordering
decision threshold
normalization
map representation
graph construction
```

The public STRIVE repository does not expose enough of this information to uniquely instantiate the original classifier.

### 1.4 Public availability

At the inspected STRIVE revision, no original public binary-classifier implementation, checkpoint, or dedicated training configuration was identified.

This differs from:

- M-01, which is publicly implemented;
- M-03/M-04, which provide public clustering/class-label workflows.

### 1.5 Assurance status

```text
verification specification: complete
companion data specification: complete
original classifier source: not identified publicly
original classifier checkpoint: not identified publicly
formal verifier: not selected
formal encoding: not implemented
formal runs: not run
verified claims: none
falsified claims: none
```

### 1.6 Verification tool

The project concept leaves the verifier/tool undecided.

A2-M-01 remains tool-neutral and can support, for example:

- SMT/MILP neural-network verification;
- abstract interpretation;
- bound propagation;
- formal robustness verification;
- solver-backed counterexample search.

The exact interpretation of `verified` must match the guarantees of the selected tool.

---

## 2. Purpose & Assurance Role

### 2.1 Primary assurance objective

The main assurance objective is:

> Determine whether the regular-vs-accident-prone mode-selection decision is invariant, or remains on the required side of a classification margin, for all inputs in a declared bounded neighborhood around a labeled anchor scene.

### 2.2 Safety relevance

The classifier is safety-relevant because:

```text
regular
    → regular planner mode

accident-prone
    → accident-handling planner mode
```

A classification change can therefore change planner behavior even when the physical scene changes only slightly.

### 2.3 Relationship to planner tuning

The classifier belongs to the paper-level multi-mode planner evaluation/tuning concept associated with F-01.

It should not be confused with the single released `final_tuned_val_1` configuration.

A multi-mode system conceptually uses:

```text
binary scene classifier
        │
        ├── regular mode configuration
        └── accident-handling mode configuration
```

### 2.4 Relationship to A2-D-01

A2-D-01 defines:

- regular/accident-prone evidence sources;
- anchor scenes;
- perturbation domains;
- label provenance;
- counterexample records;
- verification-result records.

A2-M-01 defines:

- verification target;
- formal boundary;
- properties;
- formal encoding;
- result semantics;
- equivalence and replay requirements.

### 2.5 Out-of-scope claims

A2-M-01 does not by itself prove:

- the planner avoids collisions;
- the accident-handling mode is optimal;
- C-02/C-03 correctness;
- M-01 safety;
- real-world scene safety;
- system-level STRIVE safety.

---

## 3. Target Classifier Definition

### 3.1 Input history

Source-supported temporal input:

```text
past two seconds
```

of trajectories for all agents.

The exact sampling cadence/tensor layout must be obtained from the original classifier implementation or explicitly defined for a reproduction.

### 3.2 Local map input

The project concept and supplement describe local map information as part of the classifier input.

A faithful formal model must therefore either:

1. include the actual map encoder/input;
2. freeze the map representation and explicitly exclude map robustness;
3. verify only the post-map-encoding classifier.

### 3.3 Scene representation

The classifier is described as using a graph-based neural representation similar to STRIVE's learned traffic model.

Relevant conceptual operations include:

- per-agent motion encoding;
- local map encoding;
- graph interaction/message passing;
- extraction of the ego-node feature.

### 3.4 Ego feature

The supplement describes a:

```text
64-dimensional ego feature
```

as the representation passed to the final classifier head.

For a head-only verification target, this 64-D vector can become the formal input domain.

### 3.5 Classification head

Published description:

```text
two-layer MLP
```

producing the binary classification.

Exact layer widths, activation choices, and thresholding convention must be recovered from the original artifact or declared for a reproduction.

### 3.6 Binary output

Operational classes:

```text
regular
accident-prone
```

The exact numeric mapping, such as:

```text
0 = regular
1 = accident-prone
```

must not be assumed without the artifact/configuration.

---

## 4. Distinction from Public M-04

### 4.1 Public M-04

Public M-04 corresponds to:

```text
collision scenario
→ 4-D handcrafted collision feature
→ KMeans.predict
→ cluster index
→ one of 10 human-readable collision labels
```

This is a scenario-taxonomy workflow.

### 4.2 A2-M-01 target

A2-M-01 instead targets:

```text
multi-agent history + map
→ learned graph model
→ 2-layer MLP
→ binary mode decision
```

### 4.3 Non-equivalence

Therefore:

```text
public M-04 != A2-M-01 target
```

The public clustering model cannot be substituted as the binary classifier implementation.

### 4.4 Analytical relationship

M-03/M-04 collision labels may still be useful for:

- stratifying accident-prone anchor scenes;
- comparing robustness across collision geometries;
- identifying underrepresented failure modes.

They are analysis metadata, not A2-M-01 output labels.

---

## 5. Model Availability & Reproduction Status

### 5.1 Public source-code availability

No original binary classifier source file was identified in the inspected public repository.

### 5.2 Public checkpoint availability

No original classifier checkpoint was identified in the inspected public release.

### 5.3 Published architecture information

Available from project/paper/supplement description:

```text
input history: two seconds
input entities: all agents
map context: local maps
representation: graph-based neural model
ego representation: 64-D
head: 2-layer MLP
output: binary regular / accident-prone
training objective: weighted binary cross entropy
```

### 5.4 Missing implementation details

Not available from the inspected public implementation:

- exact classifier source;
- exact checkpoint;
- exact layer widths in final head;
- exact hidden nonlinearities;
- exact output/logit convention;
- exact threshold;
- exact classifier-specific normalization;
- exact graph construction if it differs from M-01;
- exact map preprocessing if it differs from M-01;
- exact training manifest and random seed.

### 5.5 Reproduction policy

A newly implemented classifier based on the published description must be labeled:

```text
STRIVE accident-classifier reproduction
```

or equivalent.

It must not be called:

```text
the original STRIVE classifier
```

unless equivalence is established against the original source/checkpoint.

---

## 6. Inputs to the Formal Model

### 6.1 Past multi-agent trajectories

The formal input should preserve the physical variables needed to reproduce the exact classifier history.

At minimum, a reproduction should document:

```text
x
y
heading
speed
time
visibility
```

If the M-01 state encoding is reused:

```text
x, y, heading_x, heading_y, speed, heading_change_rate
```

that reuse must be explicit.

### 6.2 Agent semantics

Record:

```text
semantic category
one-hot/category encoding
```

if used.

### 6.3 Agent attributes

If the classifier consumes dimensions:

```text
length
width
```

their bounds/values must be part of the verification domain.

### 6.4 Local map representation

Possible formal inputs:

```text
raw local raster
bounded local raster
fixed map feature
```

Each implies a different verification boundary.

### 6.5 Scene graph

A graph-based verification target must specify:

```text
number of nodes
edge_index / adjacency
node ordering
relative-coordinate semantics
aggregation operation
```

### 6.6 Ego-node designation

The final scene-level classification is produced from the ego representation.

Therefore the formal record must identify:

```text
ego node index
```

and preserve it under perturbation.

### 6.7 Visibility / missing data

If masks are supported, the exact semantics must be modeled.

If the artifact is unavailable, do not invent mask behavior and attribute it to original STRIVE.

---

## 7. Outputs of the Formal Model

### 7.1 Binary class

```text
regular
accident-prone
```

### 7.2 Logits / score

Formal robustness should use the pre-threshold score when available.

Possible conventions include:

- one binary logit;
- two class logits;
- post-sigmoid probability.

The exact convention remains artifact-dependent.

### 7.3 Decision threshold

Must be recorded explicitly.

Example only:

```text
score >= τ → accident-prone
score <  τ → regular
```

No specific `τ` is claimed by this card.

### 7.4 Classification margin

For a scalar accident score:

```text
margin = score - τ
```

or the equivalent model-specific margin.

### 7.5 Planner-mode decision

The classification is translated into:

```text
regular planner mode
accident-handling planner mode
```

The class-to-mode mapping is part of the assurance interpretation.

---

## 8. Candidate Formal Properties

### 8.1 C-FN — Accident-prone non-demotion

For accident-prone anchor `x` and bounded perturbation domain `D(x)`:

```text
forall x' in D(x):
    classifier(x') = accident-prone
```

This directly addresses a mode-selection false negative.

### 8.2 C-FP — Regular-case stability

For regular anchor `x`:

```text
forall x' in D(x):
    classifier(x') = regular
```

This checks robustness against unnecessary accident-mode activation.

### 8.3 C-MARGIN — Margin robustness

When a continuous score is available:

```text
accident-prone:
    score(x') >= τ + m

regular:
    score(x') <= τ - m
```

for specified margin `m >= 0`.

### 8.4 C-TRAJ — Trajectory perturbation robustness

Allow bounded perturbation of:

```text
position
heading
speed
trajectory history
```

for selected agents.

The perturbation model should reflect measurement/tracking uncertainty or intentionally defined robustness stress, not arbitrary tensor noise.

### 8.5 C-MAP — Map perturbation robustness

Possible map properties include robustness to:

- bounded raster uncertainty;
- selected semantic-layer errors;
- bounded encoded-map-feature variation.

This property requires a defensible map-uncertainty model.

### 8.6 C-JOINT — Joint multi-agent robustness

Perturb multiple interacting agents simultaneously while preserving the declared graph assumptions.

### 8.7 C-DROP — Observation robustness

If supported by the executable classifier:

```text
allowed history/track missingness
→ class remains required mode
```

This property should not be used unless observation-mask behavior is actually defined.

---

## 9. Verification Domain

### 9.1 Anchor class

Each formal domain is centered on:

```text
regular
```

or:

```text
accident-prone
```

with explicit label provenance from A2-D-01.

### 9.2 Agent-count bounds

Initial formal studies should generally fix:

```text
N
```

because graph topology and tensor shape otherwise change.

### 9.3 Trajectory-state bounds

Each symbolic input requires explicit bounds.

Example conceptual form:

```text
x_i,t'       ∈ [x_i,t - εx, x_i,t + εx]
y_i,t'       ∈ [y_i,t - εy, y_i,t + εy]
speed_i,t'   ∈ [s_i,t - εs, s_i,t + εs]
heading_i,t' ∈ bounded heading perturbation
```

Numeric ε values are not fixed by this card.

### 9.4 Map-domain assumptions

Recommended staged scope:

```text
Stage 1: fixed map input/feature
Stage 2: bounded map feature
Stage 3: bounded raster/map uncertainty if tractable
```

### 9.5 Graph-topology assumptions

For fixed-graph verification:

```text
agent identities fixed
adjacency fixed
node order fixed
ego index fixed
```

A fixed-graph proof does not cover agent insertion/removal.

### 9.6 Ego-node assumptions

The ego node remains fixed throughout a robustness domain unless the property explicitly studies track/identity changes.

### 9.7 Class-specific domains

Use separate domain registries for:

```text
C-FN / accident-prone anchors
C-FP / regular anchors
```

because the required output side differs.

---

## 10. Formal Encoding

### 10.1 Trajectory encoder encoding

The exact original classifier encoder is not public.

If the reproduction follows M-01-like encoding, document:

- MLP or GRU structure;
- normalization;
- visibility handling;
- local coordinate transformation.

### 10.2 Map encoder encoding

Possible boundaries:

**Full**

```text
CNN map encoder inside formal model
```

**Reduced**

```text
fixed/bounded map embedding
```

### 10.3 Graph message-passing encoding

A graph formalization should preserve:

- message direction;
- relative geometry;
- aggregation;
- node update;
- edge topology.

Do not simply replace graph interactions with independent per-agent features without changing the claimed model boundary.

### 10.4 Ego-feature extraction

The published target uses the final ego-node feature.

For head-only verification:

```text
formal input = bounded 64-D ego feature
```

This verifies only the classifier head.

### 10.5 Two-layer MLP encoding

Once exact weights are available, an MLP head is a relatively tractable formal target compared with the full graph/map encoder.

### 10.6 Decision rule encoding

The formal model must encode:

```text
logit/score
threshold
class mapping
```

exactly.

### 10.7 Floating-point abstraction

Record whether verification uses:

```text
real arithmetic
float-aware arithmetic
interval abstraction
other numeric semantics
```

and state the resulting equivalence limits.

---

## 11. Verification Method

### 11.1 Verification paradigm

Not yet selected.

Potential choices depend strongly on target scope:

```text
head-only MLP:
    many standard neural-network verifiers are plausible

full graph/map classifier:
    substantially harder because of graph/message passing and CNN processing
```

### 11.2 Soundness expectations

A result must clearly distinguish:

```text
formal proof of robustness
```

from:

```text
no adversarial/class-flip example found
```

### 11.3 Solver / backend

```text
TBD
```

### 11.4 Timeout / resource policy

Freeze before final evaluation:

```text
timeout
CPU/GPU
RAM
parallelism
random seeds where relevant
```

### 11.5 Proof obligation

For class-invariance verification:

```text
domain constraints
∧ classifier constraints
∧ class(x') != required_class
```

A sound proof of infeasibility supports robustness over the encoded domain.

### 11.6 Counterexample extraction

A counterexample should include:

```text
anchor
concrete perturbation
classifier score/logit
class before
class after
planner mode before
planner mode after
property version
```

---

## 12. Verification Workflow

### 12.1 Obtain or define target artifact

Preferred:

```text
original STRIVE classifier source + checkpoint
```

Fallback:

```text
explicitly named reproduction
```

### 12.2 Freeze preprocessing

Document:

- history sampling;
- coordinate frame;
- normalization;
- semantic encoding;
- map preprocessing;
- graph construction;
- ego selection.

### 12.3 Select A2-D-01 anchor

Choose a frozen:

```text
regular
```

or:

```text
accident-prone
```

anchor.

### 12.4 Select property

Choose:

```text
C-FN
C-FP
C-MARGIN
C-TRAJ
C-MAP
C-JOINT
```

or a versioned project extension.

### 12.5 Instantiate bounded domain

Record exact symbolic dimensions and lower/upper bounds.

### 12.6 Encode classifier and property

Create the verifier-specific model.

### 12.7 Validate formal/executable equivalence

Before interpreting proofs, compare formal and executable outputs on concrete points within the domain.

### 12.8 Run verifier

Allowed result states:

```text
verified
counterexample
unknown
timeout
error
```

### 12.9 Replay counterexample

A formal class flip should be replayed in the executable classifier.

### 12.10 Store evidence

Persist into the A2-D-01 assurance manifest/regression partition.

---

## 13. Counterexample Handling

### 13.1 Counterexample definition

A valid counterexample satisfies:

```text
x' ∈ D(x)
```

and violates the selected class or margin property.

### 13.2 False-negative counterexample

```text
anchor: accident-prone
perturbed prediction: regular
```

This suppresses accident-handling mode under the operational classifier semantics.

### 13.3 False-positive counterexample

```text
anchor: regular
perturbed prediction: accident-prone
```

This unnecessarily activates accident-handling mode.

### 13.4 Executable replay

Replay against the exact target artifact using:

- identical preprocessing;
- identical graph/map context;
- identical threshold;
- identical class ordering.

### 13.5 Numeric reconciliation

Near-threshold disagreements should record:

```text
formal score
runtime score
difference
formal threshold
runtime threshold
```

### 13.6 Regression retention

Replay-confirmed class flips should become permanent regression examples unless explicitly retired.

---

## 14. Validation of the Formal Model

### 14.1 Preprocessing equivalence

Compare:

```text
trajectory tensor
map tensor/feature
graph
ego index
semantic encoding
```

between executable and formal pipelines.

### 14.2 Encoder equivalence

Where included, compare trajectory/map encoded features at concrete points.

### 14.3 Graph-layer equivalence

Compare per-node post-message-passing features.

### 14.4 Ego-feature equivalence

The 64-D ego representation is a key checkpoint for equivalence testing.

### 14.5 MLP-head equivalence

Compare:

```text
logit(s)
score
```

from executable and formal head.

### 14.6 Decision-rule equivalence

Verify the exact same:

```text
threshold
class mapping
```

is applied.

---

## 15. Quantitative Analysis

No formal assurance results exist yet.

The final report should include:

### 15.1 Verification cases

Counts by:

```text
anchor class
property
domain type
map
agent count
```

### 15.2 Verification outcomes

```text
verified
counterexample
unknown
timeout
error
```

### 15.3 False-negative robustness

For accident-prone anchors, report:

```text
verified robust domains
class-flip counterexamples
unknown/timeouts
```

### 15.4 False-positive robustness

Analogous statistics for regular anchors.

### 15.5 Runtime

Report:

```text
mean
median
max
timeout count
```

### 15.6 Robustness radius / margin

If the chosen method supports radius search, report values with the exact norm/domain definition.

### 15.7 Counterexample replay rate

Separate:

```text
formal counterexamples
replay-confirmed
non-reproducing/spurious
not replayed
```

---

## 16. Robustness & Sensitivity

### 16.1 Trajectory perturbation size

Measure how proof/counterexample outcome changes as perturbation bounds expand.

### 16.2 Agent-count sensitivity

Compare tractability across scene size.

### 16.3 Map sensitivity

Compare:

```text
fixed map
bounded map feature
full map uncertainty
```

### 16.4 Graph sensitivity

If feasible, compare fixed topology with selected topology changes.

### 16.5 Decision-margin sensitivity

Low-margin anchors are expected to be more fragile; verify this empirically/formally rather than assuming it.

### 16.6 Class asymmetry

Compare robustness for:

```text
regular
accident-prone
```

anchors separately.

---

## 17. Failure Modes

### 17.1 Accident-prone demotion

Small admissible input change causes:

```text
accident-prone → regular
```

### 17.2 Regular promotion

Small admissible input change causes:

```text
regular → accident-prone
```

### 17.3 Low-margin instability

Very small perturbations cross the decision boundary.

### 17.4 Map-induced mode flip

Classification changes primarily because of bounded map variation.

### 17.5 Multi-agent interaction instability

Minor change to another agent's recent motion causes the ego mode to flip.

### 17.6 Reproduction mismatch

A reproduced classifier may differ from the original in:

- learned weights;
- preprocessing;
- graph topology;
- class threshold;
- map encoder;
- dataset composition.

Such mismatches limit what can be claimed about original STRIVE.

---

## 18. Known Limitations

### 18.1 Original classifier unavailable

This is the principal limitation.

Without the original source/checkpoint, A2-M-01 cannot presently produce a formal guarantee about the exact classifier used in the paper.

### 18.2 Exact preprocessing unavailable

The high-level input description is public, but exact executable preprocessing is not available from the inspected repository.

### 18.3 Exact decision threshold unavailable

The binary threshold and output convention must be recovered or explicitly defined in a reproduction.

### 18.4 Operational labels

`regular` and `accident-prone` are planner-mode classes.

They should not be described as universal formal safety truth.

### 18.5 Generated positive-class bias

Accident-prone training data inherit assumptions from:

- STRIVE's learned traffic prior;
- scenario optimizer;
- planner family/configuration;
- scenario filtering.

### 18.6 Domain restriction

A local robustness proof covers only the stated domain.

### 18.7 Full graph/CNN tractability

Formal verification of:

```text
trajectory encoder + map CNN + graph network + MLP
```

is materially harder than verification of the final MLP head.

### 18.8 Classifier accuracy vs planner effectiveness

Even a correctly classified accident-prone scene can still result in planner collision.

Classifier verification and planner verification are separate assurance problems.

---

## 19. Safety & Assurance Interpretation

### 19.1 Meaning of “verified”

Acceptable result wording:

> C-FN v1.0.0 is verified for classifier artifact X on accident-prone anchor Y over perturbation domain D under formal encoding E.

Avoid:

```text
the STRIVE accident classifier is safe
```

without the required scope qualifiers.

### 19.2 Meaning of “falsified”

A replay-confirmed in-domain mode flip demonstrates that the selected robustness property does not hold for that domain.

### 19.3 Meaning of unknown / timeout

```text
No conclusion.
```

### 19.4 False-negative significance

Operational path:

```text
accident-prone context
→ regular classification
→ regular planner mode
```

This is a safety-relevant mode-selection failure.

### 19.5 False-positive significance

Operational path:

```text
regular context
→ accident-prone classification
→ accident-handling planner mode
```

This may degrade regular-mode behavior or efficiency, but does not itself imply collision.

### 19.6 System-level limits

A2-M-01 does not verify:

- the chosen planner mode's behavior;
- F-01 tuning correctness;
- M-01 traffic predictions;
- the collision-generation optimizer;
- complete STRIVE safety.

---

## 20. Reproducibility

### 20.1 Classifier source revision

Required once obtained.

For a reproduction, record the reproduction repository revision separately from STRIVE.

### 20.2 Checkpoint hash

Required:

```text
SHA-256
```

### 20.3 Effective configuration

Record:

```text
history length/cadence
trajectory feature definition
map crop/encoder
graph construction
ego-node convention
64-D feature implementation
MLP architecture
output convention
threshold
```

### 20.4 A2-D-01 dataset manifest

Required for final assurance runs.

### 20.5 Property registry

Each run must reference:

```text
property ID
version
domain hash
```

### 20.6 Verifier/toolchain

Record:

```text
verifier
solver/backend
version
formal encoding revision
numeric semantics
```

### 20.7 Execution environment

Record:

```text
OS
CPU/GPU
RAM
Python
framework
verifier environment
```

### 20.8 Companion metadata

```text
metadata/assurance/models/accident_classifier_verification.yaml
```

### 20.9 Profiler

```text
tools/profile_accident_classifier_verification.py
```

The profiler does not perform formal verification. It checks public-target availability, hashes artifacts, and summarizes optional result manifests.

---

## 21. Assurance Evidence & Results

### 21.1 Claim-evidence matrix

| Claim | Anchor class | Domain | Evidence | Status |
|---|---|---|---|---|
| C-FN accident-prone non-demotion | accident-prone | TBD | none yet | Not run |
| C-FP regular-case stability | regular | TBD | none yet | Not run |
| C-MARGIN margin robustness | both | TBD | none yet | Not run |
| C-TRAJ trajectory robustness | both | TBD | none yet | Not run |
| C-MAP map robustness | both | TBD | none yet | Not run |
| C-JOINT joint robustness | both | TBD | none yet | Not run |

### 21.2 Verified claims

```text
None.
```

### 21.3 Falsified claims

```text
None.
```

### 21.4 Inconclusive claims

No formal runs have been executed.

The present state is:

```text
not evaluated
```

rather than solver `unknown`.

### 21.5 Residual risk

Even after future verification, residual risk includes:

- unverified scenes;
- perturbations outside bounded domains;
- graph changes;
- map changes;
- unknown original classifier implementation details;
- downstream planner behavior.

---

## 22. Relationships

### 22.1 Companion data card

```text
A2-D-01 — STRIVE Accident Scenario Classifier Verification Data Card
```

### 22.2 Paper-level planner relationship

```text
traffic history + map
        │
        ▼
binary accident classifier
        │
        ├──► regular planner mode
        └──► accident-handling planner mode
```

### 22.3 Relationship to F-01

F-01 documents planner tuning and distinguishes:

- public released planner configuration;
- paper-level multi-mode tuning using a learned binary accident-mode classifier.

A2-M-01 is the formal-assurance abstraction for that learned binary mode selector.

### 22.4 Relationship to M-04

```text
M-04:
    public cluster-based scenario classifier

A2-M-01:
    paper-level learned binary mode classifier
```

They are distinct.

### 22.5 Other assurance approaches

```text
A1 — Verify STRIVE's learned traffic model
A3 — Specification-driven falsification of the collision-generation optimizer
```

---

## 23. Terms of Art

### 23.1 Regular

Operational binary classifier class associated with regular planner mode.

### 23.2 Accident-prone

Operational binary classifier class associated with accident-handling planner mode.

### 23.3 Mode selector

A classifier whose output chooses between planner operating modes.

### 23.4 Robustness domain

A bounded set of admissible perturbations around an anchor input.

### 23.5 Classification margin

Distance of a continuous classifier output from the decision boundary under the target output convention.

### 23.6 Counterexample

A concrete in-domain input that violates a class-preservation or margin property.

### 23.7 Reproduction

An independently implemented classifier based on the published architecture/training description.

### 23.8 Equivalence gap

Any semantic or numerical difference between:

```text
original classifier
reproduction
formal encoding
```

---

## 24. References

1. **Formal Assurance in STRIVE** — project concept document. It describes the learned binary classifier as consuming past two-second multi-agent trajectories and local map information through a graph-based neural network and two-layer MLP, with the output determining regular versus accident-handling planner mode.

2. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.

3. STRIVE supplementary material — binary mode-classifier architecture/training description, including the traffic-model-like encoder, 64-D ego feature, weighted binary cross entropy, and generated collision training set.

4. STRIVE public repository:  
   `https://github.com/nv-tlabs/STRIVE`

5. Existing documentation:
   - A2-D-01 — STRIVE Accident Scenario Classifier Verification Data Card
   - M-04 — STRIVE Accident / Scenario Classifier Card
   - F-01 — STRIVE Planner Tuning Fitted-Config Card
   - S-01 — STRIVE System Card

---

## 25. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed Approach-2 formal-assurance model-card specification, including original-artifact availability constraints, binary robustness properties, reproduction policy, formal encoding/equivalence workflow, and planner-mode interpretation. |
