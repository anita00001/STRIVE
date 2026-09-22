# M-01 — Main Traffic Model Card

> **Card ID:** M-01  
> **Card type:** Model Card  
> **Status:** Skeleton  
> **Model:** STRIVE Main Traffic Model  
> **Upstream:** D-01 — nuScenes Data Card for STRIVE  
> **Downstream:** C-01 Initialization Optimization, C-02 Adversarial Optimization, C-03 Solution Optimization

---

## 1. Model Details

### 1.1 Model summary
<!-- What is the STRIVE traffic model and what role does it play in the system? -->

### 1.2 Model type
<!-- Graph-based conditional variational autoencoder / learned traffic prior. -->

### 1.3 Model version
<!-- Repository revision, checkpoint identifier, paper/release version. -->

### 1.4 Model authors
<!-- STRIVE paper authors / implementation authors. -->

### 1.5 Model date
<!-- Original publication/release date and local card version date. -->

### 1.6 Model license
<!-- STRIVE code license and checkpoint/derived-artifact licensing where applicable. -->

### 1.7 Citation
<!-- STRIVE paper citation. -->

---

## 2. Model Purpose & Role in STRIVE

### 2.1 Primary purpose
<!-- Learn a distribution over plausible multi-agent future traffic behavior. -->

### 2.2 Role in STRIVE
<!-- Sampling, reconstruction, latent-space optimization, scenario generation. -->

### 2.3 Relationship to D-01
<!-- nuScenes input data and preprocessing dependency. -->

### 2.4 Downstream dependencies
<!-- C-01, C-02, C-03. -->

---

## 3. Intended Use

### 3.1 Primary intended uses
<!-- Traffic modeling, trajectory generation, latent prior, scenario optimization. -->

### 3.2 Intended users
<!-- Researchers/engineers working on autonomous-driving simulation and robustness. -->

### 3.3 Out-of-scope uses
<!-- Direct vehicle control, safety certification, accident-probability estimation, etc. -->

### 3.4 Deployment assumptions
<!-- Research/offline use; assumptions about map, state, and scene availability. -->

---

## 4. Factors

### 4.1 Geographic factors
<!-- Boston/Singapore dependence inherited from D-01. -->

### 4.2 Agent-class factors
<!-- Main-paper car/truck configuration and supplementary variants. -->

### 4.3 Scene-complexity factors
<!-- Number of agents, traffic density, map topology, interaction complexity. -->

### 4.4 Temporal factors
<!-- Past/future horizon and rollout length. -->

### 4.5 Map-context factors
<!-- Map crop, map layers, lane geometry. -->

### 4.6 Distribution-shift factors
<!-- Unseen cities, road rules, weather, agent classes, behaviors. -->

---

## 5. Architecture

### 5.1 High-level architecture
<!-- Encoder → interaction network → latent prior/posterior → decoder. -->

### 5.2 Agent state representation
<!-- Input state dimensionality and semantics. -->

### 5.3 Past trajectory encoder
<!-- Encoder type, dimensions, default configuration. -->

### 5.4 Future trajectory encoder
<!-- Posterior-only encoder details. -->

### 5.5 Map encoder
<!-- CNN layers, channels, crop size, map inputs. -->

### 5.6 Interaction network
<!-- Graph/message-passing structure and role. -->

### 5.7 Latent representation
<!-- CVAE latent dimension, prior/posterior distributions. -->

### 5.8 Decoder
<!-- Autoregressive rollout and interaction. -->

### 5.9 Output parameterization
<!-- Kinematic bicycle by default vs direct waypoint option. -->

---

## 6. Inputs

### 6.1 Required inputs
<!-- Past motion, semantic class, dimensions, map context, graph structure. -->

### 6.2 Optional inputs
<!-- Ground-truth future for posterior/training; external future injection where relevant. -->

### 6.3 Input tensor schema
<!-- Symbolic shapes for graph/node/map tensors. -->

### 6.4 Normalization
<!-- State and vehicle-attribute normalization. -->

### 6.5 Missing-data handling
<!-- Visibility masks / NaNs inherited from D-01. -->

---

## 7. Outputs

### 7.1 Future trajectories
<!-- Predicted per-agent future state/trajectory. -->

### 7.2 Prior distribution
<!-- Conditional latent prior outputs. -->

### 7.3 Posterior distribution
<!-- Training/inference posterior outputs. -->

### 7.4 Latent samples
<!-- Per-agent latent variables. -->

### 7.5 Intermediate features
<!-- Embeddings or decoder outputs used by downstream optimization. -->

---

## 8. Training Data

### 8.1 Primary training dataset
<!-- D-01 nuScenes Data Card. -->

### 8.2 Agent categories
<!-- Main-paper cars/trucks. -->

### 8.3 Split usage
<!-- STRIVE train/val/test interpretation. -->

### 8.4 Data preprocessing dependency
<!-- Link back to D-01 rather than duplicating all data-card details. -->

### 8.5 Data augmentation
<!-- Input noise or other configured augmentation. -->

---

## 9. Training Procedure

### 9.1 Training script
<!-- `src/train_traffic.py` -->

### 9.2 Optimizer
<!-- Adam and relevant settings. -->

### 9.3 Learning rate
<!-- Release-configured value. -->

### 9.4 Epochs
<!-- Distinguish paper-reported run from public config default if different. -->

