# D-02 — Generated Scenarios Data Card for STRIVE

> **Card ID:** D-02  
> **Card type:** Data Card  
> **Status:** Complete for the public STRIVE release  
> **Dataset:** STRIVE Generated Scenarios  
> **Upstream:** C-02 — Adversarial Optimization, C-03 — Solution Optimization  
> **Downstream:** M-03 — Clustering, M-04 — Accident Classifier  
> **Primary serializer:** `src/utils/scenario_gen.py::prepare_output_dict`

---

## 1. Summary

### 1.1 Dataset summary

D-02 documents the JSON scenario artifacts produced by STRIVE adversarial scenario generation.

Each saved example contains a source-scene history plus one or more future variants:

- the fitted initialization future;
- the adversarial future;
- when adversarial optimization succeeds and solution optimization is attempted, a solution future;
- latent variables and prior parameters used to represent the generated scenario;
- attack metadata and agent/map metadata.

These records are **synthetic, optimization-generated scenarios derived from nuScenes**, not observed accident records.

### 1.2 Role in the STRIVE pipeline

```text
D-01  nuScenes source data
  │
  ▼
M-01  learned traffic prior
  │
  ▼
C-01  initialization optimization
  │
  ▼
C-02  adversarial optimization
  │
  ▼
C-03  solution optimization
  │
  ▼
D-02  generated scenario JSON
  │
  ├── M-03 clustering
  └── M-04 accident/scenario classification workflow
```

The public STRIVE repository directly supports clustering and cluster-based classification of generated collision scenarios through `cluster_scenarios.py` and `eval_adv_gen.py`. In this documentation hierarchy, D-02 is also the data dependency for the later M-04 card.

### 1.3 Dataset unit

The primary unit is one JSON file:

```text
scene_XXXX.json
```

representing one source scene/window and the trajectories produced at different optimization stages.

### 1.4 Scenario result partitions

Generated scenarios are stored under:

```text
scenario_results/
├── adv_failed/
├── sol_failed/
└── adv_sol_success/
```

Interpretation:

- `adv_failed`: C-02 did not produce the selected-attacker collision; C-03 was not run.
- `sol_failed`: C-02 succeeded, C-03 was run, but the returned solution still failed the C-03 success check.
- `adv_sol_success`: both C-02 and C-03 succeeded.

---

## 2. Authorship

### 2.1 Dataset creators

The public STRIVE project was authored by:

- Davis Rempe
- Jonah Philion
- Leonidas J. Guibas
- Sanja Fidler
- Or Litany

### 2.2 Upstream dataset dependency

The generated scenarios are derived from nuScenes through the D-01 preprocessing and split logic.

### 2.3 Generation-system dependency

D-02 depends on:

- M-01 — Main Traffic Model;
- C-01 — Initialization Optimization;
- C-02 — Adversarial Optimization;
- C-03 — Solution Optimization.

Changing any of those can change generated trajectories or success partitions.

### 2.4 Maintenance

The public release is maintained through the STRIVE repository and its downloadable scenario bundle. A local derived D-02 dataset should record its own generation date, code revision, traffic-model checkpoint, planner configuration, and generation configuration.

---

## 3. Dataset Overview

### 3.1 Dataset source

D-02 is generated rather than directly collected.

The public README states that STRIVE provides generated scenarios corresponding to Sections 5.1/5.2 of the paper **where both adversarial and solution optimization succeeded**. The README instructs users to place that download under:

```text
data/strive_scenarios
```

A locally generated dataset can additionally contain `adv_failed` and `sol_failed` records.

### 3.2 Generation pipeline

A scenario originates from a D-01 scene/window and is processed through:

1. M-01 embedding and sampling;
2. feasibility filtering;
3. C-01 fitting to the source/planner initialization;
4. C-02 adversarial latent optimization;
5. C-02 final collision check;
6. C-03 solution optimization for C-02 successes;
7. C-03 final solution check;
8. JSON serialization.

### 3.3 Planner variants

The public code supports at least:

```text
ego      — replay of observed nuScenes ego future
hardcode — STRIVE rule-based planner
```

The planner and planner configuration are generation provenance even though they are not written as explicit fields inside each scenario JSON by `prepare_output_dict()`.

