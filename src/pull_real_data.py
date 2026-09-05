"""
pull_real_data.py — combine EPA GHGRP yearly "Data Summary Spreadsheets"
(ghgp_data_2019.xlsx ... ghgp_data_2023.xlsx) into one filtered CSV ready
for src/etl.py.

These yearly files (downloaded from https://www.epa.gov/ghgreporting/data-sets)
normally contain a sheet called "Direct Emitters" with facility-level data
for that year. This script reads that sheet from each year, tags it with
the year, filters to one sector, and concatenates 2019-2023 into a single
CSV in data/raw/.

Usage:
    python pull_real_data.py --folder "C:/Users/vedan/Downloads/2023_data_summary_spreadsheets" --sector "Power Plants"

If it can't find a sheet called "Direct Emitters", it will print the actual
sheet names in the file so you can tell me what they're called and I'll
adjust the script.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

YEARS = [2019, 2020, 2021, 2022, 2023]
CANDIDATE_SHEET_NAMES = ["Direct Point Emitters", "Direct Emitters", "Direct Emissions", "PART_98_Data"]


def find_sheet(xlsx_path: Path) -> str:
    """Find the right sheet in a yearly GHGRP workbook."""
    xl = pd.ExcelFile(xlsx_path)
    for candidate in CANDIDATE_SHEET_NAMES:
        if candidate in xl.sheet_names:
            return candidate
    print(f"\nCould not auto-find a known sheet name in {xlsx_path.name}.")
    print(f"Sheets available: {xl.sheet_names}")
    print("Tell me these sheet names and I'll update this script.\n")
    sys.exit(1)


def load_year(folder: Path, year: int) -> pd.DataFrame:
    path = folder / f"ghgp_data_{year}.xlsx"
    if not path.exists():
        raise FileNotFoundError(f"Expected {path} — check the filename matches what you downloaded.")

    sheet = find_sheet(path)
    # GHGRP workbooks usually have a few header/title rows before the real
    # header row — skiprows=3 is typical for these files. If your columns
    # look wrong when you check the output, adjust this.
    df = pd.read_excel(path, sheet_name=sheet, skiprows=3)
    df["Reporting Year"] = year
    print(f"  {path.name} [{sheet}]: {len(df):,} rows, {len(df.columns)} cols")
    return df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--folder", required=True, help="Folder containing ghgp_data_2019.xlsx ... ghgp_data_2023.xlsx")
    parser.add_argument("--sector", required=True, help="Sector to filter to, e.g. 'Power Plants'")
    parser.add_argument("--sector-column", default=None, help="Override: exact column name to filter on if auto-detect fails")
    parser.add_argument("--output", default="../data/raw/ghgrp_real_2019_2023.csv")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.exists():
        print(f"Folder not found: {folder}")
        sys.exit(1)

    print(f"Loading years {YEARS} from {folder}...")
    frames = [load_year(folder, yr) for yr in YEARS]
    combined = pd.concat(frames, ignore_index=True)
    print(f"Combined: {len(combined):,} rows across {len(YEARS)} years")

    # Find the sector column
    sector_col = args.sector_column
    if sector_col is None:
        candidates = [c for c in combined.columns if "industry type (sector" in c.lower()]
        if not candidates:
            print("\nCould not auto-find a sector column. Columns available:")
            print(list(combined.columns))
            print("\nRerun with --sector-column \"<exact column name>\"")
            sys.exit(1)
        sector_col = candidates[0]
        print(f"Using sector column: '{sector_col}'")

    filtered = combined[combined[sector_col].astype(str).str.contains(args.sector, case=False, na=False)]
    print(f"Filtered to sector '{args.sector}': {len(filtered):,} rows")

    if len(filtered) == 0:
        print(f"\nNo rows matched sector '{args.sector}'. Unique values in '{sector_col}':")
        print(combined[sector_col].dropna().unique()[:30])
        sys.exit(1)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(out_path, index=False)
    print(f"\nWrote {len(filtered):,} rows -> {out_path}")


if __name__ == "__main__":
    main()