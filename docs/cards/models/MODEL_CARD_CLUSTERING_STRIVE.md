# M-03 — STRIVE Scenario Clustering Model Card

> **Card ID:** M-03  
> **Card type:** Model Card  
> **Status:** Complete for the public STRIVE release  
> **Model:** STRIVE Generated-Scenario Clustering  
> **Upstream:** D-02 — Generated Scenarios Data Card  
> **Downstream:** M-04 — Accident Classifier  
> **Primary implementation:** `src/cluster_scenarios.py`

---

## 1. Model Details

### 1.1 Model summary

M-03 groups STRIVE-generated collision scenarios according to **collision geometry**.

The released clustering converts each colliding D-02 adversarial scenario into a four-dimensional feature vector describing:

1. the direction from the planner to the colliding agent, expressed in the planner's local frame; and
2. the colliding agent's heading, also expressed in the planner's local frame.

It then fits a scikit-learn `KMeans` model.

The clustering is not a trajectory predictor or accident-risk model. It is a compact taxonomy mechanism for organizing synthetic STRIVE collision scenarios by geometric collision type.

### 1.2 Model type

Released algorithm:

```text
scikit-learn KMeans
```

Default number of clusters:

```text
k = 10
```

Random state:

```text
0
```

Feature dimension:

```text
4
```

### 1.3 Model artifact

The fitted clustering is serialized as:

```text
cluster.pkl
```

The public paper clustering is provided under:

```text
data/clustering/cluster.pkl
```

A separate text file maps integer cluster indices to human-readable names:

```text
data/clustering/cluster_labels.txt
```

### 1.4 Primary implementation

Fitting:

```text
src/cluster_scenarios.py
```

Assignment of new generated scenarios:

```text
src/eval_adv_gen.py
```

Scenario loading:

```text
src/datasets/utils.py
```

### 1.5 Authors, date, and license

STRIVE was released with the CVPR 2022 paper by:

- Davis Rempe
- Jonah Philion
- Leonidas J. Guibas
- Sanja Fidler
- Or Litany

The STRIVE source code is MIT licensed. Any local model artifact created from D-02 scenarios should also respect the licensing/provenance obligations of those generated scenarios and their nuScenes-derived source.

---

## 2. Purpose & Role in STRIVE

### 2.1 Primary purpose

M-03 groups generated collisions into recurring geometric patterns to help answer questions such as:

- What kinds of collisions does STRIVE generate?
- Are generated failures concentrated in a small number of geometric modes?
- How does solution success vary across collision types?
- Which collision classes are common in a new generated-scenario set?

### 2.2 Role in analysis

The clustering supports:

- scenario-distribution plots;
- per-scenario cluster assignment;
- semantic collision-type labels;
- comparison of `adv_sol_success` and `sol_failed`;
- downstream scenario classification.

### 2.3 Relationship to D-02

M-03 consumes D-02 **collision scenarios**, normally:

```text
adv_sol_success
sol_failed
```

because both partitions contain C-02 adversarial successes.

`adv_failed` scenarios are not suitable for the released collision-feature extraction because no planner collision is guaranteed.

### 2.4 Relationship to M-04

The public evaluator uses the fitted M-03 K-means object to classify new collision scenarios and combines cluster indices with human-authored semantic labels.

In this documentation hierarchy, M-04 formalizes that downstream classification behavior.

---

## 3. Intended Use

### 3.1 Intended uses

Appropriate uses include:

- exploratory analysis of generated collision modes;
- organizing D-02 scenarios;
- assigning collision-type labels to newly generated scenarios;
- comparing collision distributions across planners/configurations;
- selecting representative generated scenarios for qualitative review.

### 3.2 Intended users

Researchers analyzing:

- autonomous-driving planner robustness;
- generated collision scenarios;
- simulation-based failure taxonomies;
- STRIVE outputs.

### 3.3 Out-of-scope uses

M-03 should not be interpreted as:

- a validated taxonomy of real-world crashes;
- a calibrated accident-severity model;
- a safety score;
- a causal model of collisions;
- evidence that cluster prevalence in D-02 reflects real-world prevalence.

---

## 4. Input Data

### 4.1 Scenario partitions used

The README demonstrates fitting clustering on:

```text
scenario_results/adv_sol_success
scenario_results/sol_failed
```

