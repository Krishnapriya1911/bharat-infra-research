"""Build a month-precision cohort from Silver rows and project trajectories.

This output is cohort/target metadata, not a predictor matrix. Reported actual
completion, resolution, consistency, censoring, event, exit, and duration are
never predictor features. Revised completion/cost remain withheld pending a
prediction-cutoff policy. Panel entry is the first observed ongoing report,
not project start; prevalent cases have left truncation.
"""

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

from schemas.monthly_record import MonthlyRecord, ObservationStatus, validate_year_month
from schemas.trajectory import Trajectory, TrajectoryResolution as State, diff_year_month


ROOT = Path(__file__).resolve().parents[2]
SILVER = ROOT / "datasets/processed/mospi_silver_validated.csv"
TRAJECTORIES = ROOT / "datasets/processed/mospi_project_trajectories.csv"
GOLD = ROOT / "datasets/processed/mospi_gold_survival_cohort.csv"
AUDIT = ROOT / "datasets/processed/mospi_gold_survival_audit.json"
COHORT_COLUMNS = (
    "project_id", "entry_month", "exit_month", "duration_months", "event_observed",
    "censoring_reason", "trajectory_resolution", "first_observed_report_month",
    "last_observed_report_month", "last_ongoing_snapshot_month",
    "reported_actual_completion_month", "completion_date_consistency_flag",
    "snapshots_observed_count",
)
NO_ENTRY = "NO_OBSERVED_ONGOING_ENTRY"
MISSING_DATE = "COMPLETED_STATUS_MISSING_ACTUAL_DATE"
DISAPPEARED = "DISAPPEARED_UNRESOLVED"
CONTRADICTION = "INCONSISTENT_COMPLETION_DATE"
INSUFFICIENT = "INSUFFICIENT_LONGITUDINAL_EVIDENCE"
EARLY_EVENT = "EVENT_BEFORE_PANEL_ENTRY"


def _read(path: Path, expected: tuple[str, ...]):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != list(expected):
            raise ValueError(f"Unexpected columns in {path}: {reader.fieldnames}")
        yield from reader


def _trajectory(row: dict[str, str]) -> Trajectory:
    # CSV represents Optional values with empty cells; Pydantic receives None.
    return Trajectory.model_validate({key: None if value == "" else value
                                      for key, value in row.items()})


