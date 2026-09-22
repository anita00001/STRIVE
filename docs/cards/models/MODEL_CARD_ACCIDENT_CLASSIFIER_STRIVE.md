# M-04 — STRIVE Accident Classifier Model Card

> **Card ID:** M-04  
> **Card type:** Model Card  
> **Status:** Complete for the public STRIVE release  
> **Model:** STRIVE Accident / Scenario Classifier  
> **Upstream:** D-02 — Generated Scenarios Data Card, M-03 — Scenario Clustering  
> **Downstream:** F-01 — Planner Tuning  
> **Primary implementation:** `src/eval_adv_gen.py::assign_cluster`

---

## 1. Model Details

### 1.1 Model summary

In the public STRIVE release, there is **no separately trained supervised model named an accident classifier**.

The released classification mechanism is a thin inference layer over M-03:

1. load a precomputed K-means clustering from `cluster.pkl`;
2. extract the same four collision-geometry features used to fit M-03;
3. call `clustering.predict(scene_feats)`;
4. map the resulting integer cluster index to a human-authored semantic label from `cluster_labels.txt`.

Accordingly, M-04 should be understood as **cluster-based scenario classification**, not as an independent neural classifier or separately fitted supervised estimator.

### 1.2 Model type

Public mechanism:

```text
M-03 KMeans.predict(...)
+
ordered semantic label lookup
```

Classification output:

```text
one hard cluster/class index
one human-readable class name
```

The public workflow does not expose a calibrated class probability.

### 1.3 Primary implementation

Classification and reporting:

```text
src/eval_adv_gen.py
```

Specifically:

```text
compute_coll_feat(...)
assign_cluster(...)
quant_eval(...)
```

Clustering model construction:

```text
src/cluster_scenarios.py
```

### 1.4 Model artifacts

Default classifier artifacts:

```text
data/clustering/cluster.pkl
data/clustering/cluster_labels.txt
```

These form a paired artifact set:

- `cluster.pkl` defines numerical decision regions;
- `cluster_labels.txt` assigns semantic names to cluster indices.

### 1.5 Authors, date, and license

STRIVE was released with the CVPR 2022 work by:

- Davis Rempe
- Jonah Philion
- Leonidas J. Guibas
- Sanja Fidler
- Or Litany

The STRIVE source code is MIT licensed. The scenario data used as classifier input is nuScenes-derived and should retain the licensing/provenance requirements documented in D-02.

---

## 2. Purpose & Role in STRIVE

### 2.1 Primary purpose

M-04 assigns each generated collision scenario to an interpretable collision-geometry category such as:

```text
Head On
T-Bone Left
Merge from Right
```

This supports scenario-distribution analysis and qualitative interpretation.

### 2.2 Role in evaluation

The README describes:

```bash
python src/eval_adv_gen.py \
  --out ./out/adv_gen_rule_based_out/eval_results \
  --scenarios ./out/adv_gen_rule_based_out/scenario_results \
  --eval_quant
```

as a way to quantitatively evaluate and **classify** generated scenarios.

The resulting outputs include:

```text
*_labels.csv
scene_distrib.png
```

### 2.3 Relationship to D-02

M-04 consumes D-02 adversarial collision scenarios.

The public quantitative workflow classifies:

```text
adv_sol_success
sol_failed
```

because both partitions contain adversarially successful collisions.

### 2.4 Relationship to M-03

M-04 directly reuses M-03:

```text
feature extraction
cluster.pkl
cluster index space
cluster_labels.txt
```

There is no separate M-04 training phase in the public release.

### 2.5 Relationship to F-01

Within this documentation hierarchy, M-04 can support planner tuning by summarizing **which collision types** appear under a planner/configuration and by enabling stratified failure analysis.

However, no direct public STRIVE code path was identified in which M-04 class labels are automatically consumed as input to planner tuning.

Therefore the edge:

```text
M-04 → F-01
```

should be treated as an **analytical/documentation dependency**, not a direct executable dependency in the released repository.

---

## 3. Intended Use

### 3.1 Intended uses

Appropriate uses include:

- assigning semantic collision categories to generated STRIVE scenarios;
- comparing failure-mode distributions across planners;
- selecting representative scenarios by collision type;
- stratifying planner evaluation;
- summarizing generated collision datasets.

### 3.2 Intended users

Researchers working on:

- planner robustness;
- autonomous-driving simulation;
- adversarial scenario generation;
- generated failure taxonomy.

### 3.3 Out-of-scope uses

M-04 should not be used as:

- a real-world crash classifier;
- a legal-fault classifier;
- a crash-severity predictor;
- a calibrated accident-risk estimator;
- a production perception or safety component.

---

## 4. Input Data

### 4.1 Input scenario partitions

The public evaluator runs classification on:

```text
adv_sol_success
sol_failed
```

and does not classify `adv_failed` through the collision-clustering path.

### 4.2 Required fields

For feature extraction, each scene needs:

```text
lw
fut_adv
dt
```

The evaluator's scene loader additionally expects D-02 fields such as:

```text
map
sem
past
fut_init
```

### 4.3 Collision requirement

The classifier assumes a collision exists between the planner and at least one non-planner agent.

The feature extractor:

- interpolates trajectories;
- detects planner-other collisions;
- chooses the earliest collision.

If no collision exists, a valid classification feature is not defined by the public workflow.

### 4.4 Input provenance

Classification depends on D-02 provenance including:

- attacked planner;
- planner configuration;
- M-01 checkpoint;
- C-02 behavior;
- source nuScenes subset;
- agent-category configuration.

---

## 5. Feature Extraction

### 5.1 Collision feature extraction

M-04 uses the same collision feature construction as M-03.

For the earliest planner-other collision:

```text
angvec = normalized attacker position in planner-local frame
hvec   = attacker heading in planner-local frame
```

### 5.2 Temporal interpolation

Hard-coded:

```text
interp_scale = 5
```

For the standard D-02 timestep:

```text
dt = 0.5 s
```

the interpolated collision spacing is approximately:

```text
0.1 s
```

### 5.3 Planner-relative coordinate frame

The colliding agent state is transformed into the planner's local frame at the collision state.

This removes absolute world position and focuses classification on relative collision geometry.

### 5.4 Feature vector schema

Exact predictor input:

```text
[
  collision_direction_x,
  collision_direction_y,
  attacker_heading_x,
  attacker_heading_y
]
```

Dimension:

```text
4
```

The evaluator constructs:

```text
scene_feats = concatenate([angvec, hvec], axis=1)
```

### 5.5 Auxiliary evaluation feature

`eval_adv_gen.py` additionally computes:

```text
rel_s
```

the relative speed near the earliest collision.

This value is useful for quantitative analysis but is **not passed to `clustering.predict()`** and therefore is not a classifier feature.

---

## 6. Classification Mechanism

### 6.1 Classifier type

The public classifier is:

```text
precomputed K-means cluster assignment
```

No separate supervised classifier fit is performed.

### 6.2 Decision rule

The numerical class is produced by:

```python
scene_labels = clustering.predict(scene_feats)
```

For scikit-learn K-means, this assigns each feature vector to the nearest fitted cluster center under the estimator's standard Euclidean-distance decision rule.

### 6.3 Number of classes

The public M-03 artifact/label set uses:

```text
10 classes
```

### 6.4 Class ordering

Semantic names are looked up by numerical index:

```python
scene["label"] = cluster_labels[scene_labels[si]]
```

Therefore:

```text
class index i ↔ label file entry i
```

### 6.5 Confidence or distance

The public STRIVE classification path outputs a hard index and label.

It does not write:

- probabilities;
- calibrated confidence;
- nearest-centroid distance;
- classification margin.

A local diagnostic may compute centroid distances, but such values are not part of the released M-04 output contract.

---

## 7. Classes & Label Semantics

### 7.1 Released class names

The public `cluster_labels.txt` maps indices as follows:

| Class index | Semantic label |
|---:|---|
| 0 | Merge from Right |
| 1 | Head On |
| 2 | Behind |
| 3 | Cutoff Left & Front |
| 4 | T-Bone Left |
| 5 | Front from Right |
| 6 | Merge from Left |
| 7 | T-Bone Right |
| 8 | Cutoff Right |
| 9 | Front from Left |

### 7.2 Cluster/class index mapping

M-04 class indices are exactly the M-03 cluster indices.

There is no additional remapping layer.

### 7.3 Human-authored labels

The semantic names are not learned from text labels.

They are human-authored descriptions of M-03's geometric clusters.

### 7.4 Label ambiguity

Cluster boundaries exist in a continuous four-dimensional geometry space.

