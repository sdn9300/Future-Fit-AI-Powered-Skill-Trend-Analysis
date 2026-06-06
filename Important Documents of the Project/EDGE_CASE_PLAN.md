# EDGE_CASE_PLAN.md
# Skill Trend Analysis — Agentic Coding Edge Case & Failure Handling Plan
**Candidate:** Soumyadeep Nath | **Environment:** Google Colab + Streamlit + Groq API

---

## PURPOSE

This document defines every **unexpected input, system failure, and logic trap** that
an autonomous AI agent (or the developer themselves) could encounter while building
this project — and the exact validation layer, fallback, and recovery action for each.

**Rule:** No phase should be able to crash silently. Every failure must surface a
human-readable error message and a defined recovery path.

---

## CATEGORY 1 — Data Loading & File Failures

### Edge Case 1.1 — Dataset File Not Found
```
TRIGGER: CSV path is wrong, Kaggle download failed, or file not uploaded to Colab
SYMPTOM: FileNotFoundError on pd.read_csv()

DETECTION:
try:
    df = pd.read_csv("data/raw/ai_jobs_market.csv")
except FileNotFoundError:
    print("❌ ERROR: Dataset not found. Did you upload the CSV to Colab?")
    print("📥 Download from: https://www.kaggle.com/datasets/...")
    raise SystemExit(1)

FALLBACK: Print download link and halt notebook — do NOT proceed with empty DataFrame
```

### Edge Case 1.2 — Wrong Dataset Uploaded
```
TRIGGER: User uploads salary dataset instead of job postings dataset
SYMPTOM: 'skills_required' column missing; only 'salary', 'company_size' columns present

DETECTION:
required_cols = ['skills_required', 'date_posted', 'job_title']
missing = [c for c in required_cols if c not in df.columns]
if missing:
    print(f"⚠️ WARNING: Expected columns missing: {missing}")
    print("🔍 Columns found:", df.columns.tolist())
    print("Did you load the correct dataset? Check the Kaggle source.")

FALLBACK: Print column list and ask user to verify dataset identity
```

### Edge Case 1.3 — Secondary Dataset Loaded in Full (Memory Overflow)
```
TRIGGER: Developer forgets nrows=10000 and loads all 1.3M LinkedIn rows
SYMPTOM: Colab crashes with MemoryError or RAM usage > 12GB

PREVENTION:
MAX_ROWS = 10000
df_secondary = pd.read_csv("linkedin_jobs.csv", nrows=MAX_ROWS)
assert df_secondary.shape[0] <= MAX_ROWS, \
    f"❌ ABORT: Loaded {df_secondary.shape[0]} rows. Cap at {MAX_ROWS} for Colab."

RECOVERY: Restart Colab runtime, then reload with nrows cap enforced
```

### Edge Case 1.4 — Encoding Error on CSV Load
```
TRIGGER: CSV has non-UTF-8 characters (common in international salary/job datasets)
SYMPTOM: UnicodeDecodeError

DETECTION:
try:
    df = pd.read_csv("data/raw/jobs.csv", encoding='utf-8')
except UnicodeDecodeError:
    print("⚠️ UTF-8 failed. Retrying with latin-1 encoding...")
    df = pd.read_csv("data/raw/jobs.csv", encoding='latin-1')
    print("✅ Loaded with latin-1 encoding.")
```

---

## CATEGORY 2 — Data Cleaning & Transformation Failures

### Edge Case 2.1 — All Rows Dropped After Null Filtering
```
TRIGGER: Wrong column name used in dropna() — drops entire DataFrame
SYMPTOM: df_clean.shape[0] == 0 after cleaning

DETECTION:
df_clean = df.dropna(subset=['skills_required'])
if df_clean.shape[0] == 0:
    print("❌ CRITICAL: All rows dropped. Check column name.")
    print("Available columns:", df.columns.tolist())
    print("Null counts:\n", df.isnull().sum())
    raise ValueError("Cleaning removed all rows. Abort.")

RECOVERY: Inspect actual column name. Rename column if necessary before dropna.
```