This includes all generated scenarios where adversarial optimization caused a collision, whether or not C-03 found a solution.

### 4.2 Required scenario fields

The fitting loader requires:

```text
map
dt
lw
past
fut_adv
```

and optionally loads:

```text
attack_t
sem
```

The clustering feature extraction itself uses:

```text
lw
fut_adv
dt
```

### 4.3 Collision-only requirement

`compute_coll_feat()` assumes at least one collision between the planner and another agent.

It selects collision entries returned by `check_single_veh_coll()` and then takes the earliest interpolated collision.

If no collision is present, operations such as `np.amin()` on the empty collision-time array would not define a valid feature.

Therefore the public clustering workflow should be applied to C-02-success scenarios.

### 4.4 Data provenance

Every fitted clustering should record:

- D-02 dataset/profile;
- planner/configuration(s);
- source nuScenes split/subset;
- traffic-model checkpoint;
- STRIVE code revision.

The public README states that the supplied paper clustering was fitted on **over 400 scenarios** generated from various nuScenes subsets and using many versions of the rule-based planner.

That statement describes the clustering source collection, not a single homogeneous D-02 generation run.

---

## 5. Feature Extraction

### 5.1 Earliest collision selection

The feature extractor first finds collisions between:

```text
planner = scene_traj[0]
other agents = scene_traj[1:]
```

After temporal interpolation, it identifies the earliest collision time and corresponding colliding agent.

If several collisions occur, only the **earliest** one determines the clustering feature.

### 5.2 Temporal interpolation

Before collision detection:

```text
interp_scale = 5
```

At D-02's standard:

```text
dt = 0.5 s
```

the effective interpolated spacing is:

```text
0.1 s
```

This interpolation improves the estimate of collision timing and geometry relative to the native 2 Hz trajectory.

### 5.3 Relative collision direction

At the earliest collision, the colliding agent state is transformed into the planner's local coordinate frame.

The relative position is normalized to unit length:

```text
angvec =
    local_attacker_position /
    ||local_attacker_position||
```

This contributes two feature components:

```text
angvec_x
angvec_y
```

Magnitude/distance at collision is discarded.

### 5.4 Relative attacker heading

The transformed attacker heading vector contributes:

```text
hvec_x
hvec_y
```

The public feature extractor also computes the angle with `atan2`, but the K-means input uses the two-dimensional heading vector rather than the scalar angle.

### 5.5 Feature vector

The exact fitted vector is:

```text
[
  angvec_x,
  angvec_y,
  hvec_x,
  hvec_y
]
```

or:

```text
scene_feats = concatenate([angvec, hvec], axis=1)
```

Dimension:

```text
4
```

### 5.6 Excluded information

The released K-means does **not** directly use:

- collision speed;
- relative speed;
- agent class;
- map/location;
- absolute trajectory position;
- attack time;
- prior likelihood;
- planner acceleration;
- solution success;
- vehicle size;
- full trajectory history.

`eval_adv_gen.py` computes relative collision speed for broader quantitative analysis, but it is not part of the M-03 clustering feature.

---

## 6. Model Architecture / Algorithm

### 6.1 Algorithm

Public fitting code:

```python
KMeans(n_clusters=k, random_state=0).fit(scene_feats)
```

### 6.2 Number of clusters

Parser default:

```text
k = 10
```

The public semantic label file contains exactly 10 labels, matching the paper clustering's cluster indices.

### 6.3 Initialization/randomness

The source explicitly fixes:

```text
random_state = 0
```

All other K-means constructor parameters are inherited from the installed scikit-learn version.

This matters because defaults such as initialization behavior and `n_init` have changed across scikit-learn releases.

### 6.4 Distance metric

Standard scikit-learn K-means minimizes within-cluster squared Euclidean distance.

Because both the collision direction and heading components are unit-vector-like representations, the four feature dimensions are geometrically bounded but are not separately standardized before clustering.

### 6.5 Fitted state

A fitted K-means artifact includes, depending on scikit-learn version:

- `cluster_centers_`;
- `labels_`;
- `inertia_`;
- `n_iter_`;
- feature-count metadata;
- constructor parameters.

The public script saves the whole estimator with Python `pickle`.

---

## 7. Training / Fitting Procedure

### 7.1 Training script

```text
src/cluster_scenarios.py
```

### 7.2 Training command

The README gives the example:

