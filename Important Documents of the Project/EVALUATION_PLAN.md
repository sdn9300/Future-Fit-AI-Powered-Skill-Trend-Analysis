# EVALUATION_PLAN.md
# Skill Trend Analysis — Agentic Code Execution & Output Evaluation Plan
**Candidate:** Soumyadeep Nath | **Evaluator Role:** Autonomous AI Agent / Human Reviewer

---

## PURPOSE

This document defines exactly **how every phase of the Skill Trend Analysis project
will be tested and graded** — covering code execution correctness, tool utilization
accuracy, data integrity, visualization quality, and final output validity.

Every evaluation is structured as:
```
WHAT is being tested → HOW it is tested → PASS / FAIL criteria
```

---

## EVALUATION FRAMEWORK

### Grading Tiers

| Tier | Label | Meaning |
|---|---|---|
| ✅ PASS | Correct | Output matches spec exactly |
| ⚠️ WARN | Partial | Output is close but has minor issues |
| ❌ FAIL | Incorrect | Output is wrong, missing, or crashes |
| 🔁 RETRY | Rerun | Non-deterministic; rerun and re-evaluate |

---

## PHASE 0 — Problem Definition Evaluation

### Test 0.1 — problem_statement.md Exists and Is Complete
```
WHAT: Check that the markdown file answers all 4 framing questions
HOW:  Open /docs/problem_statement.md and verify presence of:
      - "What", "Why", "Who", "How" sections
      - At least 5 numbered research questions
PASS: All 4 sections present + 5 research questions defined
FAIL: File missing, or fewer than 3 sections present
```

---

## PHASE 1 — Data Collection Evaluation

### Test 1.1 — Primary Dataset Loads Correctly
```python
# Automated check
assert df_primary.shape[0] >= 40000, "FAIL: Less than 40k rows loaded"
assert df_primary.shape[1] >= 5,     "FAIL: Fewer than 5 columns"
assert 'skills_required' in df_primary.columns or \
       'skills' in df_primary.columns, "FAIL: No skills column found"
```
```
PASS: DataFrame loads with ≥40k rows and skills column present
FAIL: FileNotFoundError, shape mismatch, or missing skills column
```

### Test 1.2 — Secondary Dataset Loads (Sample Only)
```python
assert df_secondary.shape[0] == 10000, "FAIL: Sample not exactly 10k rows"
assert df_secondary.shape[0] <= 15000, "WARN: Loading too many rows from 1.3M dataset"
```
```
PASS: Sample loads as 10k rows without memory error
FAIL: MemoryError (loaded full 1.3M) or FileNotFoundError
```

### Test 1.3 — Notebook Committed to GitHub
```
WHAT: Verify 01_data_collection.ipynb exists in GitHub repo
HOW:  Check github.com/sdn9300/skill-trend-analysis/notebooks/
PASS: File present in repo with at least 1 commit
FAIL: File missing from repo, or only saved locally in Colab
```

---

## PHASE 2 — Data Cleaning Evaluation

### Test 2.1 — No Nulls in Core Columns Post-Cleaning
```python
assert df_clean['skills_required'].isnull().sum() == 0, \
       "FAIL: Null values remain in skills_required"
assert df_clean['date_posted'].dtype == 'datetime64[ns]', \
       "FAIL: date_posted not parsed as datetime"
```

### Test 2.2 — Skill Extraction Correctness
```python
# Unit test on known input
test_text = "We need Python, SQL, and Power BI experience"
result = extract_skills(test_text)
assert "Python" in result, "FAIL: Python not extracted"
assert "SQL" in result,    "FAIL: SQL not extracted"
assert "Power BI" in result, "FAIL: Power BI not extracted"
assert "Java" not in result,  "FAIL: False positive — Java extracted incorrectly"
```

### Test 2.3 — Exploded DataFrame Structure
```python
assert df_exploded.shape[0] > df_primary.shape[0], \
       "FAIL: Exploded DF should have more rows than original"
assert 'skills_found' in df_exploded.columns, \
       "FAIL: skills_found column missing"
assert df_exploded['skills_found'].isnull().sum() == 0, \
       "FAIL: Null skills remain after explode+dropna"
```

