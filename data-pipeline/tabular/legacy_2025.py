"""Deterministic positional extraction for the April–June 2025 OCMS flash layout.

These reports precede the PAIMANA portal format. Only their main ongoing table
and completed-during-month table are read. North-East and added-project tables
are subsets/other statuses and must not be counted again. Ambiguity is logged.
"""

from collections import Counter
import json
import re
from pathlib import Path

import pdfplumber

from .prepare_projects import deduplicate, parse_number, report_month, valid_percentage


CODE = re.compile(r"\(([A-Z]\d{8}|\d{9})\)")
DATE = re.compile(r"([0-9]{1,2})[-/]([0-9]{4})")
NAMED_DATE = re.compile(r"([A-Za-z]{3})-([0-9]{4})")
MONTH_NAMES = {name:i for i,name in enumerate(('Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'),1)}
MISSING = {"N.A.", "N.A", "NA", "(-)", "", "-"}


def month_value(token: str | None) -> str | None:
    if token is None or token.strip("(){} ") in MISSING:
        return None
    value = token.strip("(){} ")
    named = NAMED_DATE.fullmatch(value)
    if named:
        if named[1].title() not in MONTH_NAMES:
            raise ValueError(f"invalid month token: {token!r}")
        return f"{named[2]}-{MONTH_NAMES[named[1].title()]:02d}"
    match = DATE.fullmatch(value)
    if not match or not 1 <= int(match[1]) <= 12:
        raise ValueError(f"invalid month token: {token!r}")
    return f"{match[2]}-{int(match[1]):02d}"


def _ordered(words):
    return sorted(words, key=lambda w: (round(w["top"] / 5), w["x0"]))


def _tokens(words, low, high, top, height=27):
    return [w["text"] for w in _ordered(words)
            if low <= w["x0"] < high and top - 3 <= w["top"] <= top + height]


def _row(words, anchor, end, kind, month, path, page_number, layout):
    completed = kind == "completed"
    top = anchor["top"]
    name_low, name_high = layout['name']
    body = [w for w in words if top - 2 <= w["top"] < end and
            name_low <= w["x0"] < name_high]
    codes = [(w, CODE.fullmatch(w["text"])) for w in body]
    codes = [(w, m) for w, m in codes if m]
    if len(codes) != 1:
        raise ValueError(f"expected one parenthesized project code, found {[m.group(1) for _,m in codes]}")
    code_word, match = codes[0]
    lines = {}
    for w in body:
        if w["top"] < code_word["top"]:
            lines.setdefault(round(w["top"] / 5), []).append(w)
    ordered = sorted(lines)
    if len(ordered) < 2:
        raise ValueError("project name/agency not isolated")
    agency_line = " ".join(w["text"] for w in sorted(lines[ordered[-1]], key=lambda w:w["x0"]))
    if not agency_line.startswith("(") or not agency_line.endswith(")"):
        raise ValueError(f"ambiguous agency line: {agency_line}")
    agency = agency_line.strip("() ")
    name = " ".join(w["text"] for key in ordered[:-1]
                    for w in sorted(lines[key], key=lambda w:w["x0"]))
    if not name or not agency:
        raise ValueError("missing project name or agency")
    if completed:
        original_cost = _tokens(words, *layout['cost'], top, 3)
        original_date = _tokens(words, *layout['completion'], top, 3)
        spent = _tokens(words, *layout['spent'], top, 3)
        if list(map(len, (original_cost, original_date, spent))) != [1, 1, 1]:
            raise ValueError(f"completed value columns: {original_cost}, {original_date}, {spent}")
        # State is printed on its own line immediately after the code.
        state_words = [w for w in words if name_low <= w["x0"] < name_high
                       and code_word["top"] + 2 < w["top"] < end]
        state_raw = " ".join(w["text"] for w in _ordered(state_words))
        state = state_raw.strip("() ") if state_raw.startswith("(") and state_raw.endswith(")") else None
        raw_dates = {"approval": None, "start": None, "actual": None,
                     "original": original_date[0], "revised": None}
        raw_costs = {"original": original_cost[0], "revised": None,
                     "expenditure": spent[0]}
        approval = start = revised = actual = revised_cost = progress = None
        original = month_value(original_date[0])
        sector_words = _tokens(words, 15, 105, top, 3)
    else:
        approval_tokens = _tokens(words, *layout['approval'], top, 3)
        completion_tokens = _tokens(words, *layout['completion'], top, 28)
        cost_tokens = _tokens(words, *layout['cost'], top, 28)
        spent = _tokens(words, *layout['spent'], top, 3)
        pct = _tokens(words, *layout['pct'], top, 3)
        if list(map(len, (approval_tokens, completion_tokens, cost_tokens, spent, pct))) != [1, 3, 3, 1, 1]:
            raise ValueError(f"ongoing value columns: {approval_tokens}, {completion_tokens}, {cost_tokens}, {spent}, {pct}")
        approval = month_value(approval_tokens[0])
        start = actual = None  # This layout does not print a start or actual date.
        original = month_value(completion_tokens[0])
        revised = month_value(completion_tokens[1])
        progress = valid_percentage(pct[0])
        revised_cost = parse_number(cost_tokens[1])
        raw_dates = {"approval": approval_tokens[0], "start": None, "actual": None,
                     "original": completion_tokens[0], "revised": completion_tokens[1],
                     "anticipated": completion_tokens[2]}
        raw_costs = {"original": cost_tokens[0], "revised": cost_tokens[1],
                     "anticipated": cost_tokens[2], "expenditure": spent[0]}
        original_cost = cost_tokens[:1]
        left_words = [w for w in words if top - 2 <= w['top'] < end]
        state_words = [w for w in _ordered(left_words) if 15 <= w['x0'] < 68]
        sector_words = [w for w in _ordered(left_words)
                        if 68 <= w['x0'] < layout['name'][0] - 20]
        state = ' '.join(w['text'] for w in state_words) or None
    original_cost_value = parse_number(original_cost[0])
    spent_value = parse_number(spent[0])
    if original_cost_value is None or spent_value is None:
        raise ValueError("unparseable required printed cost/expenditure")
    sector = " ".join(sector_words) if completed else " ".join(w['text'] for w in sector_words)
    sector = sector or None
    return {
        "project_id": match.group(1), "project_name": name, "ministry": None,
        "agency": agency, "sector": sector, "state": state,
        "approval_date": approval, "start_date": start,
        "original_completion_date": original, "revised_completion_date": revised,
        "actual_completion_date": actual, "original_cost_crore": original_cost_value,
        "revised_cost_crore": revised_cost, "cumulative_expenditure_crore": spent_value,
        "physical_progress_pct": progress, "report_month": month,
        "source_file": path.name, "source_page": page_number,
        "raw_date_values": json.dumps(raw_dates), "raw_cost_values": json.dumps(raw_costs),
    }