### 3.4 Agent-category variants

The main paper traffic model uses:

```text
car
truck
```

The repository also provides replay configurations supporting additional categories such as cyclists/pedestrians. The semantic encoding in each JSON is therefore configuration-dependent.

### 3.5 Temporal resolution

The serializer stores:

```text
dt
```

from the dataset.

For the primary nuScenes configuration:

```text
dt = 0.5 seconds
```

or 2 Hz.

The standard saved future horizon is 12 steps / 6 seconds in the released main model workflow.

---

## 4. Example of Data Points

### 4.1 Scenario JSON structure

Conceptual example:

```json
{
  "N": 6,
  "dt": 0.5,
  "map": "boston-seaport",
  "lw": [[...], "..."],
  "sem": [[...], "..."],
  "past": [[["..."]]],
  "fut_init": [[["..."]]],
  "fut_adv": [[["..."]]],
  "fut_internal_ego": [["..."]],
  "fut_sol": [[["..."]]],
  "attack_agt": 2,
  "attack_t": 8,
  "z_adv": [[...]],
  "z_sol": [[...]],
  "z_prior": {
    "mean": [[...]],
    "var": [[...]]
  }
}
```

The exact number of agents, semantic dimensions, and optional fields vary by scenario/configuration.

### 4.2 Initialization trajectory

`fut_init` stores the fitted initialization future after C-01 and any planner-specific initialization handling.

Shape:

```text
[N, FT, 4]
```

with state fields:

```text
x, y, heading_x, heading_y
```

in unnormalized coordinates.

### 4.3 Adversarial trajectory

`fut_adv` stores the final C-02 scenario.

For rule-based generation, the planner row is the actual final planner rollout rather than M-01's internal target approximation.

Shape:

```text
[N, FT, 4]
```

### 4.4 Solution trajectory

`fut_sol` is serialized when C-02 succeeded and C-03 was attempted.

Therefore it is expected in both:

```text
adv_sol_success
sol_failed
```

and normally absent from:

```text
adv_failed
```

In the public implementation C-03 optimizes the planner with a 16-step horizon but returns/serializes the default 12-step M-01 horizon.

### 4.5 Latent fields

`z_adv` stores C-02's final per-agent latent representation.

`z_sol` stores C-03's returned per-agent latent representation when C-03 was attempted.

`z_prior` stores:

```text
mean
var
```

for the M-01 conditional latent prior used by the generation process.

### 4.6 Attack metadata

`attack_agt` is the selected attacker index, local to the serialized scene.

`attack_t` is the selected adversarial attack timestep.

The stored attacker identifies the C-02 selected agent. Downstream evaluation can independently recompute which vehicle collides first.

### 4.7 Agent metadata

Core metadata includes:

- `N`: number of agents;
- `dt`: timestep duration;
- `map`: STRIVE map identifier;
- `lw`: unnormalized agent length/width;
- `sem`: semantic one-hot vectors;
- `past`: unnormalized full past state sequence.

The first agent/node is the planner/ego target under the generation conventions used by C-02/C-03.

---

## 5. Motivations & Intentions

### 5.1 Why the dataset is generated

The dataset exists to support controlled robustness analysis using challenging traffic situations that are optimized to cause planner failures while remaining constrained by a learned traffic prior.

### 5.2 Intended research uses

Appropriate uses include:

- planner stress testing;
- analysis of generated collision types;
- comparison of initialization/adversarial/solution trajectories;
- scenario clustering;
- scenario classification;
- studying traffic-prior likelihood and kinematics.

### 5.3 Downstream use by M-03

The README demonstrates clustering using:

```text
adv_sol_success
sol_failed
```

because both partitions contain scenarios where C-02 caused a collision.

The public clustering uses collision-relative features derived from `fut_adv` and vehicle dimensions.

### 5.4 Downstream classification

`eval_adv_gen.py` assigns newly generated collision scenarios to a precomputed clustering and writes scenario labels.

The repository README calls this quantitative evaluation and classification. The public repository does not expose a separate source file explicitly named an "accident classifier"; the later M-04 card should distinguish the documented hierarchy's classifier abstraction from the public cluster-based classification implementation.

### 5.5 Out-of-scope uses