```bash
python src/cluster_scenarios.py \
  --scenario_dirs \
    ./out/adv_gen_rule_based_out/scenario_results/adv_sol_success \
    ./out/adv_gen_rule_based_out/scenario_results/sol_failed \
  --out ./out/rule_based_clustering
```

### 7.3 Scenario loading

The script uses:

```text
datasets.utils.read_adv_scenes
```

which maps JSON fields into:

```text
veh_att
scene_past
scene_fut
dt
map
```

with `scene_fut` loaded from `fut_adv`.

### 7.4 Feature assembly

For each scene:

1. interpolate trajectories ×5;
2. detect planner-other collisions;
3. choose earliest collision;
4. transform attacker into planner-local frame;
5. normalize relative collision position;
6. extract local attacker heading;
7. concatenate to four dimensions.

### 7.5 K-means fit

The model is fitted in one call:

```text
KMeans(n_clusters=k, random_state=0).fit(scene_feats)
```

and saved to:

```text
cluster.pkl
```

### 7.6 Visualization option

With:

```text
--viz
```

the script renders each scenario to video and then moves videos into per-cluster directories.

It also writes:

```text
cluster_k<k>.jpg
```

showing collision-direction and attacker-heading vectors by cluster.

---

## 8. Public Precomputed Clustering

### 8.1 Artifact location

The repository README identifies the paper clustering under:

```text
data/clustering
```

including:

```text
cluster.pkl
cluster_labels.txt
```

### 8.2 Semantic label file

The released `cluster_labels.txt` contains these labels in cluster-index order:

| Cluster index | Label |
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

These names are post-hoc semantic descriptions paired with the numerical clustering artifact.

### 8.3 Source scenario set

The README states that the exact clustering used in the paper was performed on:

```text
over 400 scenarios
```

generated:

- from various subsets of nuScenes; and
- using many versions of the rule-based planner.

This means the public cluster model is intentionally broader than a single final-planner D-02 run.

### 8.4 Reuse on new scenarios

`eval_adv_gen.py` loads `cluster.pkl`, extracts the same four-dimensional collision features from new D-02 collision scenarios, and calls:

```text
clustering.predict(scene_feats)
```

The predicted integer index is then mapped through `cluster_labels.txt`.

---

## 9. Outputs

### 9.1 Cluster model

Primary fitted artifact:

```text
cluster.pkl
```

### 9.2 Cluster assignments

For a fitted dataset:

```text
clustering.labels_
```

For new scenarios:

```text
clustering.predict(scene_feats)
```

### 9.3 Semantic labels

The semantic label is:

```text
cluster_labels[cluster_index]
```

The pickle and label file therefore form a paired artifact set.

### 9.4 Visualization artifacts

Fitting can emit:

```text
cluster_k10.jpg
```

and, with `--viz`, cluster-specific scenario videos.

### 9.5 Downstream labels

`eval_adv_gen.py` writes per-partition CSV files containing:

```text
scene
cluster_idx
cluster_name
```

for:

```text
adv_sol_success
sol_failed
```

when present.

---

## 10. Evaluation & Analysis

### 10.1 Cluster counts

A basic audit should report:

- count per cluster;
- fraction per cluster;
- count split by `adv_sol_success` vs `sol_failed`.

### 10.2 Centroid analysis

Each centroid is a four-dimensional vector:

```text
[collision_direction_x,
 collision_direction_y,
 attacker_heading_x,
 attacker_heading_y]
```

Centroids can be converted to angles for interpretation, but those angles are derived views of the fitted vector representation.

### 10.3 Distribution by solution status

The public evaluator compares cluster distributions between:

```text
Solution Found   = adv_sol_success
No Solution      = sol_failed
```

This can reveal whether particular geometric collision modes are more or less associated with C-03 solution success in a given generated dataset.

### 10.4 Stability analysis

The public release does not provide a formal stability study.

For local re-fitting, useful checks include:

- alternative random seeds;
- alternative `k`;
- planner subsets;
- bootstrap samples;
- cluster-centroid matching across runs.

Because cluster IDs are arbitrary, cross-run comparisons require centroid/semantic matching rather than direct ID equality.

### 10.5 Coverage analysis

The released feature definition requires a detected collision. `adv_failed` scenarios therefore fall outside the natural M-03 training/assignment domain.

---

## 11. Quantitative Analysis

### 11.1 Training-set size