Scenarios close to a centroid boundary may switch labels after:

- M-03 refitting;
- changes in feature extraction;
- different scikit-learn behavior;
- small trajectory/collision-time changes.

### 7.5 Versioning

Treat these as an inseparable versioned pair:

```text
cluster.pkl
cluster_labels.txt
```

A label file from another clustering can silently attach incorrect names to numerical predictions.

---

## 8. Training / Fitting Data

### 8.1 Source generated scenarios

M-04 has no separate training dataset from M-03.

Its decision boundaries are inherited from the D-02 collision scenarios used to fit M-03.

### 8.2 Scenario count

The README describes the supplied paper clustering as fitted on:

```text
over 400 scenarios
```

An exact local classifier training-set count should be inherited from the specific M-03 profile rather than inferred from that wording.

### 8.3 Planner mix

The public paper clustering used:

```text
many versions of the rule-based planner
```

according to the README.

Thus the released class boundaries reflect a mixture of planner-generation configurations.

### 8.4 nuScenes subsets

The README states the M-03 source scenarios came from:

```text
various subsets of nuScenes
```

### 8.5 Selection bias

Training/fitting data is strongly selected:

```text
D-01 source windows
→ feasibility filtering
→ C-02 adversarial success
→ collision-only clustering set
```

The classifier therefore models geometry within STRIVE-generated collision scenarios, not arbitrary traffic scenes.

---

## 9. Training / Construction Procedure

### 9.1 Artifact construction

There is no separate M-04 fitting script.

Construction is:

```text
M-03 cluster.pkl
+
ordered semantic label file
=
M-04 classifier behavior
```

### 9.2 Model fitting

Numerical decision regions are learned entirely in M-03 using:

```text
KMeans(n_clusters=10, random_state=0)
```

under the public defaults.

### 9.3 Semantic label assignment

Human-readable class names are stored as a comma-separated sequence in:

```text
data/clustering/cluster_labels.txt
```

The evaluator strips surrounding whitespace and preserves list order.

### 9.4 Serialization

Numerical model:

```text
Python pickle: cluster.pkl
```

Semantic mapping:

```text
plain text: cluster_labels.txt
```

No separate M-04 checkpoint exists.

---

## 10. Inference Procedure

### 10.1 Scenario loading

`eval_adv_gen.py` reads each D-02 JSON and constructs tensors for:

```text
lw
fut_adv
dt
```

plus additional evaluation fields.

### 10.2 Feature computation

For every colliding scenario:

1. interpolate planner and other trajectories ×5;
2. detect planner-other collisions;
3. select earliest collision;
4. transform attacker state into planner frame;
5. form `angvec`;
6. extract `hvec`;
7. concatenate the 4-D feature.

### 10.3 Class prediction

Inference call:

```python
scene_labels = clustering.predict(scene_feats)
```

### 10.4 Semantic label lookup

For each scenario:

```python
scene["label"] = cluster_labels[scene_labels[si]]
scene["label_idx"] = scene_labels[si]
```

### 10.5 CSV/report output

If an output CSV path is supplied, the evaluator writes:

```text
scene,cluster_idx,cluster_name
```

The quantitative evaluation writes files such as:

```text
adv_sol_success_labels.csv
sol_failed_labels.csv
```

and a collision-scenario distribution plot.

---

## 11. Evaluation Metrics

### 11.1 Classification distribution

The primary released analysis is descriptive:

```text
count per class
```

split between:

```text
Solution Found = adv_sol_success
No Solution    = sol_failed
```

### 11.2 Agreement with cluster semantics

The public code provides visualization tools for examining clustered scenarios.

Human review is the main mechanism for judging whether semantic names meaningfully describe cluster geometry.

### 11.3 Stability

The public release does not report a supervised classification accuracy because there is no independently labeled ground-truth classification set.

Useful local stability tests include:

- repeat M-03 fitting;
- compare centroid assignments;
- compare semantic labels after centroid matching;
- perturb trajectory/collision timing.

### 11.4 Coverage

A classification coverage denominator should be:

```text
generated collision scenarios eligible for M-03/M-04
```

rather than all source D-01 windows.

### 11.5 Optional confidence diagnostics

For local analysis, distances from each feature to all K-means centroids can quantify assignment proximity.

These distances are not probabilities and should not be described as calibrated confidence.

---

