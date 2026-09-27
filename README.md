# Bharat Infra — Autonomous Multimodal Infrastructure Intelligence System

Research-ready foundation for evidence-backed infrastructure progress verification and early delay-risk prediction. Phase-0 exposes typed project data, an Evidence Consistency Engine, and an illustrative rule-based risk endpoint. It does **not** infer progress from images or provide validated predictions yet.

## Run locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`. Fetch `GET /projects/bridge-001`, then submit that JSON body to `POST /risk/evaluate`. Run tests from `backend` with `python -m pytest -q`.

## Data contracts and current score semantics

Percent fields are bounded from 0 to 100. `progress_discrepancy` is the absolute percentage-point gap between **planned** and reported progress; visual progress is not available yet. `financial_progress_discrepancy` is expenditure percent minus reported progress, so negative values are possible. `schedule_deviation` is nonnegative **days after** the planned end date and has no 100-day cap. Weather is 30-day rainfall in millimetres. The two scores are bounded 0–100 illustrative indicators, not calibrated probabilities or validated measures of integrity.

See [research question](docs/research-question.md) for the hypothesis, baselines, and future experiment plan. The repository separates API, evidence rules, data ingestion, model families, automation, agent explanations, and experiments so implementations can evolve independently.