The public README only gives:

```text
over 400 scenarios
```

for the paper clustering source collection.

A local fitted artifact should record its exact row count.

### 11.2 Feature statistics

Recommended profile outputs:

- min/max/mean/std for each of the four feature dimensions;
- norm checks for `angvec` and `hvec`;
- duplicate feature count;
- non-finite feature count.

### 11.3 Cluster membership distribution

For a fitted model, profile:

```text
count
fraction
```

per cluster index and semantic label.

### 11.4 Centroid coordinates

Record the exact:

```text
cluster_centers_
```

because they are the core reusable state for prediction.

### 11.5 Inertia

Record:

```text
inertia_
```

from the fitted K-means artifact.

This measures within-cluster squared distance for the fitting data but is not a standalone measure of semantic validity.

### 11.6 Iterations

Record:

```text
n_iter_
```

when available.

### 11.7 Optional diagnostics

Silhouette score or other clustering diagnostics may be useful for local analysis, but they are not part of the public STRIVE training script and should be labeled as added diagnostics.

### 11.8 Profiler

Run static source/label profiling:

```bash
python tools/profile_clustering.py \
  --repo-root . \
  --output ./out/clustering_profile.yaml
```

Optionally inspect a trusted local pickle:

```bash
python tools/profile_clustering.py \
  --repo-root . \
  --cluster-pkl ./data/clustering/cluster.pkl \
  --output ./out/clustering_profile.yaml
```

The profiler only unpickles a model when `--cluster-pkl` is explicitly supplied. Python pickle files can execute code during loading; only inspect a trusted local artifact.

---

## 12. Label Semantics

### 12.1 Cluster index vs semantic name

K-means itself produces integer IDs with no semantic meaning.

Labels such as:

```text
Head On
T-Bone Left
Merge from Right
```

are human-authored names assigned after clustering.

### 12.2 Label ordering

`eval_adv_gen.py` reads the label file as a comma-separated list and uses:

```text
cluster_labels[scene_label]
```

Therefore list order must exactly match cluster-index order.

### 12.3 Human interpretation

The labels summarize the geometry represented by cluster centroids and example scenes. They are not independently learned class names.

### 12.4 Relabeling risks

Using a label file from one `cluster.pkl` with a different fitted model can silently produce incorrect semantic names.

Treat these as a versioned pair:

```text
cluster.pkl
cluster_labels.txt
```

---

## 13. Factors

### 13.1 Planner dependence

D-02 collision geometry depends on the planner that was attacked.

The public clustering source set used many versions of the STRIVE rule-based planner, so its centroids reflect that mixed planner-generation distribution.

### 13.2 Agent-category dependence

A clustering fitted on car/truck scenarios may not describe pedestrian/cyclist collision geometry equally well.

### 13.3 Geographic dependence

All scenarios remain downstream of nuScenes/D-01 and its geographic coverage.

### 13.4 Collision-detection dependence

Features depend on:

- STRIVE interpolation;
- oriented vehicle collision checking;
- earliest-collision selection.

Changing the collision detector can change both the chosen attacker and the feature vector.

### 13.5 Dataset-composition dependence

Cluster centers depend strongly on the mix of:

- planner versions;
- nuScenes subsets;
- result partitions;
- categories;
- generation settings.

---

## 14. Limitations

### 14.1 Low-dimensional features

M-03 intentionally reduces each collision to four geometry values.

It ignores many factors that may matter for safety analysis, including speed, road context, agent class, and full temporal evolution.

### 14.2 Fixed k

The default/paper taxonomy uses 10 clusters.

`k=10` is a modeling choice, not evidence that exactly ten fundamental accident types exist.

### 14.3 K-means geometry

K-means partitions feature space using Euclidean distance around centroids. It does not model:

- non-spherical clusters;
- uncertainty;
- density;
- hierarchy.

### 14.4 Arbitrary cluster indices

Cluster IDs can permute across retraining even when the geometric solution is similar.

### 14.5 Training-set composition

The paper clustering mixes more than 400 scenarios from multiple nuScenes subsets and planner versions. This increases variety but complicates interpretation of its empirical distribution.

### 14.6 Synthetic-data dependence

The clusters summarize STRIVE-generated collisions. Their prevalence should not be interpreted as prevalence in real-world crash data.

### 14.7 Scikit-learn version not pinned