### Edge Case 2.2 — Date Parsing Fails (Mixed Date Formats)
```
TRIGGER: date_posted column has mixed formats: "2024-01-15", "Jan 15, 2024", "15/01/24"
SYMPTOM: NaT values after pd.to_datetime(), or ParserError

DETECTION:
df['date_posted'] = pd.to_datetime(df['date_posted'], errors='coerce')
nat_count = df['date_posted'].isnull().sum()
if nat_count > 0:
    pct = (nat_count / len(df)) * 100
    print(f"⚠️ WARNING: {nat_count} rows ({pct:.1f}%) have unparseable dates.")
    if pct > 20:
        print("❌ More than 20% dates unparseable. Check date column format.")
    else:
        print("✅ Acceptable loss. Proceeding after dropping NaT rows.")
        df = df.dropna(subset=['date_posted'])

FALLBACK: If >20% unparseable, try infer_datetime_format=True or manual regex parsing
```

### Edge Case 2.3 — Skill Extraction Returns All Empty Lists
```
TRIGGER: Skills column contains different formatting than expected
         (e.g., skills stored as Python list strings: "['Python', 'SQL']")
SYMPTOM: df['skills_found'].apply(len).sum() == 0

DETECTION:
total_extracted = df['skills_found'].apply(len).sum()
if total_extracted == 0:
    print("❌ CRITICAL: Zero skills extracted. Sample of skills_required column:")
    print(df['skills_required'].head(5).tolist())
    print("Check if skills are stored as: plain text / list strings / JSON")

FALLBACK:
# If stored as Python list strings, parse them:
import ast
df['skills_required'] = df['skills_required'].apply(
    lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith('[') else x
)
```

### Edge Case 2.4 — Explode Creates Infinite Rows (Nested Lists)
```
TRIGGER: skills_found contains nested lists [['Python', 'SQL'], ['R']] instead of flat lists
SYMPTOM: df_exploded has millions of rows or contains list objects instead of strings

DETECTION:
sample = df_exploded['skills_found'].iloc[0]
if isinstance(sample, list):
    print("❌ ERROR: skills_found still contains lists after explode. Flatten first.")
    df['skills_found'] = df['skills_found'].apply(
        lambda x: [i for sublist in x for i in (sublist if isinstance(sublist, list) else [sublist])]
    )
```

---

## CATEGORY 3 — Analysis & Statistics Failures

### Edge Case 3.1 — Time Series Has Only One Year of Data
```
TRIGGER: Dataset loaded but date range is only 2024–2024 (not 2020–2026 as expected)
SYMPTOM: trend['year'].nunique() == 1 — no trend visible

DETECTION:
year_range = df['year'].nunique()
if year_range < 3:
    print(f"⚠️ WARNING: Only {year_range} year(s) of data. Time series analysis is unreliable.")
    print("Date range found:", df['date_posted'].min(), "to", df['date_posted'].max())
    print("Verify you loaded the correct 2020-2026 dataset.")

FALLBACK: Proceed with available data but add a visible disclaimer note in the notebook
```

### Edge Case 3.2 — Hypothesis Test Sample Too Small
```
TRIGGER: Filtering for specific year/skill combination yields < 30 records
SYMPTOM: chi-square test runs but results are statistically invalid (n < 30)

DETECTION:
n_2022 = len(df[(df['year'] == 2022) & (df['skills_found'] == 'LLM')])
n_2024 = len(df[(df['year'] == 2024) & (df['skills_found'] == 'LLM')])
if n_2022 < 30 or n_2024 < 30:
    print(f"⚠️ WARNING: Sample sizes too small for reliable chi-square test.")
    print(f"2022 LLM mentions: {n_2022} | 2024 LLM mentions: {n_2024}")
    print("Use a different skill with higher frequency, or widen the year range.")

FALLBACK: Change hypothesis to use a higher-frequency skill like Python or SQL
```

