"""
etl.py — EPA GHGRP facility-level emissions ETL pipeline

Pipeline stages:
  1. load       — read raw CSV(s) from data/raw/, concatenate if multiple
  2. clean       — standardize columns, coerce numerics, drop/flag bad rows
  3. validate    — dedupe check, outlier flagging (sector z-score)
  4. enrich      — call scope_classifier to attach Scope 1 label + optional
                   illustrative Scope 2 estimate
  5. export      — write data/processed/emissions_clean.csv

Usage:
    python src/etl.py --input data/raw/*.csv --output data/processed/emissions_clean.csv
"""

from __future__ import annotations

import argparse
import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from scope_classifier import add_scope_columns

# ---------------------------------------------------------------------------
# Column standardization
# ---------------------------------------------------------------------------

# Map common raw GHGRP / FLIGHT export headers -> our canonical snake_case
# names. FLIGHT and Envirofacts exports don't use identical headers across
# tools/years, so this map is intentionally permissive (many raw variants ->
# one canonical name). Extend this if your download uses different labels.
COLUMN_ALIASES = {
    "facility name": "facility_name",
    "facility id": "facility_id",
    "ghgrp id": "facility_id",
    "city": "city",
    "state": "state",
    "latitude": "latitude",
    "longitude": "longitude",
    "primary naics code": "naics_code",
    "naics code": "naics_code",
    "industry type (subparts)": "subpart",
    "industry type (sectors)": "sector",
    "reporting year": "reporting_year",
    "year": "reporting_year",
    "total reported direct emissions": "total_direct_emissions_mtco2e",
    "co2 emissions": "co2_mtco2e",
    "methane (ch4) emissions": "ch4_mtco2e",
    "nitrous oxide (n2o) emissions": "n2o_mtco2e",
    "parent companies": "parent_company",
    "parent company": "parent_company",
}


def _snake_case(col: str) -> str:
    col = col.strip().lower()
    col = COLUMN_ALIASES.get(col, col)
    col = re.sub(r"[^\w\s]", "", col)
    col = re.sub(r"\s+", "_", col)
    return col


def load_raw(input_glob: str) -> pd.DataFrame:
    """Load and concatenate all CSVs matching input_glob."""
    paths = sorted(glob.glob(input_glob))
    if not paths:
        raise FileNotFoundError(
            f"No files matched '{input_glob}'. Place your EPA GHGRP CSV(s) "
            f"in data/raw/ first."
        )
    frames = []
    for p in paths:
        df = pd.read_csv(p, low_memory=False)
        df["__source_file"] = Path(p).name
        frames.append(df)
        print(f"  loaded {p}: {len(df):,} rows, {len(df.columns)} cols")
    combined = pd.concat(frames, ignore_index=True)
    print(f"  combined: {len(combined):,} rows from {len(paths)} file(s)")
    return combined


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize columns, coerce types, drop/flag invalid rows."""
    df = df.copy()
    df.columns = [_snake_case(c) for c in df.columns]

    # Some exports use a slightly different emissions column name;
    # normalize to a single working column.
    emissions_col_candidates = [
        c for c in df.columns if "direct_emission" in c or c == "total_emissions"
    ]
    if "total_direct_emissions_mtco2e" not in df.columns and emissions_col_candidates:
        df = df.rename(columns={emissions_col_candidates[0]: "total_direct_emissions_mtco2e"})

    required = ["facility_id", "total_direct_emissions_mtco2e"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(
            f"Expected column(s) {missing} not found after standardization. "
            f"Available columns: {list(df.columns)}. Update COLUMN_ALIASES "
            f"in etl.py to match your raw export's headers."
        )

    # Coerce numerics, invalid parses -> NaN
    numeric_cols = [
        "total_direct_emissions_mtco2e",
        "co2_mtco2e",
        "ch4_mtco2e",
        "n2o_mtco2e",
        "latitude",
        "longitude",
        "reporting_year",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    n_before = len(df)

    # Flag (don't silently drop) rows with null facility_id
    df["flag_null_facility_id"] = df["facility_id"].isna()

    # Flag non-positive reported emissions — these are almost always data
    # entry issues or facilities reporting zero for a given year, not
    # meaningful zero-emission facilities at this scale of reporting.
    df["flag_nonpositive_emissions"] = (
        df["total_direct_emissions_mtco2e"].isna()
        | (df["total_direct_emissions_mtco2e"] <= 0)
    )

    # Actually drop only the rows that fail the hard requirement
    # (no facility_id at all — can't attribute the record to anything).
    df_clean = df[~df["flag_null_facility_id"]].copy()

    n_dropped = n_before - len(df_clean)
    n_flagged_emissions = df_clean["flag_nonpositive_emissions"].sum()
    print(
        f"  clean(): dropped {n_dropped:,} rows with null facility_id; "
        f"flagged {n_flagged_emissions:,} rows with non-positive/missing emissions "
        f"(kept, not dropped)"
    )

    return df_clean


def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Dedupe check + sector-level outlier flagging (z-score > 3)."""
    df = df.copy()

    key_cols = [c for c in ["facility_id", "reporting_year"] if c in df.columns]
    if len(key_cols) == 2:
        dupes = df.duplicated(subset=key_cols, keep=False)
        n_dupes = dupes.sum()
        df["flag_duplicate_facility_year"] = dupes
        if n_dupes:
            print(f"  validate(): found {n_dupes:,} duplicate facility-year rows (flagged, not dropped)")
        else:
            print("  validate(): no duplicate facility-year rows found")
    else:
        df["flag_duplicate_facility_year"] = False

    # Outlier flagging: z-score within sector (fallback: whole dataset)
    group_col = "sector" if "sector" in df.columns else None
    valid_emissions = df["total_direct_emissions_mtco2e"].where(
        ~df["flag_nonpositive_emissions"]
    )

    if group_col:
        grp_mean = df.groupby(group_col)["total_direct_emissions_mtco2e"].transform("mean")
        grp_std = df.groupby(group_col)["total_direct_emissions_mtco2e"].transform("std")
    else:
        grp_mean = valid_emissions.mean()
        grp_std = valid_emissions.std()

    z = (df["total_direct_emissions_mtco2e"] - grp_mean) / grp_std.replace(0, np.nan)
    df["emissions_zscore"] = z
    df["flag_outlier"] = z.abs() > 3

    n_outliers = df["flag_outlier"].sum()
    print(f"  validate(): flagged {n_outliers:,} outlier rows (|z| > 3 within sector) — kept, not dropped")

    return df


def run_pipeline(input_glob: str, output_path: str) -> pd.DataFrame:
    print(f"[1/5] Loading raw data from '{input_glob}'...")
    df = load_raw(input_glob)

    print("[2/5] Cleaning...")
    df = clean(df)

    print("[3/5] Validating...")
    df = validate(df)

    print("[4/5] Classifying by GHG Protocol scope...")
    df = add_scope_columns(df)

    print("[5/5] Exporting...")
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"  wrote {len(df):,} rows -> {out}")

    return df


def main():
    parser = argparse.ArgumentParser(description="EPA GHGRP emissions ETL pipeline")
    parser.add_argument(
        "--input",
        default="data/raw/*.csv",
        help="Glob pattern for raw CSV(s) (default: data/raw/*.csv)",
    )
    parser.add_argument(
        "--output",
        default="data/processed/emissions_clean.csv",
        help="Output path for cleaned CSV (default: data/processed/emissions_clean.csv)",
    )
    args = parser.parse_args()

    try:
        run_pipeline(args.input, args.output)
    except (FileNotFoundError, KeyError) as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
