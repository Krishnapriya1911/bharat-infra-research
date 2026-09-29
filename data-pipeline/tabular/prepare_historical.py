"""Extend the validated April–August 2026 panel with twelve 2025–26 reports.

Only PDFs in datasets/raw/mospi/paimana are parsed. Existing 2026 records
are copied from the validated panel, not regenerated from other raw PDFs.
"""

import argparse
import csv
import json
from pathlib import Path

from .legacy_2025 import parse_legacy_report
from .prepare_projects import (
    OUTPUT, PANEL_COLUMNS, ROOT, continuity, discover_reports, parse_report, write_csv,
)


REPORTS = ROOT / "datasets/raw/mospi/paimana"
EXPECTED = {f"{year}-{month:02d}" for year, months in ((2025, range(4, 13)),
                                                      (2026, range(1, 4))) for month in months}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports-dir", type=Path, default=REPORTS)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    paths = discover_reports(args.reports_dir)
    expected_names = {f"PAIMANA_FlashReport_{m}.pdf" for m in EXPECTED}
    if {p.name for p in paths} != expected_names or len(paths) != 12:
        raise RuntimeError("expected exactly twelve unique monthly Flash Reports; duplicates/quarterly inputs are forbidden")
    input_panel = args.output_dir / "mospi_monthly_snapshots.csv"
    with input_panel.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != PANEL_COLUMNS:
            raise RuntimeError("existing panel schema differs from frozen 21 columns")
        existing_rows = list(reader)
    existing_months = {r['report_month'] for r in existing_rows}
    if existing_months != {f"2026-{m:02d}" for m in range(4, 9)}:
        raise RuntimeError(f"expected validated April–August 2026 baseline, got {sorted(existing_months)}")
    prior_audit = json.loads((args.output_dir / "mospi_multimonth_audit.json").read_text())
    rows, audits, failures = [], [], []
    for path in paths:
        month = path.stem[-7:]
        if month not in EXPECTED:
            raise RuntimeError(f"unexpected report filename month: {path}")
        ongoing, completed, audit = (parse_legacy_report(path) if month <= "2025-06"
                                     else parse_report(path))
        if audit['report_month'] != month:
            raise RuntimeError(f"{path.name}: filename/report month mismatch")
        rows.extend({**r, 'observation_status': 'ongoing'} for r in ongoing)
        rows.extend({**r, 'observation_status': 'completed'} for r in completed)
        failures.extend(audit.pop('failures'))
        audits.append(audit)
        print(f"{month}: {len(ongoing)} ongoing, {len(completed)} completed, "
              f"{audit['rejected_rows']} rejected", flush=True)
    if {a['report_month'] for a in audits} != EXPECTED:
        raise RuntimeError("missing or repeated source report month")
    rows += existing_rows
    rows.sort(key=lambda r: (r['report_month'], r['project_id'], r['observation_status']))
    combined_audits = sorted(audits + prior_audit['per_report'], key=lambda a:a['report_month'])
    combined_failures = failures + prior_audit['failures']
    audit = {
        'per_report': combined_audits,
        'continuity': continuity(rows),
        'failures': combined_failures,
        'provenance_note': (
            'Only twelve PDFs from datasets/raw/mospi/paimana were parsed this run. '
            'April–August 2026 rows/audits were retained from the previously validated panel. '
            'April–June 2025 use the older OCMS layout; their completed table has no explicit actual date. '
            'Rejected rows are not guessed or silently repaired.'),
    }
    write_csv(input_panel, rows, PANEL_COLUMNS)
    (args.output_dir / 'mospi_multimonth_audit.json').write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({'historical_months': sorted(EXPECTED),
                      'monthly_observations': len(rows), 'continuity': audit['continuity'],
                      'historical_rejected': len(failures)}, indent=2))


if __name__ == '__main__':
    main()