## 12. Quantitative Analysis

### 12.1 Class distribution

For any evaluated bundle, report:

```text
class count
class fraction
```

for all ten labels.

### 12.2 Distribution by scenario partition

Keep separate counts for:

```text
adv_sol_success
sol_failed
```

before computing combined totals.

This preserves the relationship between collision type and whether C-03 found a solution.

### 12.3 Distribution by planner/configuration

If multiple D-02 generation runs are combined, stratify by:

- planner;
- planner configuration;
- category set;
- source split;
- M-01 checkpoint.

Otherwise class-frequency differences can be confounded by generation provenance.

### 12.4 Feature-to-centroid distance

Optional local profiling can report:

- minimum centroid distance;
- second-nearest centroid distance;
- distance margin.

These are diagnostic additions, not public STRIVE output fields.

### 12.5 Unassigned/invalid cases

Track cases that cannot be classified because of:

- missing collision;
- malformed scenario JSON;
- missing model/label artifact;
- label/model class-count mismatch;
- feature extraction failure.

### 12.6 Profiler

Run static artifact/source validation:

```bash
python tools/profile_accident_classifier.py \
  --repo-root . \
  --output ./out/accident_classifier_profile.yaml
```

Inspect a trusted clustering pickle:

```bash
python tools/profile_accident_classifier.py \
  --repo-root . \
  --cluster-pkl ./data/clustering/cluster.pkl \
  --output ./out/accident_classifier_profile.yaml
```

Optionally summarize one or more classification CSV outputs:

```bash
python tools/profile_accident_classifier.py \
  --repo-root . \
  --labels-csv ./out/eval_results/adv_sol_success_labels.csv \
  --labels-csv ./out/eval_results/sol_failed_labels.csv \
  --output ./out/accident_classifier_profile.yaml
```

Only pass a trusted local pickle.

---

## 13. Validation

### 13.1 Artifact compatibility

Validate:

```text
number of cluster centers
==
number of semantic labels
```

For the released label file:

```text
10
```

is expected.

### 13.2 Feature compatibility

The classifier must use the exact M-03 feature order:

```text
[angvec_x, angvec_y, hvec_x, hvec_y]
```

Reordering components changes class assignment.

### 13.3 Label-count validation

The label file is positional, so a mismatch between class count and label count is a hard compatibility error.

### 13.4 Scenario validation

Before prediction, verify:

- `lw`, `fut_adv`, and `dt` exist;
- a planner-other collision is detected;
- the four feature values are finite.

### 13.5 Reproducibility validation

Record:

- `cluster.pkl` SHA-256;
- `cluster_labels.txt` SHA-256;
- STRIVE revision;
- scikit-learn version;
- KMeans constructor parameters;
- M-03 provenance.

---

## 14. Factors

### 14.1 Planner dependence

Class assignments reflect the collision geometry generated against a particular planner.

Class **frequencies** can therefore change substantially across planner configurations.

### 14.2 Agent-category dependence

The same geometric taxonomy may behave differently when D-02 includes pedestrians, cyclists, motorcycles, or other categories not dominant in the main car/truck model.

### 14.3 Geographic dependence

M-04 remains downstream of nuScenes and D-01 geography.

### 14.4 Collision-detection dependence

The classifier feature depends on:

- interpolation scale;
- collision geometry;
- earliest-collision choice.

Changing those can change the 4-D feature and the assigned class.

### 14.5 Model-version dependence

Refitting M-03 can:

- move decision boundaries;
- permute numerical cluster IDs;
- produce a different semantic-label pairing.

---

## 15. Limitations

### 15.1 Cluster-derived classes

M-04 classes are derived from unsupervised M-03 clusters rather than independently labeled accident categories.

### 15.2 Hard assignment

The released workflow assigns one class per scenario with no calibrated uncertainty.

### 15.3 Synthetic-data dependence

The classifier describes STRIVE-generated collisions, not the distribution of real-world traffic accidents.

### 15.4 Limited feature space

The four classifier dimensions omit:

- speed;
- collision severity;
- road topology;
- traffic control;
- semantic agent category;
- longitudinal history;
- map context.

### 15.5 Semantic-label subjectivity

Human-readable names are interpretations of geometric clusters and may not uniquely describe every member.

### 15.6 Version coupling

The classifier depends on a specific M-03 artifact plus its ordered labels.

