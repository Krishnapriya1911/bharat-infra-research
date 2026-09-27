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
