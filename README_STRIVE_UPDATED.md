# Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior (CVPR 2022)
### Davis Rempe, Jonah Philion, Leonidas Guibas, Sanja Fidler, Or Litany

## Environment Setup

> Original STRIVE note: the codebase was primarily tested on Ubuntu 18.04 with Python 3.6, PyTorch 1.9, and CUDA 11.1.

### Modern environment used successfully

| Component | Version / Hardware |
|---|---|
| Python | 3.10.2 |
| PyTorch | 2.13.0 |
| torchvision | 0.28.0 |
| torchaudio | 2.11.0 |
| torch-geometric | 2.8.0.post1 |
| NumPy | 1.26.4 |
| Matplotlib | 3.7.5 |
| scikit-learn | 1.7.2 |
| nuScenes devkit | 1.1.5 |
| NVIDIA Driver | 580.95.05 |
| CUDA reported by `nvidia-smi` | 13.0 |
| GPU | NVIDIA GeForce RTX 5090, 32 GB |

`torch-scatter` and `torch-sparse` were not installed as standalone packages. PyTorch Geometric still ran, although it warned that some scatter operations could be accelerated by installing `torch-scatter`.

### Working `requirements.txt`

```text
numpy==1.26.4

torch
torchvision
torchaudio

matplotlib==3.7.5
pyyaml==6.0.1
wandb==0.16.6
ConfigArgParse==1.7

torch-geometric

nuscenes-devkit==1.1.5
```

Compared with the original requirements, the CUDA-11.1-specific PyTorch wheel links, `torch-scatter`, `torch-sparse`, and old pinned PyTorch/PyG versions were removed.

## Compatibility Changes for Modern NumPy / PyTorch / Matplotlib

### 1. CUDA/CPU device mismatch fixes

Modern PyTorch creates `torch.arange(...)` on CPU unless a device is specified. STRIVE later subtracts these tensors from CUDA tensors, causing:

```text
RuntimeError: Expected all tensors to be on the same device, but found cuda:0 and cpu
```

In `src/adv_scenario_gen.py`:

```python
# old
init_agt_ptr = scene_graph.ptr - torch.arange(B+1)

# new
init_agt_ptr = scene_graph.ptr - torch.arange(
    B + 1,
    device=scene_graph.ptr.device
)
```

Also in `src/adv_scenario_gen.py`:

```python
# old
other_ptr = scene_graph.ptr - torch.arange(len(scene_graph.ptr))

# new
other_ptr = scene_graph.ptr - torch.arange(
    len(scene_graph.ptr),
    device=scene_graph.ptr.device
)
```

In `src/utils/adv_gen_optim.py`:

```python
# old
cur_agt_ptr = scene_graph.ptr - torch.arange(B+1)

# new
cur_agt_ptr = scene_graph.ptr - torch.arange(
    B + 1,
    device=scene_graph.ptr.device
)
```

### 2. NumPy deprecated aliases

In `src/adv_scenario_gen.py`:

```python
# old
bvalid = np.array(bvalid, dtype=np.bool)
avalid = np.zeros((NA), dtype=np.bool)

# new
bvalid = np.array(bvalid, dtype=bool)
avalid = np.zeros((NA), dtype=bool)
```

In `src/datasets/nuscenes_utils.py`, all uses of:

```python
.astype(np.int)
```

were changed to:

```python
.astype(int)
```

### 3. Matplotlib compatibility

In `src/datasets/nuscenes_utils.py`:

```python
# old
plt.grid(b=None)

# new
plt.grid(False)
```

This avoids the Matplotlib 3.7 error caused by the removed `b=` argument.

## Important Note About Timestamped Output Directories

Several STRIVE scripts automatically append a Unix timestamp to the requested output directory. For example:

```text
./out/refine_traffic_optim_out
```

may become:

```text
./out/refine_traffic_optim_out_1786370893
```

and:

```text
./out/adv_gen_rule_based_out
```

may become:

```text
./out/adv_gen_rule_based_out_1786375865
```

`eval_adv_gen.py` also timestamps its output. Always inspect `./out` before using a downstream command:

```bash
find ./out -maxdepth 1 -type d
```

## Training and Testing Traffic Model

### Training

```bash
python src/train_traffic.py --config ./configs/train_traffic.cfg
```

The training configuration used:

```text
epochs: 200
```

The latest checkpoint was:

```text
./out/train_traffic_out/checkpoints/latest_model.pth
```

### Testing

Do not use the documentation placeholder `path/to/model.pth`. Use the real checkpoint:

```bash
python src/test_traffic.py \
  --config ./configs/test_traffic.cfg \
  --ckpt ./out/train_traffic_out/checkpoints/latest_model.pth
```

## Sampling Traffic Model with Refinement Optimization

```bash
python src/refine_traffic_optim.py \
  --config ./configs/refine_traffic_optim.cfg \
  --ckpt ./out/train_traffic_out/checkpoints/latest_model.pth
```

A completed refinement run was saved to:

```text
./out/refine_traffic_optim_out_1786370893
```

with:

```text
scenario_results/success
scenario_results/failed
viz_results/success
viz_results/failed
```

Reported refinement metrics:

```text
veh_coll = 0.004585
env_coll = 0.106294
```

