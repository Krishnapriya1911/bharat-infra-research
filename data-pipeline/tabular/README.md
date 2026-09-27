# EXP-TAB-01: PAIMANA project extraction

Install `requirements.txt` from this directory, then run from the repository root:

```bash
python data-pipeline/tabular/prepare_projects.py
```

The parser discovers every PDF in `datasets/raw/mospi/reports/`, validates the month from each PDF, and writes `mospi_monthly_snapshots.csv` and `mospi_multimonth_audit.json` under `datasets/processed/`. Each report is parsed independently. Rows are ordered by report month and project ID, with `observation_status` distinguishing ongoing from completed. The same ID in different months is retained as separate observations. The existing August-only CSVs are left as historical baseline artifacts.

Extraction uses selectable PDF text and word positions; no OCR is needed. The structured audit includes per-report counts, cross-month ID continuity, and failures with source file, month, section, page, printed serial, candidate code, reason, and raw excerpt. Multi-state entries are rejected conservatively when their state text can overlap the name column. Ministry and sector headings are not assigned to projects because grouping across page breaks and subtotals has not been validated.

The report dates have **month precision** (`MM/YYYY`). The CSV stores `YYYY-MM` and contains no early-delay label. Do not invent the first or last day of a month. The June 2026 completed table omits an actual-completion column; `actual_completion_date` remains blank for those observations. Completed tables supply no physical-progress column. A printed zero cost stays zero, with the original token in `raw_cost_values`. Ongoing rows are report snapshots without outcome labels.

**Leakage boundary:** `actual_completion_date`, `revised_completion_date`, and all post-outcome snapshot values are source/audit fields, not features for an early-delay model. The April–August panel is an initial history, potentially too short for temporal modeling. It does not by itself define a defensible prediction cutoff or exact day-based outcome labels. Do not train EXP-TAB-01 from these exports yet.