D-02 should not be used as:

- a real-world accident-frequency dataset;
- an epidemiological or insurance dataset;
- a calibrated estimate of crash probability;
- proof of causal planner defects;
- a safety-certification dataset without additional validation.

---

## 6. Access, Retention & Distribution

### 6.1 Public release

The STRIVE README provides a downloadable scenario bundle for scenarios from paper Sections 5.1/5.2 where both adversarial and solution optimization succeeded.

Recommended placement:

```text
data/strive_scenarios
```

### 6.2 Local output path

Locally generated scenarios are written below the configured output directory under:

```text
scenario_results/
```

with the three result partitions documented above.

### 6.3 Redistribution

The README states that generated scenarios are derived from nuScenes and are separately licensed under:

```text
CC-BY-NC-SA-4.0
```

Upstream nuScenes terms should also be reviewed for the intended use.

### 6.4 Retention

STRIVE does not define an application-level retention policy for locally generated JSON files. Retention is therefore an operator/research-project decision subject to applicable licenses and governance requirements.

### 6.5 Deletion

Generated scenarios are ordinary local files/directories. Removing the relevant local output/scenario directory removes that local copy; external backups or previously redistributed copies must be managed separately.

---

## 7. Provenance

### 7.1 Source dataset

Primary source:

```text
D-01 — nuScenes Data Card for STRIVE
```

### 7.2 Source model

Primary model:

```text
M-01 — Main Traffic Model
```

A reproducible local dataset should record the actual checkpoint SHA-256.

### 7.3 Generation components

Generation depends on:

```text
C-01
C-02
C-03
```

and the precise public-release behaviors documented in those cards.

### 7.4 Planner provenance

At minimum record:

```text
planner
planner_cfg
```

For the main released rule-based config:

```yaml
planner: hardcode
planner_cfg: default
```

### 7.5 Configuration provenance

Record the exact config used, including:

- source split;
- validation-set size;
- sequence interval;
- optimization iteration count;
- learning rate;
- loss weights;
- solution horizon;
- feasibility settings.

### 7.6 Code revision

The public source inspected for this card corresponds to STRIVE repository revision:

```text
b708951f8665c97a1de9ed93b4ed3f58dd8cbf5d
```

A local D-02 build should record its actual code revision rather than assuming this revision.

---

## 8. Generation & Selection Criteria

### 8.1 Source scene selection

The released rule-based config uses:

```yaml
data_version: trainval
split: val
val_size: 400
seq_interval: 10
shuffle: false
```

At 2 Hz, `seq_interval: 10` means candidate windows begin approximately 5 seconds apart.

### 8.2 Feasibility filtering

Before optimization, STRIVE samples 20 M-01 futures, including the prior mean, and performs feasibility screening based on:

- proximity to the planner;
- minimum eligible attack time;
- relative in-front constraint;
- map/non-drivable separation when enabled;
- meaningful ego/planner motion.

As documented in C-02, the released caller passes `0.0` rather than the configured `feasibility_vel` to the candidate-agent velocity argument of `determine_feasibility_nusc()`.

### 8.3 Adversarial success filtering

C-02 success is determined using the selected attacker and the actual final planner trajectory.

A vehicle collision is detected with oriented vehicle polygon IoU:

```text
IoU > 0.02
```

### 8.4 Solution success filtering

For C-02 successes, C-03 is marked successful only when the returned planner solution:

- does not collide with any other agent; and
- does not collide with the environment under the default map check.

### 8.5 Result partition assignment

The caller uses:

```text
if adversarial failed:
    adv_failed
elif solution succeeded:
    adv_sol_success
else:
    sol_failed
```

### 8.6 Saved vs discarded cases

Not every source scene/window becomes a JSON record.

Scenes can be skipped before optimization when, for example:

- no feasible attacker exists;
- only the ego agent is present;
- ego/planner motion is below the required threshold;
- requested attacker category is unavailable;
- rule-based planner initialization already creates a collision and the scene is rejected.

Thus D-02 is a selected subset of source windows, not a simple transformation of all D-01 samples.

---

## 9. Processing & Transformation

### 9.1 Trajectory normalization/unnormalization

`prepare_output_dict()` unnormalizes before serialization:

- `past`;
- `fut_init`;
- `fut_adv`;
- `fut_sol`;
- `fut_internal_ego`;
- `lw`.

Therefore stored trajectory and physical-size values are in the model's unnormalized coordinate/measurement representation.

### 9.2 Planner trajectory replacement

For the final rule-based adversarial scenario, C-02 replaces the target row with the actual rule-based planner rollout before serialization.

`fut_internal_ego`, when present, preserves M-01's internal target/planner prediction for comparison.

### 9.3 Non-planner solution preservation

C-03 restores non-planner rows in `fut_sol` from the C-02 adversarial trajectories before returning them.

Thus the saved solution counterfactual is designed to preserve the adversarial surrounding traffic while changing the planner response.

### 9.4 Latent serialization

PyTorch tensors are detached, moved to CPU, converted to NumPy, then to nested JSON lists.

### 9.5 Semantic encoding

`sem` is stored as the numeric one-hot representation from the scene graph.

The JSON does not itself store a category-name vocabulary. Correct decoding therefore requires the generation configuration/dataset category ordering.

### 9.6 Map identifier

`map` stores the string from:

```text
map_env.map_list[map_idx]
```

and is later resolved by evaluation code through the current map environment's `map_list`.

---

## 10. Dataset Structure & Schema

### 10.1 Directory structure

Local generation:

```text
<generation_out>/
└── scenario_results/
    ├── adv_failed/
    │   └── scene_XXXX.json
    ├── sol_failed/
    │   └── scene_XXXX.json
    └── adv_sol_success/
        └── scene_XXXX.json
```

The separately downloadable public bundle described in the README contains paper scenarios where both adversarial and solution optimization succeeded, so it should not automatically be assumed to contain all three local-generation partitions.

### 10.2 Filename convention

The caller writes:

```text
scene_%04d.json
```

where the integer is the source dataset iteration index used by the generation run.

The filename is not a globally unique nuScenes token.

### 10.3 Core fields

Expected core fields from `prepare_output_dict()`:

| Field | Meaning | Typical shape/type |
|---|---|---|
| `N` | agent count | integer |
| `dt` | seconds per timestep | float |
| `map` | map identifier | string |
| `lw` | length/width | `[N, 2]` |
| `sem` | semantic one-hot vectors | `[N, C]` |
| `past` | source past state | `[N, PT, 6]` |
| `fut_init` | C-01/init future | `[N, FT, 4]` |
| `fut_adv` | C-02 adversarial future | `[N, FT, 4]` |

### 10.4 Conditional fields

| Field | Expected when |
|---|---|
| `fut_internal_ego` | supplied by caller; used by STRIVE generation for internal planner comparison |
| `fut_sol` | C-02 succeeded and C-03 was attempted |
| `attack_agt` | attacker selected |
| `attack_t` | attack timestep selected |
| `z_adv` | adversarial latent supplied |
| `z_sol` | solution latent supplied |
| `z_prior.mean` | prior supplied |
| `z_prior.var` | prior supplied |
| `attack_bike_prof` | bicycle-profile baseline workflow, when applicable |

### 10.5 Field shapes

For the main model:

```text
PT = 4
FT = 12
D  = 32
```

Typical shapes:

```text
past                  [N, 4, 6]
fut_init              [N, 12, 4]
fut_adv               [N, 12, 4]
fut_sol               [N, 12, 4]
fut_internal_ego      [12, 4]
lw                    [N, 2]
z_adv                 [N, 32]
z_sol                 [N, 32]
z_prior.mean          [N, 32]
z_prior.var           [N, 32]
```

Do not assume these dimensions for alternate model/category/horizon configurations without validation.

### 10.6 Data types

JSON contains:

- numbers;
- strings;
- nested arrays;
- nested objects for `z_prior`.

There are no PyTorch-specific binary objects in the serialized scenario JSON.

---

## 11. Quantitative Analysis

### 11.1 Scenario counts

Counts must be measured from the specific scenario bundle being documented.

The public repository README does not state an exact count for the downloadable Section 5.1/5.2 success-only bundle in the inspected text.

Separately, the README states that the provided paper clustering in:

```text
data/clustering
```

