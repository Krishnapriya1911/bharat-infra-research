"""New layout evidence: month tokens and the missing fields in OCMS tables."""

import pytest
import csv
import json
from pathlib import Path

from tabular.legacy_2025 import month_value


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("raw,expected", [
    ("4-1999", "1999-04"), ("(Jun-2023)", "2023-06"),
    ("{6/2023}", "2023-06"), ("(N.A.)", None),
])
def test_legacy_month_precision(raw, expected):
    assert month_value(raw) == expected


@pytest.mark.parametrize("raw", ["13/2025", "Foo-2025", "2025-06-01"])
def test_legacy_invalid_month_rejected(raw):
    with pytest.raises(ValueError):
        month_value(raw)


def test_historical_panel_source_coverage_and_audit_reconciliation():
    processed = ROOT / "datasets/processed"
    audit = json.loads((processed / "mospi_multimonth_audit.json").read_text())
    historical = audit["per_report"][:12]
    assert [entry["report_month"] for entry in historical] == [
        f"2025-{month:02d}" for month in range(4, 13)] + [
        f"2026-{month:02d}" for month in range(1, 4)]
    assert all(entry["source_file"] == f"PAIMANA_FlashReport_{entry['report_month']}.pdf"
               for entry in historical)
    assert all(sum(entry["printed_serials"].values()) ==
               entry["parsed_ongoing_rows"] + entry["parsed_completed_rows"] +
               entry["rejected_rows"] + entry["duplicate_rows_removed_within_report"]
               for entry in historical)
    with (processed / "mospi_monthly_snapshots.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert {row["report_month"] for row in rows} == {entry["report_month"] for entry in audit["per_report"]}
    assert len(rows) == sum(entry["parsed_ongoing_rows"] + entry["parsed_completed_rows"]
                            for entry in audit["per_report"])
    legacy = [row for row in rows if row["report_month"] == "2025-04"]
    assert legacy and all(row["start_date"] == "" for row in legacy)
    assert all(row["source_file"] == "PAIMANA_FlashReport_2025-04.pdf"
               and row["source_page"] and row["raw_date_values"] and row["raw_cost_values"]
               for row in legacy)
