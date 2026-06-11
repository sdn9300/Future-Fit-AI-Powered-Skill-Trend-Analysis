from __future__ import annotations

from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from scipy.stats import chi2_contingency


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_CLEAN_PATH = PROJECT_ROOT / "data" / "clean" / "primary_skills_long.csv"
LINKEDIN_VALIDATION_PATH = PROJECT_ROOT / "data" / "clean" / "linkedin_validation.csv"

TOP_SKILL_COUNT = 20
TOP_SKILLS_FOR_MATRIX = 11
GENAI_TERMS = ["llm", "rag", "genai", "prompt engineering"]


def _normalize_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ["skill", "skill_category", "skill_level", "experience_level", "source"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip().str.lower()
    if "posted_year" in df.columns:
        df["posted_year"] = df["posted_year"].apply(lambda x: int(x) if str(x).isdigit() else (x.strip() if isinstance(x, str) else x))
    return df


def load_primary_clean(path: Path | str = PRIMARY_CLEAN_PATH) -> pd.DataFrame:
    """Load the primary clean CSV.
    If the file does not exist, create a minimal placeholder DataFrame with the required columns.
    """
    if not Path(path).exists():
        # Create a placeholder with expected columns
        placeholder = pd.DataFrame({
            "skill": [],
            "skill_category": [],
            "posted_year": [],
            "job_id": [],
            "experience_level": [],
            "source": [],
        })
        return _normalize_text_columns(placeholder)
    df = pd.read_csv(path)
    return _normalize_text_columns(df)


def load_linkedin_validation(path: Path | str = LINKEDIN_VALIDATION_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    return _normalize_text_columns(df)


def describe_primary(df: pd.DataFrame) -> dict[str, Any]:
    years = sorted(df["posted_year"].dropna().astype(int).unique().tolist())
    jobs = int(df["job_id"].nunique())
    skills = int(df["skill"].nunique())
    categories = int(df["skill_category"].nunique())
    matched_rows = int(df["job_id_job"].notna().sum()) if "job_id_job" in df.columns else None

    return {
        "rows": int(len(df)),
        "jobs": jobs,
        "skills": skills,
        "skill_categories": categories,
        "years": years,
        "matched_rows": matched_rows,
    }


def top_skill_frequency(df: pd.DataFrame, n: int = TOP_SKILL_COUNT) -> pd.DataFrame:
    return (
        df["skill"]
        .value_counts()
        .head(n)
        .rename_axis("skill")
        .reset_index(name="mentions")
    )


def skill_category_frequency(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("skill_category", dropna=False)
        .size()
        .sort_values(ascending=False)
        .rename_axis("skill_category")
        .reset_index(name="mentions")
    )


def annual_skill_trends(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    annual = (
        df.groupby(["posted_year", "skill"], dropna=False)
        .size()
        .reset_index(name="mentions")
        .dropna(subset=["posted_year"])
    )
    year_totals = (
        df.groupby("posted_year")
        .size()
        .rename("year_total")
        .reset_index()
        .dropna(subset=["posted_year"])
    )
    annual = annual.merge(year_totals, on="posted_year", how="left")
    annual["share"] = annual["mentions"] / annual["year_total"]

    wide = annual.pivot(index="skill", columns="posted_year", values="share")
    wide["share_change_pp_2026_2020"] = (wide[2026] - wide[2020]) * 100
    wide = wide.sort_values("share_change_pp_2026_2020", ascending=False)

    rising = (
        wide["share_change_pp_2026_2020"]
        .sort_values(ascending=False)
        .head(5)
        .rename_axis("skill")
        .reset_index(name="share_change_pp")
    )
    declining = (
        wide["share_change_pp_2026_2020"]
        .sort_values(ascending=True)
        .head(5)
        .rename_axis("skill")
        .reset_index(name="share_change_pp")
    )

    return annual, rising, declining


def cooccurrence_matrix(df: pd.DataFrame, top_n: int = TOP_SKILLS_FOR_MATRIX) -> tuple[pd.DataFrame, pd.DataFrame]:
    top_skills = df["skill"].value_counts().head(top_n).index.tolist()
    job_skills = (
        df.groupby("job_id")["skill"]
        .apply(lambda s: sorted(set(s.dropna()).intersection(top_skills)))
    )

    counter: Counter[tuple[str, str]] = Counter()
    for skills in job_skills:
        for pair in combinations(skills, 2):
            counter[pair] += 1

    matrix = pd.DataFrame(0, index=top_skills, columns=top_skills, dtype=int)
    for (a, b), value in counter.items():
        matrix.loc[a, b] = value
        matrix.loc[b, a] = value
    for skill in top_skills:
        matrix.loc[skill, skill] = 0

    pairs = pd.DataFrame(
        list(counter.items()),
        columns=["skill_pair", "co_occurrence"]
    ).sort_values("co_occurrence", ascending=False).reset_index(drop=True)
    return matrix, pairs


def experience_level_skill_crosstab(df: pd.DataFrame, top_n: int = TOP_SKILLS_FOR_MATRIX) -> tuple[pd.DataFrame, pd.DataFrame]:
    top_skills = df["skill"].value_counts().head(top_n).index.tolist()
    subset = df.dropna(subset=["experience_level"]).copy()
    subset = subset[subset["skill"].isin(top_skills)]
    counts = pd.crosstab(subset["experience_level"], subset["skill"])
    shares = counts.div(counts.sum(axis=1), axis=0)
    return counts, shares


def genai_validation(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, float, float, int, np.ndarray]:
    term_pattern = "|".join(GENAI_TERMS)
    validation = df.copy()
    validation["genai_flag"] = validation["skill"].str.contains(term_pattern, case=False, na=False)

    contingency = pd.crosstab(validation["job_level"].fillna("unknown"), validation["genai_flag"])
    chi2, p_value, dof, expected = chi2_contingency(contingency)

    summary = (
        validation.groupby("job_level", dropna=False)["genai_flag"]
        .agg(genai_mentions="sum", total_skill_rows="count", genai_share="mean")
        .reset_index()
        .sort_values("genai_share", ascending=False)
    )
    return validation, summary, chi2, p_value, dof, expected


def plot_top_skills_bar(top_skills: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(11, 7))
    sns.barplot(data=top_skills, x="mentions", y="skill", color="#2b6cb0", ax=ax)
    ax.set_title("Top skills in the cleaned primary dataset")
    ax.set_xlabel("Mentions")
    ax.set_ylabel("")
    ax.grid(axis="x", alpha=0.2)
    sns.despine(ax=ax, left=True, bottom=False)
    return fig


def plot_skill_category_bar(category_counts: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    sns.barplot(data=category_counts, x="skill_category", y="mentions", palette=["#2b6cb0", "#6b8e23", "#d98e04"], ax=ax)
    ax.set_title("Skill categories are concentrated in ML, cloud, and programming")
    ax.set_xlabel("")
    ax.set_ylabel("Mentions")
    ax.grid(axis="y", alpha=0.2)
    sns.despine(ax=ax, left=True, bottom=True)
    return fig


def plot_annual_trends(annual: pd.DataFrame):
    top_skills = annual["skill"].value_counts().head(TOP_SKILLS_FOR_MATRIX).index.tolist()
    plot_df = annual[annual["skill"].isin(top_skills)].copy()
    fig = px.line(
        plot_df,
        x="posted_year",
        y="share",
        color="skill",
        markers=True,
        title="Annual skill share trends in the primary dataset",
        labels={"posted_year": "Year", "share": "Share of yearly skill mentions", "skill": "Skill"},
    )
    fig.update_layout(template="plotly_white", legend_title_text="Skill", hovermode="x unified")
    fig.update_yaxes(tickformat=".0%")
    return fig


def plot_cooccurrence_heatmap(matrix: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(matrix, cmap="Blues", linewidths=0.4, linecolor="white", ax=ax)
    ax.set_title("Skill co-occurrence among the most frequent skills")
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    return fig


def plot_experience_share_heatmap(shares: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(12, 4.5))
    sns.heatmap(shares, cmap="YlGnBu", linewidths=0.4, linecolor="white", ax=ax)
    ax.set_title("Skill mix by experience level")
    ax.set_xlabel("")
    ax.set_ylabel("")
    plt.xticks(rotation=35, ha="right")
    plt.yticks(rotation=0)
    return fig


def plot_genai_validation(summary: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.barplot(data=summary, x="job_level", y="genai_share", color="#2b6cb0", ax=ax)
    ax.set_title("GenAI-related skill share is higher in mid-senior roles")
    ax.set_xlabel("")
    ax.set_ylabel("Share of skill rows")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.grid(axis="y", alpha=0.2)
    sns.despine(ax=ax, left=True, bottom=True)
    return fig


def build_phase3_artifacts() -> dict[str, Any]:
    primary = load_primary_clean()
    linkedin_validation = load_linkedin_validation()

    top_skills = top_skill_frequency(primary)
    category_counts = skill_category_frequency(primary)
    annual, rising, declining = annual_skill_trends(primary)
    matrix, co_pairs = cooccurrence_matrix(primary)
    exp_counts, exp_shares = experience_level_skill_crosstab(primary)
    validation_rows, genai_summary, chi2, p_value, dof, expected = genai_validation(linkedin_validation)

    return {
        "primary_summary": describe_primary(primary),
        "top_skills": top_skills,
        "category_counts": category_counts,
        "annual_trends": annual,
        "rising_skills": rising,
        "declining_skills": declining,
        "cooccurrence_matrix": matrix,
        "cooccurrence_pairs": co_pairs,
        "experience_counts": exp_counts,
        "experience_shares": exp_shares,
        "genai_validation_rows": validation_rows,
        "genai_summary": genai_summary,
        "chi2": chi2,
        "p_value": p_value,
        "dof": dof,
        "expected": expected,
    }


def main() -> None:
    artifacts = build_phase3_artifacts()
    print("Phase 3 summary")
    for key in ["primary_summary", "chi2", "p_value", "dof"]:
        print(f"{key}: {artifacts[key]}")


if __name__ == "__main__":
    main()
