"""Descriptive report-level trajectory resolution; no survival target or features."""

from enum import Enum
from typing import Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

from .monthly_record import MonthlyRecord, ObservationStatus, validate_year_month


class TrajectoryResolution(str, Enum):
    ONGOING_ACTIVE = "ONGOING_ACTIVE"
    REPORTED_COMPLETED_EXPLICIT_DATE = "REPORTED_COMPLETED_EXPLICIT_DATE"
    REPORTED_COMPLETED_MISSING_DATE = "REPORTED_COMPLETED_MISSING_DATE"
    DISAPPEARED_UNRESOLVED = "DISAPPEARED_UNRESOLVED"


def diff_year_month(a: str, b: str) -> int:
    """Calendar-month index difference A - B; never invent day precision."""
    year_a, month_a = map(int, validate_year_month(a).split("-"))
    year_b, month_b = map(int, validate_year_month(b).split("-"))
    return (year_a * 12 + month_a) - (year_b * 12 + month_b)


class Trajectory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str
    trajectory_resolution: TrajectoryResolution
    first_observed_report_month: str
    last_observed_report_month: str
    snapshots_observed_count: int = Field(ge=1)
    last_ongoing_snapshot_month: str | None
    last_projected_completion_date: str | None
    reported_actual_completion_month: str | None
    reporting_lag_months: int | None
    forward_dated_completion_flag: bool | None
    actual_before_last_ongoing_snapshot_flag: bool | None
    completion_before_last_forecast_flag: bool | None
    completion_date_consistency_flag: Optional[bool]


def resolve_trajectory(
    project_id: str,
    records: Sequence[MonthlyRecord],
    global_latest_report_month: str,
) -> Trajectory:
    """Resolve only observed administrative states for a single project."""
    validate_year_month(global_latest_report_month)
    if not records:
        raise ValueError("trajectory requires at least one record")
    if any(record.project_id != project_id for record in records):
        raise ValueError("all records must match project_id")
    ordered = sorted(records, key=lambda record: record.report_month)
    first_month, last_month = ordered[0].report_month, ordered[-1].report_month
    if last_month > global_latest_report_month:
        raise ValueError("global_latest_report_month precedes a project observation")
    completed = [r for r in ordered if r.observation_status == ObservationStatus.completed]
    terminal = completed[-1] if completed else None
    # Forecast and preceding ongoing evidence are taken from the last ongoing
    # snapshot no later than the terminal completed report, if present.
    ongoing = [r for r in ordered if r.observation_status == ObservationStatus.ongoing
               and (terminal is None or r.report_month <= terminal.report_month)]
    last_ongoing = ongoing[-1] if ongoing else None
    actual = terminal.actual_completion_date if terminal else None
    forecast = last_ongoing.revised_completion_date if last_ongoing else None
    prior = last_ongoing.report_month if last_ongoing else None

    if terminal:
        resolution = (TrajectoryResolution.REPORTED_COMPLETED_EXPLICIT_DATE if actual
                      else TrajectoryResolution.REPORTED_COMPLETED_MISSING_DATE)
    elif last_month == global_latest_report_month:
        resolution = TrajectoryResolution.ONGOING_ACTIVE
    else:
        resolution = TrajectoryResolution.DISAPPEARED_UNRESOLVED

    forward = actual > terminal.report_month if actual and terminal else None
    before_ongoing = actual < prior if actual and prior else None
    if forward is True or before_ongoing is True:
        consistency = False
    elif actual and prior:
        consistency = True
    else:
        consistency = None
    return Trajectory(
        project_id=project_id,
        trajectory_resolution=resolution,
        first_observed_report_month=first_month,
        last_observed_report_month=last_month,
        snapshots_observed_count=len(ordered),
        last_ongoing_snapshot_month=prior,
        last_projected_completion_date=forecast,
        reported_actual_completion_month=actual,
        reporting_lag_months=diff_year_month(terminal.report_month, actual) if actual and terminal else None,
        forward_dated_completion_flag=forward,
        actual_before_last_ongoing_snapshot_flag=before_ongoing,
        completion_before_last_forecast_flag=actual < forecast if actual and forecast else None,
        completion_date_consistency_flag=consistency,
    )
