from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.phase3_eda import (
    cooccurrence_matrix,
    load_linkedin_validation,
    load_primary_clean,
)
from src.skill_gap_advisor import (
    generate_skill_gap_preview,
    get_skill_gap_advice,
    get_trending_skills,
    run_phase5_smoke_tests,
    validate_user_input,
)


PROJECT_ROOT = Path(__file__).resolve().parent
PRIMARY_CLEAN_PATH = PROJECT_ROOT / "data" / "clean" / "primary_skills_long.csv"
LINKEDIN_VALIDATION_PATH = PROJECT_ROOT / "data" / "clean" / "linkedin_validation.csv"

DEFAULT_THEME = {
    "title": "Future Fit",
    "tagline": "AI-Powered Skill Trend Analysis",
    "accent": "#d7b15a",
    "accent_soft": "#f2dfb2",
    "bg": "#120a22",
    "surface": "#1b122f",
    "surface_alt": "#26173f",
    "text": "#f6e7bf",
    "muted": "rgba(246, 231, 191, 0.78)",
    "border": "rgba(215, 177, 90, 0.28)",
    "shadow": "0 24px 70px rgba(4, 0, 12, 0.48)",
}


@st.cache_data(show_spinner=False)
def find_data_file(filename: str) -> Path | None:
    """
    Helper to locate data files in common locations within the repository.
    Checks the default data/clean path first, then scans PROJECT_ROOT and its parent.
    Returns Path if found, otherwise None.
    """
    # check the default location first
    candidate = PROJECT_ROOT / "data" / "clean" / filename
    if candidate.exists():
        return candidate

    # search PROJECT_ROOT and its parent for the filename
    for base in (PROJECT_ROOT, PROJECT_ROOT.parent):
        try:
            for match in base.rglob(filename):
                if match.is_file():
                    return match
        except Exception:
            # ignore permission errors or odd filesystem entries
            continue
    return None


@st.cache_data(show_spinner="Loading primary dataset...")
def load_primary_clean_cached(path: Path) -> pd.DataFrame:
    return load_primary_clean(path)


@st.cache_data(show_spinner="Loading LinkedIn dataset...")
def load_linkedin_validation_cached(path: Path) -> pd.DataFrame:
    return load_linkedin_validation(path)


