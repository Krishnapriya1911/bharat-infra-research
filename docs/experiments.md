# Bharat Infra — Experiment Plan

## Experiment Naming Convention

Format:

STREAM_MODEL_DATASET_VERSION

Examples:

VIS_RN50_LEVIR_v1
TAB_LGBM_PROJECTS_v1
TAB_XGB_PROJECTS_WEATHER_v1
VIS_CHANGEFORMER_v1
TEMP_TFT_v1
FUSION_LATE_v1
FUSION_CROSSATTN_v1

---

## EXP-VIS-01

### Model
ResNet-50

### Task
Bi-temporal visual change detection

### Inputs
- Image at time T1
- Image at time T2

### Output
- Change / no-change prediction

### Purpose
Establish the visual baseline.

### Metrics
- Precision
- Recall
- F1 Score
- IoU

---

## EXP-TAB-01

### Model
LightGBM

### Task
Infrastructure delay-risk prediction

### Inputs
- Project sector
- Original project cost
- Planned duration
- Schedule information
- Financial information

### Outputs
- Delay-risk estimate
- Schedule-overrun prediction

### Purpose
Establish a structured-data baseline.

### Metrics
- MAE
- RMSE
- PR-AUC
- Brier Score

---

## EXP-TAB-02

### Model
XGBoost

### Task
Weather-aware delay-risk prediction

### Inputs
EXP-TAB-01 features plus:

- Total precipitation
- Extreme rainfall days
- Extreme heat days

### Purpose
Measure whether environmental information improves delay-risk prediction.

---

## EXP-VIS-02

### Model
BIT / ChangeFormer

### Task
Advanced visual change detection

### Purpose
Compare transformer-based visual modelling against the ResNet baseline.

---

## EXP-TEMP-01

### Model
Temporal Fusion Transformer

### Task
Temporal delay-risk forecasting

### Inputs
- Historical progress
- Expenditure history
- Weather history
- Planned milestones

### Purpose
Model evolving project risk over time.

---

## EXP-FUSION-01

### Model
Late Fusion

### Inputs
- Visual model prediction
- Tabular risk prediction
- Reported progress
- Discrepancy indicators

### Purpose
Establish the first multimodal baseline.

---

## EXP-FUSION-02

### Model
Cross-Attention Multimodal Fusion

### Inputs
- Visual embeddings
- Temporal embeddings
- Structured project context

### Purpose
Test whether learned cross-modal interactions improve delay-risk prediction.

---

## Ablation Experiments

Compare:

1. Images only
2. Schedule + financial only
3. Schedule + financial + weather
4. Full multimodal model

The purpose is to quantify the contribution of each modality.
