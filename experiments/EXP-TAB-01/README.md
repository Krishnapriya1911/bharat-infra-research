# EXP-TAB-01 — LightGBM Infrastructure Delay Baseline

## Objective

Build the first reproducible structured-data baseline for infrastructure delay-risk prediction.

## Primary Data Source

MoSPI PAIMANA / Online Computerized Monitoring System (OCMS)

The source monitors Central Sector infrastructure projects and provides project-level schedule and financial information.

## Candidate Fields

- Project code
- Project name
- Sector
- Line ministry
- Original approved cost
- Revised cost
- Cumulative expenditure
- Original end date
- Revised completion date
- Physical progress where available

## Initial Target

Delay duration will be derived from:

delay_days = revised_or_actual_completion_date - original_end_date

The exact target definition will be finalized after inspecting available project records.

## Baseline Model

LightGBM

## Research Split

Chronological project-level split:

- Train: earliest 70%
- Validation: next 15%
- Test: latest 15%

No project may appear in multiple splits.

## Leakage Controls

Do not use:

- revised completion date as an input feature when it is used to create the label
- post-cutoff expenditure
- post-cutoff progress reports
- any future information unavailable at prediction time

## Evaluation

Classification:
- PR-AUC
- ROC-AUC
- Brier Score

Regression:
- MAE
- RMSE
