# IMPLEMENTATION_PLAN.md
# Skill Trend Analysis — Detailed Phase-Wise Implementation Plan
**Candidate:** Soumyadeep Nath | **Level:** Beginner Data Scientist
**Stack:** Python · Pandas · Plotly · Seaborn · Streamlit · Groq API · Google Colab · GitHub

---

## OVERVIEW

| Attribute | Detail |
|---|---|
| Project Type | Time Series Analysis + NLP/Text Mining + Clustering (optional) |
| Primary Dataset | Global AI & Data Science Job Market 2020–2026 (50k records, Kaggle) |
| Secondary Dataset | 1.3M LinkedIn Jobs & Skills 2024 (validation layer only) |
| Total Duration | 22 days (4 weeks) |
| Final Deliverables | Colab Notebooks · Streamlit App · Power BI/Tableau Dashboard · GitHub Repo |

---

## PHASE 0 — Problem Definition
**Duration:** Day 1
**Goal:** Freeze the problem statement before touching any data.

### Tasks
- [ ] Answer the 4 framing questions in writing:
  - **What:** Analyze which DS/AI/Analytics skills are trending in job postings over time
  - **Why:** Help job seekers and students prioritize what to learn next
  - **Who:** Students, career switchers, recruiters, hiring managers
  - **How:** Interactive dashboard + 3 data-backed actionable insights
- [ ] Define 5 core research questions:
  1. Which skills appear most frequently across all postings?
  2. Which skills are rising vs. declining (2020–2026)?
  3. Which skills co-occur most often in the same job posting?
  4. How does skill demand differ by experience level (fresher vs. senior)?
  5. Are GenAI skills (LLM, RAG, Prompt Engineering) a statistically significant trend post-2023?
- [ ] Write `problem_statement.md` and commit to GitHub repo

### Deliverable
```
/docs/problem_statement.md
```

---

## PHASE 1 — Data Collection & Environment Setup
**Duration:** Days 2–4
**Goal:** Acquire both datasets and configure the Colab environment.

### Tasks

#### 1.1 — Environment Setup (Day 2)
- [ ] Create new Google Colab notebook: `01_data_collection.ipynb`
- [ ] Install required libraries:
  ```python
  !pip install pandas numpy matplotlib seaborn plotly wordcloud
  !pip install streamlit groq kaggle
  ```
- [ ] Create GitHub repo: `skill-trend-analysis`
- [ ] Configure Colab → GitHub save (File → Save a copy in GitHub)

#### 1.2 — Primary Dataset Acquisition (Day 3)
- [ ] Download from Kaggle: **Global AI & Data Science Job Market 2020–2026**
- [ ] Load into Colab and inspect:
  ```python
  import pandas as pd
  df_primary = pd.read_csv("ai_jobs_market_2020_2026.csv")
  print(df_primary.shape)
  print(df_primary.columns.tolist())
  print(df_primary.head())
  ```
- [ ] Document all column names, data types, and null counts

#### 1.3 — Secondary Dataset Acquisition (Day 4)
- [ ] Download from Kaggle: **1.3M LinkedIn Jobs & Skills 2024**
- [ ] Load a sample (10k rows) for initial inspection — do NOT load all 1.3M at once
  ```python
  df_secondary = pd.read_csv("linkedin_jobs_2024.csv", nrows=10000)
  ```
- [ ] Identify which columns overlap with primary dataset
- [ ] Document schema differences

### Deliverable
```
/notebooks/01_data_collection.ipynb
/data/raw/ai_jobs_market_2020_2026.csv
/data/raw/linkedin_jobs_sample_10k.csv
```

---

## PHASE 2 — Data Cleaning & Preprocessing
**Duration:** Days 5–7
**Goal:** Produce one clean, analysis-ready DataFrame.

### Tasks

#### 2.1 — Primary Dataset Cleaning (Day 5)
- [ ] Create notebook: `02_data_cleaning.ipynb`
- [ ] Check and handle missing values:
  ```python
  print(df_primary.isnull().sum())
  df_primary.dropna(subset=['skills_required'], inplace=True)
  df_primary['experience_level'].fillna('Not Specified', inplace=True)
  ```
