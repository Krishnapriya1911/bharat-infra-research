"""Validate existing PAIMANA snapshots and export source-faithful Silver records.

The trajectory export is descriptive administrative evidence, not a target.
Run from the repository root with PYTHONPATH=data-pipeline.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from pydantic import ValidationError

from schemas.monthly_record import MonthlyRecord
from schemas.trajectory import Trajectory, TrajectoryResolution, resolve_trajectory


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "datasets/processed/mospi_monthly_snapshots.csv"
SILVER = ROOT / "datasets/processed/mospi_silver_validated.csv"
TRAJECTORIES = ROOT / "datasets/processed/mospi_project_trajectories.csv"
AUDIT = ROOT / "datasets/processed/mospi_silver_trajectory_audit.json"
SILVER_COLUMNS = tuple(MonthlyRecord.model_fields)
TRAJECTORY_COLUMNS = tuple(Trajectory.model_fields)


def build_silver(
    input_file: Path = INPUT,
    silver_file: Path = SILVER,
    trajectory_file: Path = TRAJECTORIES,
    audit_file: Path = AUDIT,
) -> dict:
    """Validate each source row and resolve projects from validated records only.

    Invalid rows remain in the input and are listed with their CSV row number
    (header is row 1) and Pydantic error details in the audit.
    """
    accepted_rows: list[dict[str, str]] = []
    projects: dict[str, list[MonthlyRecord]] = defaultdict(list)
    failures: list[dict] = []
    status_counts: Counter[str] = Counter()
    input_count = 0
    with input_file.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(SILVER_COLUMNS):
            raise ValueError(f"input columns differ from frozen Silver schema: {reader.fieldnames}")
        for row_number, row in enumerate(reader, start=2):
            input_count += 1
            try:
                record = MonthlyRecord.model_validate(row)
            except ValidationError as exc:
                failures.append({
                    "row_index": row_number,
                    "project_id": row.get("project_id"),
                    "errors": [{"field": list(e["loc"]), "type": e["type"], "message": e["msg"]}
                               for e in exc.errors()],
                })
                continue
            accepted_rows.append(row)  # Retain source strings, blank cells and printed zeros.
            projects[record.project_id].append(record)
            status_counts[record.observation_status.value] += 1

    latest = max((r.report_month for records in projects.values() for r in records), default=None)
    summaries = ([resolve_trajectory(pid, projects[pid], latest) for pid in sorted(projects)]
                 if latest is not None else [])
    resolution_counts = Counter(s.trajectory_resolution.value for s in summaries)
    consistency_counts = Counter(
        "null" if s.completion_date_consistency_flag is None else
        "true" if s.completion_date_consistency_flag else "false"
        for s in summaries
    )
    audit = {
        "input_file": str(input_file.relative_to(ROOT)) if input_file.is_relative_to(ROOT) else str(input_file),
        "input_row_count": input_count,
        "validated_row_count": len(accepted_rows),
        "validation_failure_count": len(failures),
        "unique_project_count": len(projects),
        "global_latest_report_month": latest,
        "observation_status_counts": {k: status_counts[k] for k in ("ongoing", "completed")},
        "trajectory_resolution_counts": {state.value: resolution_counts[state.value]
                                         for state in TrajectoryResolution},
        "completion_date_consistency_counts": {k: consistency_counts[k] for k in ("true", "false", "null")},
        "forward_dated_completion_count": sum(s.forward_dated_completion_flag is True for s in summaries),
        "actual_before_last_ongoing_snapshot_count": sum(
            s.actual_before_last_ongoing_snapshot_flag is True for s in summaries),
        "completion_before_last_forecast_count": sum(
            s.completion_before_last_forecast_flag is True for s in summaries),
        "projects_with_explicit_completion_date": resolution_counts["REPORTED_COMPLETED_EXPLICIT_DATE"],
        "projects_with_completed_status_missing_actual_date": resolution_counts["REPORTED_COMPLETED_MISSING_DATE"],
        "ongoing_active_count": resolution_counts["ONGOING_ACTIVE"],
        "disappeared_unresolved_count": resolution_counts["DISAPPEARED_UNRESOLVED"],
        "validation_failures": failures,
        "note": (
            "Trajectory resolution represents administrative/reporting evidence, not proof of physical "
            "completion. DISAPPEARED_UNRESOLVED is not treated as a completion event. "
            "No survival target has been created."
        ),
    }
    for path in (silver_file, trajectory_file, audit_file):
        path.parent.mkdir(parents=True, exist_ok=True)
    with silver_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SILVER_COLUMNS)
        writer.writeheader()
        writer.writerows(accepted_rows)
    with trajectory_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRAJECTORY_COLUMNS)
        writer.writeheader()
        writer.writerows(s.model_dump(mode="json") for s in summaries)
    audit_file.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--silver", type=Path, default=SILVER)
    parser.add_argument("--trajectories", type=Path, default=TRAJECTORIES)
    parser.add_argument("--audit", type=Path, default=AUDIT)
    args = parser.parse_args()
    print(json.dumps(build_silver(args.input, args.silver, args.trajectories, args.audit), indent=2))
