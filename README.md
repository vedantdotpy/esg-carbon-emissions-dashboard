# Corporate Carbon Emissions Analytics Dashboard

## Overview
Facility-level analysis of U.S. industrial greenhouse gas emissions, built on EPA's
Greenhouse Gas Reporting Program (GHGRP) data. The project answers: *which facilities
and sectors are the largest direct emitters, how has their reported output trended over
2019–2023, and how do those Scope 1 numbers relate to the broader GHG Protocol scope
framework used in corporate ESG reporting?*

> **Status: scaffold + validated pipeline.** This repo ships with a synthetic
> GHGRP-shaped sample dataset (`data/raw/ghgrp_sample_2019_2023.csv`) so the ETL
> pipeline, scope classifier, and dashboard structure are all proven end-to-end.
> Swap in your real EPA FLIGHT export to `data/raw/` and rerun `src/etl.py` — the
> numbers below (marked *sample data*) will be replaced by real findings once you do.

## Data Source
EPA Greenhouse Gas Reporting Program (GHGRP), via the [FLIGHT tool](https://ghgdata.epa.gov/ghgp/main.do).
Recommended scope: one sector (e.g. Power Plants, Petroleum & Natural Gas Systems, or
Chemicals) × 2019–2023, to keep the dataset to a manageable 500–3,000 facility-year rows.

*Sample data currently in this repo:* 220 synthetic facilities × 5 years ≈ 1,100
facility-year rows across three illustrative sectors (Power Plants, Petroleum & Natural
Gas Systems, Chemicals).

## Methodology

**ETL (`src/etl.py`)**
1. Load raw CSV(s) from `data/raw/`, concatenate if multiple sector/year pulls.
2. Standardize column names to snake_case via an alias map (raw GHGRP/FLIGHT exports
   don't use identical headers across tools or years).
3. Coerce emissions and coordinate columns to numeric; invalid parses become `NaN`
   rather than silently breaking the pipeline.
4. Drop rows with no `facility_id` (can't attribute the record to anything). Flag —
   but keep — rows with null or non-positive reported emissions, duplicate
   facility-year rows, and statistical outliers (`|z| > 3` within sector). Flagging
   instead of dropping keeps the audit trail visible instead of hiding it.

**Scope classification (`src/scope_classifier.py`)**
GHGRP is a Scope 1 (direct emissions) dataset by design — it does not report facility
electricity purchases or supply-chain data. Rather than fabricate Scope 2/3 numbers the
data doesn't contain, this project:
- Labels every row explicitly **Scope 1** (reported directly to EPA).
- Adds a small, clearly-flagged **illustrative Scope 2 estimate** for 2–3 sample
  facilities, using published EPA eGRID regional grid emission factors against assumed
  electricity consumption — to demonstrate the Scope 1/Scope 2 boundary, not to estimate
  Scope 2 for the full dataset.
- Labels **Scope 3 explicitly out of scope** for this dataset, since GHGRP has no
  supply-chain / value-chain emissions data. This is a boundary limitation of the source
  data, not something a bigger pipeline can paper over.

This is the more rigorous of the two options considered (vs. finding a Kaggle mirror
with pre-labeled CDP Scope 1/2/3 disclosures), because every number in the dashboard can
be traced back to exactly how it was derived.

## Key Insights
*(from the synthetic sample data shipped in this repo — replace with your real-data
findings once you swap in an actual EPA download)*

- Total reported direct emissions across the sample fell **~2.5%** from 2019 to 2023,
  with a peak in 2021 before declining in 2022–2023.
- **Chemicals** was the largest-emitting sector in the sample, followed by
  Petroleum & Natural Gas Systems and Power Plants.
- 20 of 1,101 facility-year records (~1.8%) were flagged as statistical outliers
  (`|z| > 3` within their sector) — kept in the dataset but visibly tagged, rather than
  silently dropped, so a reviewer can judge for themselves.
- 8 duplicate facility-year rows were detected and flagged during validation — a
  reminder that even structured regulatory exports need a dedupe check before analysis.

## Dashboard
[Tableau Public link — add once published]

4 views, built directly against `data/processed/emissions_clean.csv`:
1. **Emissions trend over time** — line chart, total reported emissions by year,
   filterable by sector/facility.
2. **Sector/facility comparison** — bar chart ranking top-N emitters in the slice.
3. **Scope breakdown** — Scope 1 (full dataset) vs. illustrative Scope 2 sample, with a
   text box on the dashboard itself noting the eGRID methodology and that Scope 3 is
   out of scope for this dataset.
4. **Geographic view** — map of facility locations sized/colored by emissions volume.

*(screenshot — add once dashboard is built)*

## Tech Stack
Python (pandas, numpy) · Jupyter · Tableau

## Limitations & Next Steps
- **Scope 2** is only estimated illustratively for a small sample; a full Scope 2
  estimate for every facility would require actual electricity purchase data, which
  GHGRP does not report.
- **Scope 3** estimation would require supply-chain data not available in GHGRP; a
  natural extension would be layering in CDP supply-chain disclosures for facilities
  whose parent companies report to CDP.
- Outlier flags are statistical (`|z| > 3`), not investigated case-by-case — a next
  iteration could cross-reference flagged facilities against EPA's public enforcement
  or facility-change records to distinguish real anomalies from data entry errors.
- Sample data in this repo is synthetic and exists only to prove the pipeline works;
  it should not be cited as a real emissions finding.