- [ ] Parse and standardize date column:
  ```python
  df_primary['date_posted'] = pd.to_datetime(df_primary['date_posted'])
  df_primary['year'] = df_primary['date_posted'].dt.year
  df_primary['month'] = df_primary['date_posted'].dt.to_period('M')
  df_primary['quarter'] = df_primary['date_posted'].dt.to_period('Q')
  ```
- [ ] Standardize text columns (lowercase, strip whitespace)
- [ ] Remove duplicate rows

#### 2.2 — Skill Extraction (Day 6)
- [ ] Define master skill dictionary (100+ skills across categories):
  ```python
  skill_categories = {
      "Languages": ["Python", "SQL", "R", "Java", "Scala", "Julia"],
      "ML/AI": ["Machine Learning", "Deep Learning", "NLP", "Computer Vision",
                "LLM", "RAG", "Prompt Engineering", "TensorFlow", "PyTorch"],
      "Data Tools": ["Pandas", "NumPy", "Spark", "dbt", "Airflow"],
      "Visualization": ["Tableau", "Power BI", "Matplotlib", "Plotly", "Seaborn"],
      "Cloud": ["AWS", "GCP", "Azure", "Databricks", "Snowflake"],
      "Other": ["Excel", "Git", "Docker", "FastAPI", "MLflow"]
  }
  ```
- [ ] Build skill extraction function:
  ```python
  all_skills = [s for skills in skill_categories.values() for s in skills]

  def extract_skills(text):
      text = str(text).lower()
      return [skill for skill in all_skills if skill.lower() in text]

  df_primary['skills_found'] = df_primary['skills_required'].apply(extract_skills)
  df_primary = df_primary[df_primary['skills_found'].map(len) > 0]
  ```
- [ ] Explode to long format (one row per skill mention):
  ```python
  df_exploded = df_primary.explode('skills_found').reset_index(drop=True)
  df_exploded['skill_category'] = df_exploded['skills_found'].map(
      {s: cat for cat, skills in skill_categories.items() for s in skills}
  )
  ```

#### 2.3 — Secondary Dataset Validation Prep (Day 7)
- [ ] Apply same cleaning pipeline to LinkedIn 10k sample
- [ ] Create a `source` column: `"primary"` vs `"linkedin_validation"`
- [ ] Save both clean files:
  ```python
  df_exploded.to_csv("data/clean/primary_skills_long.csv", index=False)
  df_secondary_clean.to_csv("data/clean/linkedin_validation.csv", index=False)
  ```

### Deliverable
```
/notebooks/02_data_cleaning.ipynb
/data/clean/primary_skills_long.csv
/data/clean/linkedin_validation.csv
```

---

## PHASE 3 — Exploratory Data Analysis
**Duration:** Days 8–11
**Goal:** Answer all 5 research questions with visualizations and stats.

### Tasks

#### 3.1 — Skill Frequency Analysis (Day 8)
- [ ] Top 20 skills by total mention count
- [ ] Skill frequency by category (Languages vs. ML/AI vs. Cloud etc.)
- [ ] Visualize: Horizontal bar chart (Seaborn)

#### 3.2 — Time Series Trend Analysis (Day 9)
- [ ] Monthly skill mention counts per skill (2020–2026)
- [ ] Identify top 10 rising skills and top 5 declining skills
- [ ] Visualize: Multi-line interactive Plotly chart

#### 3.3 — Skill Co-occurrence Analysis (Day 10)
- [ ] Build co-occurrence matrix:
  ```python
  from itertools import combinations
  from collections import Counter

  co_occur = Counter()
  for skills in df_primary['skills_found']:
      for pair in combinations(sorted(skills), 2):
          co_occur[pair] += 1
  ```
- [ ] Visualize: Seaborn heatmap (top 15 skills × top 15 skills)

#### 3.4 — Skill by Experience Level (Day 10)
- [ ] Cross-tabulate: experience level × skill
- [ ] Identify which skills are fresher-friendly vs. senior-only
- [ ] Visualize: Grouped bar chart

#### 3.5 — Hypothesis Testing (Day 11)
- [ ] Frame hypothesis:
  > H₀: LLM skill demand proportion is the same in 2022 vs. 2024
- [ ] Perform chi-square test or proportion z-test:
  ```python
  from scipy import stats
  # Build observed contingency table
  # Run chi2_contingency
  # Report p-value and conclusion
  ```
