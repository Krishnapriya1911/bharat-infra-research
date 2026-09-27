"""Local mock project store. Replace with a repository adapter later."""

import json
from pathlib import Path

from .models import Project


MOCK_FILE = Path(__file__).resolve().parents[2] / "datasets" / "mock_project.json"


def get_project(project_id: str) -> Project | None:
    project = Project.model_validate(json.loads(MOCK_FILE.read_text(encoding="utf-8")))
    return project if project.project_id == project_id else None
