from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
from wordcloud import WordCloud

from src.phase3_eda import (
    annual_skill_trends,
    cooccurrence_matrix,
    experience_level_skill_crosstab,
    load_linkedin_validation,
    load_primary_clean,
    skill_category_frequency,
    top_skill_frequency,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHART_DIR = PROJECT_ROOT / "assets" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)


def _style_axes(ax: plt.Axes) -> None:
    ax.grid(axis="x", alpha=0.15)
    sns.despine(ax=ax, left=True, bottom=False)


def _save(fig: plt.Figure, filename: str) -> Path:
    path = CHART_DIR / filename
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def build_chart_1_top_skills(df: pd.DataFrame) -> tuple[plt.Figure, Path]:
    top_skills = top_skill_frequency(df, n=11).sort_values("mentions")

    fig, ax = plt.subplots(figsize=(11, 7))
    palette = sns.color_palette("Blues", n_colors=len(top_skills) + 2)[2:]
    ax.barh(top_skills["skill"], top_skills["mentions"], color=palette, edgecolor="#1f2937", linewidth=0.6)
    ax.set_title("Cloud and ML skills dominate the 224k-row primary skill table", loc="left", pad=14, weight="bold")
    ax.set_xlabel("Mentions")
    ax.set_ylabel("")
    _style_axes(ax)

    xmax = top_skills["mentions"].max() * 1.05
    ax.set_xlim(0, xmax)
    for y, value in enumerate(top_skills["mentions"]):
        ax.text(value + xmax * 0.01, y, f"{value:,}", va="center", ha="left", fontsize=9, color="#111827")

    fig.text(0.01, 0.01, "Top 11 skills from the cleaned primary dataset. Source: data/clean/primary_skills_long.csv", fontsize=9, color="#4b5563")
    return fig, _save(fig, "01_top_skills_ranking.png")


def build_chart_2_trends(df: pd.DataFrame) -> tuple[plt.Figure, Path]:
    annual, rising, declining = annual_skill_trends(df)
    trend_skills = pd.concat([rising, declining]).drop_duplicates("skill")["skill"].tolist()
    plot_df = annual[annual["skill"].isin(trend_skills)].copy()
    plot_df["posted_year"] = plot_df["posted_year"].astype(int)
    plot_df = plot_df.sort_values(["skill", "posted_year"])

    fig, ax = plt.subplots(figsize=(11, 7))
    colors = sns.color_palette("colorblind", n_colors=len(trend_skills))
    for color, skill in zip(colors, trend_skills):
        subset = plot_df[plot_df["skill"] == skill]
        ax.plot(subset["posted_year"], subset["share"] * 100, marker="o", linewidth=2.3, color=color, label=skill)

    ax.set_title("Computer Vision and Scikit-Learn gain the most share from 2020 to 2026", loc="left", pad=14, weight="bold")
    ax.set_xlabel("Year")
    ax.set_ylabel("Share of annual skill mentions (%)")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100))
    ax.legend(ncol=2, frameon=False, loc="upper left")
    ax.grid(alpha=0.2)
    sns.despine(ax=ax)
    fig.text(0.01, 0.01, "Annual share trends from the cleaned primary dataset; primary source only provides posted_year.", fontsize=9, color="#4b5563")
    return fig, _save(fig, "02_skill_trends_annual.png")


def build_chart_3_cooccurrence(df: pd.DataFrame) -> tuple[plt.Figure, Path]:
    matrix, pairs = cooccurrence_matrix(df)

    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(matrix, cmap="Blues", linewidths=0.35, linecolor="white", cbar_kws={"label": "Co-occurrence count"}, ax=ax)
    ax.set_title("The core skills repeatedly co-occur in the same job posting", loc="left", pad=14, weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=40)
    ax.tick_params(axis="y", rotation=0)
    fig.text(0.01, 0.01, "Top 11 skills only. Darker cells indicate skills that are more often requested together.", fontsize=9, color="#4b5563")
    return fig, _save(fig, "03_skill_cooccurrence_heatmap.png")


def build_chart_4_experience_mix(df: pd.DataFrame) -> tuple[plt.Figure, Path]:
    counts, shares = experience_level_skill_crosstab(df)
    ordered_levels = [lvl for lvl in ["entry", "mid", "senior"] if lvl in shares.index]
    ordered_skills = shares.sum(axis=0).sort_values(ascending=False).index.tolist()
    shares = shares.loc[ordered_levels, ordered_skills]

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(shares, cmap="YlGnBu", linewidths=0.35, linecolor="white", cbar_kws={"label": "Share within experience level"}, ax=ax)
    ax.set_title("Skill mix changes only slightly across experience levels", loc="left", pad=14, weight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=35)
    ax.tick_params(axis="y", rotation=0)
    fig.text(0.01, 0.01, "Share within each experience bucket. The differences are subtle, not dramatic.", fontsize=9, color="#4b5563")
    return fig, _save(fig, "04_skill_mix_by_experience.png")


def build_chart_5_wordcloud(df: pd.DataFrame) -> tuple[plt.Figure, Path]:
    skill_counts = skill_category_frequency(df).set_index("skill_category")["mentions"].to_dict()
    skill_weights = df["skill"].value_counts().to_dict()

    cloud = WordCloud(
        width=1800,
        height=1000,
        background_color="white",
        colormap="Blues",
        prefer_horizontal=0.95,
        max_words=200,
        random_state=42,
    ).generate_from_frequencies(skill_weights)

    fig, ax = plt.subplots(figsize=(12, 7))
    ax.imshow(cloud, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("A compact visual summary of the skill landscape", loc="left", pad=14, weight="bold")
    fig.text(0.01, 0.01, "Word cloud sized by mention frequency from the cleaned primary dataset.", fontsize=9, color="#4b5563")
    return fig, _save(fig, "05_skill_wordcloud.png")


def build_all_charts() -> dict[str, Any]:
    primary = load_primary_clean()
    linkedin_validation = load_linkedin_validation()

    outputs = {
        "chart_1": build_chart_1_top_skills(primary),
        "chart_2": build_chart_2_trends(primary),
        "chart_3": build_chart_3_cooccurrence(primary),
        "chart_4": build_chart_4_experience_mix(primary),
        "chart_5": build_chart_5_wordcloud(primary),
    }
    return {
        "charts": {k: str(v[1]) for k, v in outputs.items()},
        "primary_rows": len(primary),
        "linkedin_rows": len(linkedin_validation),
    }


def main() -> None:
    summary = build_all_charts()
    print("Phase 4 chart exports:")
    for key, value in summary["charts"].items():
        print(f"{key}: {value}")
    print(summary)


if __name__ == "__main__":
    main()