High-quality visualization:

```bash
python src/viz_scenario_dir.py \
  --scenarios ./out/refine_traffic_optim_out_1786370893/scenario_results/success \
  --out ./out/refine_traffic_viz_out \
  --viz_video
```

## Adversarial Scenario Generation

### Running Optimization

```bash
python src/adv_scenario_gen.py \
  --config ./configs/adv_gen_rule_based.cfg \
  --ckpt ./out/train_traffic_out/checkpoints/latest_model.pth
```

Completed run:

```text
./out/adv_gen_rule_based_out_1786375865
```

Overall sweep:

```text
1199 / 1199 candidate samples
runtime: approximately 28 h 31 min
```

Saved result counts:

```text
adv_failed       : 215
adv_sol_success  : 152
sol_failed       : 46
total saved      : 413
```

Result categories:

- `adv_failed`: adversarial optimization failed, so solution optimization was not performed.
- `adv_sol_success`: adversarial optimization succeeded and a solution was found.
- `sol_failed`: adversarial optimization succeeded, but solution optimization failed.

## Analyzing Scenarios

### Quantitative Evaluation

Because these scenarios use the full nuScenes `trainval` data, explicitly pass `--data_version trainval`:

```bash
python src/eval_adv_gen.py \
  --out ./out/adv_gen_rule_based_out_1786375865/eval_results \
  --scenarios ./out/adv_gen_rule_based_out_1786375865/scenario_results \
  --data_version trainval \
  --eval_quant
```

One successful timestamped evaluation output was:

```text
./out/adv_gen_rule_based_out_1786375865/eval_results_1786481102
```

It contains:

```text
eval_quant/eval_per_seq_all_adv.csv
eval_quant/eval_total_all_scenes.csv
eval_quant/eval_per_seq_all_scenes.csv
eval_quant/eval_per_seq_adv_sol.csv
eval_quant/scene_distrib.png
eval_quant/adv_sol_success_labels.csv
eval_quant/sol_failed_labels.csv
eval_quant/eval_total_all_adv.csv
eval_quant/eval_total_adv_sol.csv
```

The supplied `cluster.pkl` was created with scikit-learn 0.24.2. Loading it with scikit-learn 1.7.2 produces an `InconsistentVersionWarning`. The evaluation still ran, but cluster/classification results should be interpreted with that compatibility warning in mind.

### Qualitative Evaluation

```bash
python src/eval_adv_gen.py \
  --out ./out/adv_gen_rule_based_out_1786375865/eval_results \
  --scenarios ./out/adv_gen_rule_based_out_1786375865/scenario_results \
  --data_version trainval \
  --eval_qual \
  --viz_res adv_sol_success \
  --viz_stage init adv sol \
  --viz_video
```

## Planner Evaluation

The default config points to a non-timestamped scenario directory. To preserve the original config file, override `scenario_dir` from the command line:

```bash
python src/eval_planner.py \
  --config ./configs/eval_planner.cfg \
  --scenario_dir ./out/adv_gen_rule_based_out_1786375865/scenario_results/adv_sol_success
```

This evaluates the planner on the 152 complete `adv_sol_success` scenarios.

## Clustering

Cluster all scenarios where adversarial collision generation succeeded, whether or not solution optimization succeeded:

```bash
python src/cluster_scenarios.py \
  --scenario_dirs \
    ./out/adv_gen_rule_based_out_1786375865/scenario_results/adv_sol_success \
    ./out/adv_gen_rule_based_out_1786375865/scenario_results/sol_failed \
  --out ./out/rule_based_clustering
```

Do not include `adv_failed`, because those cases did not produce the successful adversarial collision required by the collision-feature extraction.

Observed clustering input:

```text
(198, 4)
Clustering using k=10 clusters...
```

The 198 collision scenarios are:

```text
152 adv_sol_success + 46 sol_failed = 198
```

Each scenario is represented by four collision features:

```text
collision direction x
collision direction y
adversary heading x
adversary heading y
```

## Compatibility Warnings Observed

The following warnings were non-fatal in the tested setup:

- Shapely deprecation warnings while rasterizing nuScenes maps.
- PyTorch Geometric warning that `scatter(reduce='max')` can be faster with `torch-scatter`.
- scikit-learn `InconsistentVersionWarning` when loading the provided KMeans model created with scikit-learn 0.24.2.

## Reproducibility Summary

This modernized setup successfully completed:

```text
Traffic model training           ✓
Traffic model testing            ✓
Refinement optimization          ✓
Adversarial scenario generation  ✓
1199-sample adversarial sweep    ✓
Quantitative evaluation          ✓
Planner evaluation setup         ✓
Collision clustering             ✓
```

The source changes above are compatibility fixes for modern NumPy, PyTorch, CUDA-era hardware, and Matplotlib. They do not intentionally change the STRIVE algorithm or optimization objectives.

## Citation

```bibtex
@inproceedings{rempe2022strive,
    author={Rempe, Davis and Philion, Jonah and Guibas, Leonidas J. and Fidler, Sanja and Litany, Or},
    title={Generating Useful Accident-Prone Driving Scenarios via a Learned Traffic Prior},
    booktitle={Conference on Computer Vision and Pattern Recognition (CVPR)},
    year={2022}
}
```
