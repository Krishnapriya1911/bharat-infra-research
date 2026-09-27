"""Unit checks for source-preserving parsing and label semantics."""

import importlib.util
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location("prepare_projects", Path(__file__).with_name("prepare_projects.py"))
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


@pytest.mark.parametrize("raw,expected", [
    ("(08/2026)", "2026-08"), ("02/2020", "2020-02"),
    ("2020-02-29", "2020-02-29"), ("02/2021", "2021-02"),
    ("13/2026", None), ("2021-02-29", None), ("(-)", None),
    ("NA", None), (None, None),
])
def test_date_parsing(raw, expected):
    assert module.parse_date(raw) == expected


@pytest.mark.parametrize("raw,expected", [
    ("(23,136.00)", 23136.0), ("0.00", 0.0),
    ("1,000,000,000.75", 1000000000.75), ("(-)", None),
    ("NA", None), (None, None), ("not a number", None),
])
def test_numeric_parsing(raw, expected):
    assert module.parse_number(raw) == expected


def test_percentage_validation():
    assert module.valid_percentage("100.00") == 100
    assert module.valid_percentage("(-)") is None
    with pytest.raises(ValueError):
        module.valid_percentage("100.01")
    with pytest.raises(ValueError):
        module.valid_percentage("-0.01")


def test_deduplication_drops_only_identical_records():
    first = {"project_id": "123", "report_month": "2026-08", "project_name": "A", "source_page": 1}
    identical = {**first, "source_page": 2}
    conflicting = {**first, "project_name": "B", "source_page": 3}
    kept, removed, conflicts = module.deduplicate([first, identical, conflicting])
    assert kept == [first]
    assert removed == 1
    assert len(conflicts) == 1


def test_day_precision_required_for_delay_labels():
    monthly = module.add_delay_labels({"start_date": "2020-01",
        "original_completion_date": "2021-01", "actual_completion_date": "2021-04"})
    assert all(monthly[key] is None for key in module.LABELS)
    exact = module.add_delay_labels({"start_date": "2020-01-01",
        "original_completion_date": "2020-11-01", "actual_completion_date": "2021-02-01"})
    assert exact["planned_duration_days"] == 305
    assert exact["delay_days"] == 92
    assert exact["delay_over_20pct"] == 1
    assert exact["delay_ratio"] == pytest.approx(92 / 305)


def test_discovery_uses_pdf_files_only(tmp_path):
    (tmp_path / "b.pdf").touch()
    (tmp_path / "a.PDF").touch()
    (tmp_path / "note.txt").touch()
    assert [p.name for p in module.discover_reports(tmp_path)] == ["a.PDF", "b.pdf"]


def test_report_month_from_content_and_ambiguity():
    assert module.report_month("PAIMANA FLASH REPORT APRIL 2026") == "2026-04"
    assert module.report_month("Completed Projects During Month\nJUNE 2026") == "2026-06"
    with pytest.raises(ValueError):
        module.report_month("APRIL 2026 and MAY 2026")
    with pytest.raises(ValueError):
        module.report_month("no dated header")


def test_same_id_preserved_across_months_and_continuity():
    rows = [
        {"project_id": "A", "report_month": "2026-04", "observation_status": "ongoing"},
        {"project_id": "A", "report_month": "2026-05", "observation_status": "ongoing"},
        {"project_id": "B", "report_month": "2026-05", "observation_status": "ongoing"},
        {"project_id": "A", "report_month": "2026-06", "observation_status": "completed"},
    ]
    summary = module.continuity(rows)
    assert summary["unique_project_ids"] == 2
    assert summary["projects_present_in_multiple_months"] == 1
    assert summary["previously_ongoing_ids_later_in_completed_tables"] == 1
    assert summary["ongoing_panel_changes"][1]["entering_ongoing_ids"] == 1
    assert summary["ongoing_panel_changes"][2]["leaving_ongoing_ids"] == 2


def test_deduplication_only_within_month():
    first = {"project_id": "123", "report_month": "2026-04", "source_page": 1}
    later = {**first, "report_month": "2026-05", "source_page": 2}
    kept, removed, failures = module.deduplicate([first, later])
    assert kept == [first, later]
    assert removed == 0 and not failures


def test_chronological_sort_and_provenance_fields():
    rows = [
        {"project_id": "2", "report_month": "2026-05", "observation_status": "ongoing"},
        {"project_id": "2", "report_month": "2026-04", "observation_status": "ongoing"},
        {"project_id": "1", "report_month": "2026-04", "observation_status": "completed"},
    ]
    rows.sort(key=lambda r: (r["report_month"], r["project_id"], r["observation_status"]))
    assert [(r["report_month"], r["project_id"]) for r in rows] == [
        ("2026-04", "1"), ("2026-04", "2"), ("2026-05", "2")]
    assert {"project_id", "report_month", "source_file", "source_page",
            "raw_date_values", "raw_cost_values", "observation_status"} <= set(module.PANEL_COLUMNS)
    assert not set(module.LABELS) & set(module.PANEL_COLUMNS)


def test_malformed_row_rejected_with_source_context():
    with pytest.raises(ValueError, match="project code"):
        module.parse_block([], "ongoing", 17, 1, 300, [], "2026-04", "source.pdf", False)
