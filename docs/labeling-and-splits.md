# Bharat Infra — Labeling, Provenance and Split Specification

## 1. Prediction Cutoff

Every prediction must be associated with a cutoff date.

Only information available on or before the cutoff date may be used as model input.

This prevents future information from leaking into training features.

---

## 2. Delay Regression Target

For completed projects:

delay_days =
actual_completion_date - original_planned_completion_date

A positive value represents delay.

For ratio-based evaluation:

schedule_overrun_ratio =
delay_days / original_planned_duration_days

---

## 3. Delay Classification Target

Initial binary label:

- 0 = project delay <= 20% of original planned duration
- 1 = project delay > 20% of original planned duration

The 20% threshold is an experimental definition and will be reported explicitly.

---

## 4. Visual Change Target

For public change-detection datasets:

- input: image at T1
- input: image at T2
- target: annotated change mask

The initial visual model predicts physical change rather than true construction progress percentage.

Therefore:

visual change != verified project progress

The visual baseline will be treated as a proxy experiment.

---

## 5. Future Progress Labels

For infrastructure-specific data, potential labels include:

- milestone completed / not completed
- observed physical progress percentage
- progress category
- construction stage
- change magnitude

These labels require reliable ground truth or expert annotation.

---

## 6. Data Provenance

Each dataset must record:

- source name
- source URL
- license
- retrieval date
- geographic coverage
- temporal coverage
- raw fields
- preprocessing performed
- label definition
- known limitations

---

## 7. Tabular Temporal Split

Project records must be split chronologically.

Example strategy:

- earliest 70% of project start/sanction dates -> training
- next 15% -> validation
- latest 15% -> test

Exact dates will be selected after inspecting the final dataset distribution.

Random splitting across time should not be used for the primary experiment.

---

## 8. Visual Geographic Split

Satellite image patches from the same geographic region must not appear across train and test sets.

Recommended:

- 70% geographic regions -> train
- 15% -> validation
- 15% -> test

This reduces geographic leakage.

---

## 9. Multimodal Split

For future multimodal experiments, all records belonging to the same infrastructure project must remain within a single split.

No project may appear partially in train and partially in test.

---

## 10. Leakage Rules

Do not use:

- actual completion date as an input feature
- revised completion date if created after prediction cutoff
- final project cost for early-risk prediction
- expenditure recorded after prediction cutoff
- future weather observations
- future progress reports
- overlapping image tiles between train and test

---

## 11. Reproducibility

For every experiment store:

- split file
- project IDs
- image/tile IDs
- prediction cutoff
- label-generation version
- random seed
- preprocessing configuration

The test set must remain untouched until final evaluation.