### Test 2.4 — Clean CSV Saved Correctly
```python
import os
assert os.path.exists("data/clean/primary_skills_long.csv"), \
       "FAIL: Clean CSV not saved"
df_reload = pd.read_csv("data/clean/primary_skills_long.csv")
assert df_reload.shape[0] > 0, "FAIL: Saved CSV is empty"
```

---

## PHASE 3 — EDA Evaluation

### Test 3.1 — Research Questions Answered
```
WHAT: Verify all 5 research questions have a corresponding code cell + output
HOW:  Review notebook 03_eda_analysis.ipynb for:
      Q1 → skill_counts variable exists and is non-empty
      Q2 → trend DataFrame exists with 'month' and 'skills_found' columns
      Q3 → co_occur Counter exists with at least 10 pairs
      Q4 → crosstab output exists with experience_level as index
      Q5 → p_value variable exists and hypothesis conclusion written in markdown
PASS: All 5 present with non-empty outputs
FAIL: Any research question has no associated code or output
```

### Test 3.2 — Hypothesis Test Validity
```python
from scipy.stats import chi2_contingency
# Verify test was run and conclusion is stated
assert 'p_value' in dir(),  "FAIL: p_value not computed"
assert isinstance(p_value, float), "FAIL: p_value is not a float"
assert 0.0 <= p_value <= 1.0,      "FAIL: p_value out of valid range [0,1]"
# Check markdown cell contains conclusion
# Manual check: "reject H0" or "fail to reject H0" must appear in notebook
```

### Test 3.3 — Time Series Completeness
```python
assert trend['month'].nunique() >= 24, \
       "WARN: Fewer than 24 months in trend data — time series may be thin"
assert trend['skills_found'].nunique() >= 10, \
       "FAIL: Fewer than 10 skills tracked in trend analysis"
```

---

## PHASE 4 — Visualization Evaluation

### Test 4.1 — All 5 Charts Exist as PNG Files
```python
import os
required_charts = [
    "assets/charts/skill_frequency.png",
    "assets/charts/skill_trend.png",
    "assets/charts/skill_cooccurrence.png",
    "assets/charts/skill_by_level.png",
    "assets/charts/skill_wordcloud.png"
]
for chart in required_charts:
    assert os.path.exists(chart), f"FAIL: {chart} not exported"
```

### Test 4.2 — Chart Title Quality Check (Manual)
```
WHAT: Verify every chart title is a finding, not a label
HOW:  Reviewer checks each chart title against this rule:
      - Title must contain a data-backed claim (number, percentage, or comparison)
      - Title must NOT be generic (e.g., "Skill Frequency" = FAIL)
PASS: All 5 titles contain specific insights
WARN: 3–4 titles contain insights
FAIL: 2 or fewer titles contain insights
```

### Test 4.3 — Insight Sentence Present Per Chart
```
WHAT: Every chart cell in notebook must have a markdown cell below it
      with at least one sentence of interpretation
HOW:  Manual review of notebook cell order
PASS: All 5 charts have narrative markdown below them
FAIL: Any chart has no markdown interpretation
```

---

## PHASE 5 — GenAI / Skill Gap Advisor Evaluation

### Test 5.1 — API Call Succeeds
```python
# Test with a known skill input
test_input = "Python, SQL, Pandas, Matplotlib"
response = get_skill_gap_advice(test_input)
assert response is not None,      "FAIL: API returned None"
assert len(response) > 50,        "FAIL: Response too short to be meaningful"
assert "learn" in response.lower() or "skill" in response.lower(), \
       "WARN: Response does not mention learning or skills"
```

### Test 5.2 — No Hallucinated Skills
```python
# Verify LLM does not recommend skills that are NOT in the trending skill list
trending = get_top_rising_skills(df_exploded)
# Manual review: check if LLM output recommends skills outside trending_skills
# Flag any skill in LLM output that is not in the known skill_list
```