def parse_legacy_report(path: Path):
    ongoing, completed, failures = [], [], []
    serials = {"ongoing": [], "completed": []}
    section_pages = Counter()
    with pdfplumber.open(path) as pdf:
        # Cover is blank in these PDFs. The text contents/page header prints the month.
        month = report_month(pdf.pages[1].extract_text() or "")
        for page_number, page in enumerate(pdf.pages, 1):
            header = (page.crop((0, 25, page.width, 135)).extract_text() or "")
            kind = ("ongoing" if re.search(r"Table:-7\. Project List: Ongoing Projects as of", header) else
                    "completed" if re.search(r"Table:-3\. Project List: Completed during", header) else None)
            if kind is None:
                continue
            if report_month(header) != month:
                raise RuntimeError(f"{path.name} page {page_number}: report month mismatch")
            section_pages[kind] += 1
            all_words = page.extract_words()
            headers = [w for w in all_words if 70 <= w['top'] <= 84]
            def header_x(label):
                found = [w['x0'] for w in headers if w['text'] == label]
                if len(found) != 1:
                    raise RuntimeError(f"{path.name} page {page_number}: ambiguous {label} header")
                return found[0]
            sl = header_x('Sl' if kind == 'ongoing' else 'Sl.')
            cost = header_x('Cost' if kind == 'ongoing' else 'Original')
            spent_x = header_x('Cumulative')
            if kind == 'ongoing':
                dates = sorted(w['x0'] for w in headers if w['text'] == 'Date')
                if len(dates) != 2:
                    raise RuntimeError(f"{path.name} page {page_number}: ambiguous date headers")
                approval_x, completion_x = dates
                pct_x = header_x('Physical')
                layout = {'name':(sl+16,approval_x-15), 'approval':(approval_x-25,completion_x-15),
                          'completion':(completion_x-15,cost-15), 'cost':(cost-15,spent_x-15),
                          'spent':(spent_x-15,pct_x-15), 'pct':(pct_x-15,page.width)}
            else:
                date_x = header_x('Date')
                layout = {'name':(sl+16,cost-15), 'cost':(cost-15,date_x-15),
                          'completion':(date_x-15,spent_x-15), 'spent':(spent_x-15,page.width)}
            words = [w for w in all_words if 120 <= w["top"] < page.height - 25]
            low, high = sl + 4, sl + 22
            anchors = sorted((w for w in words if low <= w["x0"] < high and w["text"].isdigit()
                              and 1 <= int(w["text"]) <= 10000), key=lambda w:w["top"])
            for index, anchor in enumerate(anchors):
                serials[kind].append(int(anchor["text"]))
                end = anchors[index + 1]["top"] - 1 if index + 1 < len(anchors) else page.height - 25
                try:
                    record = _row(words, anchor, end, kind, month, path, page_number, layout)
                    (ongoing if kind == "ongoing" else completed).append(record)
                except ValueError as exc:
                    failures.append({"source_file": path.name, "report_month": month, "section": kind,
                                     "page": page_number, "serial": anchor["text"], "reason": str(exc),
                                     "raw_excerpt": " ".join(w["text"] for w in words
                                                              if anchor["top"] - 2 <= w["top"] < end)[:300]})
    if not serials["ongoing"] or not serials["completed"]:
        raise RuntimeError(f"{path.name}: missing legacy project table")
    for kind, values in serials.items():
        if values != list(range(1, len(values) + 1)):
            first = next(((i, v) for i, v in enumerate(values, 1) if i != v), None)
            raise RuntimeError(f"{path.name}: {kind} serial coverage mismatch: count={len(values)}, first={first}, last={values[-5:]}")
    ongoing, od, oc = deduplicate(ongoing)
    completed, cd, cc = deduplicate(completed)
    failures.extend(oc + cc)
    audit = {
        "source_file": path.name, "report_month": month,
        "printed_serials": {k:len(v) for k,v in serials.items()},
        "section_pages": dict(section_pages), "parsed_ongoing_rows": len(ongoing),
        "parsed_completed_rows": len(completed), "rejected_rows": len(failures),
        "duplicate_rows_removed_within_report": od + cd,
        "missing_critical_dates": {
            "ongoing": sum(not r["start_date"] or not r["original_completion_date"] for r in ongoing),
            "completed": sum(not r["start_date"] or not r["original_completion_date"]
                             or not r["actual_completion_date"] for r in completed)},
        "completed_without_explicit_actual_date": len(completed),
        "failures": failures,
    }
    return ongoing, completed, audit
