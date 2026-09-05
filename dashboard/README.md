# Tableau Dashboard

Connect Tableau (Public or Desktop) directly to `data/processed/emissions_clean.csv`.

Build 4 sheets, then combine into one dashboard (`carbon_dashboard.twbx`):

1. **Emissions trend over time** — line chart. `SUM(total_direct_emissions_mtco2e)` by
   `reporting_year`, colored by `sector`. Add a sector/facility filter.
2. **Sector/facility comparison** — horizontal bar chart. `SUM(total_direct_emissions_mtco2e)`
   by `facility_name`, sorted descending, filtered to top N (parameter-driven if you want
   it adjustable on the dashboard).
3. **Scope breakdown** — since every row is already Scope 1, this sheet is mainly a
   composition view: CO2 vs CH4 vs N2O within `total_direct_emissions_mtco2e`
   (stacked bar or treemap using `co2_mtco2e`, `ch4_mtco2e`, `n2o_mtco2e`). Add a text
   box on the dashboard: *"All facility data reported here is Scope 1 (direct) per EPA
   GHGRP. Scope 2 estimated illustratively for a small sample using eGRID regional
   factors — see README. Scope 3 not estimated — GHGRP contains no supply-chain data."*
4. **Geographic view** — map using `latitude` / `longitude`, sized/colored by
   `total_direct_emissions_mtco2e`. Use `flag_outlier` as a filter/highlight so reviewers
   can toggle outliers on or off.

Once built, publish to Tableau Public, grab the share link, and drop it into the main
README's Dashboard section + your resume bullet.

This repo does not ship a pre-built `.twbx` — Tableau workbooks are binary and are best
built directly against your real (not synthetic) processed CSV once you've swapped in
the actual EPA GHGRP download.