`src/cluster_scenarios.py` imports:

```text
sklearn.cluster.KMeans
```

but the inspected public `requirements.txt` does not list or pin `scikit-learn`.

Because KMeans defaults have changed across scikit-learn versions, exact refitting can depend on the locally installed version despite `random_state=0`.

For reproduction, explicitly record:

```text
scikit-learn version
KMeans.get_params()
```

from the fitted artifact/environment.

### 14.8 Pickle portability and security

`cluster.pkl` is a Python pickle. It can be sensitive to Python/scikit-learn version changes and must not be loaded from an untrusted source.

---

## 15. Ethical & Safety Considerations

### 15.1 Interpretation

Cluster names describe synthetic collision geometry; they do not establish real-world accident causes, severity, or frequency.

### 15.2 Bias

M-03 inherits bias from:

- D-01;
- M-01;
- planner choice;
- D-02 feasibility filtering;
- adversarial optimization;
- selected collision-only training data.

### 15.3 Misuse

Cluster membership should not be used alone as:

- a vehicle safety score;
- a driver-risk score;
- a real-world accident probability;
- evidence of fault.

---

## 16. Reproducibility

### 16.1 Source files

```text
src/cluster_scenarios.py
src/eval_adv_gen.py
src/datasets/utils.py
src/losses/adv_gen_nusc.py
src/utils/transforms.py
```

### 16.2 Input data

Document exact D-02 directories used for fitting.

The README's example uses:

```text
adv_sol_success
sol_failed
```

### 16.3 Configuration

Core fitting parameters:

```text
scenario_dirs
k
viz
```

with:

```text
k default = 10
random_state = 0  # hard-coded
interp_scale = 5 # hard-coded
```

### 16.4 Saved artifacts

```text
cluster.pkl
cluster_labels.txt
```

### 16.5 Companion metadata

```text
metadata/models/clustering.yaml
```

### 16.6 Quantitative profiler

```text
tools/profile_clustering.py
```

The profiler reports:

- source hashes;
- detected source constants;
- semantic labels;
- requirements coverage;
- optional trusted pickle hash/size;
- estimator class;
- scikit-learn version at inspection time;
- constructor parameters when available;
- cluster-center shape/values;
- label counts;
- inertia;
- iteration count.

### 16.7 Dependency versions

The public requirements pin many STRIVE dependencies but do not pin scikit-learn.

A reproducible M-03 build should explicitly record:

```text
Python version
NumPy version
scikit-learn version
```

and ideally the full KMeans parameter set.

---

## 17. Relationships

### 17.1 Upstream

```text
D-02 — Generated Scenarios Data Card
```

### 17.2 Downstream

```text
M-04 — Accident Classifier
```

### 17.3 Dependency chain

```text
D-02  Generated Scenarios
  │
  ▼
M-03  Scenario Clustering
  │
  ▼
M-04  Accident Classifier
```

---

## 18. Terms of Art

### 18.1 Collision direction

The normalized direction from planner position to colliding-agent position at the earliest interpolated collision, expressed in the planner's local frame.

### 18.2 Relative attacker heading

The colliding agent's heading vector expressed in the planner-local frame at the earliest interpolated collision.

### 18.3 Cluster index

The numerical K-means assignment.

The index has no intrinsic ordinal meaning.

### 18.4 Cluster label

A human-authored semantic name paired with one cluster index.

### 18.5 Paper clustering

The supplied precomputed clustering in `data/clustering`, fitted on the mixed set of over 400 generated scenarios described in the README.

---

## 19. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.  
   https://openaccess.thecvf.com/content/CVPR2022/html/Rempe_Generating_Useful_Accident-Prone_Driving_Scenarios_via_a_Learned_Traffic_Prior_CVPR_2022_paper.html

2. STRIVE public repository.  
   https://github.com/nv-tlabs/STRIVE

3. Relevant release files:
   - `src/cluster_scenarios.py`
   - `src/eval_adv_gen.py`
   - `src/datasets/utils.py`
   - `data/clustering/cluster.pkl`
   - `data/clustering/cluster_labels.txt`
   - `requirements.txt`

4. D-02 — Generated Scenarios Data Card.

---

## 20. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed M-03 for the public STRIVE clustering workflow, including exact 4-D features, ten semantic labels, paper-clustering provenance, and dependency/reproducibility constraints. |
