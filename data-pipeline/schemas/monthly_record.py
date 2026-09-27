"""Schema for one accepted PAIMANA monthly CSV row; no feature selection here."""

import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


_YEAR_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def validate_year_month(value: str) -> str:
    """Keep source month precision; reject dates and malformed months."""
    if not isinstance(value, str) or not _YEAR_MONTH.fullmatch(value):
        raise ValueError("expected YYYY-MM with a valid month")
    return value


class ObservationStatus(str, Enum):
    ongoing = "ongoing"
    completed = "completed"


class MonthlyRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    project_id: str = Field(min_length=1)
    project_name: str = Field(min_length=1)
    ministry: str | None = None
    agency: str | None = None
    sector: str | None = None
    state: str | None = None
    approval_date: str | None = None
    start_date: str | None = None
    original_completion_date: str | None = None
    revised_completion_date: str | None = None
    actual_completion_date: str | None = None
    original_cost_crore: float | None = None
    revised_cost_crore: float | None = None
    cumulative_expenditure_crore: float | None = None
    physical_progress_pct: float | None = Field(default=None, ge=0, le=100)
    report_month: str
    source_file: str = Field(min_length=1)
    source_page: int = Field(ge=1)
    raw_date_values: str | None = None
    raw_cost_values: str | None = None
    observation_status: ObservationStatus

    @field_validator("approval_date", "start_date", "original_completion_date",
                     "revised_completion_date", "actual_completion_date", "report_month")
    @classmethod
    def month_precision(cls, value: str | None) -> str | None:
        return None if value is None else validate_year_month(value)

    @field_validator("ministry", "agency", "sector", "state", "approval_date",
                     "start_date", "original_completion_date", "revised_completion_date",
                     "actual_completion_date", "original_cost_crore", "revised_cost_crore",
                     "cumulative_expenditure_crore", "physical_progress_pct", "raw_date_values",
                     "raw_cost_values", mode="before")
    @classmethod
    def csv_blank_is_null(cls, value: object) -> object:
        return None if value == "" else value
