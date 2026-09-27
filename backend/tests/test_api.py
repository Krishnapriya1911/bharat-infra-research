from datetime import date

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.evidence_engine import calculate_evidence, evaluate_risk
from app.main import app
from app.mock_data import get_project
from app.models import Project


client = TestClient(app)


def test_get_project() -> None:
    response = client.get("/projects/bridge-001")
    assert response.status_code == 200
    assert response.json()["project_id"] == "bridge-001"


def test_unknown_project() -> None:
    assert client.get("/projects/unknown").status_code == 404


def test_evaluate_endpoint() -> None:
    project = get_project("bridge-001")
    assert project is not None
    response = client.post("/risk/evaluate", json=project.model_dump(mode="json"))
    assert response.status_code == 200
    result = response.json()
    assert result["evidence"] == {
        "progress_discrepancy": 15.0,
        "financial_progress_discrepancy": 18.0,
        "schedule_deviation": 27,
    }
    assert 0 <= result["delay_risk_score"] <= 100
    assert 0 <= result["integrity_score"] <= 100
    assert "illustrative" in result["explanation"]


def test_long_schedule_deviation_in_days() -> None:
    project = get_project("bridge-001")
    assert project is not None
    delayed = project.model_copy(update={"current_date": date(2027, 2, 1)})
    evidence = calculate_evidence(delayed)
    assert evidence.schedule_deviation == 154
    assert evaluate_risk(delayed).evidence.schedule_deviation == 154


def test_no_overdue_days_before_end() -> None:
    project = get_project("bridge-001")
    assert project is not None
    early = project.model_copy(update={"current_date": date(2026, 7, 1)})
    assert calculate_evidence(early).schedule_deviation == 0


@pytest.mark.parametrize("field,value", [
    ("reported_progress", 101),
    ("expenditure_percent", -1),
    ("latitude", 91),
    ("rainfall_30d", -1),
    ("planned_end_date", "2024-01-01"),
])
def test_invalid_project_rejected(field: str, value: object) -> None:
    project = get_project("bridge-001")
    assert project is not None
    payload = project.model_dump(mode="json")
    payload[field] = value
    with pytest.raises(ValidationError):
        Project.model_validate(payload)
    assert client.post("/risk/evaluate", json=payload).status_code == 422