@st.cache_data(show_spinner="Loading association rules...")
def load_mba_rules_cached(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_data(show_spinner="Parsing uploaded dataset...")
def parse_uploaded_csv_cached(file_bytes: bytes) -> pd.DataFrame:
    import io
    df = pd.read_csv(io.BytesIO(file_bytes))
    for col in ["skill", "skill_category", "skill_level", "experience_level", "source"]:
        if col in df.columns:
            df[col] = df[col].astype("string").str.strip().str.lower()
    if "posted_year" in df.columns:
        df["posted_year"] = df["posted_year"].apply(lambda x: int(x) if str(x).isdigit() else (x.strip() if isinstance(x, str) else x))
    return df
def load_dashboard_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Robust loading: try default path, search the repo for the file, then fall back to file uploader.
    Returns two DataFrames (primary, linkedin_validation) — may be empty if not provided.
    """
    primary = pd.DataFrame()
    linkedin_validation = pd.DataFrame()

    # --- primary data ---
    primary_file: Path | None = None
    # existing constant path keeps backward compatibility
    if PRIMARY_CLEAN_PATH.exists():
        primary_file = PRIMARY_CLEAN_PATH
    else:
        primary_file = find_data_file("primary_skills_long.csv")

    if primary_file:
        try:
            primary = load_primary_clean_cached(primary_file)
        except Exception as exc:
            st.warning(f"Failed to load primary data from {primary_file}: {exc}")
    else:
        st.warning(
            "Primary data file not found in the repository. "
            "You can upload it below (CSV expected: primary_skills_long.csv)."
        )
        uploaded_primary = st.file_uploader(
            "Upload primary_skills_long.csv", type="csv", key="upload_primary"
        )
        if uploaded_primary is not None:
            try:
                primary = parse_uploaded_csv_cached(uploaded_primary.getvalue())
            except Exception as exc:
                st.error(f"Uploaded primary file could not be read: {exc}")

    # --- linkedin validation data ---
    linkedin_file: Path | None = None
    if LINKEDIN_VALIDATION_PATH.exists():
        linkedin_file = LINKEDIN_VALIDATION_PATH
    else:
        linkedin_file = find_data_file("linkedin_validation.csv")

    if linkedin_file:
        try:
            linkedin_validation = load_linkedin_validation_cached(linkedin_file)
        except Exception as exc:
            st.warning(f"Failed to load LinkedIn validation data from {linkedin_file}: {exc}")
    else:
        st.info(
            "LinkedIn validation file not found. You can upload it below (optional):"
        )
        uploaded_linkedin = st.file_uploader(
            "Upload linkedin_validation.csv", type="csv", key="upload_linkedin"
        )
        if uploaded_linkedin is not None:
            try:
                linkedin_validation = parse_uploaded_csv_cached(uploaded_linkedin.getvalue())
            except Exception as exc:
                st.error(f"Uploaded LinkedIn file could not be read: {exc}")

    return primary, linkedin_validation


def get_config_value(key: str, default: str) -> str:
    try:
        secret_value = st.secrets.get(key)  # type: ignore[attr-defined]
    except Exception:
        secret_value = None

    env_value = os.getenv(key)
    value = env_value if env_value not in (None, "") else secret_value
    return str(value) if value not in (None, "") else default


def get_theme() -> dict[str, str]:
    return {
        "title": get_config_value("APP_TITLE", DEFAULT_THEME["title"]),
        "tagline": get_config_value("APP_TAGLINE", DEFAULT_THEME["tagline"]),
        "accent": get_config_value("APP_ACCENT", DEFAULT_THEME["accent"]),
        "accent_soft": get_config_value("APP_ACCENT_SOFT", DEFAULT_THEME["accent_soft"]),
        "bg": get_config_value("APP_BG", DEFAULT_THEME["bg"]),
        "surface": get_config_value("APP_SURFACE", DEFAULT_THEME["surface"]),
        "surface_alt": get_config_value("APP_SURFACE_ALT", DEFAULT_THEME["surface_alt"]),
        "text": get_config_value("APP_TEXT", DEFAULT_THEME["text"]),
        "muted": get_config_value("APP_MUTED", DEFAULT_THEME["muted"]),
        "border": get_config_value("APP_BORDER", DEFAULT_THEME["border"]),
        "shadow": get_config_value("APP_SHADOW", DEFAULT_THEME["shadow"]),
    }


def inject_css(theme: dict[str, str]) -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --app-title: "{theme["title"]}";
            --app-tagline: "{theme["tagline"]}";
            --app-accent: {theme["accent"]};
            --app-accent-soft: {theme["accent_soft"]};
            --app-bg: {theme["bg"]};
            --app-surface: {theme["surface"]};
            --app-surface-alt: {theme["surface_alt"]};
            --app-text: {theme["text"]};
            --app-muted: {theme["muted"]};
            --app-border: {theme["border"]};
            --app-shadow: {theme["shadow"]};
        }}

        [data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(circle at top right, rgba(215, 177, 90, 0.12), transparent 22%),
                radial-gradient(circle at left center, rgba(152, 78, 255, 0.16), transparent 28%),
                linear-gradient(180deg, #160b2a 0%, var(--app-bg) 54%, #0c0717 100%);
            color: var(--app-text);
        }}

        [data-testid="stHeader"] {{
            background: transparent;
        }}

        section[data-testid="stSidebar"] {{
            background:
                linear-gradient(180deg, rgba(27, 18, 47, 0.98), rgba(16, 9, 31, 0.98));
            border-right: 1px solid rgba(215, 177, 90, 0.16);
        }}

        section[data-testid="stSidebar"] * {{
            color: var(--app-text);
        }}

        section[data-testid="stSidebar"] .stButton > button {{
            background: linear-gradient(135deg, var(--app-accent), #f2d889);
            color: #1a1329;
            border: 0;
            font-weight: 700;
            box-shadow: 0 12px 28px rgba(215, 177, 90, 0.22);
        }}

        section[data-testid="stSidebar"] .stButton > button:hover {{
            filter: brightness(1.03);
        }}

        .brand-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.25rem;
            padding: 0.95rem 1rem 1rem;
            margin: 0 0 1rem 0;
            border-radius: 22px;
            border: 1px solid rgba(215, 177, 90, 0.24);
            background:
                linear-gradient(135deg, rgba(43, 27, 73, 0.96), rgba(24, 14, 45, 0.98));
            box-shadow: var(--app-shadow);
        }}

        .brand-mark {{
            display: flex;
            align-items: center;
            gap: 0.9rem;
            min-width: 0;
        }}

        .brand-mark__icon {{
            width: 68px;
            height: 68px;
            flex: 0 0 auto;
            display: grid;
            place-items: center;
            border-radius: 20px;
            border: 1px solid rgba(242, 223, 178, 0.28);
            background:
                radial-gradient(circle at 32% 20%, rgba(255, 245, 206, 0.28), transparent 34%),
                linear-gradient(145deg, rgba(67, 44, 107, 1), rgba(24, 14, 45, 1));
            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.14),
                inset 0 -1px 0 rgba(0, 0, 0, 0.24),
                0 12px 30px rgba(0, 0, 0, 0.28);
        }}

        .brand-mark__word {{
            display: flex;
            flex-direction: column;
            min-width: 0;
        }}

        .brand-mark__title {{
            font-size: clamp(1.55rem, 2vw, 2rem);
            font-weight: 800;
            letter-spacing: -0.06em;
            color: var(--app-text);
            line-height: 0.98;
            text-shadow: 0 2px 0 rgba(0, 0, 0, 0.12);
        }}

        .brand-mark__tagline {{
            margin-top: 0.42rem;
            font-size: 0.92rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: rgba(246, 231, 191, 0.82);
        }}

        .brand-nav {{
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 0.65rem 1rem;
            color: rgba(246, 231, 191, 0.78);
            font-size: 0.92rem;
            letter-spacing: 0.03em;
        }}

        .brand-nav span {{
            white-space: nowrap;
        }}

        .block-container {{
            padding-top: 1.1rem;
            padding-bottom: 2rem;
            max-width: 1400px;
        }}

        .hero {{
            background:
                radial-gradient(circle at top right, rgba(215, 177, 90, 0.10), transparent 30%),
                linear-gradient(145deg, rgba(35, 21, 58, 0.96), rgba(18, 10, 34, 0.98));
            border: 1px solid rgba(215, 177, 90, 0.30);
            border-radius: 24px;
            padding: 1.4rem 1.5rem;
            box-shadow: var(--app-shadow);
            margin-bottom: 1rem;
        }}

        .hero__eyebrow {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            font-size: 0.72rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--app-muted);
            margin-bottom: 0.55rem;
        }}

        .hero__title {{
            margin: 0;
            font-size: clamp(2rem, 3.6vw, 3.35rem);
            line-height: 0.96;
            letter-spacing: -0.06em;
            color: var(--app-text);
        }}

        .hero__copy {{
            margin-top: 0.85rem;
            max-width: 70ch;
            color: var(--app-muted);
            font-size: 1.01rem;
            line-height: 1.6;
        }}

        .hero__meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.95rem;
        }}

        .chip {{
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            border: 1px solid rgba(215, 177, 90, 0.24);
            background: rgba(255,255,255,0.04);
            color: var(--app-text);
            padding: 0.38rem 0.72rem;
            font-size: 0.84rem;
            line-height: 1;
        }}

        .section-label {{
            color: var(--app-muted);
            font-size: 0.76rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.65rem;
        }}

        .section-heading {{
            margin: 0 0 0.25rem 0;
            font-size: 1.2rem;
            letter-spacing: -0.03em;
            color: var(--app-text);
        }}

        .section-copy {{
            margin: 0 0 0.9rem 0;
            color: var(--app-muted);
            line-height: 1.55;
            max-width: 70ch;
        }}

        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.8rem;
            margin: 0.25rem 0 1rem 0;
        }}

        .kpi-card {{
            background: linear-gradient(180deg, rgba(44, 28, 74, 0.96), rgba(24, 14, 45, 0.96));
            border: 1px solid rgba(215, 177, 90, 0.22);
            border-radius: 18px;
            padding: 0.95rem 1rem;
            box-shadow: 0 16px 34px rgba(0, 0, 0, 0.26);
            min-height: 108px;
        }}

        .kpi-label {{
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.14em;
            color: var(--app-muted);
            margin-bottom: 0.5rem;
        }}

        .kpi-value {{
            font-size: 1.7rem;
            font-weight: 700;
            letter-spacing: -0.05em;
            color: var(--app-text);
            line-height: 1.05;
            margin-bottom: 0.35rem;
        }}

        .kpi-note {{
            font-size: 0.9rem;
            color: var(--app-muted);
            line-height: 1.4;
        }}

        .panel {{
            background: linear-gradient(180deg, rgba(33, 20, 56, 0.94), rgba(21, 12, 38, 0.96));
            border: 1px solid rgba(215, 177, 90, 0.22);
            border-radius: 22px;
            padding: 1rem;
            box-shadow: var(--app-shadow);
        }}

        .panel--flat {{
            background: transparent;
            border: 0;
            box-shadow: none;
            padding: 0;
        }}

        .detail-callout {{
            background: linear-gradient(180deg, rgba(215, 177, 90, 0.10), rgba(255,255,255,0.02));
            border: 1px solid rgba(215, 177, 90, 0.22);
            border-radius: 18px;
            padding: 0.9rem 1rem;
            color: var(--app-text);
            margin-top: 0.9rem;
        }}

        .small-muted {{
            color: var(--app-muted);
            font-size: 0.92rem;
        }}

        @media (max-width: 980px) {{
            .kpi-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}

        @media (max-width: 640px) {{
            .kpi-grid {{
                grid-template-columns: 1fr;
            }}
            .brand-bar {{
                flex-direction: column;
                align-items: flex-start;
            }}
            .hero {{
                padding: 1.1rem;
            }}
            .panel {{
                padding: 0.85rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_card_grid(cards: list[dict[str, str]]) -> None:
    st.markdown('<div class="kpi-grid">', unsafe_allow_html=True)
    cols = st.columns(len(cards))
    for col, card in zip(cols, cards):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{card["label"]}</div>
                    <div class="kpi-value">{card["value"]}</div>
                    <div class="kpi-note">{card["note"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    with st.sidebar:
        st.markdown("### Filters")
        st.caption("These controls shape the overview, trends, and heatmap tabs.")

        numeric_years = sorted([int(y) for y in df["posted_year"].dropna().unique() if str(y).isdigit()])
        non_numeric = sorted([str(y) for y in df["posted_year"].dropna().unique() if not str(y).isdigit()])
        available_years = numeric_years + non_numeric
        selected_years = st.multiselect(
            "Years",
            available_years,
            default=available_years,
        )

        available_categories = sorted(df["skill_category"].dropna().astype(str).unique().tolist())
        selected_categories = st.multiselect(
            "Skill categories",
            available_categories,
            default=available_categories,
        )

        if st.button("Reset filters", use_container_width=True):
            st.session_state["reset_filters"] = True

        st.markdown("---")
        api_ready = bool(get_groq_api_key())
        st.write("Advisor status")
        st.caption("Live Groq key configured" if api_ready else "Using local preview until Groq key is available")

    if st.session_state.pop("reset_filters", False):
        st.rerun()

    filtered = df.copy()
    if selected_years:
        filtered = filtered[filtered["posted_year"].apply(lambda x: str(x) in map(str, selected_years))]
    if selected_categories:
        filtered = filtered[filtered["skill_category"].isin(selected_categories)]

    return filtered


def get_groq_api_key() -> str | None:
    secret_key = None
    try:
        secret_key = st.secrets.get("GROQ_API_KEY")  # type: ignore[attr-defined]
    except Exception:
        secret_key = None
    return secret_key or os.getenv("GROQ_API_KEY")


def make_top_skills_figure(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    top = (
        df.groupby(["skill", "skill_category"], dropna=False)
        .size()
        .reset_index(name="mentions")
        .sort_values("mentions", ascending=False)
        .head(top_n)
        .sort_values("mentions", ascending=True)
    )

    palette = {
        "programming": "#f2d889",
        "ml": "#d7b15a",
        "cloud": "#a67cff",
    }
    colors = [palette.get(cat, "#64748b") for cat in top["skill_category"]]

    fig = go.Figure(
        go.Bar(
            x=top["mentions"],
            y=top["skill"],
            orientation="h",
            marker=dict(color=colors, line=dict(color="rgba(15,23,42,0.35)", width=0.5)),
            hovertemplate="<b>%{y}</b><br>Mentions: %{x:,}<extra></extra>",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        margin=dict(l=20, r=20, t=15, b=20),
        height=620,
        showlegend=False,
        xaxis_title="Mentions",
        yaxis_title="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=DEFAULT_THEME["text"]),
    )
    fig.update_xaxes(gridcolor="rgba(246,231,191,0.10)")
    fig.update_yaxes(gridcolor="rgba(246,231,191,0.10)")
    return fig


def make_trend_figure(df: pd.DataFrame, skill: str) -> go.Figure:
    trend_df = df.copy()
    trend_df = trend_df[trend_df["posted_year"].apply(lambda x: str(x).isdigit())]
    trend_df["posted_year"] = trend_df["posted_year"].astype("Int64")
    trend_df = trend_df[trend_df["skill"] == skill]

    year_totals = df.groupby("posted_year").size().rename("year_total").reset_index()
    annual = (
        trend_df.groupby("posted_year")
        .size()
        .rename("mentions")
        .reset_index()
        .merge(year_totals, on="posted_year", how="left")
    )
    annual["share"] = annual["mentions"] / annual["year_total"]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=annual["posted_year"],
            y=annual["share"],
            mode="lines+markers",
            line=dict(color=DEFAULT_THEME["accent"], width=3),
            marker=dict(size=9, color=DEFAULT_THEME["accent"]),
            customdata=annual[["mentions"]],
            hovertemplate=(
                "Year %{x}<br>"
                "Share: %{y:.2%}<br>"
                "Mentions: %{customdata[0]:,}<extra></extra>"
            ),
            name=skill,
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=540,
        margin=dict(l=20, r=20, t=15, b=20),
        xaxis_title="Year",
        yaxis_title="Share of annual skill mentions",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=DEFAULT_THEME["text"]),
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_xaxes(gridcolor="rgba(246,231,191,0.10)")
    fig.update_yaxes(gridcolor="rgba(246,231,191,0.10)")
    return fig


def make_heatmap_figure(df: pd.DataFrame, top_n: int) -> tuple[go.Figure, pd.DataFrame, pd.DataFrame]:
    matrix, pairs = cooccurrence_matrix(df, top_n=top_n)

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix.values,
            x=matrix.columns.tolist(),
            y=matrix.index.tolist(),
            colorscale=[
                [0.0, "#241438"],
                [0.32, "#5f3fa0"],
                [0.68, "#c99f4d"],
                [1.0, "#f2dfb2"],
            ],
            hoverongaps=False,
            colorbar=dict(title="Co-occurrence"),
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=640,
        margin=dict(l=20, r=20, t=15, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=DEFAULT_THEME["text"]),
    )
    return fig, matrix, pairs


def render_header(theme: dict[str, str], df: pd.DataFrame) -> None:
    years = sorted([int(y) for y in df["posted_year"].dropna().unique() if str(y).isdigit()])
    top_skill = df["skill"].value_counts().idxmax()
    hero_chip_text = [
        f"{df['job_id'].nunique():,} jobs",
        f"{len(years)} annual buckets",
        f"top skill: {top_skill}",
    ]
    chips = "".join(f"<span class='chip'>{chip}</span>" for chip in hero_chip_text)
    logo_svg = """
    <svg width="52" height="52" viewBox="0 0 52 52" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
        <defs>
            <linearGradient id="goldFill" x1="8" y1="6" x2="44" y2="46" gradientUnits="userSpaceOnUse">
                <stop stop-color="#F7E8BE"/>
                <stop offset="0.45" stop-color="#D7B15A"/>
                <stop offset="1" stop-color="#9B6C1F"/>
            </linearGradient>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
                <feDropShadow dx="0" dy="2" stdDeviation="1.8" flood-color="#000000" flood-opacity="0.42"/>
            </filter>
        </defs>
        <rect x="1" y="1" width="50" height="50" rx="14" fill="url(#goldFill)" fill-opacity="0.08" stroke="url(#goldFill)" stroke-opacity="0.38"/>
        <path d="M14 14H25.8C29.2 14 31.8 16.6 31.8 20C31.8 23.4 29.2 26 25.8 26H18.8L14 14Z" fill="url(#goldFill)" filter="url(#shadow)"/>
        <path d="M14 14V38" stroke="url(#goldFill)" stroke-width="4.5" stroke-linecap="round" filter="url(#shadow)"/>
        <path d="M14 14H38" stroke="url(#goldFill)" stroke-width="4.5" stroke-linecap="round" filter="url(#shadow)"/>
        <path d="M14 38L24 26" stroke="url(#goldFill)" stroke-width="4.2" stroke-linecap="round" filter="url(#shadow)"/>
        <circle cx="14" cy="14" r="4.8" fill="#12203A" stroke="url(#goldFill)" stroke-width="2.3"/>
        <circle cx="38" cy="14" r="4.8" fill="#12203A" stroke="url(#goldFill)" stroke-width="2.3"/>
        <circle cx="14" cy="38" r="4.8" fill="#12203A" stroke="url(#goldFill)" stroke-width="2.3"/>
        <circle cx="24" cy="26" r="4.8" fill="#12203A" stroke="url(#goldFill)" stroke-width="2.3"/>
        <circle cx="30.8" cy="26" r="4.8" fill="#12203A" stroke="url(#goldFill)" stroke-width="2.3"/>
    </svg>
    """
    st.markdown(
        f"""
        <div class="brand-bar">
            <div class="brand-mark">
                <div class="brand-mark__icon">{logo_svg}</div>
                <div class="brand-mark__word">
                    <div class="brand-mark__title">{theme["title"]}</div>
                    <div class="brand-mark__tagline">{theme["tagline"]}</div>
                </div>
            </div>
            <div class="brand-nav" aria-hidden="true">
                <span>Dashboard</span>
                <span>Skill Trends</span>
                <span>Job Market</span>
                <span>My Profile</span>
            </div>
        </div>
        <div class="hero">
            <div class="hero__eyebrow">skill trend dashboard</div>
            <h1 class="hero__title">Find the skills that matter next.</h1>
            <p class="hero__copy">
                A source-backed dashboard for exploring skill concentration, annual movement,
                co-occurrence patterns, and the Groq-powered Skill Gap Advisor.
            </p>
            <div class="hero__meta">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_overview_tab(df: pd.DataFrame, theme: dict[str, str]) -> None:
    st.markdown('<div class="section-label">overview</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="section-heading">Core skill mix at a glance</h2>', unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>The default view leads with summary volume, then the ranked skill mix, and finishes with a short interpretation so the page answers the main question before any interaction.</p>",
        unsafe_allow_html=True,
    )

    skill_counts = df.groupby(["skill", "skill_category"], dropna=False).size().reset_index(name="mentions")
    top_skill = skill_counts.sort_values("mentions", ascending=False).iloc[0]
    top_category = (
        df.groupby("skill_category", dropna=False)
        .size()
        .sort_values(ascending=False)
        .index[0]
    )
    avg_skills_per_job = df.groupby("job_id")["skill"].nunique().mean()
    digit_years = df["posted_year"][df["posted_year"].apply(lambda x: str(x).isdigit())]
    year_min = int(digit_years.min()) if not digit_years.empty else 2020
    year_max = int(digit_years.max()) if not digit_years.empty else 2026

    render_card_grid(
        [
            {
                "label": "Skill mentions",
                "value": f"{len(df):,}",
                "note": "Long-form skill rows in the cleaned primary dataset.",
            },
            {
                "label": "Unique jobs",
                "value": f"{df['job_id'].nunique():,}",
                "note": "Distinct posting records contributing skill demand.",
            },
            {
                "label": "Avg skills / job",
                "value": f"{avg_skills_per_job:.1f}",
                "note": "Average number of unique skills requested per job.",
            },
            {
                "label": "Years covered",
                "value": f"{year_min} to {year_max}",
                "note": f"Annual coverage across {len(range(year_min, year_max + 1))} yearly buckets.",
            },
        ]
    )

    col_left, col_right = st.columns([1.45, 0.85], gap="large")
    with col_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.plotly_chart(make_top_skills_figure(df, top_n=20), use_container_width=True, theme=None, config={"displayModeBar": False, "responsive": True})
        st.markdown("</div>", unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="detail-callout">
                <strong>What stands out:</strong> {top_skill["skill"]} leads the current filtered view, and {top_category}
                is the largest category by total mentions.
            </div>
            """,
            unsafe_allow_html=True,
        )

        category_counts = (
            df.groupby("skill_category", dropna=False)
            .size()
            .reset_index(name="mentions")
            .sort_values("mentions", ascending=False)
        )
        fig = px.bar(
            category_counts,
            x="mentions",
            y="skill_category",
            orientation="h",
            text="mentions",
            title="Category mix",
            color="skill_category",
            color_discrete_sequence=["#d7b15a", "#a67cff", "#f2d889"],
        )
        fig.update_layout(
            template="plotly_dark",
            height=320,
            margin=dict(l=10, r=10, t=35, b=10),
            showlegend=False,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Mentions",
            yaxis_title="",
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False, "responsive": True})
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        f"<p class='small-muted'>This view is intentionally compact. It is built to give the audience the shape of the market first, then let them drill into yearly movement, co-occurrence, and the advisor.</p>",
        unsafe_allow_html=True,
    )


def render_trend_tab(df: pd.DataFrame, theme: dict[str, str]) -> None:
    st.markdown('<div class="section-label">trend explorer</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="section-heading">Pick a skill and inspect its annual movement</h2>', unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>The source only exposes annual granularity, so the explorer shows yearly changes instead of monthly motion. Use the selected skill to see whether the share is rising, flattening, or falling.</p>",
        unsafe_allow_html=True,
    )

    all_skills = get_trending_skills(df, top_n=20)
    if not all_skills:
        all_skills = sorted(df["skill"].dropna().unique().tolist())

    c1, c2, c3 = st.columns([1.15, 0.95, 1.0], gap="large")
    with c1:
        selected_skill = st.selectbox("Skill", options=all_skills, index=0)
    with c2:
        metric = st.radio("Measure", ["Share", "Mentions"], horizontal=True)
    with c3:
        digit_years = df["posted_year"][df["posted_year"].apply(lambda x: str(x).isdigit())]
        year_min = int(digit_years.min()) if not digit_years.empty else 2020
        year_max = int(digit_years.max()) if not digit_years.empty else 2026
        st.caption(f"Coverage: {year_min} to {year_max}")

    skill_rows = df[df["skill"] == selected_skill].copy()
    if skill_rows.empty:
        st.warning("No rows available for the current skill after filters.")
        return

    year_totals = df.groupby("posted_year").size().rename("year_total").reset_index()
    annual = (
        skill_rows.groupby("posted_year")
        .size()
        .rename("mentions")
        .reset_index()
        .merge(year_totals, on="posted_year", how="left")
    )
    annual["share"] = annual["mentions"] / annual["year_total"]
    
    # Exclude non-digit years for trend calculations
    annual = annual[annual["posted_year"].apply(lambda x: str(x).isdigit())]

    latest = annual.iloc[-1]
    first = annual.iloc[0]
    delta_pp = (latest["share"] - first["share"]) * 100
    peak_year = int(annual.sort_values("share", ascending=False).iloc[0]["posted_year"])

    render_card_grid(
        [
            {
                "label": "Latest share",
                "value": f"{latest['share']:.1%}",
                "note": f"Share of annual mentions in {int(latest['posted_year'])}.",
            },
            {
                "label": "Change since first year",
                "value": f"{delta_pp:+.2f} pp",
                "note": "Difference between the first and last year in the filtered view.",
            },
            {
                "label": "Peak year",
                "value": str(peak_year),
                "note": "The year with the strongest share for this skill.",
            },
            {
                "label": "Annual rows",
                "value": f"{len(annual):,}",
                "note": "Observed yearly points in the current view.",
            },
        ]
    )

    value_column = "mentions" if metric == "Mentions" else "share"
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=annual["posted_year"],
            y=annual[value_column],
            mode="lines+markers",
            line=dict(color=theme["accent"], width=3),
            marker=dict(size=9, color=theme["accent"]),
            customdata=annual[["mentions", "share"]],
            hovertemplate=(
                "Year %{x}<br>"
                "Mentions: %{customdata[0]:,}<br>"
                "Share: %{customdata[1]:.2%}<extra></extra>"
            ),
            name=selected_skill,
        )
    )
    fig.update_layout(
        template="plotly_white",
        height=520,
        margin=dict(l=20, r=20, t=10, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=theme["text"]),
        xaxis_title="Year",
        yaxis_title=metric,
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="rgba(15,23,42,0.08)")
    fig.update_yaxes(gridcolor="rgba(15,23,42,0.08)")
    if metric == "Share":
        fig.update_yaxes(tickformat=".0%")

    st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False, "responsive": True})

    annual_ranking = (
        annual.sort_values("share" if metric == "Share" else "mentions", ascending=False)
        .loc[:, ["posted_year", "mentions", "share"]]
    )
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("**Year-by-year values**")
    st.dataframe(
        annual_ranking.assign(share=annual_ranking["share"].map(lambda v: f"{v:.2%}")),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def render_heatmap_tab(df: pd.DataFrame, theme: dict[str, str]) -> None:
    st.markdown('<div class="section-label">skill heatmap</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="section-heading">See which skills travel together</h2>', unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>The heatmap uses the most frequent skills in the current filter context. Stronger cells mean the two skills are more often requested in the same job posting.</p>",
        unsafe_allow_html=True,
    )

    top_n = st.slider("Top skills in the matrix", min_value=8, max_value=15, value=11, step=1)
    fig, matrix, pairs = make_heatmap_figure(df, top_n=top_n)

    strongest_pair = pairs.iloc[0]
    non_zero_pairs = int((matrix.values > 0).sum())
    render_card_grid(
        [
            {
                "label": "Matrix size",
                "value": f"{matrix.shape[0]} x {matrix.shape[1]}",
                "note": "Top skill set used for the current heatmap.",
            },
            {
                "label": "Non-zero cells",
                "value": f"{non_zero_pairs:,}",
                "note": "Cells with at least one co-occurrence.",
            },
            {
                "label": "Strongest pair",
                "value": str(tuple(strongest_pair["skill_pair"])),
                "note": f"{int(strongest_pair['co_occurrence']):,} joint mentions.",
            },
            {
                "label": "Pair rows",
                "value": f"{len(pairs):,}",
                "note": "Sortable pair list underneath the chart.",
            },
        ]
    )

    st.plotly_chart(fig, use_container_width=True, theme=None, config={"displayModeBar": False, "responsive": True})

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown("**Top co-occurring pairs**")
    display_pairs = pairs.head(15).copy()
    display_pairs["skill_pair"] = display_pairs["skill_pair"].map(lambda x: " + ".join(x))
    st.dataframe(display_pairs, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_gap_advisor_tab(df: pd.DataFrame, theme: dict[str, str], mba_rules: pd.DataFrame | None = None) -> None:
    st.markdown('<div class="section-label">skill gap advisor</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="section-heading">Paste your skills and get a prioritized learning path</h2>', unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>The advisor compares your skill list against the current trending set from the filtered data. If the Groq key is not available, the app falls back to a local preview instead of failing.</p>",
        unsafe_allow_html=True,
    )

    api_key = get_groq_api_key()
    trending_skills = get_trending_skills(df, top_n=20)

    left, right = st.columns([1.15, 0.85], gap="large")
    with left:
        with st.form("advisor_form", clear_on_submit=False):
            skill_source = st.selectbox(
                "Quick start",
                [
                    "Custom input",
                    "Python, SQL, Pandas",
                    "Excel, PowerPoint",
                    "TensorFlow, PyTorch, CUDA",
                ],
            )
            user_input = (
                st.text_area(
                    "Your current skills",
                    value="" if skill_source == "Custom input" else skill_source,
                    placeholder="Python, SQL, Pandas",
                    height=120,
                )
            )
            submitted = st.form_submit_button("Analyze skill gap", use_container_width=True)

        if submitted:
            valid, parsed = validate_user_input(user_input)
            if not valid:
                st.error(parsed)
            else:
                assert isinstance(parsed, list)
                if api_key:
                    try:
                        advice = get_skill_gap_advice(parsed, trending_skills, mba_rules=mba_rules)
                    except Exception as exc:
                        st.warning(f"Live Groq call failed. Showing a local preview instead: {exc}")
                        advice = generate_skill_gap_preview(parsed, trending_skills, mba_rules=mba_rules)
                else:
                    st.info("Groq key not configured, so the app is showing a local preview.")
                    advice = generate_skill_gap_preview(parsed, trending_skills, mba_rules=mba_rules)

                st.success(advice)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown("**Current trending skills used by the advisor**")
        st.write(", ".join(trending_skills[:11]))
        st.caption("The list updates with the current dashboard filters.")
        st.markdown("---")
        st.markdown("**Advisor behavior**")
        st.caption("Valid inputs trigger the live Groq call when a key exists. Empty or nonsense inputs are blocked before the API step.")
        st.markdown("---")
        st.markdown("**Smoke tests**")
        with st.expander("Open the five plan tests"):
            for row in run_phase5_smoke_tests(df):
                status = "valid" if row["valid"] else "invalid"
                st.markdown(f"**Test {row['test']}**: `{row['input']}`")
                st.caption(f"Status: {status}")
                st.write(row["result"])
        st.markdown("</div>", unsafe_allow_html=True)


def render_market_basket_panel(rules: pd.DataFrame) -> None:
    st.markdown('<div class="section-label">skill associations</div>', unsafe_allow_html=True)
    st.markdown('<h2 class="section-heading">Identify co-occurring skill relationships</h2>', unsafe_allow_html=True)
    st.markdown(
        "<p class='section-copy'>Market Basket Analysis reveals which skills frequently appear together in the same job postings. Choose a confidence threshold to see the rules.</p>",
        unsafe_allow_html=True,
    )

    if rules.empty:
        st.warning("No association rules found. Please ensure data/clean/mba_rules.csv exists.")
        return

    st.info("Support = how often a skill pair appears together. "
            "Confidence = how often the rule holds true. "
            "Lift > 1.2 means the pair co-occurs more than chance.")

    # Determine dynamic confidence range based on available rules
    min_rules_conf = float(rules['confidence'].min()) if not rules.empty else 0.1
    max_rules_conf = float(rules['confidence'].max()) if not rules.empty else 1.0
    
    # We will use a flexible slider to handle different rule sets gracefully
    min_conf = st.slider("Minimum Confidence", min_rules_conf, 1.0, min_rules_conf, 0.05)
    filtered = rules[rules['confidence'] >= min_conf]

    if filtered.empty:
        st.warning("No rules match the selected confidence threshold.")
    else:
        left, right = st.columns([1.1, 0.9], gap="large")
        with left:
            st.dataframe(
                filtered[['antecedents','consequents','support','confidence','lift']]
                .rename(columns={
                    'antecedents': 'If job needs',
                    'consequents': 'Also needs',
                    'support': 'Support',
                    'confidence': 'Confidence',
                    'lift': 'Lift'
                }),
                use_container_width=True
            )
        with right:
            top10 = filtered.head(10).copy()
            top10['label'] = top10['antecedents'] + " → " + top10['consequents']
            fig = px.bar(
                top10, 
                x='lift', 
                y='label', 
                orientation='h',
                color='confidence', 
                title="Strongest Skill Associations by Lift",
                color_continuous_scale="Blues"
            )
            # Apply styling to match theme
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#f6e7bf',
                title_font_color='#f6e7bf'
            )
            st.plotly_chart(fig, use_container_width=True)

    st.caption("Lift > 1.2 = genuinely associated. Confidence = reliability of the rule.")


def main() -> None:
    theme = get_theme()
    st.set_page_config(
        page_title=theme["title"],
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_css(theme)

    primary, linkedin_validation = load_dashboard_data()
    filtered_primary = apply_filters(primary)

    # Load association rules for MBA tab
    rules_file = find_data_file("mba_rules.csv")
    if rules_file:
        try:
            rules = load_mba_rules_cached(rules_file)
        except Exception as exc:
            st.warning(f"Failed to load association rules: {exc}")
            rules = pd.DataFrame()
    else:
        rules = pd.DataFrame()

    if filtered_primary.empty:
        st.error("The current filters return no rows. Reset the filters in the sidebar.")
        st.stop()

    render_header(theme, filtered_primary)
    st.caption(
        "Primary source: cleaned 2020 to 2026 skill table. Validation source: LinkedIn sample. The brand name and color system are centralized so you can swap them later."
    )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Trend Explorer", "Skill Heatmap", "Skill Gap Advisor", "🛒 Skill Associations"])

    with tab1:
        render_overview_tab(filtered_primary, theme)

    with tab2:
        render_trend_tab(filtered_primary, theme)

    with tab3:
        render_heatmap_tab(filtered_primary, theme)

    with tab4:
        render_gap_advisor_tab(filtered_primary, theme, mba_rules=rules)

    with tab5:
        render_market_basket_panel(rules)


if __name__ == "__main__":
    main()
