from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
CLEAN_DIR = PROJECT_ROOT / "data" / "clean"

PRIMARY_OUTPUT = CLEAN_DIR / "primary_skills_long.csv"
LINKEDIN_OUTPUT = CLEAN_DIR / "linkedin_validation.csv"


PRIMARY_JOB_TEXT_COLS = [
    "job_title",
    "company_type",
    "industry",
    "country",
    "city",
    "remote_type",
    "experience_level",
    "employment_type",
    "company_size",
]

PRIMARY_SKILL_TEXT_COLS = ["skill", "skill_category", "skill_level"]

LINKEDIN_POSTING_TEXT_COLS = [
    "job_title",
    "company",
    "job_location",
    "search_city",
    "search_country",
    "search_position",
    "job_level",
    "job_type",
]


def _normalize_text(series: pd.Series) -> pd.Series:
    """Lowercase, strip, and preserve missing values."""
    return series.astype("string").str.strip().str.lower()


def _ensure_dirs() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)


def _load_primary_sources() -> tuple[pd.DataFrame, pd.DataFrame]:
    jobs = pd.read_csv(RAW_DIR / "ai_jobs.csv", dtype={"job_id": "string"})
    skills = pd.read_csv(RAW_DIR / "skills_demand.csv", dtype={"job_id": "string"})
    return jobs, skills


