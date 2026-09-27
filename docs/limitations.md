# Bharat Infra — Limitations and Research Risks

## 1. Dataset Limitations

No single public dataset currently contains all required modalities together:

- satellite / drone imagery
- financial expenditure
- project schedules
- weather
- reported progress

As a result, the project may initially rely on independently sourced datasets and synthetic alignment between modalities.

This limits how strongly early results can be generalized to real infrastructure projects.

---

## 2. Visual Data Resolution

Satellite imagery may not capture fine-grained construction details.

For example:

- Sentinel-2 imagery is suitable for large-scale land and infrastructure change
- Small structural changes may require higher-resolution commercial satellite, drone, or site imagery

Therefore, visual model performance will depend strongly on image resolution and project type.

---

## 3. Temporal Alignment

Different data modalities may arrive at different frequencies.

Examples:

- weather: daily
- satellite imagery: periodic
- project expenditure: monthly
- reported progress: milestone-based
- drone/site imagery: irregular

This creates synchronization challenges for multimodal fusion.

---

## 4. Data Quality

Infrastructure project reports may contain:

- missing fields
- inconsistent reporting formats
- delayed updates
- inaccurate progress values
- incomplete financial information

The system must distinguish between model uncertainty and poor-quality input data.

---

## 5. Ground-Truth Availability

True physical progress percentages are difficult to obtain.

Public datasets may provide change masks or project completion dates, but not reliable continuous physical progress labels.

This may require:

- proxy labels
- milestone labels
- human annotation
- expert verification

for advanced progress-estimation experiments.

---

## 6. Model Generalization

A model trained on one infrastructure type may not generalize well to another.

Examples:

- roads
- bridges
- railways
- dams
- urban construction

Separate evaluation by project type may be required.

---

## 7. Weather Causality

Weather correlation does not necessarily imply that weather caused a delay.

Rainfall may be associated with project slowdown, but delays can also result from:

- procurement issues
- financial constraints
- contractor performance
- land acquisition
- regulatory approvals
- labor shortages

Weather-aware risk estimates must therefore be interpreted carefully.

---

## 8. Financial-Progress Interpretation

High expenditure with low visual progress does not automatically imply misuse.

Possible legitimate explanations include:

- material procurement
- equipment mobilization
- advance payments
- design or engineering work

Therefore, the Evidence Consistency Engine should flag inconsistencies for investigation rather than make definitive accusations.

---

## 9. Infrastructure Integrity Score

The Infrastructure Integrity Score is an experimental composite indicator.

Its formulation, weighting, calibration, and thresholds must be validated empirically.

It must not be interpreted as a definitive measure of project integrity without external validation.

---

## 10. Explainability Limitations

Explainability methods such as:

- SHAP
- attention visualization
- feature importance

help interpret model behaviour but do not prove causality.

Generated explanations must remain grounded in model evidence.

---

## 11. Automation Risks

Automated re-evaluation may generate false alerts when:

- images are cloudy
- financial updates are delayed
- sensor data is missing
- weather data is incomplete
- models are uncertain

Automation should include confidence thresholds and human-review mechanisms.

---

## 12. Research Scope

The initial objective is to build and evaluate a research prototype.

The project is not initially intended to replace:

- government audit systems
- engineering inspections
- financial audits
- physical site verification

The goal is to provide additional evidence-backed decision support.
