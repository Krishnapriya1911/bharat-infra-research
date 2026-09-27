# Bharat Infra — Research Foundation

## Problem Statement

Infrastructure projects are monitored using progress reports, site inspections,
financial expenditure, schedules, and periodic imagery. These sources may not
always agree, which makes it difficult to independently verify physical progress
and identify potential delays early.

Bharat Infra investigates whether multiple evidence sources can be combined into
an intelligent infrastructure monitoring system capable of verifying reported
progress and estimating early delay risk.

## Research Question

Can multimodal fusion of visual, temporal, financial, weather, and reported
project data improve infrastructure progress verification and early delay-risk
prediction compared with unimodal baselines?

## Hypothesis

Multimodal fusion will improve infrastructure progress verification and early
delay-risk prediction compared with unimodal baselines.

## Data Modalities

The proposed system uses:

1. Satellite imagery
2. Drone and site imagery
3. Project schedules and milestones
4. Financial expenditure
5. Weather and environmental data
6. Reported project progress

## Proposed Contribution

Bharat Infra investigates an evidence-backed infrastructure intelligence
framework combining:

- Visual progress verification
- Schedule and milestone analysis
- Financial-progress consistency analysis
- Weather-aware risk modelling
- Evidence Consistency Engine
- Infrastructure Integrity Score
- Explainable delay-risk predictions
- Automated re-evaluation when new evidence arrives

## Evidence Consistency Engine

The Evidence Consistency Engine compares different representations of project
progress.

Examples include:

- Reported progress vs visually observed progress
- Financial expenditure vs physical progress
- Planned progress vs observed progress
- Expected timeline vs actual progress trajectory

Large inconsistencies are treated as evidence requiring further investigation.

## Infrastructure Integrity Score

The Infrastructure Integrity Score is a research-oriented composite indicator
representing agreement between multiple evidence sources.

Potential components include:

- Visual progress discrepancy
- Financial-progress discrepancy
- Schedule deviation
- Reporting inconsistency
- Model confidence

The exact formulation will be experimentally evaluated rather than assumed.

## Baseline Models

### Visual Baseline
ResNet-50 based bi-temporal visual change detection.

### Tabular Baseline
LightGBM using project schedule and financial metadata.

### Weather Baseline
XGBoost using project metadata combined with weather features.

## Advanced Models

Future experiments will investigate:

- BIT / ChangeFormer for visual change detection
- Temporal Fusion Transformer for temporal risk forecasting
- Multimodal late fusion
- Cross-attention based multimodal fusion

## Evaluation Strategy

Visual verification:
- Precision
- Recall
- F1 Score
- Intersection over Union

Delay prediction:
- MAE
- RMSE
- PR-AUC
- Brier Score

Research evaluation will also include:

- Modality ablation studies
- Fusion architecture comparisons
- Data leakage controls
- Failure-case analysis
- Model confidence analysis

## Long-Term Research Goal

The final system should move beyond conventional infrastructure dashboards.

Instead of only displaying reported project data, Bharat Infra aims to
independently examine available evidence, detect inconsistencies, estimate
future delay risk, explain why the risk was identified, and automatically
re-evaluate projects when new evidence becomes available.