- [ ] Add written interpretation in markdown cell

### Deliverable
```
/notebooks/03_eda_analysis.ipynb
```

---

## PHASE 4 — Visualization & Storytelling
**Duration:** Days 12–14
**Goal:** Produce 5 publication-ready, insight-titled charts.

### Tasks
- [ ] Create notebook: `04_visualization_report.ipynb`
- [ ] Build all 5 charts with finding-titles:

| # | Chart Title (Finding Format) | Tool |
|---|---|---|
| 1 | "Python & SQL Dominate X% of All Data Job Postings" | Seaborn |
| 2 | "LLM & Prompt Engineering Rose X% from 2022 to 2024" | Plotly |
| 3 | "Python Always Pairs with SQL: Top Skill Combos Revealed" | Seaborn Heatmap |
| 4 | "Cloud Skills Locked Behind 3+ Years Experience" | Matplotlib |
| 5 | Skill Word Cloud (visual summary) | wordcloud lib |

- [ ] Export each chart as `.png` to `/assets/charts/`
- [ ] Write one insight sentence per chart in markdown

### Deliverable
```
/notebooks/04_visualization_report.ipynb
/assets/charts/*.png
```

---

## PHASE 5 — GenAI Enhancement (Skill Gap Advisor)
**Duration:** Days 15–17
**Goal:** Build a standalone LLM-powered Skill Gap Advisor.

### Tasks
- [ ] Create `skill_gap_advisor.py`:
  ```python
  # Input: user's skill list (pasted as comma-separated text)
  # Logic: compare against top 20 trending skills from analysis
  # Output: LLM-generated narrative about the gap + what to learn next
  ```
- [ ] Connect to Groq API (LLaMA 3.3 70B) — reuse AlignResume's API pattern
- [ ] Structure the prompt:
  ```
  System: You are a career advisor specializing in Data Science job market trends.
  User: My current skills are: {user_skills}
        Top trending skills in 2024-2026 are: {trending_skills}
        Identify my skill gaps and explain concisely what I should prioritize learning.
  ```
- [ ] Test with 5 different skill inputs
- [ ] Integrate into Streamlit app (Phase 6)

### Deliverable
```
/src/skill_gap_advisor.py
```

---

## PHASE 6 — Streamlit Dashboard App
**Duration:** Days 18–20
**Goal:** Ship a live, interactive web app.

### Tasks
- [ ] Create `app.py` with these 4 panels:

| Panel | Feature |
|---|---|
| Overview | Top 20 skills bar chart + summary stats |
| Trend Explorer | Dropdown: pick skill → see time series |
| Skill Heatmap | Interactive co-occurrence matrix |
| Skill Gap Advisor | Paste your skills → get LLM gap analysis |

- [ ] Deploy to Streamlit Cloud (free):
  - Connect GitHub repo to streamlit.io
  - Set `GROQ_API_KEY` in Streamlit Secrets
- [ ] Test on mobile and desktop
- [ ] Record the live app URL

### Deliverable
```
/app.py
Live URL: https://[your-app].streamlit.app
```

---

## PHASE 6B — Power BI / Tableau Dashboard (Separate Deliverable)
**Duration:** Days 20–21 (parallel or sequential)
**Goal:** Demonstrate BI tool proficiency as a distinct portfolio artifact.

### Tasks
- [ ] Import `primary_skills_long.csv` into Power BI Desktop
- [ ] Build 4 visuals:
  1. Skill Frequency Bar Chart
  2. Skill Trend Line Chart (Year slicer)
  3. Skill by Experience Level Matrix
  4. KPI Cards: Total Jobs · Unique Skills · Top Skill
- [ ] Publish to Power BI Service (free account)
- [ ] Export as PDF for portfolio
- [ ] Note separately on resume: "Power BI Dashboard" as distinct skill signal

### Deliverable
```
/dashboards/skill_trend_powerbi.pbix
/dashboards/skill_trend_dashboard.pdf
Power BI URL: [published link]
```

---

## PHASE 7 — Documentation & Portfolio Packaging
**Duration:** Day 22
**Goal:** GitHub-ready, recruiter-readable project packaging.

