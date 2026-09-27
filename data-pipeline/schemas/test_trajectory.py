"""Descriptive trajectory states, calendar months, and consistency evidence."""

import pytest

from schemas.monthly_record import MonthlyRecord
from schemas.trajectory import TrajectoryResolution as State, diff_year_month, resolve_trajectory


def record(month, status="ongoing", actual=None, revised=None):
    return MonthlyRecord(
        project_id="P1", project_name="Test", report_month=month,
        source_file="report.pdf", source_page=1, observation_status=status,
        actual_completion_date=actual, revised_completion_date=revised,
    )


@pytest.mark.parametrize("a,b,expected", [
    ("2026-08", "2026-05", 3), ("2026-01", "2025-12", 1),
    ("2025-12", "2026-01", -1),
])
def test_exact_month_difference(a, b, expected):
    assert diff_year_month(a, b) == expected


def test_active_and_disappeared_are_distinct_from_completion():
    active = resolve_trajectory("P1", [record("2026-08")], "2026-08")
    disappeared = resolve_trajectory("P1", [record("2026-05")], "2026-08")
    assert active.trajectory_resolution == State.ONGOING_ACTIVE
    assert disappeared.trajectory_resolution == State.DISAPPEARED_UNRESOLVED
    assert disappeared.reported_actual_completion_month is None
    assert disappeared.completion_date_consistency_flag is None


def test_latest_completed_observation_controls_resolution_and_order():
    records = [record("2026-08", "completed"), record("2026-04", revised="2026-09"),
               record("2026-06", "completed", "2026-06")]
    result = resolve_trajectory("P1", records, "2026-08")
    assert result.trajectory_resolution == State.REPORTED_COMPLETED_MISSING_DATE
    assert result.first_observed_report_month == "2026-04"
    assert result.last_observed_report_month == "2026-08"
    assert result.snapshots_observed_count == 3
    assert result.last_projected_completion_date == "2026-09"


def test_explicit_completion_and_consistent_prior_ongoing_evidence():
    result = resolve_trajectory("P1", [record("2026-05", revised="2026-12"),
                                        record("2026-08", "completed", "2026-07")], "2026-08")
    assert result.trajectory_resolution == State.REPORTED_COMPLETED_EXPLICIT_DATE
    assert result.reporting_lag_months == 1
    assert result.forward_dated_completion_flag is False
    assert result.actual_before_last_ongoing_snapshot_flag is False
    assert result.completion_before_last_forecast_flag is True
    assert result.completion_date_consistency_flag is True


def test_forward_dated_completion_is_inconsistent():
    result = resolve_trajectory("P1", [record("2026-05"),
                                        record("2026-08", "completed", "2026-09")], "2026-08")
    assert result.forward_dated_completion_flag is True
    assert result.reporting_lag_months == -1
    assert result.completion_date_consistency_flag is False


def test_actual_before_last_ongoing_is_inconsistent():
    result = resolve_trajectory("P1", [record("2026-07"),
                                        record("2026-08", "completed", "2026-06")], "2026-08")
    assert result.actual_before_last_ongoing_snapshot_flag is True
    assert result.completion_date_consistency_flag is False


def test_forward_dated_without_prior_ongoing_is_inconsistent():
    result = resolve_trajectory("P1", [record("2026-08", "completed", "2026-09")], "2026-08")
    assert result.forward_dated_completion_flag is True
    assert result.completion_date_consistency_flag is False


def test_no_prior_ongoing_without_contradiction_is_unknown_consistency():
    result = resolve_trajectory("P1", [record("2026-08", "completed", "2026-08")], "2026-08")
    assert result.forward_dated_completion_flag is False
    assert result.completion_date_consistency_flag is None


def test_reject_wrong_project_empty_or_invalid_global_month():
    with pytest.raises(ValueError):
        resolve_trajectory("P2", [record("2026-08")], "2026-08")
    with pytest.raises(ValueError):
        resolve_trajectory("P1", [], "2026-08")
    with pytest.raises(ValueError):
        resolve_trajectory("P1", [record("2026-08")], "2026-07")
