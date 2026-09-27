"""Builder integration checks use isolated outputs and retain source bytes."""

import csv
import hashlib
import json
from pathlib import Path

from schemas.monthly_record import MonthlyRecord
from silver.build_silver import INPUT, SILVER_COLUMNS, TRAJECTORY_COLUMNS, build_silver


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def execute(tmp_path, source=INPUT):
    silver = tmp_path / "silver.csv"
    trajectories = tmp_path / "trajectories.csv"
    audit = tmp_path / "audit.json"
    result = build_silver(source, silver, trajectories, audit)
    assert json.loads(audit.read_text()) == result
    return result, silver, trajectories


def test_real_panel_validates_and_preserves_input(tmp_path):
    before = hashlib.sha256(INPUT.read_bytes()).digest()
    audit, silver, trajectory = execute(tmp_path)
    assert hashlib.sha256(INPUT.read_bytes()).digest() == before
    fields, rows = read_csv(silver)
    assert fields == list(SILVER_COLUMNS) == list(MonthlyRecord.model_fields)
    assert audit["input_row_count"] == 8728
    assert audit["validated_row_count"] == len(rows)
    assert audit["validation_failure_count"] == 0
    assert audit["validation_failures"] == []
    source_fields, source_rows = read_csv(INPUT)
    assert fields == source_fields and rows == source_rows
    tfields, summaries = read_csv(trajectory)
    assert tfields == list(TRAJECTORY_COLUMNS)
    assert len(summaries) == audit["unique_project_count"]
    assert len({r["project_id"] for r in summaries}) == len(summaries)
    assert audit["global_latest_report_month"] == max(r["report_month"] for r in rows)
    assert sum(audit["trajectory_resolution_counts"].values()) == len(summaries)
    assert sum(audit["completion_date_consistency_counts"].values()) == len(summaries)


def test_states_and_consistency_use_global_month(tmp_path):
    def row(pid, month, status="ongoing", actual=""):
        return dict.fromkeys(SILVER_COLUMNS, "") | {
            "project_id": pid, "project_name": pid, "report_month": month,
            "source_file": "report.pdf", "source_page": "1",
            "observation_status": status, "actual_completion_date": actual,
        }

    source = tmp_path / "input.csv"
    with source.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=SILVER_COLUMNS)
        writer.writeheader()
        writer.writerows([
            row("active", "2026-08"), row("disappeared", "2026-07"),
            row("explicit", "2026-05"), row("explicit", "2026-08", "completed", "2026-07"),
            row("missing", "2026-08", "completed"),
            row("forward", "2026-08", "completed", "2026-09"),
            row("unknown", "2026-08", "completed", "2026-08"),
            row("invalid", "2026-08", "ongoing") | {"physical_progress_pct": "101"},
        ])
    audit, silver, trajectory = execute(tmp_path, source)
    assert audit["input_row_count"] == 8
    assert audit["validated_row_count"] == 7
    assert audit["validation_failure_count"] == 1
    assert audit["validation_failures"][0]["row_index"] == 9
    assert audit["validation_failures"][0]["project_id"] == "invalid"
    assert audit["validation_failures"][0]["errors"][0]["field"] == ["physical_progress_pct"]
    assert audit["global_latest_report_month"] == "2026-08"
    _, records = read_csv(trajectory)
    by_id = {r["project_id"]: r for r in records}
    assert len(by_id) == audit["unique_project_count"] == 6
    assert by_id["active"]["trajectory_resolution"] == "ONGOING_ACTIVE"
    assert by_id["disappeared"]["trajectory_resolution"] == "DISAPPEARED_UNRESOLVED"
    assert by_id["disappeared"]["reported_actual_completion_month"] == ""
    assert by_id["explicit"]["trajectory_resolution"] == "REPORTED_COMPLETED_EXPLICIT_DATE"
    assert by_id["missing"]["trajectory_resolution"] == "REPORTED_COMPLETED_MISSING_DATE"
    assert by_id["forward"]["completion_date_consistency_flag"] == "False"
    assert by_id["unknown"]["completion_date_consistency_flag"] == ""
    assert by_id["explicit"]["completion_date_consistency_flag"] == "True"
