# EXP-TAB-01: PAIMANA project extraction

Install `requirements.txt` from this directory, then run from the repository root:

```bash
python data-pipeline/tabular/prepare_projects.py
```

The parser reads only `datasets/raw/mospi/reports/FlashReport_August_2026.pdf` and writes two project CSVs plus `mospi_parsing_failures.json` under `datasets/processed/`. It uses selectable PDF text and word positions; no OCR is needed. The audit log includes section, PDF page, printed serial, candidate code, reason, and a raw excerpt for each rejected row. Multi-state entries are rejected conservatively when their state text can overlap the name column. Ministry and sector headings are not assigned to projects because grouping across page breaks and subtotals has not been validated.

The report dates have **month precision** (`MM/YYYY`). The CSV stores `YYYY-MM`, and the completed-project day-based labels remain blank. Do not invent the first or last day of a month to fill them. The completed report supplies no physical-progress column; its value remains blank. A printed zero cost stays zero, with the original token in `raw_cost_values`. Ongoing rows are report snapshots without outcome labels.

**Leakage boundary:** `actual_completion_date`, `revised_completion_date`, and all post-outcome snapshot values are source/audit fields, not features for an early-delay model. The current single monthly snapshot does not define a defensible prediction cutoff or provide exact day-based delay labels. Do not train EXP-TAB-01 from these exports yet.
