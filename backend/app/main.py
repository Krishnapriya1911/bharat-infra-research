"""Minimal HTTP interface for the Phase-0 research foundation."""

from fastapi import FastAPI, HTTPException

from .evidence_engine import evaluate_risk
from .mock_data import get_project
from .models import Project, RiskEvaluation


app = FastAPI(title="Bharat Infra Research API", version="0.1.0")


@app.get("/projects/{project_id}", response_model=Project)
def read_project(project_id: str) -> Project:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/risk/evaluate", response_model=RiskEvaluation)
def risk_evaluate(project: Project) -> RiskEvaluation:
    return evaluate_risk(project)