### Edge Case 3.3 — Co-occurrence Matrix Is Empty
```
TRIGGER: Most jobs list only one skill → no pairs exist
SYMPTOM: co_occur Counter is empty or has fewer than 5 pairs

DETECTION:
if len(co_occur) < 5:
    print("⚠️ WARNING: Very few skill co-occurrences found.")
    multi_skill_jobs = df_primary[df_primary['skills_found'].apply(len) > 1]
    print(f"Jobs with >1 skill: {len(multi_skill_jobs)} of {len(df_primary)}")
    if len(multi_skill_jobs) < 100:
        print("❌ Skill extraction may have failed — most jobs showing only 1 skill.")

FALLBACK: Expand skill_list dictionary with more variations and synonyms
```

---

## CATEGORY 4 — Visualization Failures

### Edge Case 4.1 — Chart Renders Blank in Colab
```
TRIGGER: Plotly chart renders blank (common in Colab without renderer setting)
SYMPTOM: Empty box where chart should appear

DETECTION & FIX:
import plotly.io as pio
pio.renderers.default = "colab"  # Add this at top of visualization notebook

FALLBACK: Use fig.show(renderer="iframe") or export to HTML with fig.write_html()
```

### Edge Case 4.2 — Word Cloud Fails on Empty Skill Text
```
TRIGGER: skill string passed to WordCloud is empty after joining
SYMPTOM: ValueError: We need at least 1 word to plot a word cloud

DETECTION:
skill_text = " ".join(df_exploded['skills_found'].dropna().tolist())
if len(skill_text.strip()) == 0:
    print("❌ ERROR: No skill text available for word cloud.")
    print("Check df_exploded is not empty:", df_exploded.shape)
else:
    wordcloud = WordCloud(...).generate(skill_text)
```

### Edge Case 4.3 — Chart PNG Export Path Does Not Exist
```
TRIGGER: assets/charts/ directory not created before saving
SYMPTOM: FileNotFoundError on fig.savefig() or fig.write_image()

PREVENTION:
import os
os.makedirs("assets/charts", exist_ok=True)  # Always run before any export
fig.savefig("assets/charts/skill_frequency.png", dpi=150, bbox_inches='tight')
```

---

## CATEGORY 5 — GenAI / Groq API Failures

### Edge Case 5.1 — API Key Missing
```
TRIGGER: GROQ_API_KEY not set in environment or Streamlit Secrets
SYMPTOM: AuthenticationError or 401 Unauthorized

DETECTION:
import os
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise EnvironmentError(
        "❌ GROQ_API_KEY not found. "
        "In Colab: use userdata.get('GROQ_API_KEY'). "
        "In Streamlit: add to .streamlit/secrets.toml"
    )
```

### Edge Case 5.2 — API Rate Limit Exceeded
```
TRIGGER: Too many requests sent in one session
SYMPTOM: RateLimitError from Groq API

DETECTION:
import time
from groq import RateLimitError

try:
    response = client.chat.completions.create(...)
except RateLimitError:
    print("⚠️ Rate limit hit. Waiting 60 seconds...")
    time.sleep(60)
    response = client.chat.completions.create(...)  # retry once
```

### Edge Case 5.3 — LLM Returns Empty or Malformed Response
```
TRIGGER: Groq API returns an empty string or truncated JSON
SYMPTOM: response.choices[0].message.content is "" or None

DETECTION:
content = response.choices[0].message.content
if not content or len(content.strip()) < 10:
    print("⚠️ LLM returned empty response. Retrying with simplified prompt...")
    # Retry with shorter, simpler prompt
    # If retry also fails, return a default fallback message:
    return "Unable to generate advice at this time. Please try again."
```

### Edge Case 5.4 — User Inputs Nonsense into Skill Gap Advisor
```
TRIGGER: User types "asdfghjkl" or "I know everything" as their skills
SYMPTOM: LLM generates irrelevant or nonsensical advice

PREVENTION (input validation before API call):
def validate_skill_input(user_input):
    known_skills = set(all_skills)
    input_skills = [s.strip() for s in user_input.split(",")]
    valid = [s for s in input_skills if any(k.lower() in s.lower() for k in known_skills)]
    if len(valid) == 0:
        return False, "⚠️ No recognizable skills found. Please enter skills like: Python, SQL, Tableau"
    return True, valid
```

---