### 9.5 Batch size
<!-- Release configuration. -->

### 9.6 Checkpointing and validation
<!-- Save/validation cadence and checkpoint behavior. -->

### 9.7 Training environment
<!-- Python, PyTorch, CUDA, PyG. -->

---

## 10. Training Objective

### 10.1 Reconstruction loss
<!-- Definition and weight. -->

### 10.2 KL divergence
<!-- Conditional VAE KL term, annealing, weight. -->

### 10.3 Vehicle-collision prior loss
<!-- Purpose and weight. -->

### 10.4 Environment-collision prior loss
<!-- Purpose and weight. -->

### 10.5 Total objective
<!-- How terms combine. -->

---

## 11. Evaluation Data

### 11.1 Default held-out data
<!-- STRIVE held-out split. -->

### 11.2 Official prediction-challenge option
<!-- `use_challenge_splits`. -->

### 11.3 Evaluation configuration
<!-- `configs/test_traffic.cfg`. -->

### 11.4 Sampling setup
<!-- Number of samples and future horizon. -->

---

## 12. Evaluation Metrics

### 12.1 Reconstruction losses
<!-- Metrics produced by loss implementation. -->

### 12.2 Displacement error
<!-- Sampling/reconstruction displacement errors. -->

### 12.3 Vehicle collision rate
<!-- Definition and evaluation use. -->

### 12.4 Environment collision rate
<!-- If evaluated. -->

### 12.5 Likelihood / latent diagnostics
<!-- If available. -->

### 12.6 Qualitative visualization
<!-- Multi-sample and rollout visualization. -->

---

## 13. Quantitative Analysis

### 13.1 Paper-reported results
<!-- Metrics reported in the STRIVE paper. -->

### 13.2 Release-configured evaluation
<!-- What the default test config measures. -->

### 13.3 Checkpoint-specific measurements
<!-- Populated by profiler or evaluation output. -->

### 13.4 Parameter count
<!-- Calculated from local checkpoint/model instantiation. -->

### 13.5 Checkpoint size and hash
<!-- Local artifact identity. -->

### 13.6 Profiler
<!-- `tools/profile_traffic_model.py` -->

---

## 14. Performance Considerations

### 14.1 Compute requirements
<!-- GPU/CPU assumptions. -->

### 14.2 Memory considerations
<!-- Variable-size scene graphs and agent count. -->

### 14.3 Runtime characteristics
<!-- Training vs inference vs sampling. -->

### 14.4 Scaling with number of agents
<!-- Graph/message-passing implications. -->

---

## 15. Ethical Considerations

### 15.1 Safety
<!-- Research model, not safety guarantee. -->

### 15.2 Dataset bias
<!-- Inherited from D-01. -->

### 15.3 Misuse
<!-- Avoid treating likelihood as real-world probability or deploying unvalidated. -->

### 15.4 Failure interpretation
<!-- Model failure vs planner failure vs data limitation. -->

---

## 16. Limitations

### 16.1 Learned-prior limitations
<!-- Plausibility is learned, not guaranteed. -->

### 16.2 Collision artifacts
<!-- Samples can collide; refinement exists. -->

### 16.3 Agent-category limitations
<!-- Main model cars/trucks. -->

### 16.4 Geographic/domain limitations
<!-- nuScenes domain. -->

### 16.5 Long-horizon limitations
<!-- Error accumulation and rollout stability. -->

### 16.6 Map-model limitations
<!-- Rasterized local map representation. -->

---

## 17. Caveats & Recommendations

### 17.1 Appropriate interpretation
<!-- What model likelihood/samples mean. -->

### 17.2 Validation before reuse
<!-- Re-evaluate for new city, category, map, checkpoint, etc. -->

### 17.3 Reproducibility recommendations
<!-- Pin code/config/checkpoint/data versions. -->

### 17.4 Downstream optimization caution
<!-- Optimizing latents can expose weaknesses of the prior. -->

---

## 18. Reproducibility

### 18.1 Source files
<!-- `src/models/traffic_model.py`, interaction network, losses, train/test scripts. -->

### 18.2 Configuration files
<!-- train/test configs. -->

### 18.3 Checkpoint location
<!-- Expected local `model_ckpt` path. -->

### 18.4 Companion metadata
<!-- `metadata/models/traffic_model.yaml` -->

### 18.5 Quantitative profiler
<!-- `tools/profile_traffic_model.py` -->

### 18.6 Required versions
<!-- Python/PyTorch/CUDA/PyG/nuScenes devkit. -->

---

## 19. Relationships

### 19.1 Upstream

```text
D-01 — nuScenes Data Card for STRIVE
```

### 19.2 Downstream

```text
C-01 — Initialization Optimization
C-02 — Adversarial Optimization
C-03 — Solution Optimization
```

### 19.3 Dependency chain

```text
D-01  nuScenes Data Card
  │
  ▼
M-01  Main Traffic Model Card
  │
  ├── C-01 Initialization Optimization
  ├── C-02 Adversarial Optimization
  └── C-03 Solution Optimization
```

---

## 20. References

<!-- STRIVE paper -->
<!-- STRIVE GitHub repository -->
<!-- D-01 nuScenes data card -->
<!-- Original Model Cards paper / internal Playbook reference -->

---

## 21. Change Log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | TBD | Initial M-01 skeleton |
