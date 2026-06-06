# Architecture

## Overview
Future Fit is a lightweight analytics application built around one cleaned primary dataset and one LinkedIn validation sample. The project is organized as a pipeline:

1. raw data ingestion
2. deterministic cleaning and long-format transformation
3. exploratory analysis and hypothesis testing
4. chart export and visual storytelling
5. LLM-powered skill gap advice
6. Streamlit dashboard packaging

## System Flow
```text
Kaggle raw CSVs
  -> notebooks/01_data_collection.ipynb
  -> notebooks/02_data_cleaning.ipynb
  -> data/clean/primary_skills_long.csv
  -> notebooks/03_eda_analysis.ipynb
  -> notebooks/04_visualization_report.ipynb
  -> assets/charts/*.png
  -> src/skill_gap_advisor.py
  -> app.py
```

## Folder Responsibilities
- `notebooks/` holds the phase notebooks used for exploration and reproducibility.
- `src/` holds reusable logic so the notebooks and Streamlit app stay thin.
- `data/raw/` stores the original Kaggle downloads.
- `data/clean/` stores the analysis-ready outputs used by EDA, the app, and the advisor.
- `assets/charts/` stores the exported charts used in the README and portfolio.
- `dashboards/` is reserved for the manual Power BI deliverable.
- `Important Documents of the Project/` stores the phase plan and problem statement history.

## Runtime Notes
- The app loads the cleaned primary CSV and the LinkedIn validation CSV.
- The data is analyzed at annual granularity because the primary source exposes `posted_year` rather than a monthly posting date.
- The Skill Gap Advisor uses `GROQ_API_KEY` from Streamlit secrets, with an offline preview fallback for local testing.
- The app theme is centralized in `app.py`, so the site name and color palette can be changed without touching the analysis pipeline.

## Current Brand Layer
- Site name: `Future Fit`
- Tagline: `AI-Powered Skill Trend Analysis`
- Palette: dark purple background with gold accent
- Hero treatment: branded mark plus compact navigation row

## Deployment Notes
- Local Streamlit validation is complete.
- Streamlit Cloud deployment is still a separate publish step.
- A Power BI-compatible CSV export is included for the manual BI deliverable.