### Tasks
- [ ] Write `README.md` with:
  - 2-sentence project summary
  - 3 key insights (with actual numbers from your analysis)
  - Tech stack badge row
  - Screenshots of all 5 charts
  - Live app link
  - How to run locally
- [ ] Write `ARCHITECTURE.md` (see separate document)
- [ ] Write `MISSION_PLAN.md` (see separate document)
- [ ] Final commit with clean folder structure:
  ```
  skill-trend-analysis/
  ├── notebooks/
  │   ├── 01_data_collection.ipynb
  │   ├── 02_data_cleaning.ipynb
  │   ├── 03_eda_analysis.ipynb
  │   └── 04_visualization_report.ipynb
  ├── src/
  │   └── skill_gap_advisor.py
  ├── data/
  │   ├── raw/        (gitignored if large)
  │   └── clean/
  ├── assets/charts/
  ├── dashboards/
  ├── app.py
  ├── requirements.txt
  ├── README.md
  ├── ARCHITECTURE.md
  └── MISSION_PLAN.md
  ```
- [ ] Draft LinkedIn post with 3 findings + app link

### Deliverable
```
Fully packaged GitHub repo
LinkedIn post draft
```

---

## PHASE 8 — Deployment
**Duration:** Day 23
**Goal:** Launch the Streamlit dashboard on Streamlit Cloud and capture the public URL.

### Tasks
- [ ] Confirm `app.py` and `requirements.txt` are ready for publish
- [ ] Connect the GitHub repository to Streamlit Cloud
- [ ] Add `GROQ_API_KEY` to Streamlit Cloud secrets
- [ ] Verify the live app loads in incognito mode
- [ ] Record the public Streamlit URL in the project docs and `README.md`

### Deliverable
```
Live Streamlit Cloud URL
```

### Validation
- ✅ PASS: Streamlit Cloud app loads publicly within 30 seconds and the Skill Gap Advisor works
- ❌ FAIL: Any tab errors or the live URL is inaccessible

### Notes
- Keep `.streamlit/secrets.toml` locally ignored
- Do not publish sensitive keys directly in the repository

---

## PHASE 9 — Power BI Dashboard
**Duration:** Day 21
**Goal:** Create a BI dashboard using the cleaned analysis output.

### Tasks
- [ ] Import `data/clean/primary_skills_long.csv` into Power BI Desktop
- [ ] Build four visuals: skill frequency, trend line, experience-level matrix, and KPI cards
- [ ] Add a year slicer that updates all visuals
- [ ] Publish to Power BI Service and export a PDF
- [ ] Save deliverables to `dashboards/skill_trend_powerbi.pbix` and `dashboards/skill_trend_dashboard.pdf`

### Deliverable
```
/dashboards/skill_trend_powerbi.pbix
/dashboards/skill_trend_dashboard.pdf
```

### Validation
- ✅ PASS: All visuals render with data and the year slicer updates the report
- ❌ FAIL: Any visual shows "No data"

---

## PHASE 10 — Documentation & Portfolio Packaging
**Duration:** Day 22
**Goal:** Finalize recruiter-ready project packaging and publish-ready documentation.

### Tasks
- [ ] Write `README.md` with all required sections and actual analysis numbers
- [ ] Verify `ARCHITECTURE.md` is up to date
- [ ] Confirm repository structure matches the plan
- [ ] Draft LinkedIn copy using the locked insights from EDA
- [ ] Note Phase 10 status in the mission plan and portfolio notes

### Deliverable
```
README.md
ARCHITECTURE.md
MISSION_PLAN.md
/docs/linkedin_post_draft.md
```

### Validation
- ✅ PASS: `README.md` contains actual numbers from the dataset, not placeholders
- ✅ PASS: `ARCHITECTURE.md` reflects current folder and pipeline structure
- ❌ FAIL: Any README section includes placeholder text such as "X%" or "TBD"

---

## Full Timeline

```
Week 1 (Days 01–07) → Phases 0, 1, 2   → Define · Collect · Clean
Week 2 (Days 08–11) → Phase 3           → EDA + Stats
Week 3 (Days 12–17) → Phases 4, 5       → Visualize + GenAI Layer
Week 4 (Days 18–22) → Phases 6, 6B, 7, 8, 9, 10  → App + BI + Packaging
```
