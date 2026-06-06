# ARCHITECTURE.md
# Skill Trend Analysis — System Architecture Blueprint
**Candidate:** Soumyadeep Nath | **Version:** 1.0 | **Status:** Frozen Pre-Implementation

---

## PURPOSE

This document is the **single source of architectural truth** for the Skill Trend
Analysis project. It defines the complete system design — data flow, component
boundaries, module interfaces, folder structure, and technology decisions — before
a single line of implementation code is written.

An AI coding agent reading this file must NOT deviate from the decisions made here
without creating a new versioned section documenting the reason for the change.

---

## SYSTEM OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SKILL TREND ANALYSIS SYSTEM                      │
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │  DATA LAYER  │───▶│ ANALYSIS     │───▶│  PRESENTATION LAYER  │  │
│  │              │    │ LAYER        │    │                      │  │
│  │ • Kaggle CSV │    │ • EDA        │    │ • Streamlit App      │  │
│  │ • LinkedIn   │    │ • NLP        │    │ • Power BI Dashboard │  │
│  │   Sample     │    │ • Time Series│    │ • GitHub README      │  │
│  └──────────────┘    │ • Stats      │    └──────────────────────┘  │
│                      └──────┬───────┘                              │
│                             │                                       │
│                      ┌──────▼───────┐                              │
│                      │  GENAI LAYER │                              │
│                      │              │                              │
│                      │ • Groq API   │                              │
│                      │ • Skill Gap  │                              │
│                      │   Advisor    │                              │
│                      └──────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## TECHNOLOGY DECISIONS (FROZEN)

| Component | Technology | Decision Rationale |
|---|---|---|
| Language | Python 3.10+ | Universal DS standard; Colab native |
| Notebook Environment | Google Colab | Free GPU/RAM; built-in GitHub save |
| Data Manipulation | Pandas | Industry standard for tabular data |
| Statistical Testing | SciPy | Chi-square, z-tests; IIT Roorkee aligned |
| Static Visualization | Matplotlib + Seaborn | Publication-quality; poster/BI export |
| Interactive Visualization | Plotly | Web-native; Streamlit compatible |
| NLP / Text Mining | Python string ops + regex | Beginner-appropriate; no NLTK overhead |
| LLM API | Groq (LLaMA 3.3 70B) | Already integrated in AlignResume |
| Web App Framework | Streamlit | Fastest Python-to-web pipeline |
| BI Dashboard | Power BI Desktop | Identified skill gap; portfolio signal |
| Version Control | GitHub | CI/CD ready; portfolio visible |
| Deployment | Streamlit Cloud | Free tier; direct GitHub integration |
| Primary Dataset | Kaggle: AI Jobs 2020–2026 | Clean, structured, time-series ready |
| Secondary Dataset | LinkedIn Jobs 2024 (10k sample) | Validation only; raw, beginner caution |

**LOCKED:** No technology substitutions without creating a versioned ADR section below.

---

## DATA FLOW ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────────┐
│ INGESTION                                                           │
│                                                                     │
│  Kaggle CSV ──────────────────────────────────────────────────────┐ │
│  (50k rows, 2020-2026)                                            │ │
│                                                                   │ │
│  LinkedIn CSV ─────────────────────────────────────────────────┐  │ │
│  (10k sample, 2024 only)                                       │  │ │
└────────────────────────────────────────────────────────────────┼──┘ │
                                                                 │
┌────────────────────────────────────────────────────────────────▼────┐
│ CLEANING & PREPROCESSING                                            │
│                                                                     │
│  Raw Text ──▶ Null Removal ──▶ Date Parsing ──▶ Skill Extraction   │
│                                                                     │
│  skill_list[100+ skills] ──▶ extract_skills(text) ──▶ explode()    │
│                                                                     │
│  Output: primary_skills_long.csv  (one row per skill mention)      │
│  Output: linkedin_validation.csv  (same schema, secondary source)  │
└─────────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│ ANALYSIS LAYER                                                      │
│                                                                     │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ Frequency       │  │ Time Series      │  │ Co-occurrence    │  │
│  │ Analysis        │  │ Trend Analysis   │  │ Matrix           │  │
│  │                 │  │                  │  │                  │  │
│  │ value_counts()  │  │ groupby(month)   │  │ combinations()   │  │
│  │ → bar chart     │  │ → line chart     │  │ → heatmap        │  │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘  │
│                                                                     │
│  ┌─────────────────┐  ┌──────────────────────────────────────────┐ │
│  │ Experience      │  │ Hypothesis Testing                       │ │
│  │ Level Analysis  │  │                                          │ │
│  │                 │  │ H₀: LLM demand unchanged 2022 vs 2024   │ │
│  │ crosstab()      │  │ Test: chi2_contingency (SciPy)          │ │
│  │ → grouped bar   │  │ Output: p_value + markdown conclusion   │ │
│  └─────────────────┘  └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│ GENAI LAYER                                                         │
│                                                                     │
│  trending_skills ──┐                                               │
│                    ├──▶ skill_gap_advisor.py ──▶ Groq API          │
│  user_skills ──────┘   (LLaMA 3.3 70B)           │                │
│                                                    ▼               │
│                                          Natural language advice   │
│                                          "You're missing X, Y, Z"  │
└─────────────────────────────────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│ PRESENTATION LAYER                                                  │
│                                                                     │
│  ┌────────────────────────┐    ┌──────────────────────────────────┐ │
│  │ STREAMLIT APP (app.py) │    │ POWER BI DASHBOARD (.pbix)       │ │
│  │                        │    │                                  │ │
│  │ Panel 1: Overview      │    │ Visual 1: Skill Frequency Bar    │ │
│  │ Panel 2: Trend Explorer│    │ Visual 2: Trend Line Chart       │ │
│  │ Panel 3: Heatmap       │    │ Visual 3: Experience Matrix      │ │
│  │ Panel 4: Gap Advisor   │    │ Visual 4: KPI Cards              │ │
│  │                        │    │                                  │ │
│  │ Deploy: Streamlit Cloud│    │ Deploy: Power BI Service         │ │
│  └────────────────────────┘    └──────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## MODULE INTERFACE DEFINITIONS

### Module: `src/skill_extractor.py`
```python
# Public interface — do NOT change function signatures without updating ARCHITECTURE.md

def build_skill_list() -> dict[str, list[str]]:
    """Returns categorized skill dictionary: {category: [skill1, skill2, ...]}"""
    pass

def extract_skills(text: str, skill_list: list[str]) -> list[str]:
    """
    Extracts skills from free text using case-insensitive matching.
    Args:
        text: Raw job description text
        skill_list: Flat list of skill strings to search for
    Returns:
        List of matched skill strings (may be empty)
    """
    pass

def build_long_format(df: pd.DataFrame, skill_col: str) -> pd.DataFrame:
    """
    Explodes skills_found column into one-row-per-skill format.
    Args:
        df: DataFrame with 'skills_found' column (list of strings)
        skill_col: Column name containing skill lists
    Returns:
        Exploded DataFrame with one skill per row
    """
    pass
```

### Module: `src/skill_gap_advisor.py`
```python
def get_trending_skills(df_exploded: pd.DataFrame, top_n: int = 20) -> list[str]:
    """Returns top N trending skills from the analyzed dataset."""
    pass

def validate_user_input(user_input: str) -> tuple[bool, list[str] | str]:
    """
    Validates user-provided skill list.
    Returns: (is_valid: bool, valid_skills OR error_message)
    """
    pass

def get_skill_gap_advice(user_skills: list[str], trending_skills: list[str]) -> str:
    """
    Calls Groq API with structured prompt.
    Returns natural language advice string.
    Raises: EnvironmentError if API key missing
            RuntimeError if API call fails after 1 retry
    """
    pass
```

### Module: `app.py` (Streamlit)
```python
# Four panels — each implemented as a separate function:

def render_overview_panel(df_exploded: pd.DataFrame) -> None:
    """Top 20 skills bar chart + summary KPIs"""
    pass

def render_trend_panel(df_exploded: pd.DataFrame) -> None:
    """Skill dropdown + time series line chart"""
    pass

def render_heatmap_panel(df_primary: pd.DataFrame) -> None:
    """Co-occurrence heatmap for top 15 skills"""
    pass

def render_gap_advisor_panel(df_exploded: pd.DataFrame) -> None:
    """Text input + Groq API call + advice output"""
    pass
```

---

## FOLDER STRUCTURE (CANONICAL)

```
skill-trend-analysis/                   ← GitHub repo root
│
├── notebooks/                          ← All Colab notebooks
│   ├── 01_data_collection.ipynb
│   ├── 02_data_cleaning.ipynb
│   ├── 03_eda_analysis.ipynb
│   └── 04_visualization_report.ipynb
│
├── src/                                ← Reusable Python modules
│   ├── __init__.py
│   ├── skill_extractor.py              ← Skill parsing & extraction
│   └── skill_gap_advisor.py            ← Groq API integration
│
├── data/
│   ├── raw/                            ← gitignored (large files)
│   └── clean/
│       ├── primary_skills_long.csv     ← One row per skill mention
│       └── linkedin_validation.csv     ← Secondary validation data
│
├── assets/
│   └── charts/                         ← Exported PNG visualizations
│       ├── skill_frequency.png
│       ├── skill_trend.png
│       ├── skill_cooccurrence.png
│       ├── skill_by_level.png
│       └── skill_wordcloud.png
│
├── dashboards/
│   ├── skill_trend_powerbi.pbix        ← Power BI source file
│   └── skill_trend_dashboard.pdf       ← Exported PDF for portfolio
│
├── docs/
│   └── problem_statement.md
│
├── app.py                              ← Streamlit application entry point
├── requirements.txt                    ← All Python dependencies
├── .gitignore                          ← Excludes data/raw/, *.csv >10MB
├── README.md                           ← Portfolio-facing documentation
├── ARCHITECTURE.md                     ← This file
├── MISSION_PLAN.md                     ← Agentic execution blueprint
├── IMPLEMENTATION_PLAN.md              ← Phase-wise task checklist
├── EVALUATION_PLAN.md                  ← Testing & grading criteria
└── EDGE_CASE_PLAN.md                   ← Failure handling & fallbacks
```

---

## ARCHITECTURE DECISION LOG (ADR)

### ADR-001 — Use String Matching for Skill Extraction (not NLP models)
```
Date: Project start
Decision: Use case-insensitive string matching against a predefined skill list
          instead of spaCy NER or transformer-based extraction.
Reason:   Beginner-appropriate. Sufficient for structured job posting data.
          Avoids GPU dependency in Colab free tier.
          AlignResume uses the same pattern — code can be reused.
Trade-off: Will miss synonym variations (e.g., "ML" vs "Machine Learning").
           Mitigation: Add both variants to skill_list.
Status:   ACCEPTED
```

### ADR-002 — Groq API Over OpenAI for GenAI Feature
```
Date: Project start
Decision: Use Groq API (LLaMA 3.3 70B) for Skill Gap Advisor
Reason:   Already integrated in AlignResume — reuse existing code pattern.
          Free tier available. Faster inference than OpenAI.
Trade-off: LLaMA 3.3 70B slightly less capable than GPT-4o for nuanced reasoning.
           Acceptable for skill gap narration use case.
Status:   ACCEPTED
```

### ADR-003 — Streamlit Over Plotly Dash for Web App
```
Date: Project start
Decision: Use Streamlit for the interactive dashboard
Reason:   Beginner-friendly. Pure Python, no HTML/CSS required.
          Free deployment on Streamlit Cloud.
          Faster to build than Dash for a solo developer.
Trade-off: Less customizable than Dash. No multi-page routing without st.pages.
Status:   ACCEPTED
```

---

## STATE TRANSITION MAP

```
CURRENT STATE                    TARGET STATE
─────────────────────────────────────────────────────────────────────
Raw CSVs on Kaggle          ──▶  Clean DataFrames in Colab
                                 (primary_skills_long.csv)

Colab Notebooks (local)     ──▶  Committed to GitHub repo
                                 (organized folder structure)

Static chart images         ──▶  Interactive Plotly charts in Streamlit
                                 (embedded in live app)

AlignResume Groq API code   ──▶  Refactored into skill_gap_advisor.py
                                 (standalone, reusable module)

No BI presence              ──▶  Power BI dashboard published
                                 (separate portfolio artifact)

No second portfolio project ──▶  Live Streamlit app at public URL
                                 (portfolio.sdn9300.github.io updated)
```