was fitted using a **large set of over 400 scenarios** generated from various nuScenes subsets and many versions of the rule-based planner. That statement describes the clustering source collection and should not be treated as the exact size of a particular D-02 bundle.

### 11.2 Counts by result partition

For a local generation output, profile:

```text
adv_failed
sol_failed
adv_sol_success
```

separately.

### 11.3 Agent-count distribution

Useful statistics:

- minimum/maximum `N`;
- mean/median `N`;
- percentiles;
- count of single-agent cases if any serialized cases exist.

### 11.4 Map/location distribution

Count scenarios by stored `map`.

This helps identify geographic imbalance inherited from D-01 and generation filtering.

### 11.5 Attack metadata distribution

Profile:

- `attack_agt`;
- `attack_t`;
- selected attacker's semantic vector/category when the category vocabulary is known.

### 11.6 Success rates

The public evaluator defines:

```text
N_total = |adv_failed| + |sol_failed| + |adv_sol_success|

N_adv_success = |sol_failed| + |adv_sol_success|

adversarial_success_rate =
    N_adv_success / N_total

solution_success_rate =
    |adv_sol_success| / N_adv_success

total_success_rate =
    adversarial_success_rate × solution_success_rate
```

The solution rate is conditional on adversarial success.

### 11.7 Collision statistics

`eval_adv_gen.py` can compute:

- whether the adversarial trajectory collided;
- non-planner vehicle collision rate before first planner collision;
- attacker environment collision;
- other-agent environment collision.

### 11.8 Kinematic statistics

The public evaluator computes acceleration-related plausibility metrics for:

- attacker;
- other controlled agents.

It derives velocity/acceleration from stored `fut_adv`, headings, and `dt`.

### 11.9 Latent statistics

When latent fields are present, the evaluator measures:

- attacker latent log likelihood under M-01 prior;
- other-agent latent log likelihood;
- planner internal matching errors when `fut_internal_ego` is present.

### 11.10 Profiler

The companion profiler operates directly on JSON files and does not require PyTorch or nuScenes.

Run on a complete local generation result:

```bash
python tools/profile_generated_scenarios.py \
  --scenarios ./out/adv_gen_rule_based_out/scenario_results \
  --output ./out/generated_scenarios_profile.yaml
```

Run on a single success-only public bundle:

```bash
python tools/profile_generated_scenarios.py \
  --scenarios ./data/strive_scenarios \
  --assume-partition adv_sol_success \
  --output ./out/generated_scenarios_profile.yaml
```

To merge measurements into metadata:

```bash
python tools/profile_generated_scenarios.py \
  --scenarios ./out/adv_gen_rule_based_out/scenario_results \
  --metadata ./metadata/data/generated_scenarios.yaml
```

---

## 12. Validation & Quality Assurance

### 12.1 Schema validation

Validate core fields:

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

and conditional fields according to result partition.

### 12.2 Shape validation

At minimum verify:

```text
len(lw)       == N
len(sem)      == N
len(past)     == N
len(fut_init) == N
len(fut_adv)  == N
```

and, if present:

```text
len(fut_sol)  == N
len(z_adv)    == N
len(z_sol)    == N
len(z_prior.mean) == N
len(z_prior.var)  == N
```

### 12.3 Finite-value checks

Generated JSON should be checked recursively for:

```text
NaN
Infinity
-Infinity
```

Python's JSON parser may accept non-standard NaN values depending on producer/settings, so validation should not assume valid JSON numbers are automatically finite.

### 12.4 Collision validation

When full STRIVE geometry utilities are available, recompute:

- adversarial collision;
- selected-attacker collision;
- solution vehicle collisions;
- solution map collision.

The lightweight D-02 profiler intentionally performs schema/statistical checks only and does not reimplement STRIVE geometry.

### 12.5 Partition consistency

Expected release behavior:

- `adv_failed`: no C-03 solution fields expected;
- `sol_failed`: C-03 was attempted, so `fut_sol`/`z_sol` are normally present;
- `adv_sol_success`: C-03 was attempted and succeeded, so `fut_sol`/`z_sol` are normally present.

### 12.6 Map/category consistency

Validate:

- non-empty map identifier;
- consistent semantic-vector width within a dataset;
- category vocabulary against the generation configuration.

