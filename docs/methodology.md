# Bharat Infra — Research Methodology

## 1. Research Objective

The objective of Bharat Infra is to investigate whether multimodal evidence can improve infrastructure progress verification and early delay-risk prediction.

The system is designed to combine:

- Visual evidence from satellite, drone, and site imagery
- Project schedules and milestones
- Financial expenditure
- Weather and environmental conditions
- Reported progress

The goal is not only to predict delay risk, but also to identify inconsistencies between reported and independently observed evidence.

## 2. Research Streams

The research is divided into three primary streams.

### Stream A — Visual Progress Verification

This stream analyzes bi-temporal or multi-temporal imagery to determine whether meaningful construction progress has occurred.

Initial baseline:
- ResNet-50 based bi-temporal change detection

Future models:
- BIT
- ChangeFormer
- Geospatial foundation-model encoders

Expected outputs:
- Change / no-change prediction
- Change mask
- Visual progress representation

### Stream B — Delay-Risk Prediction

This stream uses structured project data to estimate delay risk.

Initial baseline:
- LightGBM using schedule and financial metadata

Weather-enhanced baseline:
- XGBoost using project metadata and weather features

Future model:
- Temporal Fusion Transformer

Expected outputs:
- Delay-risk probability
- Estimated schedule overrun
- Important contributing factors

### Stream C — Multimodal Fusion

This stream combines visual and structured evidence.

Initial fusion:
- Late fusion of independent visual and tabular predictions

Future fusion:
- Cross-attention based multimodal fusion

The purpose of this stream is to determine whether combining modalities improves performance compared with individual models.

## 3. Evidence Consistency Engine

The Evidence Consistency Engine compares multiple evidence sources.

Example comparisons:

- Reported progress vs visually observed progress
- Planned progress vs observed progress
- Expenditure percentage vs physical progress
- Schedule trajectory vs current progress
- Weather disruption vs observed slowdown

The engine produces discrepancy indicators that contribute to the Infrastructure Integrity Score.

## 4. Infrastructure Integrity Score

The Infrastructure Integrity Score is a composite research indicator representing agreement between multiple evidence sources.

Possible components:

- Visual progress discrepancy
- Financial-progress discrepancy
- Schedule deviation
- Reporting inconsistency
- Model confidence

The score formulation will be tested experimentally and will not be treated as a fixed rule.

## 5. Automation

When new evidence arrives, such as:

- a new satellite image
- a site image
- a progress update
- a financial update
- new weather information

the system should automatically:

1. Ingest the new evidence
2. Preprocess the data
3. Run the relevant model
4. Recalculate discrepancy measures
5. Update delay-risk estimates
6. Recalculate the Infrastructure Integrity Score
7. Generate an explainable alert if required

## 6. Experimental Strategy

The system will be evaluated in stages.

### Baseline Experiments

- ResNet-50 visual baseline
- LightGBM tabular baseline
- XGBoost + weather baseline

### Advanced Experiments

- BIT / ChangeFormer
- Temporal Fusion Transformer
- Late multimodal fusion
- Cross-attention fusion

### Ablation Studies

The following modality combinations will be compared:

- Images only
- Schedule + financial data only
- Schedule + financial + weather
- Full multimodal system

## 7. Evaluation Metrics

### Visual Models

- Precision
- Recall
- F1 Score
- Intersection over Union

### Delay-Risk Models

- Mean Absolute Error
- Root Mean Squared Error
- PR-AUC
- Brier Score

### System Evaluation

- Inference latency
- Failure cases
- Missing-modality resilience
- Model confidence
- Explainability quality

## 8. Research Validation Principles

The experiments will follow these principles:

- Separate train, validation, and test sets
- Avoid temporal leakage
- Avoid geographic image overlap leakage
- Fit preprocessing transformations only on training data
- Preserve experiment seeds
- Record model configurations and results
- Compare advanced methods against reproducible baselines

## 9. Expected Research Outcome

The project aims to determine whether multimodal evidence produces more reliable infrastructure monitoring than single-source approaches.

The final research system should provide:

- independently verified progress evidence
- early delay-risk prediction
- evidence inconsistency detection
- interpretable risk explanations
- automated re-evaluation when new evidence arrives
