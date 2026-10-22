"""Minimal HTTP interface for the Phase-0 research foundation."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from .evidence_engine import evaluate_risk
from .mock_data import get_project
from .models import Project, RiskEvaluation


app = FastAPI(title="Bharat Infra Research API", version="0.1.0")


@app.get("/", include_in_schema=False)
def research_console() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "bharat-infra-research", "mode": "research-demo"}


@app.get("/projects/{project_id}", response_model=Project)
def read_project(project_id: str) -> Project:
    project = get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/risk/evaluate", response_model=RiskEvaluation)
def risk_evaluate(project: Project) -> RiskEvaluation:
    return evaluate_risk(project)
