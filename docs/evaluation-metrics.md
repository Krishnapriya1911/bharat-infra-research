# Bharat Infra — Evaluation Metrics

## 1. Visual Progress Verification

### Precision
Measures how many detected progress/change events were actually correct.

### Recall
Measures how many actual progress/change events were successfully detected.

### F1 Score
Balances precision and recall.

### Intersection over Union (IoU)
Used for evaluating change masks or segmented construction regions.

---

## 2. Delay-Risk Prediction

### Mean Absolute Error (MAE)
Measures average error in predicted delay duration.

### Root Mean Squared Error (RMSE)
Penalizes larger delay prediction errors more strongly.

### PR-AUC
Primary metric for imbalanced delay-risk classification.

### ROC-AUC
Secondary discrimination metric.

### Brier Score
Measures calibration quality of predicted delay probabilities.

---

## 3. Multimodal Fusion Evaluation

Compare:

- Visual-only model
- Tabular-only model
- Tabular + weather
- Full multimodal model

The main research question is whether multimodal fusion improves performance over unimodal baselines.

---

## 4. Evidence Consistency Evaluation

Potential measures include:

- Reported vs visual progress discrepancy
- Financial vs physical progress discrepancy
- Planned vs observed schedule deviation
- Consistency agreement across modalities

The Infrastructure Integrity Score will be experimentally evaluated rather than assumed to be correct.

---

## 5. Robustness Evaluation

The system will be tested under:

- Missing visual evidence
- Missing weather information
- Cloud-covered satellite imagery
- Sparse financial updates
- Noisy or delayed reporting

---

## 6. System Metrics

Record:

- Inference latency
- Training time
- Model size
- Memory usage where relevant
- Failure cases
- Model confidence

---

## 7. Research Reporting

For every experiment, save:

- Experiment ID
- Dataset version
- Model version
- Random seed
- Train/validation/test split
- Hyperparameters
- Metrics
- Confusion matrix
- Learning curves
- Model checkpoint
