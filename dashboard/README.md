# Corporate Carbon Emissions Analytics Dashboard

Facility-level greenhouse gas emissions analysis of the U.S. Power Plants sector using real EPA Greenhouse Gas Reporting Program (GHGRP) data from 2019–2023.

The project combines a Python-based ETL and data-quality pipeline with an interactive Tableau dashboard to analyze direct emissions trends, identify high-emitting facilities, examine greenhouse gas composition, and visualize the geographic distribution of reported emissions.

---

## Overview

Corporate sustainability and ESG reporting increasingly requires organizations to understand where emissions originate, how they change over time, and how reported emissions map to established GHG accounting boundaries.

This project analyzes facility-level emissions reported to the **U.S. Environmental Protection Agency (EPA)** through the **Greenhouse Gas Reporting Program (GHGRP)**.

The analysis focuses on the **Power Plants sector** and answers four core questions:

- How have reported direct emissions changed from 2019–2023?
- Which facilities are the largest direct emitters?
- What is the composition of reported emissions across CO₂, CH₄, and N₂O?
- Where are major emitting facilities geographically concentrated?

The project also explicitly addresses the boundary between **Scope 1, Scope 2, and Scope 3 emissions** rather than assigning unsupported scope classifications to data that does not contain the required information.

---

## Key Results

| Metric | Result |
|---|---:|
| **Analysis Period** | 2019–2023 |
| **Facility-Year Records** | 6,701 |
| **Unique Facilities** | 1,419 |
| **2019 Direct Emissions** | 1.69B mtCO₂e |
| **2023 Direct Emissions** | 1.49B mtCO₂e |
| **Overall Change** | **−11.7%** |
| **Outlier Records Flagged** | 171 |
| **Missing/Non-positive Emissions Records** | 50 |
| **Duplicate Facility-Year Records** | 0 |

Reported direct emissions declined by approximately **11.7%** between 2019 and 2023, falling from **1.69 billion mtCO₂e to 1.49 billion mtCO₂e**.

The time series shows a decline in 2020, a partial rebound in 2021, followed by continued declines through 2022 and 2023.

---

## Data Source

Data is sourced from the **U.S. Environmental Protection Agency (EPA) Greenhouse Gas Reporting Program (GHGRP)** yearly Data Summary Spreadsheets.

**Source:** EPA GHGRP Data Sets  
https://www.epa.gov/ghgreporting/data-sets

### Dataset Scope

- **Sector:** Power Plants
- **Years:** 2019, 2020, 2021, 2022, 2023
- **Source sheet:** `Direct Point Emitters`
- **Final processed records:** 6,701 facility-year observations
- **Unique facilities:** 1,419

The five yearly EPA files were combined and filtered into a single analysis-ready dataset:

```text
data/processed/emissions_clean.csv