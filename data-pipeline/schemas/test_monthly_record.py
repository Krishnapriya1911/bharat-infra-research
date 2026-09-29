"""Validation against the existing CSV and month-precision boundary cases."""

import csv
from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas.monthly_record import MonthlyRecord, ObservationStatus, validate_year_month


CSV_PATH = Path(__file__).resolve().parents[2] / "datasets/processed/mospi_monthly_snapshots.csv"


def rows():
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


@pytest.mark.parametrize("value", ["2026-01", "2026-12", "1900-01"])
def test_year_month_accepted(value):
    assert validate_year_month(value) == value


@pytest.mark.parametrize("value", ["2026-00", "2026-13", "2026-08-01", "08/2026", "2026-8"])
def test_year_month_rejected(value):
    with pytest.raises(ValueError):
        validate_year_month(value)


def test_schema_fields_and_actual_status_values_match_csv():
    source = rows()
    assert list(MonthlyRecord.model_fields) == list(source[0])
    assert {r["observation_status"] for r in source} == {s.value for s in ObservationStatus}


def test_representative_source_rows_and_nullable_fields():
    source = rows()
    selected = [
        next(r for r in source if r["observation_status"] == "ongoing"),
        next(r for r in source if r["observation_status"] == "completed" and r["actual_completion_date"]),
        next(r for r in source if r["observation_status"] == "completed" and not r["actual_completion_date"]),
    ]
    records = [MonthlyRecord.model_validate(r) for r in selected]
    assert records[0].ministry is None
    assert records[0].report_month == selected[0]["report_month"]
    assert records[1].actual_completion_date == selected[1]["actual_completion_date"]
    assert records[2].actual_completion_date is None
    assert records[2].physical_progress_pct is None
    assert all(r.source_file and r.source_page and r.raw_date_values and r.raw_cost_values for r in records)


def test_all_existing_rows_validate_or_report_failure_categories():
    failures = {}
    source = rows()
    for row in source:
        try:
            MonthlyRecord.model_validate(row)
        except ValidationError as exc:
            for error in exc.errors():
                category = (str(error["loc"]), error["type"])
                failures[category] = failures.get(category, 0) + 1
    assert not failures, f"CSV validation failure categories: {failures}"
    assert sum("2026-04" <= r["report_month"] <= "2026-08" for r in source) == 8728


def test_percentage_bounds_zero_cost_and_extra_fields():
    row = rows()[0]
    row["original_cost_crore"] = "0"
    row["physical_progress_pct"] = "100"
    assert MonthlyRecord.model_validate(row).original_cost_crore == 0
    for value in ("-0.01", "100.01"):
        with pytest.raises(ValidationError):
            MonthlyRecord.model_validate({**row, "physical_progress_pct": value})
    with pytest.raises(ValidationError):
        MonthlyRecord.model_validate({**row, "unknown": "value"})