### 15.7 Scikit-learn version dependence

The public `requirements.txt` does not pin scikit-learn even though M-03 uses it.

The serialized pickle can also be version-sensitive.

### 15.8 No direct planner-tuning interface

The public code supports classification and planner evaluation as separate analyses. No direct released mechanism was identified that uses M-04 labels as an optimization objective or automatic planner-tuning input.

---

## 16. Ethical & Safety Considerations

### 16.1 Interpretation

An M-04 label means:

```text
"this generated collision is closest to this M-03 geometric cluster"
```

not:

```text
"this is the verified real-world cause or legal category of an accident"
```

### 16.2 Bias

M-04 inherits bias from:

- D-01;
- M-01;
- C-01/C-02/C-03;
- D-02 selection;
- M-03 feature design and fitting data;
- human cluster naming.

### 16.3 Misuse

Do not use the class label alone for:

- fault assignment;
- insurance decisions;
- real-world severity prediction;
- operational risk scoring.

### 16.4 Reporting

Reports should clearly state that classes are assigned to **synthetic STRIVE-generated collision scenarios** using a precomputed K-means taxonomy.

---

## 17. Reproducibility

### 17.1 Source files

```text
src/eval_adv_gen.py
src/cluster_scenarios.py
src/datasets/utils.py
src/losses/adv_gen_nusc.py
src/utils/transforms.py
```

### 17.2 Input artifacts

```text
D-02 scenario JSON
data/clustering/cluster.pkl
data/clustering/cluster_labels.txt
```

### 17.3 Output artifacts

Typical classification outputs:

```text
adv_sol_success_labels.csv
sol_failed_labels.csv
scene_distrib.png
```

### 17.4 Companion metadata

```text
metadata/models/accident_classifier.yaml
```

### 17.5 Quantitative profiler

```text
tools/profile_accident_classifier.py
```

The profiler reports:

- source-file hashes;
- classification-call behavior;
- feature-contract checks;
- semantic label order;
- optional trusted pickle metadata;
- model/label compatibility;
- optional CSV class distributions.

### 17.6 Required dependency versions

Record:

```text
Python
NumPy
scikit-learn
```

plus the STRIVE repository revision.

The public repository does not pin scikit-learn in `requirements.txt`.

---

## 18. Relationships

### 18.1 Upstream

```text
D-02 — Generated Scenarios
  │
  ▼
M-03 — Scenario Clustering
```

### 18.2 Downstream

```text
F-01 — Planner Tuning
```

This is an analytical/documentation relationship in the current card hierarchy. The public STRIVE release does not directly wire cluster labels into planner tuning.

### 18.3 Dependency chain

```text
D-02  Generated Scenarios
  │
  ▼
M-03  Scenario Clustering
  │
  ▼
M-04  Accident Classifier
  │
  ▼
F-01  Planner Tuning
```

---

## 19. Terms of Art

### 19.1 Accident class

A human-readable semantic category assigned to an M-03 cluster.

### 19.2 Class index

The integer returned by:

```text
KMeans.predict()
```

### 19.3 Cluster label

The human-authored string at the corresponding index of `cluster_labels.txt`.

### 19.4 Classification

The combination of:

```text
collision feature extraction
→ KMeans.predict
→ semantic label lookup
```

### 19.5 Classifier

For M-04, the classifier is the **M-03 K-means predictor plus the ordered semantic label mapping**. It is not a separate supervised model.

---

## 20. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.  
   https://openaccess.thecvf.com/content/CVPR2022/html/Rempe_Generating_Useful_Accident-Prone_Driving_Scenarios_via_a_Learned_Traffic_Prior_CVPR_2022_paper.html

2. STRIVE public repository.  
   https://github.com/nv-tlabs/STRIVE

3. Relevant release files:
   - `src/eval_adv_gen.py`
   - `src/cluster_scenarios.py`
   - `src/datasets/utils.py`
   - `data/clustering/cluster.pkl`
   - `data/clustering/cluster_labels.txt`
   - `src/eval_planner.py`
   - `configs/eval_planner.cfg`

4. D-02 — Generated Scenarios Data Card.

5. M-03 — STRIVE Scenario Clustering Model Card.

---

## 21. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed M-04 as the public STRIVE cluster-based classification workflow; documented lack of a separate learned classifier and lack of direct class-label-to-planner-tuning wiring. |
