# Gold survival cohort, first research cut

From the repository root, run:

```bash
PYTHONPATH=data-pipeline python -m gold.build_survival_cohort
```

The builder reads validated Silver snapshots and the project trajectory summary. It writes `datasets/processed/mospi_gold_survival_cohort.csv` and `mospi_gold_survival_audit.json`; source files are read only. The audit lists every excluded project with its reason.

`entry_month` is the first **observed ongoing report month**, not `start_date` or project inception. These are prevalent cases with left truncation. Duration is an exact calendar-month difference from observed panel entry. An event is a **validated reported completion event** supported by an explicit month and consistent prior ongoing evidence; it is not physical completion ground truth. Only active projects are administratively right-censored at the global latest report month. Disappearance is excluded, never treated as completion or routine censoring.

This CSV is cohort/target metadata, **not a predictor feature matrix**. `reported_actual_completion_month`, `actual_completion_date`, `trajectory_resolution`, `completion_date_consistency_flag`, `censoring_reason`, `event_observed`, `exit_month`, and `duration_months` are not predictor features. `revised_completion_date` and `revised_cost_crore` remain withheld until a prediction-cutoff and availability policy is established. No feature rows, data splits, or models are produced.
