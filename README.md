# Bharat Infra Research

A research prototype for infrastructure project evidence checking and delay analysis, built with **Python, FastAPI and Pydantic**. The repository combines an illustrative evidence API with a tabular pipeline for MoSPI PAIMANA project reports.

[Try the API locally](#run-the-api) · [Data pipeline](data-pipeline) · [Research question](docs/research-question.md) · [Limitations](docs/limitations.md)

## Implemented components

| Component | What it does | Source |
| --- | --- | --- |
| Typed API | Validates project locations, dates, progress and expenditure fields | [API](backend/app/main.py), [contracts](backend/app/models.py) |
| Evidence rules | Calculates progress discrepancy, expenditure discrepancy and days overdue | [Evidence engine](backend/app/evidence_engine.py) |
| Report extraction | Parses supported PAIMANA PDF layouts and records provenance and parsing failures | [Tabular pipeline](data-pipeline/tabular) |
| Silver validation | Validates monthly records and resolves project reporting trajectories | [Silver builder](data-pipeline/silver/build_silver.py), [schemas](data-pipeline/schemas) |
| Gold cohort | Builds a reported-completion survival cohort with exclusions and audit metadata | [Cohort builder and methodology](data-pipeline/gold) |
| Verification | Tests API behaviour, schemas, parsing, trajectories and cohort construction | [API tests](backend/tests), [pipeline tests](data-pipeline) |

The API currently uses mock project data and illustrative rule-based scores. It does not call the tabular pipeline or a trained prediction model. A visual-progress model and frontend application are planned, not implemented.

## Run the API

Use Python 3.10 or later. From the repository root:

```bash
git clone https://github.com/Krishnapriya1911/bharat-infra-research.git
cd bharat-infra-research
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --reload
```

Open [the interactive API documentation](http://127.0.0.1:8000/docs). There are two application endpoints:

| Method | Path | Behaviour |
| --- | --- | --- |
| GET | `/projects/{project_id}` | Returns a mock project; unknown IDs return 404 |
| POST | `/risk/evaluate` | Validates a project payload and returns evidence metrics with illustrative scores |

Try the complete example from the repository root in a second terminal while the server runs:

```bash
curl --fail http://127.0.0.1:8000/projects/bridge-001
curl --fail -X POST http://127.0.0.1:8000/risk/evaluate \
  -H 'Content-Type: application/json' \
  --data-binary @datasets/mock_project.json
```

## Interpret the evidence correctly

- `progress_discrepancy`: absolute percentage-point gap between planned and reported progress. Visual progress is not measured.
- `financial_progress_discrepancy`: expenditure percent minus reported progress; negative values are valid.
- `schedule_deviation`: nonnegative days after the planned end date.
- `rainfall_30d`: rainfall in millimetres over 30 days.
- `delay_risk_score` and `integrity_score`: illustrative 0–100 indicators, not calibrated probabilities or validated findings of misconduct.

## Explore the report pipeline

The [processed datasets](datasets/processed) include monthly snapshots, validated records, trajectory summaries, a survival cohort and audit files.

From the repository root, with the environment above active:

```bash
PYTHONPATH=data-pipeline python -m silver.build_silver
PYTHONPATH=data-pipeline python -m gold.build_survival_cohort
```

These commands regenerate derived outputs from the committed inputs and overwrite their respective processed CSV/audit files. Raw-report extraction additionally requires the source PDFs and [tabular dependencies](data-pipeline/tabular/requirements.txt); see the [extraction guide](data-pipeline/tabular/README.md) before rerunning it.

The survival cohort uses reported completion evidence rather than verified physical completion. First observation is panel entry, not project inception. Unresolved disappearance is excluded rather than assumed to be completion. The cohort is target metadata, not a predictor feature matrix; see the [Gold methodology](data-pipeline/gold/README.md) for censoring, exclusions and leakage boundaries.

## Run existing tests

API tests, from the repository root:

```bash
cd backend
python -m pytest -q
```

Pipeline tests, from the repository root, after installing the tabular dependencies:

```bash
python -m pip install -r data-pipeline/tabular/requirements.txt
PYTHONPATH=data-pipeline python -m pytest -q data-pipeline
```

## Research documentation

- [Research question](docs/research-question.md) and [methodology](docs/methodology.md)
- [Dataset notes](docs/datasets.md) and [labeling and splits](docs/labeling-and-splits.md)
- [Evaluation metrics](docs/evaluation-metrics.md) and [experiments](docs/experiments.md)
- [Limitations and research risks](docs/limitations.md)

## Current scope

The repository is a research foundation, not a validated infrastructure prediction system. No trained model accuracy, satellite-derived progress estimate or verified live deployment is claimed. The next research steps are to establish prediction cutoffs, construct leakage-safe features, evaluate baselines and connect validated results to an interface.
