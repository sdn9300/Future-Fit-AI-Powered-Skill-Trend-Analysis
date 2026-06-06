# Problem Statement

## Background

The AI and Data Science job market is evolving rapidly. Hiring datasets contain many overlapping and noisy skill mentions, and the most useful trends are not always visible without careful cleaning and validation.

## Objective

Build a reproducible analysis workflow that:
- ingests the two user-provided datasets in `data/raw/`
- validates dataset schemas and row counts
- cleans and transforms skill text into a long-format analytics table
- analyzes skill demand trends, co-occurrence, and experience-level differences
- validates insights with a LinkedIn sample
- packages findings into portfolio-ready documentation and a local Streamlit dashboard scaffold

## Scope

- Use only the supplied datasets in `data/raw/`: `ai_jobs.csv` and `linkedin_job_postings.csv`
- Keep only original source files in `data/raw/`; move notebook-derived outputs to `data/clean/`
- Do not add extra Kaggle or external datasets
- Keep raw data under `data/raw/` and cleaned outputs under `data/clean/`
- Preserve a reproduction-first structure with notebooks and reusable source code
- Do not push code changes to GitHub without explicit user approval

## Success Criteria

- `docs/problem_statement.md` exists and describes the project scope
- `README.md` documents local setup and current deployment status
- `docs/linkedin_post_draft.md` captures a portfolio-ready announcement draft
- Only the two approved raw datasets are present in `data/raw/`
- The repository structure is clear for a portfolio reviewer