## CATEGORY 6 — Streamlit App Failures

### Edge Case 6.1 — App Crashes on Import (Missing Package)
```
TRIGGER: Package installed locally but not in requirements.txt → fails on Streamlit Cloud
SYMPTOM: ModuleNotFoundError on cloud deployment

PREVENTION:
# requirements.txt must include ALL packages used:
pandas
numpy
plotly
seaborn
matplotlib
wordcloud
groq
streamlit
scipy

# Always test with: pip install -r requirements.txt in a fresh environment
```

### Edge Case 6.2 — Data File Not Found in Deployed App
```
TRIGGER: app.py references local path "data/clean/primary_skills_long.csv"
         but file is not committed to GitHub (gitignored)
SYMPTOM: FileNotFoundError on Streamlit Cloud

PREVENTION:
# Option A: Commit the clean CSV (if file size < 25MB GitHub limit)
# Option B: Load from URL (Google Drive or GitHub raw link)
# Option C: Rebuild data in app.py from scratch using cached computation

@st.cache_data
def load_data():
    return pd.read_csv("data/clean/primary_skills_long.csv")
```

### Edge Case 6.3 — Streamlit Secrets Not Configured in Cloud
```
TRIGGER: GROQ_API_KEY not added to Streamlit Cloud secrets before deployment
SYMPTOM: App loads but Skill Gap Advisor crashes with AuthenticationError

PREVENTION:
# Add to .streamlit/secrets.toml (local) AND Streamlit Cloud dashboard:
GROQ_API_KEY = "gsk_..."

# In app.py:
import streamlit as st
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("⚠️ API key not configured. Skill Gap Advisor is temporarily unavailable.")
    st.stop()
```

---

## CATEGORY 7 — GitHub / Version Control Failures

### Edge Case 7.1 — Colab "Save to GitHub" Overwrites Wrong Branch
```
TRIGGER: Save to GitHub accidentally pushes to main instead of a feature branch
SYMPTOM: Main branch contains broken/incomplete code

PREVENTION:
- Always create a branch before major phase work: git checkout -b phase-2-cleaning
- Use File → Save a copy in GitHub, then select the correct branch
- Merge to main only after phase evaluation passes
```

### Edge Case 7.2 — Large Data Files Accidentally Committed
```
TRIGGER: 50k-row CSV or 1.3M-row CSV pushed to GitHub
SYMPTOM: Push rejected (file > 100MB) or repo bloated

PREVENTION:
# .gitignore must include:
data/raw/
data/clean/*.csv
*.pkl
*.parquet

# Only commit:
# - notebooks (.ipynb)
# - src/*.py
# - app.py
# - requirements.txt
# - docs/*.md
# - assets/charts/*.png (small exported images only)
```

---

## MASTER EDGE CASE REGISTRY

| ID | Category | Risk Level | Automated? | Recovery |
|---|---|---|---|---|
| 1.1 | File Not Found | 🔴 Critical | ✅ try/except | Print download link + halt |
| 1.2 | Wrong Dataset | 🔴 Critical | ✅ column check | Print columns + warn |
| 1.3 | Memory Overflow | 🔴 Critical | ✅ nrows cap | Restart + reload |
| 2.1 | All Rows Dropped | 🔴 Critical | ✅ shape check | Inspect column names |
| 2.3 | Zero Skills Extracted | 🔴 Critical | ✅ sum check | Debug column format |
| 3.1 | Single Year Data | 🟡 High | ✅ nunique check | Add disclaimer |
| 3.2 | Small Sample Stats | 🟡 High | ✅ n < 30 check | Switch skill |
| 5.1 | API Key Missing | 🔴 Critical | ✅ env check | Set key in secrets |
| 5.2 | Rate Limit | 🟡 High | ✅ except + sleep | Auto-retry |
| 5.4 | Nonsense Input | 🟠 Medium | ✅ input validation | Prompt user to correct |
| 6.2 | File Not in Repo | 🔴 Critical | ❌ Manual | Commit or load from URL |
| 7.2 | Large File in Git | 🟡 High | ✅ .gitignore | Remove + reclean history |
