"""Deterministic extraction of PAIMANA monthly project tables.

Usage: python data-pipeline/tabular/prepare_projects.py

Dates have month precision. The parser writes YYYY-MM and does not invent a day
or an outcome label. See the JSON audit alongside the longitudinal CSV.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

import pdfplumber


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "datasets/raw/mospi/reports"
OUTPUT = ROOT / "datasets/processed"
MONTH_NAMES = {name.upper(): number for number, name in enumerate(
    ("January", "February", "March", "April", "May", "June", "July", "August",
     "September", "October", "November", "December"), 1)}
COLUMNS = [
    "project_id", "project_name", "ministry", "agency", "sector", "state",
    "approval_date", "start_date", "original_completion_date",
    "revised_completion_date", "actual_completion_date",
    "original_cost_crore", "revised_cost_crore",
    "cumulative_expenditure_crore", "physical_progress_pct", "report_month",
    "source_file", "source_page", "raw_date_values", "raw_cost_values",
]
LABELS = ["delay_days", "planned_duration_days", "delay_ratio", "delay_over_20pct"]
PANEL_COLUMNS = COLUMNS + ["observation_status"]
DATE = re.compile(r"\(?\d{2}/\d{4}\)?|\(-\)|NA|N/A")
NUMBER = re.compile(r"\(?-?\d[\d,]*(?:\.\d+)?\)?|\(-\)")
CODE = re.compile(r"\(?\d{6}\)?")


def discover_reports(directory: Path) -> list[Path]:
    """Discover PDF inputs; month/order are validated from PDF contents later."""
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix.lower() == ".pdf")


def report_month(text: str) -> str:
    matches = re.findall(r"\b(" + "|".join(MONTH_NAMES) + r")\s+(20\d{2})\b",
                         text.upper())
    months = {f"{year}-{MONTH_NAMES[name]:02d}" for name, year in matches}
    if len(months) != 1:
        raise ValueError(f"expected one report month, found {sorted(months)}")
    return months.pop()


def parse_date(raw: str | None) -> str | None:
    """Preserve source precision: MM/YYYY becomes YYYY-MM, never a guessed day."""
    if raw is None or raw.strip() in {"", "-", "(-)", "NA", "N/A"}:
        return None
    value = raw.strip().strip("()")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return None
    match = re.fullmatch(r"(\d{2})/(\d{4})", value)
    if match and 1 <= int(match[1]) <= 12:
        return f"{match[2]}-{match[1]}"
    return None


def parse_number(raw: str | None) -> float | None:
    if raw is None or raw.strip() in {"", "-", "(-)", "NA", "N/A"}:
        return None
    value = raw.strip()
    if value.startswith("(") and value.endswith(")"):
        value = value[1:-1]
    value = value.replace(",", "")
    try:
        return float(value) if re.fullmatch(r"-?\d+(?:\.\d+)?", value) else None
    except ValueError:
        return None


def valid_percentage(raw: str | None) -> float | None:
    value = parse_number(raw)
    if value is not None and not 0 <= value <= 100:
        raise ValueError(f"physical progress outside 0–100: {raw}")
    return value


def add_delay_labels(record: dict) -> dict:
    """Only day-precision dates support exact day-based outcomes."""
    result = dict(record)
    result.update({key: None for key in LABELS})
    values = [result.get(key) for key in
              ("start_date", "original_completion_date", "actual_completion_date")]
    if not all(isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) for v in values):
        return result
    start, original, actual = (date.fromisoformat(v) for v in values)
    duration = (original - start).days
    if duration <= 0:
        return result
    delay = (actual - original).days
    ratio = delay / duration
    result.update(delay_days=delay, planned_duration_days=duration,
                  delay_ratio=ratio, delay_over_20pct=int(ratio > 0.20))
    return result


def deduplicate(rows: list[dict]) -> tuple[list[dict], int, list[dict]]:
    """Drop only identical repeated records; conflicting IDs require review."""
    seen: dict[tuple[str, str], dict] = {}
    kept, conflicts, removed = [], [], 0
    for row in rows:
        key = (row["report_month"], row["project_id"])
        if key in seen:
            comparable = lambda r: {k: v for k, v in r.items() if k != "source_page"}
            if comparable(row) == comparable(seen[key]):
                removed += 1
            else:
                conflicts.append({"project_id": row["project_id"],
                                  "source_file": row.get("source_file"),
                                  "report_month": row["report_month"],
                                  "section": row.get("observation_status", "unknown"),
                                  "page": row.get("source_page"),
                                  "raw_excerpt": row.get("project_name"),
                                  "pages": [seen[key]["source_page"], row["source_page"]],
                                  "reason": "conflicting duplicate ID"})
            continue
        seen[key] = row
        kept.append(row)
    return kept, removed, conflicts


def column_words(words: list[dict], low: int, high: int) -> list[dict]:
    return sorted((w for w in words if low <= w["x0"] < high),
                  key=lambda w: (round(w["top"] / 5), w["x0"]))


def tokens(words: list[dict], low: int, high: int, pattern: re.Pattern) -> list[str]:
    return [w["text"] for w in column_words(words, low, high)
            if pattern.fullmatch(w["text"])]


def name_and_agency(words: list[dict], code_top: float) -> tuple[str, str | None]:
    name_words = [w for w in words if 84 <= w["x0"] < 475 and w["top"] <= code_top]
    agency_words = [w for w in name_words if "BoldOblique" in w["fontname"]]
    agency = " ".join(w["text"] for w in sorted(agency_words, key=lambda w: (w["top"], w["x0"])))
    agency = agency.strip("() ") or None
    normal = [w for w in name_words if "Bold" not in w["fontname"]]
    lines: dict[float, list[dict]] = {}
    for word in normal:
        lines.setdefault(round(word["top"], 1), []).append(word)
    # Section headings are separated from the project name by a larger gap.
    ordered = sorted(lines)
    if not ordered:
        return "", agency
    start = 0
    for n in range(1, len(ordered)):
        if ordered[n] - ordered[n - 1] >= 15:
            start = n
    selected = [w for y in ordered[start:] for w in sorted(lines[y], key=lambda w: w["x0"])]
    return " ".join(w["text"] for w in selected).strip(), agency


def parse_block(words: list[dict], kind: str, page: int, serial: int,
                anchor_top: float, page_words: list[dict], month: str,
                source_file: str, actual_column: bool) -> dict:
    completed = kind == "completed"
    name_high = 475 if not completed else 480
    codes = [w for w in words if 84 <= w["x0"] < 160 and CODE.fullmatch(w["text"])
             and "Bold" in w["fontname"]]
    if len(codes) != 1:
        raise ValueError(f"expected one project code, found {[w['text'] for w in codes]}")
    code = codes[0]
    project_name, agency = name_and_agency(words, code["top"])
    if not project_name or not agency:
        raise ValueError("project name or agency could not be isolated")
    # Values are vertically stacked around the printed serial, while names can
    # span many lines. Restrict data columns to the row's three value lines.
    data_words = [w for w in page_words if anchor_top - 16 <= w["top"] <= anchor_top + 16]
    state_words = column_words(data_words, name_high, 570)
    state = " ".join(w["text"] for w in sorted(state_words, key=lambda w: (w["top"], w["x0"]))) or None
    # Multi-state labels can extend left across the project-name column in this
    # PDF. Without a reliable boundary we must not publish a corrupted name.
    if state and ("Multi-States" in state or "(" in state or ")" in state):
        raise ValueError("multi-state value crosses or may cross the name/state boundary")
    if project_name.startswith("("):
        raise ValueError("project name begins with a state-column fragment")
    if completed:
        approval = tokens(data_words, 570, 680, DATE)
        completion = tokens(data_words, 680, 820, DATE)
        costs = tokens(data_words, 820, 940, NUMBER)
        spent = tokens(data_words, 940, 1050, NUMBER)
        expected_dates = 3 if actual_column else 2
        if [len(approval), len(completion), len(costs), len(spent)] != [2, expected_dates, 2, 1]:
            raise ValueError(f"column token counts: approval={approval}, completion={completion}, cost={costs}, expenditure={spent}")
        if actual_column:
            actual, original, revised = completion
        else:
            actual = None
            original, revised = completion
        progress = None
    else:
        approval = tokens(data_words, 570, 665, DATE)
        completion = tokens(data_words, 665, 755, DATE)
        costs = tokens(data_words, 755, 845, NUMBER)
        spent = tokens(data_words, 845, 945, NUMBER)
        pct = tokens(data_words, 945, 1050, NUMBER)
        if [len(approval), len(completion), len(costs), len(spent), len(pct)] != [2, 2, 2, 1, 1]:
            raise ValueError(f"column token counts: approval={approval}, completion={completion}, cost={costs}, expenditure={spent}, progress={pct}")
        actual, original, revised = None, *completion
        progress = valid_percentage(pct[0])
    raw_dates = {"approval": approval[0], "start": approval[1],
                 "actual": actual, "original": original, "revised": revised}
    raw_costs = {"original": costs[0], "revised": costs[1], "expenditure": spent[0]}
    result = {
        "project_id": code["text"].strip("()"), "project_name": project_name,
        "ministry": None, "agency": agency, "sector": None, "state": state,
        "approval_date": parse_date(approval[0]), "start_date": parse_date(approval[1]),
        "original_completion_date": parse_date(original),
        "revised_completion_date": parse_date(revised),
        "actual_completion_date": parse_date(actual),
        "original_cost_crore": parse_number(costs[0]),
        "revised_cost_crore": parse_number(costs[1]),
        "cumulative_expenditure_crore": parse_number(spent[0]),
        "physical_progress_pct": progress, "report_month": month,
        "source_file": source_file, "source_page": page,
        "raw_date_values": json.dumps(raw_dates, ensure_ascii=False),
        "raw_cost_values": json.dumps(raw_costs, ensure_ascii=False),
    }
    for field, raw in [("approval_date", approval[0]), ("start_date", approval[1]),
                       ("original_completion_date", original),
                       ("revised_completion_date", revised),
                       ("actual_completion_date", actual)]:
        if raw is not None and raw not in {"(-)", "NA", "N/A"} and result[field] is None:
            raise ValueError(f"invalid {field}: {raw}")
    return result


def page_rows(page, page_number: int, kind: str, month: str,
              source_file: str, actual_column: bool) -> tuple[list[dict], list[dict], list[int]]:
    words = [w for w in page.extract_words(extra_attrs=["fontname"])
             if 250 < w["top"] < 1420]
    anchors = [w for w in words if w["x0"] < 85 and w["text"].isdigit()
               and 1 <= int(w["text"]) <= 10000]
    anchors.sort(key=lambda w: w["top"])
    codes = [w for w in words if 84 <= w["x0"] < 160 and CODE.fullmatch(w["text"])
             and "Bold" in w["fontname"]]
    codes.sort(key=lambda w: w["top"])
    rows, failures = [], []
    prior_end = 250.0
    for anchor in anchors:
        following = [c for c in codes if anchor["top"] - 50 <= c["top"]
                     and c["top"] > prior_end]
        if not following:
            failures.append({"source_file": source_file, "report_month": month,
                             "section": kind, "page": page_number, "serial": anchor["text"],
                             "reason": "no following project code",
                             "raw_excerpt": " ".join(w["text"] for w in words
                                                     if abs(w["top"] - anchor["top"]) < 18)[:300]})
            continue
        end = following[0]["top"] + 1
        block = [w for w in words if prior_end < w["top"] <= end]
        try:
            rows.append(parse_block(block, kind, page_number, int(anchor["text"]),
                                    anchor["top"], words, month, source_file, actual_column))
        except ValueError as exc:
            failures.append({"source_file": source_file, "report_month": month,
                             "section": kind, "page": page_number, "serial": anchor["text"],
                             "project_code_candidate": following[0]["text"],
                             "reason": str(exc),
                             "raw_excerpt": " ".join(w["text"] for w in block[:35])})
        prior_end = end
    return rows, failures, [int(a["text"]) for a in anchors]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def parse_report(path: Path) -> tuple[list[dict], list[dict], dict]:
    ongoing, completed, failures = [], [], []
    serials = {"ongoing": [], "completed": []}
    section_pages = Counter()
    with pdfplumber.open(path) as pdf:
        month = report_month(pdf.pages[0].extract_text() or "")
        for index, page in enumerate(pdf.pages):
            header = page.crop((0, 100, page.width, 250)).extract_text() or ""
            kind = ("completed" if "Completed Projects During Month" in header else
                    "ongoing" if "All Ongoing Projects" in header else None)
            if kind is None:
                continue
            if report_month(header) != month:
                raise RuntimeError(f"{path.name} page {index + 1}: inconsistent report month")
            actual_column = "Actual Date of Completion" in header
            if kind == "ongoing" and actual_column:
                raise RuntimeError(f"{path.name} page {index + 1}: unexpected ongoing header")
            records, errors, page_serials = page_rows(
                page, index + 1, kind, month, path.name, actual_column)
            section_pages[kind] += 1
            serials[kind].extend(page_serials)
            (completed if kind == "completed" else ongoing).extend(records)
            failures.extend(errors)
    for kind in ("ongoing", "completed"):
        actual = serials[kind]
        if not actual or actual != list(range(1, max(actual) + 1)):
            raise RuntimeError(f"{path.name}: {kind} printed serials are missing, repeated or out of order")
    ongoing, ongoing_dupes, ongoing_conflicts = deduplicate(ongoing)
    completed, completed_dupes, completed_conflicts = deduplicate(completed)
    failures.extend(ongoing_conflicts + completed_conflicts)
    total_serials = len(serials["ongoing"]) + len(serials["completed"])
    if len(failures) > total_serials * 0.30:
        raise RuntimeError(f"{path.name}: {len(failures)}/{total_serials} rows rejected; layout requires review")
    audit = {
        "source_file": path.name, "report_month": month,
        "printed_serials": {kind: len(values) for kind, values in serials.items()},
        "section_pages": dict(section_pages),
        "parsed_ongoing_rows": len(ongoing), "parsed_completed_rows": len(completed),
        "rejected_rows": len(failures),
        "duplicate_rows_removed_within_report": ongoing_dupes + completed_dupes,
        "missing_critical_dates": {
            "ongoing": sum(not r["start_date"] or not r["original_completion_date"] for r in ongoing),
            "completed": sum(not r["start_date"] or not r["original_completion_date"]
                             or not r["actual_completion_date"] for r in completed),
        },
        "completed_without_explicit_actual_date": sum(not r["actual_completion_date"] for r in completed),
        "failures": failures,
    }
    return ongoing, completed, audit


def continuity(rows: list[dict]) -> dict:
    months = sorted({r["report_month"] for r in rows})
    all_ids = {r["project_id"] for r in rows}
    id_months: dict[str, set[str]] = {}
    ongoing = {month: set() for month in months}
    completed = {month: set() for month in months}
    for row in rows:
        ident, month = row["project_id"], row["report_month"]
        id_months.setdefault(ident, set()).add(month)
        (ongoing if row["observation_status"] == "ongoing" else completed)[month].add(ident)
    transitions = []
    for index, month in enumerate(months):
        previous = ongoing[months[index - 1]] if index else set()
        transitions.append({
            "report_month": month,
            "entering_ongoing_ids": len(ongoing[month] - previous),
            "leaving_ongoing_ids": len(previous - ongoing[month]) if index else 0,
            "ongoing_ids": len(ongoing[month]),
        })
    previously_ongoing: set[str] = set()
    later_completed: set[str] = set()
    for month in months:
        later_completed.update(previously_ongoing & completed[month])
        previously_ongoing.update(ongoing[month])
    return {
        "unique_project_ids": len(all_ids),
        "projects_present_in_multiple_months": sum(len(seen) > 1 for seen in id_months.values()),
        "ongoing_panel_changes": transitions,
        "previously_ongoing_ids_later_in_completed_tables": len(later_completed),
        "note": "Direct project-ID matches only; rejected rows are excluded. Leaving ongoing is not itself proof of completion.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=REPORTS)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    paths = discover_reports(args.reports_dir)
    if not paths:
        raise RuntimeError(f"no PDF reports found in {args.reports_dir}")
    rows, audits, failures = [], [], []
    for path in paths:
        ongoing, completed, audit = parse_report(path)
        rows.extend({**r, "observation_status": "ongoing"} for r in ongoing)
        rows.extend({**r, "observation_status": "completed"} for r in completed)
        failures.extend(audit.pop("failures"))
        audits.append(audit)
        print(f"{path.name}: {audit['parsed_ongoing_rows']} ongoing, "
              f"{audit['parsed_completed_rows']} completed, {audit['rejected_rows']} rejected",
              flush=True)
    months = [a["report_month"] for a in audits]
    if len(set(months)) != len(months):
        raise RuntimeError(f"multiple reports claim the same month: {months}")
    rows.sort(key=lambda r: (r["report_month"], r["project_id"], r["observation_status"]))
    audits.sort(key=lambda a: a["report_month"])
    summary = continuity(rows)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "mospi_monthly_snapshots.csv", rows, PANEL_COLUMNS)
    (args.output_dir / "mospi_multimonth_audit.json").write_text(
        json.dumps({"per_report": audits, "continuity": summary, "failures": failures},
                   indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"per_report": audits, "continuity": summary}, indent=2))


if __name__ == "__main__":
    main()
