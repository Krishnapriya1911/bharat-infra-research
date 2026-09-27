# Bharat Infra — Literature Review

## 1. Construction Progress Monitoring

This section will review research on automated infrastructure and construction progress monitoring using:

- Satellite imagery
- UAV / drone imagery
- Site photographs
- Computer vision
- Change detection

### Key Questions
- How is physical progress currently estimated?
- What visual models are commonly used?
- What are the limitations of image-only monitoring?

---

## 2. Construction Delay Prediction

This section will review machine-learning and statistical methods for predicting:

- Schedule delays
- Cost overruns
- Project risk
- Milestone slippage

### Model Families
- Random Forest
- XGBoost / LightGBM
- Artificial Neural Networks
- LSTM
- Transformer-based temporal models

### Key Questions
- Which project features are predictive of delays?
- How early can delay risk be detected?
- How are results evaluated?

---

## 3. Weather-Aware Infrastructure Risk

This section will examine how environmental variables influence infrastructure execution.

Potential factors include:

- Rainfall
- Extreme heat
- Flooding
- Soil moisture
- Seasonal disruptions

Research will examine whether weather-aware models improve delay-risk prediction over project-metadata-only baselines.

---

## 4. Multimodal Infrastructure Monitoring

This section will review approaches that combine multiple evidence sources.

Possible modalities include:

- Images
- Project schedules
- Financial expenditure
- Weather
- Progress reports

The central question is whether multimodal fusion improves reliability compared with independent single-modality models.

---

## 5. Explainable AI for Infrastructure Decisions

This section will review explainability techniques used for infrastructure and project-risk prediction.

Potential methods:

- SHAP
- Feature importance
- Attention visualization
- Model confidence
- Evidence-based explanations

---

## 6. Identified Research Gap

Existing work commonly focuses on individual problems such as:

- visual progress detection
- delay prediction
- cost-overrun prediction
- weather impact analysis

Bharat Infra will investigate an integrated multimodal framework that combines independent visual verification, project metadata, financial expenditure, weather information, and reported progress.

The research will specifically study:

1. Whether multimodal fusion improves progress verification and delay-risk prediction.
2. Whether inconsistencies between visual, financial, schedule, and reported evidence can be quantified.
3. Whether an Infrastructure Integrity Score can provide a useful evidence-consistency indicator.
4. Whether automated re-evaluation can support earlier identification of emerging project risk.

---

## 7. Literature Tracking Table

| Paper | Year | Dataset | Modality | Model | Task | Metrics | Limitation | Relevance |
|---|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |
