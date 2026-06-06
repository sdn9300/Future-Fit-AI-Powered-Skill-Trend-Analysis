# MISSION_PLAN.md
# Skill Trend Analysis — Agentic Execution Mission Plan
**Candidate:** Soumyadeep Nath | **Version:** 1.0 | **Mode:** Plan-Implement-Validate (PIV)

---

## PRIME DIRECTIVE

This document governs how an autonomous AI coding agent — or the developer operating
with agentic discipline — executes the Skill Trend Analysis project.

**The core rule is: PLAN → IMPLEMENT → VALIDATE. In that order. Always.**

No implementation step begins until its plan entry is written and approved.
No plan entry is closed until its validation gate passes.
The agent must NEVER skip a validation gate to accelerate progress.

---

## MISSION STATEMENT

```
MISSION:   Build a portfolio-grade Skill Trend Analysis project that demonstrates
           Time Series Analysis, NLP/Text Mining, Statistical Reasoning,
           and GenAI integration to a hiring manager in Data Science / AI.

SUCCESS:   Live Streamlit app + Power BI dashboard + clean GitHub repo
           with a documented, reproducible analysis pipeline.

CONSTRAINT: Zero fabrication. Every insight must be backed by real data.
            Every code module must pass its validation gate before merge.
```

---

## HOW TO READ THIS DOCUMENT

Each mission step is structured as:

```
STEP [N] — [PHASE NAME]
───────────────────────
STATUS:    [ ] PENDING | [P] PLANNED | [I] IN PROGRESS | [V] VALIDATED | [✓] COMPLETE
PREREQ:    Step(s) that must be COMPLETE before this step can begin
GOAL:      Exact outcome this step produces
PLAN:      What will be built / written / run
IMPLEMENT: Agent execution notes
VALIDATE:  Exact pass/fail check that closes this step
FREEZE:    Architectural decisions locked by this step
```

---

## MISSION STEPS

---

### STEP 0 — MISSION FREEZE
```
STATUS:    [ ] PENDING
PREREQ:    None — this is always the first step
GOAL:      Lock the problem statement and research questions before any code runs
PLAN:
  - Read ARCHITECTURE.md completely
  - Read IMPLEMENTATION_PLAN.md completely
  - Confirm the 5 research questions are clear
  - Create /docs/problem_statement.md

IMPLEMENT:
  Agent action: Create problem_statement.md with this exact structure:
  ---
  # Problem Statement
  ## What
  ## Why
  ## Who
  ## How Success Looks
  ## Research Questions (numbered 1–5)
  ---

VALIDATE:
  ✅ PASS: problem_statement.md exists and contains all 5 sections + 5 RQs
  ❌ FAIL: Any section missing → rewrite before proceeding

FREEZE:
  - Research questions are LOCKED after this step
  - No new research questions added mid-project without creating STEP 0-ADDENDUM
```

---

### STEP 1 — ENVIRONMENT INITIALIZATION
```
STATUS:    [ ] PENDING
PREREQ:    STEP 0 COMPLETE
GOAL:      Reproducible, dependency-complete Colab environment
PLAN:
  - Open Google Colab
  - Install all required libraries
  - Verify imports succeed without error
  - Create GitHub repo: skill-trend-analysis
  - Commit empty folder structure

IMPLEMENT:
  # Run in Colab Cell 1:
  !pip install pandas numpy matplotlib seaborn plotly wordcloud groq scipy streamlit

  # Run in Colab Cell 2 — verify imports:
  import pandas as pd
  import numpy as np
  import matplotlib.pyplot as plt
  import seaborn as sns
  import plotly.express as px
  from scipy import stats
  from wordcloud import WordCloud
  from groq import Groq
  print("✅ All imports successful")

VALIDATE:
  ✅ PASS: Cell 2 prints "✅ All imports successful" with no errors
  ❌ FAIL: Any ImportError → install the specific package and retry
           Do NOT proceed to Step 2 with a broken environment

FREEZE:
  - requirements.txt is written and committed after this step
  - Library versions are pinned (use pip freeze >> requirements.txt)
```

---

### STEP 2 — DATA ACQUISITION
```
STATUS:    [ ] PENDING
PREREQ:    STEP 1 COMPLETE
GOAL:      Both datasets loaded into Colab with schema documented
PLAN:
  - Download primary dataset from Kaggle
  - Load primary dataset and document all columns
  - Download secondary dataset from Kaggle
  - Load 10k sample of secondary dataset
  - Document schema differences between both datasets

IMPLEMENT:
  df_primary = pd.read_csv("ai_jobs_market_2020_2026.csv")
  df_secondary = pd.read_csv("linkedin_jobs_2024.csv", nrows=10000)

  # Document schema:
  print("PRIMARY:", df_primary.shape, df_primary.columns.tolist())
  print("SECONDARY:", df_secondary.shape, df_secondary.columns.tolist())

VALIDATE:
  ✅ PASS: df_primary.shape[0] >= 40000 AND skills column exists
           df_secondary.shape[0] == 10000
  ❌ FAIL: Shape mismatch or FileNotFoundError
           → See EDGE_CASE_PLAN.md: Cases 1.1, 1.2, 1.3

FREEZE:
  - Column names for both datasets are documented and fixed
  - If column names differ from expected, update ARCHITECTURE.md
    before writing any extraction code
```

---

### STEP 3 — DATA CLEANING
```
STATUS:    [ ] PENDING
PREREQ:    STEP 2 COMPLETE
GOAL:      Clean, exploded DataFrame: primary_skills_long.csv
PLAN:
  Phase A — Null removal and date parsing
  Phase B — Skill extraction using string matching
  Phase C — Explode to long format
  Phase D — Save clean CSV

IMPLEMENT:
  Phase A:
    df = df_primary.dropna(subset=['skills_required'])
    df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
    df = df.dropna(subset=['date_posted'])
    df['year'] = df['date_posted'].dt.year
    df['month'] = df['date_posted'].dt.to_period('M')

  Phase B:
    from src.skill_extractor import build_skill_list, extract_skills
    skill_list = build_skill_list()
    all_skills = [s for skills in skill_list.values() for s in skills]
    df['skills_found'] = df['skills_required'].apply(
        lambda x: extract_skills(x, all_skills)
    )

  Phase C:
    df_exploded = df.explode('skills_found').dropna(subset=['skills_found'])

  Phase D:
    df_exploded.to_csv("data/clean/primary_skills_long.csv", index=False)

VALIDATE:
  ✅ PASS: All assertions in EVALUATION_PLAN.md Tests 2.1–2.4 pass
           Specifically: extract_skills unit test on known input passes
  ❌ FAIL: Zero skills extracted → See EDGE_CASE_PLAN.md Case 2.3
           All rows dropped → See EDGE_CASE_PLAN.md Case 2.1

AGENT HALT CONDITION:
  If df_exploded.shape[0] == 0: HALT. Do not proceed.
  Write error to console and wait for human review.

FREEZE:
  - skill_list dictionary is LOCKED after this step
  - Adding new skills is permitted but removing existing ones requires
    re-running all downstream steps
```

---

### STEP 4 — EXPLORATORY DATA ANALYSIS
```
STATUS:    [ ] PENDING
PREREQ:    STEP 3 COMPLETE + primary_skills_long.csv exists
GOAL:      All 5 research questions answered with code + visualization + markdown interpretation
PLAN:
  RQ1: Skill frequency analysis → horizontal bar chart
  RQ2: Skill trend over time → Plotly multi-line chart
  RQ3: Co-occurrence matrix → Seaborn heatmap
  RQ4: Skill by experience level → grouped bar chart
  RQ5: Hypothesis test → chi-square + p-value + written conclusion

IMPLEMENT:
  [See IMPLEMENTATION_PLAN.md Phase 3 for detailed code]

  Agent rule: Every code cell that produces a visualization MUST be
  followed immediately by a markdown cell containing:
  - Finding title (not generic label)
  - One sentence interpretation
  - Connection to the research question it answers

VALIDATE:
  ✅ PASS: All 5 RQs have code + non-empty output + markdown interpretation
           Hypothesis test produces a float p_value between 0.0 and 1.0
           trend['month'].nunique() >= 24
  ❌ FAIL: Any RQ has no code cell → add before proceeding
           p_value is NaN or outside [0,1] → See EDGE_CASE_PLAN.md Case 3.2

FREEZE:
  - The 5 key insights (finding titles) used in charts are LOCKED
  - These same insights must appear verbatim in README.md and LinkedIn post
```

---

### STEP 5 — VISUALIZATION FINALIZATION
```
STATUS:    [ ] PENDING
PREREQ:    STEP 4 COMPLETE
GOAL:      5 publication-ready PNG charts exported to assets/charts/
PLAN:
  - Polish all 5 charts (font size, color palette, finding titles)
  - Export each as PNG at 150 DPI
  - Verify all files exist at correct paths

IMPLEMENT:
  import os
  os.makedirs("assets/charts", exist_ok=True)

  # For each chart:
  fig.savefig("assets/charts/skill_frequency.png", dpi=150, bbox_inches='tight')

VALIDATE:
  ✅ PASS: All 5 PNG files exist (Tests 4.1–4.3 in EVALUATION_PLAN.md pass)
           All 5 chart titles follow finding format (contain a specific claim)
  ❌ FAIL: Any chart missing → re-export
           Chart title is generic → rewrite title before export

FREEZE:
  - Chart filenames are LOCKED (README.md uses these exact paths for screenshots)
```

---

### STEP 6 — GENAI MODULE IMPLEMENTATION
```
STATUS:    [ ] PENDING
PREREQ:    STEP 4 COMPLETE (trending skills data available)
GOAL:      Working skill_gap_advisor.py that passes all 4 GenAI tests
PLAN:
  - Create src/skill_gap_advisor.py
  - Implement validate_user_input()
  - Implement get_trending_skills()
  - Implement get_skill_gap_advice()
  - Test with 5 different inputs

IMPLEMENT:
  [See IMPLEMENTATION_PLAN.md Phase 5 + ARCHITECTURE.md Module Interfaces]

  Test 1: "Python, SQL, Pandas"             (strong base, missing GenAI)
  Test 2: "Excel, PowerPoint"               (weak profile, many gaps)
  Test 3: "TensorFlow, PyTorch, CUDA"       (deep learning specialist)
  Test 4: ""                                (empty — should trigger validation error)
  Test 5: "asdfghjkl"                       (nonsense — should trigger validation error)

VALIDATE:
  ✅ PASS: Tests 1–3 return coherent, skill-specific advice (>50 chars)
           Tests 4–5 trigger validation error messages, NOT API calls
           No test crashes with an unhandled exception
  ❌ FAIL: API key error → See EDGE_CASE_PLAN.md Case 5.1
           Empty response on valid input → See EDGE_CASE_PLAN.md Case 5.3

AGENT HALT CONDITION:
  If GROQ_API_KEY is not set: HALT. Do not write placeholder key.
  Print instructions for setting the key and wait for human action.
```

---

### STEP 7 — STREAMLIT APP CONSTRUCTION
```
STATUS:    [ ] PENDING
PREREQ:    STEPS 4, 5, 6 ALL COMPLETE
GOAL:      Working app.py with 4 panels, running locally without errors
PLAN:
  - Scaffold app.py with st.tabs() structure
  - Implement render_overview_panel()
  - Implement render_trend_panel()
  - Implement render_heatmap_panel()
  - Implement render_gap_advisor_panel()
  - Load data with @st.cache_data

IMPLEMENT:
  import streamlit as st
  import pandas as pd
  from src.skill_gap_advisor import get_skill_gap_advice

  @st.cache_data
  def load_data():
      return pd.read_csv("data/clean/primary_skills_long.csv")

  df = load_data()
  tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Trends", "Co-occurrence", "Skill Gap Advisor"])

  with tab1: render_overview_panel(df)
  with tab2: render_trend_panel(df)
  with tab3: render_heatmap_panel(df)
  with tab4: render_gap_advisor_panel(df)

VALIDATE:
  ✅ PASS: streamlit run app.py opens at localhost:8501 with no traceback
           All 4 tabs render with data (not empty/None)
           Skill Gap Advisor returns advice for "Python, SQL" input
  ❌ FAIL: Any tab blank or erroring → fix before proceeding to Step 8

FREEZE:
  - app.py panel structure is LOCKED
  - Adding new panels requires updating ARCHITECTURE.md first
```

---

### STEP 8 — DEPLOYMENT
```
STATUS:    [ ] PENDING
PREREQ:    STEP 7 COMPLETE + GitHub repo up to date
GOAL:      Live app accessible at public Streamlit Cloud URL
PLAN:
  - Push final app.py and requirements.txt to GitHub main branch
  - Connect repo to streamlit.io
  - Set GROQ_API_KEY in Streamlit Cloud secrets
  - Verify live URL in incognito browser

VALIDATE:
  ✅ PASS: App loads at public URL within 30 seconds (incognito test)
           Skill Gap Advisor works on live deployment
  ❌ FAIL: See EDGE_CASE_PLAN.md Cases 6.1, 6.2, 6.3

FREEZE:
  - Live app URL is recorded here: ________________________________
  - This URL is used in README.md, LinkedIn post, and portfolio site
```

---

### STEP 9 — POWER BI DASHBOARD
```
STATUS:    [ ] PENDING
PREREQ:    STEP 3 COMPLETE (primary_skills_long.csv available)
GOAL:      Power BI dashboard with 4 visuals, exported as PDF
PLAN:
  - Import primary_skills_long.csv into Power BI Desktop
  - Build 4 visuals (bar, line, matrix, KPI cards)
  - Add year slicer
  - Publish to Power BI Service
  - Export as PDF

VALIDATE:
  ✅ PASS: All 4 visuals render with data
           Year slicer updates all visuals
           PDF exported to /dashboards/
  ❌ FAIL: Any visual shows "No data" → check data import step

NOTE: This step can run IN PARALLEL with Steps 6–8 (independent of Streamlit)
```

---

### STEP 10 — DOCUMENTATION & PORTFOLIO PACKAGING
```
STATUS:    [ ] PENDING
PREREQ:    ALL STEPS 1–9 COMPLETE
GOAL:      Recruiter-ready GitHub repo + LinkedIn post draft
PLAN:
  - Write README.md (all 6 required sections)
  - Verify ARCHITECTURE.md is up to date
  - Final commit with clean structure
  - Draft LinkedIn post using 3 LOCKED insights from Step 4
  - Update portfolio site: sdn9300.github.io

VALIDATE:
  ✅ PASS: All tests in EVALUATION_PLAN.md Tests 7.1–7.2 pass
           README contains actual numbers from the analysis (not placeholders)
           Repo folder structure matches ARCHITECTURE.md canonical layout
  ❌ FAIL: Any README section contains "[placeholder]" text → fill before publish
```

---

## AGENT BEHAVIORAL RULES

### Rule 1 — PIV Loop Enforcement
```
The agent MUST complete: Plan → Implement → Validate for EACH step.
Skipping Validate to move faster is PROHIBITED.
If a Validate gate fails, the agent returns to Implement — not to the next Step.
```

### Rule 2 — Halt Conditions
```
The agent MUST halt and notify the human when:
- df_exploded.shape[0] == 0  (cleaning destroyed all data)
- GROQ_API_KEY is not set    (cannot proceed with GenAI step)
- Any test assertion raises an AssertionError with ❌ FAIL label
- A file required by a downstream step does not exist
```

### Rule 3 — No Fabrication
```
The agent MUST NOT:
- Insert placeholder numbers into README.md ("Python appears in ~X% of jobs")
- Generate synthetic data to fill gaps in the dataset
- Claim a visualization "shows" an insight that is not visible in the actual chart
- Report a hypothesis test conclusion without running the actual scipy test
```

### Rule 4 — Freeze Respect
```
All FREEZE entries are architectural constraints.
The agent MUST update ARCHITECTURE.md BEFORE making any change to a frozen decision.
A frozen decision changed without documentation is a plan violation.
```

### Rule 5 — Sequential Step Execution
```
Steps must be executed in order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
Exception: Step 9 (Power BI) may run in parallel with Steps 6–8.
No step begins before its PREREQ is marked COMPLETE.
```

---

## MISSION STATUS DASHBOARD

```
STEP 0  — Problem Definition         [ ] PENDING
STEP 1  — Environment Setup          [ ] PENDING
STEP 2  — Data Acquisition           [ ] PENDING
STEP 3  — Data Cleaning              [ ] PENDING
STEP 4  — EDA                        [ ] PENDING
STEP 5  — Visualization              [ ] PENDING
STEP 6  — GenAI Module               [ ] PENDING
STEP 7  — Streamlit App              [ ] PENDING
STEP 8  — Deployment                 [ ] PENDING
STEP 9  — Power BI Dashboard         [ ] PENDING
STEP 10 — Documentation              [ ] PENDING

OVERALL MISSION STATUS: ⬜ NOT STARTED
```

*Update this dashboard at the start of each working session.*
*Mark: [P] Planned | [I] In Progress | [V] Validated | [✓] Complete*

---

## LOCKED TECHNICAL DECISIONS SUMMARY

| Decision | Value | Locked In Step |
|---|---|---|
| Primary dataset | Global AI Jobs 2020–2026 (Kaggle) | Step 2 |
| Secondary dataset | LinkedIn Jobs 2024 (10k sample only) | Step 2 |
| Skill extraction method | String matching against predefined list | Step 3 |
| LLM provider | Groq API (LLaMA 3.3 70B) | Step 6 |
| Web framework | Streamlit | Step 7 |
| Deployment platform | Streamlit Cloud | Step 8 |
| BI tool | Power BI Desktop + Service | Step 9 |
| 5 key insights | From Step 4 EDA findings | Step 4 |
| Live app URL | TBD — fill after Step 8 | Step 8 |