### 12.7 Provenance validation

For a reproducible local release, record:

- dataset-directory hash/manifest;
- STRIVE revision;
- config hash;
- M-01 checkpoint hash;
- planner configuration;
- card versions.

---

## 13. Known Applications & Benchmarks

### 13.1 Planner stress testing

D-02 is the core generated input to planner evaluation on challenging scenes.

### 13.2 Scenario clustering

The public clustering pipeline extracts collision features from `fut_adv`:

- relative collision direction;
- relative attacker heading.

It then fits K-means.

Default clustering command parameter:

```text
k = 10
```

with:

```text
random_state = 0
```

in the public implementation.

### 13.3 Cluster-based classification

`eval_adv_gen.py` loads a precomputed clustering and label file, assigns collision scenarios to clusters, and writes:

```text
*_labels.csv
scene_distrib.png
```

### 13.4 Quantitative scenario evaluation

The evaluator writes per-scenario and aggregate CSV outputs for progressively larger subsets:

- `*_adv_sol`;
- `*_all_adv`;
- `*_all_scenes`.

### 13.5 Planner evaluation

`eval_planner.py` can compare planner behavior on generated challenging scenarios and corresponding initialization/regular scenarios.

---

## 14. Known Limitations

### 14.1 Synthetic/optimized nature

D-02 contains model-generated counterfactual trajectories, not observed crash events.

### 14.2 Learned-prior dependence

M-01 defines the latent space and its notion of plausibility. Generated data inherits M-01 biases and approximation errors.

### 14.3 Planner dependence

A scenario's adversarial status depends on the attacked planner and configuration.

### 14.4 Selection bias

D-02 excludes many source windows through feasibility and generation filtering. Success-only public bundles add another strong selection step.

### 14.5 Geographic/category bias

The main configuration inherits D-01's nuScenes geography and car/truck focus.

### 14.6 Collision-model limitations

Differentiable optimization losses and final geometric collision checks use different approximations and thresholds.

### 14.7 Finite-horizon limitations

The standard serialized future is approximately 6 seconds. C-03 uses a longer 8-second optimization horizon internally but returns the standard horizon.

### 14.8 Missing explicit provenance fields

The JSON schema does not directly store:

- source nuScenes token;
- STRIVE commit hash;
- checkpoint hash;
- planner name/config;
- generation config hash;
- result partition.

Those must be preserved through directory structure and external metadata.

### 14.9 Filename identity

`scene_XXXX.json` uses a run-local dataset iteration index. It should not be treated as a globally stable scene identifier.

---

## 15. Ethical, Safety & Societal Considerations

### 15.1 Safety interpretation

A generated collision is a controlled simulation stress test. It is not evidence that the same event is likely to occur in real traffic.

### 15.2 Misuse risk

These scenarios are intended to improve safety evaluation. They should not be operationalized as instructions for causing real-world crashes or unsafe interactions.

### 15.3 Dataset bias

Bias can arise from:

- source data;
- category filtering;
- traffic model;
- feasibility screening;
- planner choice;
- optimization objectives;
- result-partition filtering.

### 15.4 Reporting requirements

Reports should label D-02 examples as:

```text
generated / synthetic / optimized STRIVE scenarios
```

and should not describe them as observed nuScenes accidents.

---

## 16. Licensing & Terms

### 16.1 STRIVE generated scenario license

The STRIVE README states that the released generated scenarios are derived from nuScenes and are separately licensed under:

```text
CC-BY-NC-SA-4.0
```

### 16.2 nuScenes-derived status

Because D-02 is derived from nuScenes, users should also review the current upstream nuScenes terms applicable to their use.

### 16.3 STRIVE source license

STRIVE source code is MIT licensed.

This is distinct from the licensing statement for pretrained models and generated scenarios.

### 16.4 Redistribution considerations

Before redistributing a local D-02 bundle, preserve:

- applicable attribution;
- license notices;
- upstream dataset obligations;
- provenance identifying the generation configuration.

---

## 17. Reproducibility & Maintenance

### 17.1 Required source versions

Record:

- STRIVE commit;
- D-01 card/data version;
- M-01 checkpoint SHA-256;
- planner implementation/version;
- C-01/C-02/C-03 versions.

