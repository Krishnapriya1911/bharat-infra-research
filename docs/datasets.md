# Bharat Infra — Dataset Plan

## 1. Visual Progress Verification

### Primary Baseline Dataset
LEVIR-CD

Purpose:
- Bi-temporal change detection
- Establish ResNet-50 visual baseline

Inputs:
- Image at T1
- Image at T2
- Change labels / masks

Use in:
- EXP-VIS-01

### Additional Visual Datasets
- S2Looking
- SpaceNet 7
- Sentinel-1 / Sentinel-2 imagery
- Future drone/site imagery

---

## 2. Project Schedule and Financial Data

Potential sources:
- World Bank infrastructure project data
- MoSPI infrastructure monitoring data
- NHAI / MoRTH public project disclosures
- India Open Government Data

Important fields:
- project ID
- project sector
- original cost
- revised cost
- sanction date
- planned completion date
- actual/revised completion date
- planned duration
- expenditure
- reported progress

Use in:
- EXP-TAB-01
- EXP-TAB-02
- Future temporal models

---

## 3. Weather Data

Potential sources:
- NASA POWER
- ERA5-Land
- IMD gridded weather data

Features:
- total precipitation
- extreme rainfall days
- maximum temperature
- extreme heat days
- seasonal weather indicators

Use in:
- EXP-TAB-02
- Temporal Fusion Transformer
- What-if simulation experiments

---

## 4. Data Split Strategy

### Visual
Use geographic holdout.

Target split:
- 70% train
- 15% validation
- 15% test

Avoid overlapping geographic patches across splits.

### Tabular
Use temporal holdout.

Example:
- older projects → train
- middle period → validation
- most recent projects → test

---

## 5. Data Leakage Controls

Avoid:
- revised completion information as input features
- post-outcome financial data
- weather information beyond prediction cutoff
- overlapping satellite patches across train/test
- preprocessing fitted on full dataset

---

## 6. Data Governance

For every dataset record:

- source
- license
- retrieval date
- geographic coverage
- temporal coverage
- preprocessing steps
- train/validation/test split
- known limitations

must be documented.
