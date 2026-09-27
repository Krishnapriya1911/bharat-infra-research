"""Gold cohort inclusion, exclusions, arithmetic, and source immutability."""

import csv
import hashlib
import json
from collections import defaultdict

import pytest

from gold.build_survival_cohort import (
    AUDIT, COHORT_COLUMNS, GOLD, SILVER, TRAJECTORIES, build_survival_cohort,
)
from schemas.monthly_record import MonthlyRecord
from schemas.trajectory import Trajectory, diff_year_month, resolve_trajectory


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames, list(reader)


def row(pid, month, status="ongoing", actual=""):
    return dict.fromkeys(MonthlyRecord.model_fields, "") | {
        "project_id": pid, "project_name": pid, "report_month": month,
        "source_file": "report.pdf", "source_page": "1",
        "observation_status": status, "actual_completion_date": actual,
    }


def fixture_files(tmp_path, rows):
    silver = tmp_path / "silver.csv"
    trajectory = tmp_path / "trajectory.csv"
    with silver.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=MonthlyRecord.model_fields)
        writer.writeheader()
        writer.writerows(rows)
    groups = defaultdict(list)
    for raw in rows:
        item = MonthlyRecord.model_validate(raw)
        groups[item.project_id].append(item)
    latest = max(r["report_month"] for r in rows)
    with trajectory.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=Trajectory.model_fields)
        writer.writeheader()
        writer.writerows(resolve_trajectory(pid, group, latest).model_dump(mode="json")
                         for pid, group in sorted(groups.items()))
    return silver, trajectory


def test_month_arithmetic_across_year_boundary():
    assert diff_year_month("2026-01", "2025-12") == 1


def test_inclusion_and_all_exclusion_categories(tmp_path):
    rows = [
        row("event", "2026-05"), row("event", "2026-08", "completed", "2026-07"),
        row("active", "2026-05"), row("active", "2026-08"),
        row("gone", "2026-07"),
        row("missing", "2026-05"), row("missing", "2026-08", "completed"),
        row("forward", "2026-05"), row("forward", "2026-08", "completed", "2026-09"),
        row("unknown", "2026-08", "completed", "2026-08"),
        row("completed_only", "2026-08", "completed", "2026-09"),
        row("early", "2026-05"), row("early", "2026-08", "completed", "2026-04"),
    ]
    silver, trajectory = fixture_files(tmp_path, rows)
    before = [hashlib.sha256(p.read_bytes()).digest() for p in (silver, trajectory)]
    out, audit_path = tmp_path / "gold.csv", tmp_path / "audit.json"
    audit = build_survival_cohort(silver, trajectory, out, audit_path)
    assert [hashlib.sha256(p.read_bytes()).digest() for p in (silver, trajectory)] == before
    assert json.loads(audit_path.read_text()) == audit
    fields, cohort = read_rows(out)
    assert fields == list(COHORT_COLUMNS)
    assert {r["project_id"] for r in cohort} == {"event", "active"}
    assert len(cohort) == len({r["project_id"] for r in cohort})
    by_id = {r["project_id"]: r for r in cohort}
    assert (by_id["event"]["entry_month"], by_id["event"]["exit_month"],
            by_id["event"]["duration_months"], by_id["event"]["event_observed"]) == (
                "2026-05", "2026-07", "2", "1")
    assert (by_id["active"]["entry_month"], by_id["active"]["exit_month"],
            by_id["active"]["duration_months"], by_id["active"]["event_observed"],
            by_id["active"]["censoring_reason"]) == (
                "2026-05", "2026-08", "3", "0", "ADMINISTRATIVE_END_OF_PANEL")
    assert all(int(r["duration_months"]) >= 0 and int(r["event_observed"]) in (0, 1)
               for r in cohort)
    reasons = {r["project_id"]: r["reason"] for r in audit["exclusions"]}
    assert reasons == {
        "gone": "DISAPPEARED_UNRESOLVED",
        "missing": "COMPLETED_STATUS_MISSING_ACTUAL_DATE",
        "forward": "INCONSISTENT_COMPLETION_DATE",
        "unknown": "NO_OBSERVED_ONGOING_ENTRY",
        "completed_only": "NO_OBSERVED_ONGOING_ENTRY",
        "early": "EVENT_BEFORE_PANEL_ENTRY",
    }
    assert audit["included_project_count"] == audit["event_count"] + audit["censored_count"]
    assert audit["total_projects_considered"] == audit["included_project_count"] + audit["excluded_project_count"]


def test_consistency_none_with_ongoing_evidence_excluded(tmp_path):
    silver, trajectory = fixture_files(tmp_path, [
        row("p", "2026-05"), row("p", "2026-08", "completed", "2026-07")])
    fields, records = read_rows(trajectory)
    assert records[0]["completion_date_consistency_flag"] == "True"
    records[0]["completion_date_consistency_flag"] = ""
    with trajectory.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    audit = build_survival_cohort(silver, trajectory, tmp_path / "gold.csv", tmp_path / "audit.json")
    assert audit["exclusion_counts_by_reason"] == {"INSUFFICIENT_LONGITUDINAL_EVIDENCE": 1}


def test_real_source_files_untouched_and_counts_reconcile(tmp_path):
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (SILVER, TRAJECTORIES)}
    audit = build_survival_cohort(SILVER, TRAJECTORIES, tmp_path / "gold.csv", tmp_path / "audit.json")
    assert {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before} == before
    _, cohort = read_rows(tmp_path / "gold.csv")
    assert len(cohort) == audit["included_project_count"]
    assert len({r["project_id"] for r in cohort}) == len(cohort)
    assert audit["included_project_count"] == audit["event_count"] + audit["censored_count"]
    assert audit["total_projects_considered"] == audit["included_project_count"] + audit["excluded_project_count"]
    assert all(int(r["duration_months"]) >= 0 and r["event_observed"] in {"0", "1"}
               for r in cohort)