### 17.2 Generation configuration

Store the exact config file used for scenario generation.

The JSON alone is insufficient to recover all relevant parameters.

### 17.3 Randomness

Generation can depend on:

- prior sampling used during feasibility screening;
- dataset split randomization/order;
- GPU numerical behavior;
- any external random seeds.

The released configs do not by themselves establish full bitwise determinism.

### 17.4 Companion metadata

```text
metadata/data/generated_scenarios.yaml
```

### 17.5 Quantitative profiler

```text
tools/profile_generated_scenarios.py
```

The profiler produces:

- file/partition counts;
- success rates from directory membership;
- map distribution;
- agent-count statistics;
- `dt`, horizon, semantic width, latent width statistics;
- attack-index/time distributions;
- field-presence rates;
- schema/shape/finite-value issues;
- per-file SHA-256 manifest;
- aggregate manifest SHA-256.

### 17.6 Update triggers

Update D-02 metadata/card when any of these change:

- upstream D-01;
- M-01 checkpoint;
- planner or planner configuration;
- C-01/C-02/C-03 behavior;
- generation configuration;
- semantic category set;
- scenario serialization schema.

---

## 18. Relationships

### 18.1 Upstream

```text
D-01 — nuScenes Data Card
  │
  ▼
M-01 — Main Traffic Model
  │
  ▼
C-01 — Initialization Optimization
  │
  ▼
C-02 — Adversarial Optimization
  │
  ▼
C-03 — Solution Optimization
```

### 18.2 Downstream

```text
M-03 — Clustering
M-04 — Accident Classifier
```

### 18.3 Dependency chain

```text
D-01  nuScenes Data Card
  │
  ▼
M-01  Main Traffic Model
  │
  ▼
C-01  Initialization Optimization
  │
  ▼
C-02  Adversarial Optimization
  │
  ▼
C-03  Solution Optimization
  │
  ▼
D-02  Generated Scenarios
  │
  ├── M-03 Clustering
  └── M-04 Accident Classifier
```

---

## 19. Terms of Art

### 19.1 Initialization scenario

The C-01 fitted source/planner future stored in `fut_init`.

### 19.2 Adversarial scenario

The C-02 optimized scenario stored in `fut_adv`.

### 19.3 Solution scenario

The C-03 collision-avoidance counterfactual stored in `fut_sol` when solution optimization was attempted.

### 19.4 Attacker

The C-02 selected non-planner agent associated with the optimized attack objective.

### 19.5 Attack time

The C-02 selected timestep associated with the final attack objective.

### 19.6 `adv_failed`

C-02 did not create a selected-attacker collision; C-03 was not run.

### 19.7 `sol_failed`

C-02 succeeded but C-03's returned planner solution failed vehicle and/or environment collision validation.

### 19.8 `adv_sol_success`

C-02 successfully caused the selected-attacker collision and C-03 found a returned collision-free solution.

---

## 20. References

1. Davis Rempe, Jonah Philion, Leonidas J. Guibas, Sanja Fidler, Or Litany. **Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior.** CVPR 2022.  
   https://openaccess.thecvf.com/content/CVPR2022/html/Rempe_Generating_Useful_Accident-Prone_Driving_Scenarios_via_a_Learned_Traffic_Prior_CVPR_2022_paper.html

2. STRIVE public repository.  
   https://github.com/nv-tlabs/STRIVE

3. Relevant release files:
   - `src/utils/scenario_gen.py`
   - `src/adv_scenario_gen.py`
   - `src/eval_adv_gen.py`
   - `src/cluster_scenarios.py`
   - `src/datasets/utils.py`
   - `configs/adv_gen_rule_based.cfg`
   - `configs/adv_gen_replay.cfg`

4. D-01 — nuScenes Data Card for STRIVE.

5. M-01 — Main Traffic Model Card.

6. C-01 — Initialization Optimization Component Card.

7. C-02 — Adversarial Optimization Component Card.

8. C-03 — Solution Optimization Component Card.

---

## 21. Change Log

| Version | Date | Change |
|---|---|---|
| 1.0.0 | 2026-09-21 | Completed D-02 for STRIVE generated scenario JSON, partitions, provenance, public-release scope, and dataset profiling contract. |