def build_survival_cohort(
    silver_file: Path = SILVER,
    trajectory_file: Path = TRAJECTORIES,
    cohort_file: Path = GOLD,
    audit_file: Path = AUDIT,
) -> dict:
    """Write included IDs once and record every excluded ID with one reason.

    Fail closed on invalid/mismatched inputs; do not reconstruct missing evidence.
    """
    ongoing_months: dict[str, list[str]] = defaultdict(list)
    all_ids: set[str] = set()
    report_months: list[str] = []
    for raw in _read(silver_file, tuple(MonthlyRecord.model_fields)):
        record = MonthlyRecord.model_validate(raw)
        all_ids.add(record.project_id)
        report_months.append(record.report_month)
        if record.observation_status == ObservationStatus.ongoing:
            ongoing_months[record.project_id].append(record.report_month)
    latest = max(report_months) if report_months else None
    trajectories: dict[str, Trajectory] = {}
    for raw in _read(trajectory_file, tuple(Trajectory.model_fields)):
        item = _trajectory(raw)
        if item.project_id in trajectories:
            raise ValueError(f"duplicate project_id in trajectories: {item.project_id}")
        trajectories[item.project_id] = item
    if all_ids != trajectories.keys():
        raise ValueError("Silver and trajectory project IDs differ")

    cohort: list[dict] = []
    exclusions: list[dict[str, str]] = []
    input_resolutions = Counter(item.trajectory_resolution.value for item in trajectories.values())
    for pid in sorted(trajectories):
        item = trajectories[pid]
        entry = min(ongoing_months[pid]) if ongoing_months[pid] else None
        state = item.trajectory_resolution
        actual = item.reported_actual_completion_month
        reason = None
        if entry is None:
            reason = NO_ENTRY
        elif state == State.DISAPPEARED_UNRESOLVED:
            reason = DISAPPEARED
        elif state == State.REPORTED_COMPLETED_MISSING_DATE:
            reason = MISSING_DATE
        elif state == State.REPORTED_COMPLETED_EXPLICIT_DATE:
            if actual is None:
                raise ValueError(f"explicit-date trajectory missing actual month: {pid}")
            validate_year_month(actual)
            if diff_year_month(actual, entry) < 0:
                reason = EARLY_EVENT
            elif item.completion_date_consistency_flag is False:
                reason = CONTRADICTION
            elif item.completion_date_consistency_flag is None:
                reason = INSUFFICIENT
            else:
                exit_month, event, censoring = actual, 1, ""
        elif state == State.ONGOING_ACTIVE:
            if latest is None:
                raise ValueError("active project without a global report month")
            exit_month, event, censoring = latest, 0, "ADMINISTRATIVE_END_OF_PANEL"
        else:
            raise ValueError(f"unrecognized trajectory resolution: {state}")
        if reason:
            exclusions.append({"project_id": pid, "trajectory_resolution": state.value, "reason": reason})
            continue
        duration = diff_year_month(exit_month, entry)
        if duration < 0:
            raise ValueError(f"negative duration for {pid}")
        cohort.append({
            "project_id": pid, "entry_month": entry, "exit_month": exit_month,
            "duration_months": duration, "event_observed": event,
            "censoring_reason": censoring, "trajectory_resolution": state.value,
            "first_observed_report_month": item.first_observed_report_month,
            "last_observed_report_month": item.last_observed_report_month,
            "last_ongoing_snapshot_month": item.last_ongoing_snapshot_month,
            "reported_actual_completion_month": actual,
            "completion_date_consistency_flag": item.completion_date_consistency_flag,
            "snapshots_observed_count": item.snapshots_observed_count,
        })
    durations = [row["duration_months"] for row in cohort]
    event_count = sum(row["event_observed"] for row in cohort)
    censored_count = len(cohort) - event_count
    exclusion_counts = Counter(row["reason"] for row in exclusions)
    audit = {
        "source_silver_file": str(silver_file.relative_to(ROOT)) if silver_file.is_relative_to(ROOT) else str(silver_file),
        "source_trajectory_file": str(trajectory_file.relative_to(ROOT)) if trajectory_file.is_relative_to(ROOT) else str(trajectory_file),
        "global_latest_report_month": latest,
        "total_projects_considered": len(trajectories),
        "included_project_count": len(cohort),
        "event_count": event_count,
        "censored_count": censored_count,
        "excluded_project_count": len(exclusions),
        "exclusion_counts_by_reason": dict(sorted(exclusion_counts.items())),
        "trajectory_resolution_counts_input": {state.value: input_resolutions[state.value] for state in State},
        "included_event_project_count": event_count,
        "included_active_censored_project_count": censored_count,
        "duration_months_summary": {
            "min": min(durations) if durations else None,
            "max": max(durations) if durations else None,
            "median": median(durations) if durations else None,
            "mean": mean(durations) if durations else None,
        },
        "entry_month_counts": dict(sorted(Counter(row["entry_month"] for row in cohort).items())),
        "exit_month_counts": dict(sorted(Counter(row["exit_month"] for row in cohort).items())),
        "event_definition_note": "Validated reported completion event requires an explicit month, consistent prior ongoing evidence and event month at or after observed panel entry; it is administrative reporting evidence, not physical completion ground truth.",
        "censoring_definition_note": "Only ongoing-active projects are administratively right-censored at the global latest report month; unresolved disappearances are excluded.",
        "left_truncation_note": "First observed ongoing month is administrative panel entry, not project start. Prevalent cases have left truncation; durations measure time from observed panel entry, not full project lifetime.",
        "research_boundary_note": "Cohort/target metadata only, not a predictor matrix. Actual completion, resolution, consistency, censoring, event, exit and duration are not predictor features. Revised completion and revised cost are withheld. No model training.",
        "exclusions": exclusions,
    }
    if len(cohort) + len(exclusions) != len(trajectories):
        raise AssertionError("project counts did not reconcile")
    cohort_file.parent.mkdir(parents=True, exist_ok=True)
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    with cohort_file.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COHORT_COLUMNS)
        writer.writeheader()
        writer.writerows(cohort)
    audit_file.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return audit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--silver", type=Path, default=SILVER)
    parser.add_argument("--trajectories", type=Path, default=TRAJECTORIES)
    parser.add_argument("--cohort", type=Path, default=GOLD)
    parser.add_argument("--audit", type=Path, default=AUDIT)
    args = parser.parse_args()
    result = build_survival_cohort(args.silver, args.trajectories, args.cohort, args.audit)
    print(json.dumps({key: value for key, value in result.items() if key != "exclusions"}, indent=2))