### Test 5.3 — Guardrail: Empty Input Handling
```python
response_empty = get_skill_gap_advice("")
assert "please" in response_empty.lower() or \
       "provide" in response_empty.lower() or \
       len(response_empty) < 20, \
       "FAIL: Empty input should trigger a graceful prompt, not a full analysis"
```

---

## PHASE 6 — Streamlit App Evaluation

### Test 6.1 — App Runs Locally Without Error
```bash
streamlit run app.py
# PASS: App opens at localhost:8501 with no crash
# FAIL: ImportError, AttributeError, or any traceback on launch
```

### Test 6.2 — All 4 Panels Render
```
WHAT: Manually navigate to each panel/tab in the app
HOW:  Check each panel loads its chart or feature without blank output
PASS: All 4 panels render with data
FAIL: Any panel shows empty chart, None, or error message
```

### Test 6.3 — Live Deployment Check
```
WHAT: Verify app is accessible at public Streamlit Cloud URL
HOW:  Open URL in incognito browser (no local session)
PASS: App loads fully within 30 seconds
FAIL: 404 error, "App not found", or loading spinner that never resolves
```

### Test 6.4 — Skill Gap Advisor Works End-to-End in App
```
WHAT: Paste "Python, Excel" into Skill Gap Advisor input in the live app
HOW:  Click submit and verify LLM response appears within 10 seconds
PASS: Coherent, skill-specific advice appears in the output area
FAIL: Blank output, error message, or API key not found error
```

---

## PHASE 6B — Power BI Dashboard Evaluation

### Test 6B.1 — Dashboard Contains Required Visuals
```
WHAT: Open .pbix file and verify 4 visuals are present
HOW:  Manual check in Power BI Desktop
PASS: Bar chart · Line chart · Matrix · KPI cards all present
FAIL: Fewer than 3 visuals, or charts show "No data"
```

### Test 6B.2 — Year Slicer Works Correctly
```
WHAT: Change year slicer from 2020 to 2024 and verify charts update
HOW:  Manual interaction test
PASS: All visuals reflect filtered year data
FAIL: Any visual does not respond to slicer
```

---

## PHASE 7 — Documentation Evaluation

### Test 7.1 — README Completeness
```
WHAT: Check README.md contains all required sections
HOW:  Grep for required headings:
      - Project summary (2 sentences)
      - 3 Key Insights (with actual numbers)
      - Tech stack badges
      - Screenshots (≥3 chart images)
      - Live app link
      - How to run locally
PASS: All 6 sections present
WARN: 4–5 sections present
FAIL: Fewer than 4 sections
```

### Test 7.2 — Repo Folder Structure
```python
required_paths = [
    "notebooks/01_data_collection.ipynb",
    "notebooks/02_data_cleaning.ipynb",
    "notebooks/03_eda_analysis.ipynb",
    "notebooks/04_visualization_report.ipynb",
    "src/skill_gap_advisor.py",
    "app.py",
    "requirements.txt",
    "README.md",
    "ARCHITECTURE.md",
    "MISSION_PLAN.md"
]
# Manual check: all paths exist in GitHub repo
```

---

## FINAL PROJECT SCORECARD

| Phase | Weight | Max Score | Pass Threshold |
|---|---|---|---|
| Phase 0: Problem Definition | 5% | 5 | 4/5 |
| Phase 1: Data Collection | 10% | 10 | 8/10 |
| Phase 2: Data Cleaning | 20% | 20 | 16/20 |
| Phase 3: EDA + Stats | 25% | 25 | 20/25 |
| Phase 4: Visualization | 15% | 15 | 12/15 |
| Phase 5: GenAI Feature | 10% | 10 | 8/10 |
| Phase 6: Streamlit App | 10% | 10 | 8/10 |
| Phase 7: Documentation | 5% | 5 | 4/5 |
| **TOTAL** | **100%** | **100** | **80/100** |

**Portfolio-Ready Threshold: ≥ 80/100**
**Publishable to LinkedIn: ≥ 85/100**
