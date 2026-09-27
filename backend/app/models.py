"""Typed contracts shared by the API and evidence engine."""

from datetime import date

from pydantic import BaseModel, Field, HttpUrl, model_validator


class Project(BaseModel):
    project_id: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    project_type: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    planned_progress: float = Field(ge=0, le=100)
    reported_progress: float = Field(ge=0, le=100)
    expenditure_percent: float = Field(ge=0, le=100)
    planned_start_date: date
    planned_end_date: date
    current_date: date
    rainfall_30d: float = Field(ge=0, description="Rainfall in millimetres over 30 days")
    site_image_url: HttpUrl | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "Project":
        if self.planned_end_date <= self.planned_start_date:
            raise ValueError("planned_end_date must be after planned_start_date")
        return self


class EvidenceMetrics(BaseModel):
    progress_discrepancy: float = Field(ge=0, le=100)
    financial_progress_discrepancy: float = Field(ge=-100, le=100)
    schedule_deviation: int = Field(ge=0, description="Days overdue after the planned end date")


class RiskEvaluation(BaseModel):
    project_id: str
    evidence: EvidenceMetrics
    delay_risk_score: float = Field(ge=0, le=100)
    integrity_score: float = Field(ge=0, le=100)
    explanation: str