def _normalize_primary_job_ids(jobs: pd.DataFrame, skills: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    jobs = jobs.copy()
    skills = skills.copy()

    jobs["job_id"] = jobs["job_id"].astype("string").str.strip()
    skills["job_id"] = skills["job_id"].astype("string").str.strip()

    valid_job_ids = set(jobs["job_id"].dropna())
    prefix_lookup = {job_id[:11]: job_id for job_id in jobs["job_id"].dropna()}

    skills["job_id_normalized"] = skills["job_id"]
    skills["job_match_method"] = "unmatched"

    exact_match = skills["job_id"].isin(valid_job_ids)
    skills.loc[exact_match, "job_match_method"] = "exact"

    prefix_candidates = skills["job_id"].astype("string").str.startswith("E")
    prefix_keys = skills.loc[prefix_candidates, "job_id"].astype("string").str[1:]
    mapped_prefix = prefix_keys.map(prefix_lookup)
    prefix_match = prefix_candidates.copy()
    prefix_match.loc[prefix_candidates] = mapped_prefix.notna()
    skills.loc[prefix_match, "job_id_normalized"] = mapped_prefix.loc[mapped_prefix.notna()]
    skills.loc[prefix_match, "job_match_method"] = "prefix11"

    return jobs, skills


def clean_primary_dataset() -> pd.DataFrame:
    """
    Create the primary analysis-ready long table by joining job metadata
    with the already-exploded skill records.
    """
    jobs, skills = _load_primary_sources()
    jobs, skills = _normalize_primary_job_ids(jobs, skills)

    jobs = jobs.drop_duplicates(subset=["job_id"]).copy()
    skills = skills.drop_duplicates(subset=["job_id", "skill", "skill_category", "skill_level"]).copy()

    for col in PRIMARY_JOB_TEXT_COLS:
        if col in jobs.columns:
            jobs[col] = _normalize_text(jobs[col])

    for col in PRIMARY_SKILL_TEXT_COLS:
        if col in skills.columns:
            skills[col] = _normalize_text(skills[col])

    numeric_cols = [
        "min_experience_years",
        "salary_min_usd",
        "salary_max_usd",
        "posted_year",
    ]
    for col in numeric_cols:
        if col in jobs.columns:
            jobs[col] = pd.to_numeric(jobs[col], errors="coerce").astype("Int64")

    jobs = jobs.rename(columns={"job_id": "job_id_job"})

    merged = skills.merge(
        jobs,
        left_on="job_id_normalized",
        right_on="job_id_job",
        how="left",
        indicator=True,
        suffixes=("_skill", "_job"),
    )

    matched_rows = int((merged["_merge"] == "both").sum())
    total_rows = len(merged)

    merged = merged.drop(columns=["_merge"])
    merged["source"] = "primary"
    merged["job_id"] = merged["job_id_normalized"]
    merged = merged.drop(columns=["job_id_normalized"])

    for col in ["min_experience_years", "salary_min_usd", "salary_max_usd", "posted_year"]:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce").astype("Int64")

    merged.to_csv(PRIMARY_OUTPUT, index=False)

    print(f"[primary] rows in skills source: {len(skills):,}")
    print(f"[primary] rows matched to job metadata: {matched_rows:,} / {total_rows:,}")
    print(f"[primary] output written: {PRIMARY_OUTPUT}")
    print(f"[primary] output shape: {merged.shape}")

    return merged


def _load_linkedin_samples(sample_rows: int = 10000) -> tuple[pd.DataFrame, pd.DataFrame]:
    postings = pd.read_csv(RAW_DIR / "linkedin_job_postings.csv", nrows=sample_rows)
    links = set(postings["job_link"].dropna())
    
    # Read job_skills.csv in chunks to find matching rows for the postings sample
    matched_chunks = []
    for chunk in pd.read_csv(RAW_DIR / "job_skills.csv", chunksize=100000):
        matched_chunk = chunk[chunk["job_link"].isin(links)]
        if not matched_chunk.empty:
            matched_chunks.append(matched_chunk)
            
    if matched_chunks:
        skills = pd.concat(matched_chunks, ignore_index=True)
    else:
        skills = pd.DataFrame(columns=["job_link", "job_skills"])
        
    return postings, skills


def _explode_linkedin_skills(skills: pd.DataFrame) -> pd.DataFrame:
    skills = skills.copy()
    skills["skill_list"] = (
        skills["job_skills"]
        .astype("string")
        .fillna("")
        .str.split(",")
    )
    exploded = skills.explode("skill_list", ignore_index=True)
    exploded["skill"] = exploded["skill_list"].astype("string").str.strip().str.lower()
    exploded = exploded.drop(columns=["skill_list"])
    exploded = exploded[exploded["skill"].notna() & (exploded["skill"] != "")]
    exploded = exploded.drop_duplicates(subset=["job_link", "skill"])
    return exploded


def clean_linkedin_validation_dataset(sample_rows: int = 10000) -> pd.DataFrame:
    """
    Clean a LinkedIn sample into a long skill table for validation.
    """
    postings, skills = _load_linkedin_samples(sample_rows=sample_rows)
    postings = postings.copy()
    skills = _explode_linkedin_skills(skills)

    for col in LINKEDIN_POSTING_TEXT_COLS:
        if col in postings.columns:
            postings[col] = _normalize_text(postings[col])

    if "first_seen" in postings.columns:
        postings["first_seen"] = pd.to_datetime(postings["first_seen"], errors="coerce")
        postings["first_seen_year"] = postings["first_seen"].dt.year.astype("Int64")

    merged = skills.merge(postings, on="job_link", how="left", suffixes=("_skill", "_posting"))
    merged["source"] = "linkedin_validation"

    keep_cols = [
        "job_link",
        "job_title",
        "company",
        "job_location",
        "first_seen",
        "first_seen_year",
        "search_city",
        "search_country",
        "search_position",
        "job_level",
        "job_type",
        "job_skills",
        "skill",
        "source",
    ]
    existing_cols = [col for col in keep_cols if col in merged.columns]
    merged = merged[existing_cols].copy()

    merged.to_csv(LINKEDIN_OUTPUT, index=False)

    print(f"[linkedin] posting sample rows: {len(postings):,}")
    print(f"[linkedin] exploded skill rows: {len(skills):,}")
    print(f"[linkedin] merged rows: {len(merged):,}")
    print(f"[linkedin] output written: {LINKEDIN_OUTPUT}")
    print(f"[linkedin] output shape: {merged.shape}")

    return merged


def run_phase2(sample_rows: int = 10000) -> dict[str, Any]:
    """
    Run the full Phase 2 preprocessing flow and return a compact summary.
    """
    _ensure_dirs()

    primary_clean = clean_primary_dataset()
    linkedin_clean = clean_linkedin_validation_dataset(sample_rows=sample_rows)

    summary = {
        "primary_output": str(PRIMARY_OUTPUT),
        "primary_rows": int(len(primary_clean)),
        "primary_cols": int(primary_clean.shape[1]),
        "linkedin_output": str(LINKEDIN_OUTPUT),
        "linkedin_rows": int(len(linkedin_clean)),
        "linkedin_cols": int(linkedin_clean.shape[1]),
    }

    return summary


def main() -> None:
    summary = run_phase2()
    print("\nPhase 2 summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
