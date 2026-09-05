"""
scope_classifier.py — GHG Protocol scope labeling

GHGRP is a Scope 1 (direct emissions) dataset by design — every row here is
already Scope 1 by definition of what EPA collects. This module:

  1. Labels every row explicitly as "Scope 1" (no ambiguity, no estimation).
  2. Adds an ILLUSTRATIVE Scope 2 sub-analysis for a small sample of
     facilities, using published eGRID regional grid emission factors, to
     demonstrate the Scope 1 vs Scope 2 boundary concept — clearly labeled
     as an estimate, not derived from anything GHGRP reports.
  3. Explicitly labels Scope 3 as out of scope for this dataset (no supply
     chain / value chain data exists in GHGRP), rather than fabricating a
     number.

This is option (a) from the project spec: the "simplest, most honest"
approach. Nothing here invents Scope 2 or Scope 3 totals for the full
dataset — only a small, clearly-flagged illustrative subset.

eGRID regional emission factors (lb CO2e/MWh, approximate, illustrative
values based on EPA eGRID published subregion output rates — replace with
the exact eGRID year/subregion values you cite in your README if you use
this for real reporting). Source: EPA eGRID
https://www.epa.gov/egrid/download-data
"""

from __future__ import annotations

import pandas as pd

# Illustrative eGRID subregion CO2e output emission rates (lb/MWh).
# These are representative values for demonstration — for a real
# submission, pull the exact year's eGRID subregion table and cite it.
EGRID_FACTORS_LB_PER_MWH = {
    "RFCW": 1180,  # RFC West (e.g., parts of OH, PA, WV)
    "SRMV": 950,   # SERC Mississippi Valley (e.g., LA, AR, MS)
    "CAMX": 560,   # WECC California
    "ERCT": 830,   # ERCOT (Texas)
    "NYUP": 380,   # NYISO Upstate
    "AZNM": 900,   # WECC Southwest
    "default": 850,  # fallback national-average-ish factor
}

LB_TO_METRIC_TON = 1 / 2204.62


def add_scope_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Attach ghg_scope label to every row. All GHGRP rows are Scope 1."""
    df = df.copy()
    df["ghg_scope"] = "Scope 1 (direct, reported to EPA GHGRP)"
    df["scope_2_estimate_mtco2e"] = pd.NA  # populated only for illustrative subset
    df["scope_3_note"] = "Out of scope for this dataset — no supply-chain data in GHGRP"
    return df


def estimate_scope2_illustrative(
    facility_electricity_mwh: dict[str, float],
    egrid_subregion: dict[str, str],
) -> pd.DataFrame:
    """
    Illustrative Scope 2 estimate for a SMALL SAMPLE of facilities where
    electricity consumption (MWh) is known or assumed for demonstration.

    This is NOT derived from GHGRP data — GHGRP does not report facility
    electricity purchases. It exists to show the Scope 1 vs Scope 2
    boundary using real eGRID factors, on a handful of sample facilities,
    not to estimate Scope 2 for the whole dataset.

    Parameters
    ----------
    facility_electricity_mwh : dict
        {facility_name: assumed/estimated annual electricity purchase in MWh}
    egrid_subregion : dict
        {facility_name: eGRID subregion code, e.g. "CAMX"}

    Returns
    -------
    DataFrame with columns: facility_name, egrid_subregion,
    electricity_mwh, emission_factor_lb_per_mwh, scope_2_estimate_mtco2e
    """
    rows = []
    for facility, mwh in facility_electricity_mwh.items():
        subregion = egrid_subregion.get(facility, "default")
        factor = EGRID_FACTORS_LB_PER_MWH.get(subregion, EGRID_FACTORS_LB_PER_MWH["default"])
        estimate_mtco2e = mwh * factor * LB_TO_METRIC_TON
        rows.append(
            {
                "facility_name": facility,
                "egrid_subregion": subregion,
                "electricity_mwh": mwh,
                "emission_factor_lb_per_mwh": factor,
                "scope_2_estimate_mtco2e": round(estimate_mtco2e, 1),
            }
        )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    # Small demo of the illustrative Scope 2 sub-analysis, matching the
    # spec's "2-3 sample facilities" suggestion.
    sample_electricity = {
        "Sample Facility A": 45000,
        "Sample Facility B": 78000,
        "Sample Facility C": 12000,
    }
    sample_subregion = {
        "Sample Facility A": "CAMX",
        "Sample Facility B": "ERCT",
        "Sample Facility C": "NYUP",
    }
    demo = estimate_scope2_illustrative(sample_electricity, sample_subregion)
    print(demo.to_string(index=False))
