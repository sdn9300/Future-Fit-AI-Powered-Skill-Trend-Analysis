# PROBLEM_STATEMENT.md
# Skill Trend Analysis — Agent-Optimized Execution Ticket
**Format:** Agentic Feature Ticket | **Version:** 1.0
**Candidate:** Soumyadeep Nath | **Repo:** github.com/sdn9300/skill-trend-analysis

---

## AGENT READ PROTOCOL

```
STEP 1 → Read this file top to bottom before touching any file or tool.
STEP 2 → Map every TICKET against your available codebase tools.
STEP 3 → Generate a temporary PLAN.md scoped only to this ticket's requirements.
STEP 4 → Execute implementation referencing CRITERIA entries line-by-line.
STEP 5 → Run UNIT TEST BLOCK for this ticket before marking it RESOLVED.
STEP 6 → Pull Request is CLOSED only when all DoD (Definition of Done) items are ✅.

AGENT MUST NOT:
  - Resolve a ticket without running its associated unit tests
  - Skip a dependency listed in TARGET DEPENDENCIES
  - Fabricate test output values
  - Modify files outside the ticket's SCOPE OF CHANGE
  - Proceed to the next ticket while any test in the current block is ❌
```

---

## TICKET REGISTRY

| Ticket ID | Feature Module | Priority | Status | Depends On |
|---|---|---|---|---|
| PST-001 | Data Ingestion & Schema Validation | 🔴 P0 | OPEN | None |
| PST-002 | Data Cleaning Pipeline | 🔴 P0 | OPEN | PST-001 |
| PST-003 | Skill Extraction Engine | 🔴 P0 | OPEN | PST-002 |
| PST-004 | Long-Format Transformation | 🔴 P0 | OPEN | PST-003 |
| PST-005 | Skill Frequency Analysis | 🟡 P1 | OPEN | PST-004 |
| PST-006 | Time Series Trend Engine | 🟡 P1 | OPEN | PST-004 |
| PST-007 | Co-occurrence Matrix Builder | 🟡 P1 | OPEN | PST-004 |
| PST-008 | Experience-Level Cross Analysis | 🟡 P1 | OPEN | PST-004 |
| PST-009 | Hypothesis Testing Module | 🟡 P1 | OPEN | PST-006 |
| PST-010 | Visualization Export Pipeline | 🟠 P2 | OPEN | PST-005 → PST-009 |
| PST-011 | Skill Gap Advisor — Groq Integration | 🟠 P2 | OPEN | PST-006 |
| PST-012 | Streamlit App Scaffold | 🟠 P2 | OPEN | PST-010, PST-011 |
| PST-013 | Streamlit Cloud Deployment | 🟠 P2 | OPEN | PST-012 |
| PST-014 | Power BI Dashboard Export | 🔵 P3 | OPEN | PST-004 |
| PST-015 | README & Portfolio Packaging | 🔵 P3 | OPEN | PST-013, PST-014 |

---
---

## PST-001 — Data Ingestion & Schema Validation

```
TICKET ID:     PST-001
FEATURE:       Load both datasets and validate schema integrity
FILE SCOPE:    notebooks/01_data_collection.ipynb
               src/validators.py  (CREATE NEW)
PRIORITY:      P0 — Blocks all downstream tickets
```

### Localized Description
The agent must load two distinct CSV datasets into Pandas DataFrames and
validate that both contain the minimum required columns before any downstream
processing begins. If schema validation fails, the agent HALTS with a
structured error payload — it does NOT attempt cleaning or extraction on a
malformed or incorrectly identified dataset.

### Target Dependencies
```
pandas >= 1.5.0
os (stdlib)
sys (stdlib)
```

### Required Columns Contract

**Primary Dataset** (`ai_jobs_market_2020_2026.csv`):
```python
PRIMARY_REQUIRED_COLS = [
    "job_title",        # dtype: str
    "skills_required",  # dtype: str  ← CRITICAL: must not be empty
    "date_posted",      # dtype: str  (will be parsed in PST-002)
    "experience_level", # dtype: str
    "company_location"  # dtype: str
]
```

**Secondary Dataset** (`linkedin_jobs_2024.csv`, 10k sample):
```python
SECONDARY_REQUIRED_COLS = [
    "title",            # maps to job_title
    "description",      # maps to skills_required (raw text)
]
```

### Exact Failure Payloads

**Failure Payload A — FileNotFoundError:**
```python
{
  "ticket": "PST-001",
  "error_type": "FileNotFoundError",
  "file": "<attempted_path>",
  "message": "Dataset not found at specified path. Verify Kaggle download completed.",
  "recovery": "Re-download from Kaggle. Upload to Colab via Files panel.",
  "agent_action": "HALT"
}
```

**Failure Payload B — Schema Mismatch:**
```python
{
  "ticket": "PST-001",
  "error_type": "SchemaMismatchError",
  "missing_columns": ["<col1>", "<col2>"],
  "found_columns": ["<actual_col_list>"],
  "message": "Required columns absent. Wrong dataset may have been loaded.",
  "recovery": "Verify dataset identity. Check column aliases and rename if needed.",
  "agent_action": "HALT"
}
```

**Failure Payload C — Row Count Below Threshold:**
```python
{
  "ticket": "PST-001",
  "error_type": "InsufficientDataError",
  "expected_min_rows": 40000,
  "actual_rows": "<n>",
  "message": "Primary dataset has fewer rows than expected. Partial download suspected.",
  "recovery": "Re-download full dataset. Do not proceed with partial data.",
  "agent_action": "HALT"
}
```

### Implementation Contract
```python
# src/validators.py — Functions the agent must implement:

def validate_schema(df: pd.DataFrame,
                    required_cols: list[str],
                    dataset_name: str) -> dict:
    """
    Validates DataFrame has all required columns.
    Returns: {"valid": True} OR structured Failure Payload B dict.
    Must NOT raise — must return the failure dict instead.
    """

def validate_row_count(df: pd.DataFrame,
                       min_rows: int,
                       dataset_name: str) -> dict:
    """
    Validates DataFrame meets minimum row threshold.
    Returns: {"valid": True} OR structured Failure Payload C dict.
    Must NOT raise — must return the failure dict instead.
    """

def load_dataset(path: str,
                 required_cols: list[str],
                 dataset_name: str,
                 nrows: int = None) -> pd.DataFrame:
    """
    Master loader: wraps pd.read_csv with all validation checks.
    Calls validate_schema and validate_row_count internally.
    On any failure: prints failure payload JSON and calls sys.exit(1).
    On success: returns validated DataFrame.
    """
```

### Unit Test Block — PST-001
```python
# tests/test_pst001_ingestion.py

import pytest
import pandas as pd
from src.validators import validate_schema, validate_row_count, load_dataset

# --- Test 1.1: Schema validation passes on correct columns ---
def test_schema_valid():
    df = pd.DataFrame(columns=["job_title", "skills_required",
                                "date_posted", "experience_level",
                                "company_location"])
    result = validate_schema(df, PRIMARY_REQUIRED_COLS, "primary")
    assert result == {"valid": True}, \
        "FAIL PST-001-T1.1: Valid schema should return {'valid': True}"

# --- Test 1.2: Schema validation catches missing columns ---
def test_schema_missing_column():
    df = pd.DataFrame(columns=["job_title", "date_posted"])
    result = validate_schema(df, PRIMARY_REQUIRED_COLS, "primary")
    assert result["error_type"] == "SchemaMismatchError", \
        "FAIL PST-001-T1.2: Missing columns should trigger SchemaMismatchError"
    assert "skills_required" in result["missing_columns"], \
        "FAIL PST-001-T1.2: 'skills_required' must appear in missing_columns"

# --- Test 1.3: Row count threshold enforced ---
def test_row_count_below_threshold():
    df = pd.DataFrame({"a": range(100)})
    result = validate_row_count(df, min_rows=40000, dataset_name="primary")
    assert result["error_type"] == "InsufficientDataError", \
        "FAIL PST-001-T1.3: Row count below 40k should trigger InsufficientDataError"
    assert result["actual_rows"] == 100, \
        "FAIL PST-001-T1.3: actual_rows must reflect true count"

# --- Test 1.4: load_dataset returns DataFrame on valid input ---
def test_load_dataset_returns_dataframe(tmp_path):
    # Create a minimal valid CSV
    data = {"job_title": ["DS"], "skills_required": ["Python"],
            "date_posted": ["2024-01"], "experience_level": ["EN"],
            "company_location": ["IN"]}
    csv_path = tmp_path / "test.csv"
    pd.DataFrame(data * 100).to_csv(csv_path, index=False)  # 500 rows
    # Patch min_rows to 100 for test
    df = load_dataset(str(csv_path), PRIMARY_REQUIRED_COLS, "primary")
    assert isinstance(df, pd.DataFrame), \
        "FAIL PST-001-T1.4: load_dataset must return pd.DataFrame on success"
```

### Definition of Done — PST-001
```
✅ validators.py created at src/validators.py
✅ validate_schema() returns {"valid": True} for correct schema
✅ validate_schema() returns SchemaMismatchError payload for wrong schema
✅ validate_row_count() returns InsufficientDataError for < 40k rows
✅ load_dataset() calls sys.exit(1) on any validation failure
✅ All 4 unit tests pass with no AssertionError
✅ Notebook 01_data_collection.ipynb uses load_dataset() for BOTH datasets
✅ Notebook committed to GitHub
```

---
---

## PST-002 — Data Cleaning Pipeline

```
TICKET ID:     PST-002
FEATURE:       Null removal, date parsing, column standardization
FILE SCOPE:    notebooks/02_data_cleaning.ipynb
               src/cleaner.py  (CREATE NEW)
PRIORITY:      P0 — Blocks PST-003
DEPENDS ON:    PST-001 (validated DataFrames)
```

### Localized Description
The agent receives two validated DataFrames from PST-001 and applies a
deterministic, ordered cleaning pipeline. Every step is reversible via
inspection — the agent must NOT perform in-place mutations without first
logging the row counts before and after each step. The cleaning pipeline
has a strict execution order that must not be permuted.

### Execution Order Contract (FROZEN — do not reorder)
```
ORDER 1 → Drop rows where skills_required is null or empty string
ORDER 2 → Strip leading/trailing whitespace from all string columns
ORDER 3 → Lowercase all string columns except job_title
ORDER 4 → Parse date_posted to datetime with errors='coerce'
ORDER 5 → Drop rows where date_posted is NaT after parsing
ORDER 6 → Extract: year (int), month (Period['M']), quarter (Period['Q'])
ORDER 7 → Fill remaining nulls in experience_level with "Not Specified"
ORDER 8 → Drop exact duplicate rows
ORDER 9 → Reset index
ORDER 10 → Log final row count and column dtypes
```

### Exact Failure Payloads

**Failure Payload D — All Rows Dropped After Null Filter:**
```python
{
  "ticket": "PST-002",
  "error_type": "EmptyDataFrameError",
  "step": "ORDER 1 — skills_required null drop",
  "rows_before": "<n>",
  "rows_after": 0,
  "message": "All rows dropped. Column name may be wrong or data is entirely null.",
  "recovery": "Print df.columns and df['skills_required'].head(10) to inspect.",
  "agent_action": "HALT"
}
```

**Failure Payload E — Date Parse Failure > 20%:**
```python
{
  "ticket": "PST-002",
  "error_type": "DateParseFailureError",
  "step": "ORDER 4 — date_posted parsing",
  "nat_count": "<n>",
  "nat_percentage": "<pct>",
  "message": "More than 20% of dates unparseable. Column format may be unexpected.",
  "recovery": "Print df['date_posted'].head(20) and identify format. Use explicit format= parameter.",
  "agent_action": "HALT"
}
```

**Failure Payload F — Derived Columns Missing:**
```python
{
  "ticket": "PST-002",
  "error_type": "DerivedColumnError",
  "step": "ORDER 6 — temporal feature extraction",
  "missing_derived": ["year", "month", "quarter"],
  "message": "One or more temporal columns not created. Date parsing may have failed silently.",
  "recovery": "Verify date_posted dtype is datetime64 before running ORDER 6.",
  "agent_action": "HALT"
}
```

### Implementation Contract
```python
# src/cleaner.py

def clean_primary(df: pd.DataFrame,
                  max_nat_pct: float = 0.20) -> pd.DataFrame:
    """
    Applies the 10-step cleaning pipeline in strict order.
    Args:
        df: Validated DataFrame from PST-001
        max_nat_pct: Max tolerated proportion of NaT dates (default 20%)
    Returns: Cleaned DataFrame with year, month, quarter columns added.
    Raises: SystemExit(1) with Failure Payload D, E, or F if any step fails.
    Side effect: Prints row count before/after each step to stdout.
    """

def log_cleaning_step(step_name: str,
                       rows_before: int,
                       rows_after: int) -> None:
    """
    Prints: [PST-002] <step_name>: <rows_before> → <rows_after> rows
    Agent must call this after every ORDER step.
    """
```

### Unit Test Block — PST-002
```python
# tests/test_pst002_cleaning.py

import pytest
import pandas as pd
import numpy as np
from src.cleaner import clean_primary

BASE_DF = pd.DataFrame({
    "job_title": ["  Data Scientist  ", "ML Engineer"],
    "skills_required": ["Python, SQL", None],
    "date_posted": ["2024-01-15", "not-a-date"],
    "experience_level": [np.nan, "SE"],
    "company_location": ["IN", "US"]
})

# --- Test 2.1: Nulls in skills_required are dropped ---
def test_null_skills_dropped():
    df = clean_primary(BASE_DF.copy())
    assert df['skills_required'].isnull().sum() == 0, \
        "FAIL PST-002-T2.1: Null skills_required rows must be removed"

# --- Test 2.2: date_posted parsed as datetime ---
def test_date_parsed_correctly():
    df = pd.DataFrame({
        "job_title": ["DS"], "skills_required": ["Python"],
        "date_posted": ["2023-06-01"],
        "experience_level": ["EN"], "company_location": ["IN"]
    })
    result = clean_primary(df)
    assert result['date_posted'].dtype == 'datetime64[ns]', \
        "FAIL PST-002-T2.2: date_posted must be datetime64[ns] after cleaning"

# --- Test 2.3: Temporal derived columns created ---
def test_temporal_columns_created():
    df = pd.DataFrame({
        "job_title": ["DS"], "skills_required": ["Python"],
        "date_posted": ["2023-06-01"],
        "experience_level": ["EN"], "company_location": ["IN"]
    })
    result = clean_primary(df)
    assert "year" in result.columns,    "FAIL PST-002-T2.3: 'year' column missing"
    assert "month" in result.columns,   "FAIL PST-002-T2.3: 'month' column missing"
    assert "quarter" in result.columns, "FAIL PST-002-T2.3: 'quarter' column missing"
    assert result['year'].iloc[0] == 2023, \
        "FAIL PST-002-T2.3: year extraction returned wrong value"

# --- Test 2.4: experience_level nulls filled ---
def test_experience_level_filled():
    df = pd.DataFrame({
        "job_title": ["DS"], "skills_required": ["Python"],
        "date_posted": ["2023-06-01"],
        "experience_level": [np.nan], "company_location": ["IN"]
    })
    result = clean_primary(df)
    assert result['experience_level'].iloc[0] == "Not Specified", \
        "FAIL PST-002-T2.4: Null experience_level must be filled with 'Not Specified'"

# --- Test 2.5: No exact duplicates remain ---
def test_no_duplicates():
    df = pd.DataFrame({
        "job_title": ["DS", "DS"], "skills_required": ["Python", "Python"],
        "date_posted": ["2023-06-01", "2023-06-01"],
        "experience_level": ["EN", "EN"], "company_location": ["IN", "IN"]
    })
    result = clean_primary(df)
    assert result.duplicated().sum() == 0, \
        "FAIL PST-002-T2.5: Duplicate rows must be removed"

# --- Test 2.6: Row count logged (smoke test for log_cleaning_step) ---
def test_cleaning_log_runs(capsys):
    from src.cleaner import log_cleaning_step
    log_cleaning_step("Test Step", 1000, 950)
    captured = capsys.readouterr()
    assert "1000" in captured.out and "950" in captured.out, \
        "FAIL PST-002-T2.6: log_cleaning_step must print before/after counts"
```

### Definition of Done — PST-002
```
✅ cleaner.py created at src/cleaner.py
✅ clean_primary() executes all 10 steps in documented order
✅ log_cleaning_step() called after every ORDER step
✅ clean_primary() raises SystemExit(1) with structured payload for E, F failures
✅ clean_primary() raises SystemExit(1) with payload D if output has 0 rows
✅ All 6 unit tests pass with no AssertionError
✅ Output: df_clean has no nulls in skills_required or date_posted
✅ Output: year (int), month (Period), quarter (Period) columns all present
✅ Notebook 02_data_cleaning.ipynb uses clean_primary() function (not inline code)
```

---
---

## PST-003 — Skill Extraction Engine

```
TICKET ID:     PST-003
FEATURE:       Extract structured skill mentions from raw text using string matching
FILE SCOPE:    src/skill_extractor.py  (CREATE NEW)
               data/skill_taxonomy.json  (CREATE NEW)
PRIORITY:      P0 — Blocks PST-004
DEPENDS ON:    PST-002 (cleaned DataFrame)
```

### Localized Description
The agent builds a deterministic, taxonomy-driven skill extraction engine.
Skills are matched against a predefined JSON taxonomy — NOT inferred by NLP
models. The taxonomy is the single source of truth: every skill in the output
must trace back to an entry in `skill_taxonomy.json`. The extraction function
must handle case-insensitivity, partial word boundary matching prevention
(e.g., "R" must NOT match inside "Regression"), and multi-word skill names
(e.g., "Power BI", "Random Forest").

### Taxonomy Contract
```json
// data/skill_taxonomy.json — Agent must create with this structure:
{
  "Languages": ["Python", "SQL", "R", "Java", "Scala", "Julia", "TypeScript"],
  "ML_AI": [
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "LLM", "RAG", "Prompt Engineering", "TensorFlow", "PyTorch",
    "scikit-learn", "XGBoost", "Random Forest", "Gradient Boosting"
  ],
  "Data_Tools": ["Pandas", "NumPy", "Spark", "dbt", "Airflow", "Kafka"],
  "Visualization": ["Tableau", "Power BI", "Matplotlib", "Plotly", "Seaborn", "Looker"],
  "Cloud": ["AWS", "GCP", "Azure", "Databricks", "Snowflake", "BigQuery"],
  "DevOps_MLOps": ["Docker", "Git", "FastAPI", "MLflow", "Kubernetes", "CI/CD"],
  "General": ["Excel", "Statistics", "A/B Testing", "Hypothesis Testing",
               "Data Storytelling", "Communication"]
}
```

### Exact Failure Payloads

**Failure Payload G — Taxonomy File Not Found:**
```python
{
  "ticket": "PST-003",
  "error_type": "TaxonomyNotFoundError",
  "file": "data/skill_taxonomy.json",
  "message": "Taxonomy JSON missing. Skill extraction cannot proceed without it.",
  "recovery": "Create data/skill_taxonomy.json from the contract in PST-003.",
  "agent_action": "HALT"
}
```

**Failure Payload H — Zero Skills Extracted Across All Rows:**
```python
{
  "ticket": "PST-003",
  "error_type": "ZeroExtractionError",
  "total_skills_extracted": 0,
  "sample_text": "<first 3 values of skills_required column>",
  "message": "No skills matched. Column text format may differ from taxonomy entries.",
  "recovery": "Print sample texts. Check for list-string format: ['Python','SQL']. Apply ast.literal_eval first.",
  "agent_action": "HALT"
}
```

**Failure Payload I — False Positive Detected in Unit Test:**
```python
{
  "ticket": "PST-003",
  "error_type": "FalsePositiveExtractionError",
  "text": "<input text>",
  "falsely_extracted": "<skill_name>",
  "reason": "Short skill token matched inside a longer word.",
  "recovery": "Use word boundary regex: r'\\b{skill}\\b' for single-token skills.",
  "agent_action": "FIX extraction function and re-run unit tests"
}
```

### Implementation Contract
```python
# src/skill_extractor.py

import json, re
import pandas as pd

def load_taxonomy(path: str = "data/skill_taxonomy.json") -> dict[str, list[str]]:
    """
    Loads taxonomy JSON. Returns {category: [skill, ...]} dict.
    On FileNotFoundError: prints Failure Payload G and calls sys.exit(1).
    """

def flatten_taxonomy(taxonomy: dict) -> list[str]:
    """
    Returns flat list of all skills, sorted by length descending.
    Sorting by length descending ensures 'Random Forest' matches before 'R'.
    """

def extract_skills(text: str, flat_skills: list[str]) -> list[str]:
    """
    Extracts skill mentions from text using case-insensitive word-boundary regex.
    Args:
        text: Raw job description string
        flat_skills: Sorted flat list from flatten_taxonomy()
    Returns: Deduplicated list of matched skill strings.
    Rules:
        - Case-insensitive: "python" matches "Python"
        - Word boundary: "R" must NOT match inside "Regression" or "Career"
        - Multi-word: "Power BI" matched as whole phrase
        - Deduplication: "Python" appears at most once per row
        - Returns [] for empty or non-string input (never raises)
    """

def apply_extraction(df: pd.DataFrame,
                     text_col: str,
                     flat_skills: list[str]) -> pd.DataFrame:
    """
    Applies extract_skills() to every row. Adds 'skills_found' column.
    After extraction: validates total extraction count > 0.
    On zero extraction: prints Failure Payload H and calls sys.exit(1).
    Returns: DataFrame with 'skills_found' column (list of str per row).
    """

def get_skill_category(skill: str, taxonomy: dict) -> str:
    """
    Returns the category name for a given skill string.
    Returns "Unknown" if skill is not found in any category.
    """
```

### Unit Test Block — PST-003
```python
# tests/test_pst003_extraction.py

import pytest
from src.skill_extractor import (
    load_taxonomy, flatten_taxonomy, extract_skills,
    apply_extraction, get_skill_category
)

SAMPLE_TAXONOMY = {
    "Languages": ["Python", "SQL", "R"],
    "ML_AI": ["Random Forest", "Machine Learning"],
    "Visualization": ["Power BI", "Tableau"]
}
FLAT_SKILLS = flatten_taxonomy(SAMPLE_TAXONOMY)

# --- Test 3.1: Known skills extracted correctly ---
def test_known_skills_extracted():
    text = "We need Python, SQL, and Power BI experience."
    result = extract_skills(text, FLAT_SKILLS)
    assert "Python" in result, "FAIL PST-003-T3.1: Python not extracted"
    assert "SQL" in result,    "FAIL PST-003-T3.1: SQL not extracted"
    assert "Power BI" in result, "FAIL PST-003-T3.1: Power BI not extracted"

# --- Test 3.2: Case-insensitive matching ---
def test_case_insensitive():
    text = "experience with python and sql required"
    result = extract_skills(text, FLAT_SKILLS)
    assert "Python" in result, "FAIL PST-003-T3.2: Lowercase 'python' must match 'Python'"
    assert "SQL" in result,    "FAIL PST-003-T3.2: Lowercase 'sql' must match 'SQL'"

# --- Test 3.3: Word boundary — 'R' must NOT match inside 'Regression' ---
def test_no_false_positive_R():
    text = "Knowledge of Regression analysis and career planning required"
    result = extract_skills(text, FLAT_SKILLS)
    assert "R" not in result, \
        "FAIL PST-003-T3.3: 'R' falsely extracted from 'Regression' or 'career' — word boundary broken"

# --- Test 3.4: Multi-word skill matched as whole phrase ---
def test_multiword_skill():
    text = "Experience with Random Forest and boosting methods"
    result = extract_skills(text, FLAT_SKILLS)
    assert "Random Forest" in result, \
        "FAIL PST-003-T3.4: Multi-word skill 'Random Forest' not extracted"

# --- Test 3.5: Deduplication — skill appears only once per row ---
def test_deduplication():
    text = "Python developer with Python experience using Python"
    result = extract_skills(text, FLAT_SKILLS)
    assert result.count("Python") == 1, \
        "FAIL PST-003-T3.5: 'Python' must appear at most once per row"

# --- Test 3.6: Empty / null input returns empty list, never raises ---
def test_empty_input_safe():
    assert extract_skills("", FLAT_SKILLS) == [], \
        "FAIL PST-003-T3.6: Empty string must return []"
    assert extract_skills(None, FLAT_SKILLS) == [], \
        "FAIL PST-003-T3.6: None input must return [] not raise"

# --- Test 3.7: get_skill_category returns correct category ---
def test_skill_category():
    assert get_skill_category("Python", SAMPLE_TAXONOMY) == "Languages", \
        "FAIL PST-003-T3.7: Python must map to 'Languages'"
    assert get_skill_category("UnknownTool", SAMPLE_TAXONOMY) == "Unknown", \
        "FAIL PST-003-T3.7: Unknown skill must return 'Unknown'"

# --- Test 3.8: flatten_taxonomy sorts by length descending ---
def test_flatten_sorted_by_length():
    flat = flatten_taxonomy(SAMPLE_TAXONOMY)
    for i in range(len(flat) - 1):
        assert len(flat[i]) >= len(flat[i+1]), \
            f"FAIL PST-003-T3.8: flat_skills not sorted by length desc at index {i}"
```

### Definition of Done — PST-003
```
✅ data/skill_taxonomy.json created with all 7 categories and 50+ skills
✅ src/skill_extractor.py created with all 5 functions
✅ flatten_taxonomy() returns skills sorted by length descending
✅ extract_skills() uses word-boundary regex (not simple 'in' check)
✅ "R" does NOT appear in extraction result for text containing "Regression"
✅ "Power BI" extracted as a full phrase (not "Power" and "BI" separately)
✅ All 8 unit tests pass with no AssertionError
✅ apply_extraction() raises SystemExit(1) with Payload H on zero extraction
✅ get_skill_category() returns "Unknown" for skills not in taxonomy
```

---
---

## PST-004 — Long-Format Transformation

```
TICKET ID:     PST-004
FEATURE:       Explode skills_found into one-row-per-skill-mention format
FILE SCOPE:    src/transformer.py  (CREATE NEW)
               data/clean/primary_skills_long.csv  (GENERATE)
PRIORITY:      P0 — Blocks PST-005 through PST-009
DEPENDS ON:    PST-003
```

### Localized Description
The agent transforms the wide-format DataFrame (one row per job posting,
skills as a list) into a long-format DataFrame (one row per skill mention).
This is the canonical analysis-ready format used by ALL downstream tickets.
The agent must validate structural integrity of the exploded output and
persist it as the primary clean artifact before proceeding.

### Structural Contract (Long-Format Schema)
```
PRIMARY_SKILLS_LONG SCHEMA:
─────────────────────────────────────────────────────────────────────
Column Name        | dtype           | Constraint
─────────────────────────────────────────────────────────────────────
job_title          | object (str)    | Not null
skills_found       | object (str)    | Not null; must be in taxonomy
skill_category     | object (str)    | Not null; not "Unknown" > 5%
date_posted        | datetime64[ns]  | Not null
year               | int64           | Range: 2020–2026 inclusive
month              | Period[M]       | Not null
quarter            | Period[Q]       | Not null
experience_level   | object (str)    | Not null (filled in PST-002)
company_location   | object (str)    | Not null
─────────────────────────────────────────────────────────────────────
```

### Exact Failure Payloads

**Failure Payload J — Exploded DataFrame Smaller Than Input:**
```python
{
  "ticket": "PST-004",
  "error_type": "ExplodeReductionError",
  "rows_before_explode": "<n>",
  "rows_after_explode": "<m>",
  "message": "Exploded DF has fewer rows than input — skills_found may contain empty lists.",
  "recovery": "Filter out rows where skills_found is [] before calling explode().",
  "agent_action": "HALT"
}
```

**Failure Payload K — skills_found Column Contains List Objects Post-Explode:**
```python
{
  "ticket": "PST-004",
  "error_type": "NestedListError",
  "sample_value": "<type and repr of df_exploded['skills_found'].iloc[0]>",
  "message": "Explode produced list objects instead of strings. skills_found may be nested.",
  "recovery": "Flatten nested lists before explode: df['skills_found'].apply(lambda x: [i for sub in x for i in (sub if isinstance(sub, list) else [sub])])",
  "agent_action": "FIX and re-run explode"
}
```

**Failure Payload L — Year Out of Expected Range:**
```python
{
  "ticket": "PST-004",
  "error_type": "YearRangeError",
  "unexpected_years": ["<year1>", "<year2>"],
  "message": "year column contains values outside 2020–2026. Date parsing or dataset identity issue.",
  "recovery": "Filter: df = df[df['year'].between(2020, 2026)]",
  "agent_action": "WARN — filter and continue (do not HALT)"
}
```

### Implementation Contract
```python
# src/transformer.py

def explode_skills(df: pd.DataFrame) -> pd.DataFrame:
    """
    Explodes 'skills_found' list column into one row per skill.
    Pre-condition: df has 'skills_found' column of type list[str].
    Post-condition:
        - df_long.shape[0] > df.shape[0]
        - df_long['skills_found'].apply(type).eq(str).all() == True
        - df_long['skills_found'].isnull().sum() == 0
    On violation: prints appropriate Failure Payload and calls sys.exit(1).
    """

def validate_long_format(df_long: pd.DataFrame) -> list[dict]:
    """
    Runs all structural checks on the long-format DataFrame.
    Returns: list of Failure Payload dicts for any violations found.
    Returns: [] if all checks pass.
    Agent must print all failures and HALT if any HALT-class payload is returned.
    """

def save_long_format(df_long: pd.DataFrame,
                     output_path: str = "data/clean/primary_skills_long.csv") -> None:
    """
    Saves long-format DataFrame to CSV.
    Creates parent directory if it does not exist.
    Prints: "[PST-004] Saved: <n> rows to <output_path>"
    """
```

### Unit Test Block — PST-004
```python
# tests/test_pst004_transformer.py

import pytest
import pandas as pd
from src.transformer import explode_skills, validate_long_format

BASE = pd.DataFrame({
    "job_title": ["DS", "MLE"],
    "skills_found": [["Python", "SQL"], ["Python", "TensorFlow", "Docker"]],
    "date_posted": pd.to_datetime(["2023-01-01", "2024-06-01"]),
    "year": [2023, 2024],
    "month": pd.PeriodIndex(["2023-01", "2024-06"], freq="M"),
    "quarter": pd.PeriodIndex(["2023Q1", "2024Q2"], freq="Q"),
    "experience_level": ["EN", "SE"],
    "company_location": ["IN", "US"],
    "skill_category": [["Languages", "Languages"], ["Languages", "ML_AI", "DevOps_MLOps"]]
})

# --- Test 4.1: Exploded DF has more rows than input ---
def test_explode_increases_rows():
    result = explode_skills(BASE.copy())
    assert result.shape[0] > BASE.shape[0], \
        "FAIL PST-004-T4.1: Exploded DF must have more rows than input"

# --- Test 4.2: skills_found column contains strings only post-explode ---
def test_skills_found_is_string():
    result = explode_skills(BASE.copy())
    types = result['skills_found'].apply(type).unique()
    assert all(t == str for t in types), \
        "FAIL PST-004-T4.2: skills_found must contain str objects after explode, not lists"

# --- Test 4.3: No nulls in skills_found post-explode ---
def test_no_nulls_after_explode():
    result = explode_skills(BASE.copy())
    assert result['skills_found'].isnull().sum() == 0, \
        "FAIL PST-004-T4.3: Null values must not exist in skills_found after explode+dropna"

# --- Test 4.4: Row count matches expected expansion ---
def test_exact_row_count():
    result = explode_skills(BASE.copy())
    # Row 1: 2 skills, Row 2: 3 skills → total 5
    assert result.shape[0] == 5, \
        f"FAIL PST-004-T4.4: Expected 5 rows after explode, got {result.shape[0]}"

# --- Test 4.5: validate_long_format returns [] on valid input ---
def test_validate_passes_clean_data():
    df_long = explode_skills(BASE.copy())
    df_long['skill_category'] = "Languages"
    failures = validate_long_format(df_long)
    assert failures == [], \
        f"FAIL PST-004-T4.5: validate_long_format should return [] on valid input. Got: {failures}"
```

### Definition of Done — PST-004
```
✅ src/transformer.py created with 3 functions
✅ explode_skills() output has strictly more rows than input
✅ Every cell in skills_found column is type str (not list)
✅ No nulls in skills_found, date_posted, year, month, quarter
✅ validate_long_format() checks all 9 schema columns
✅ data/clean/primary_skills_long.csv written to disk
✅ File is readable: pd.read_csv("data/clean/primary_skills_long.csv").shape[0] > 0
✅ All 5 unit tests pass
✅ Notebook 02_data_cleaning.ipynb ends with save_long_format() call
```

---
---

## PST-005 — Skill Frequency Analysis

```
TICKET ID:     PST-005
FEATURE:       Compute top-N skill frequencies and render bar chart
FILE SCOPE:    notebooks/03_eda_analysis.ipynb (Section 1)
               src/analysis.py  (CREATE NEW — frequency functions)
PRIORITY:      P1
DEPENDS ON:    PST-004
```

### Localized Description
Compute aggregate skill mention counts from the long-format DataFrame.
Render a horizontal bar chart with a finding-titled label. Chart title must
embed an actual computed percentage, not a placeholder. Export chart PNG.

### Computation Contract
```python
# Agent must produce these variables:
skill_counts: pd.Series         # index=skill name, values=count, sorted descending
top_20_skills: pd.Series        # top 20 only
top_skill_name: str             # skill_counts.index[0]
top_skill_count: int            # skill_counts.iloc[0]
total_mentions: int             # skill_counts.sum()
top_skill_pct: float            # (top_skill_count / total_mentions) * 100, rounded 1dp
```

### Chart Contract
```python
# Title format (agent must use actual computed values):
title = f"{top_skill_name} Leads All Skills, Appearing in {top_skill_pct}% of All Job Postings"
# xlabel: "Number of Mentions"
# ylabel: "Skill"
# Style: horizontal bar, Seaborn, figure size (12, 8)
# Export: "assets/charts/01_skill_frequency.png", dpi=150
```

### Unit Test Block — PST-005
```python
def test_skill_counts_sorted_descending():
    assert skill_counts.is_monotonic_decreasing, \
        "FAIL PST-005-T5.1: skill_counts must be sorted descending"

def test_top_20_length():
    assert len(top_20_skills) == 20, \
        "FAIL PST-005-T5.2: top_20_skills must contain exactly 20 entries"

def test_top_skill_pct_valid():
    assert 0 < top_skill_pct <= 100, \
        "FAIL PST-005-T5.3: top_skill_pct must be between 0 and 100"

def test_chart_exported():
    import os
    assert os.path.exists("assets/charts/01_skill_frequency.png"), \
        "FAIL PST-005-T5.4: Chart PNG not found at expected path"

def test_title_contains_actual_values():
    assert top_skill_name in title and str(top_skill_pct) in title, \
        "FAIL PST-005-T5.5: Chart title must embed actual computed values, not placeholders"
```

### Definition of Done — PST-005
```
✅ skill_counts, top_20_skills, top_skill_pct all computed
✅ Chart title contains actual skill name and actual percentage
✅ assets/charts/01_skill_frequency.png exists at 150 DPI
✅ Markdown cell below chart contains one insight sentence
✅ All 5 unit tests pass
```

---
---

## PST-006 — Time Series Trend Engine

```
TICKET ID:     PST-006
FEATURE:       Month-over-month skill trend computation and multi-line Plotly chart
FILE SCOPE:    notebooks/03_eda_analysis.ipynb (Section 2)
               src/analysis.py  (EXTEND)
PRIORITY:      P1
DEPENDS ON:    PST-004
```

### Computation Contract
```python
# Agent must produce:
trend_df: pd.DataFrame
# Columns: ["month", "skills_found", "count"]
# month column: string format "YYYY-MM" (converted from Period for Plotly compatibility)
# Minimum unique months: 24
# Minimum unique skills tracked: 10

top_rising_skills: list[str]
# Top 5 skills with highest count delta: (count at max_month - count at min_month)
# Computed only on skills present in BOTH first and last month of dataset

top_declining_skills: list[str]
# Bottom 5 skills with largest negative count delta
```

### Chart Contract
```python
# Plotly multi-line chart:
# x = "month", y = "count", color = "skills_found"
# Filter: display only top 10 skills by total mentions
# Title: "LLM & GenAI Skills Rose X% While Traditional Tools Stabilized (2020–2026)"
# Export: fig.write_html("assets/charts/02_skill_trend.html")
# Static backup: fig.write_image("assets/charts/02_skill_trend.png")
```

### Unit Test Block — PST-006
```python
def test_trend_df_columns():
    required = {"month", "skills_found", "count"}
    assert required.issubset(set(trend_df.columns)), \
        f"FAIL PST-006-T6.1: trend_df missing columns: {required - set(trend_df.columns)}"

def test_minimum_month_coverage():
    assert trend_df['month'].nunique() >= 24, \
        f"FAIL PST-006-T6.2: Expected ≥24 unique months, got {trend_df['month'].nunique()}"

def test_rising_declining_lists_non_empty():
    assert len(top_rising_skills) >= 1,   "FAIL PST-006-T6.3: top_rising_skills is empty"
    assert len(top_declining_skills) >= 1, "FAIL PST-006-T6.3: top_declining_skills is empty"

def test_trend_chart_exported():
    import os
    assert os.path.exists("assets/charts/02_skill_trend.png"), \
        "FAIL PST-006-T6.4: Trend chart PNG missing"
```

### Definition of Done — PST-006
```
✅ trend_df produced with month, skills_found, count columns
✅ trend_df['month'].nunique() >= 24
✅ top_rising_skills and top_declining_skills computed (not hardcoded)
✅ assets/charts/02_skill_trend.html and .png both exported
✅ All 4 unit tests pass
```

---
---

## PST-009 — Hypothesis Testing Module

```
TICKET ID:     PST-009
FEATURE:       Chi-square test on LLM skill demand change 2022 vs 2024
FILE SCOPE:    notebooks/03_eda_analysis.ipynb (Section 5)
               src/stats.py  (CREATE NEW)
PRIORITY:      P1
DEPENDS ON:    PST-006
```

### Hypothesis Contract
```
H₀ (Null):       The proportion of job postings mentioning LLM-related skills
                  is the same in 2022 as in 2024.
H₁ (Alternative): The proportion differs significantly between 2022 and 2024.
α (Significance): 0.05
Test:            scipy.stats.chi2_contingency on 2×2 contingency table
```

### Contingency Table Contract
```python
# Agent must construct:
contingency_table = pd.crosstab(
    df_exploded[df_exploded['year'].isin([2022, 2024])]['year'],
    df_exploded[df_exploded['year'].isin([2022, 2024])]['skills_found'] \
        .isin(['LLM', 'RAG', 'Prompt Engineering'])
)
# Columns: [False (non-LLM), True (LLM-related)]
# Index: [2022, 2024]
# Minimum cell size: all 4 cells must be >= 5 (chi-square validity condition)
```

### Result Contract
```python
# Agent must produce and PRINT these exact variables:
chi2_stat: float          # chi-square statistic
p_value: float            # p-value from test (must be in [0.0, 1.0])
dof: int                  # degrees of freedom (expected: 1)
conclusion: str           # One of: "REJECT H₀" or "FAIL TO REJECT H₀"
interpretation: str       # One sentence plain-English interpretation
```

### Exact Failure Payload — Small Sample Guard:
```python
{
  "ticket": "PST-009",
  "error_type": "InsufficientSampleError",
  "year": "<year>",
  "skill_group": "LLM/RAG/Prompt Engineering",
  "count": "<n>",
  "minimum_required": 30,
  "message": "Cell count too small for valid chi-square test. Switch to higher-frequency skill.",
  "recovery": "Replace LLM group with 'Machine Learning' or expand year range to 2021–2024.",
  "agent_action": "WARN and substitute skill group"
}
```

### Unit Test Block — PST-009
```python
def test_p_value_is_valid_float():
    assert isinstance(p_value, float), \
        "FAIL PST-009-T9.1: p_value must be a float"
    assert 0.0 <= p_value <= 1.0, \
        f"FAIL PST-009-T9.1: p_value {p_value} outside valid range [0.0, 1.0]"

def test_dof_correct():
    assert dof == 1, \
        f"FAIL PST-009-T9.2: degrees of freedom should be 1 for 2×2 table, got {dof}"

def test_conclusion_is_valid_string():
    valid = {"REJECT H₀", "FAIL TO REJECT H₀"}
    assert conclusion in valid, \
        f"FAIL PST-009-T9.3: conclusion must be one of {valid}, got '{conclusion}'"

def test_interpretation_is_non_empty_string():
    assert isinstance(interpretation, str) and len(interpretation) > 20, \
        "FAIL PST-009-T9.4: interpretation must be a non-empty sentence"

def test_all_contingency_cells_valid():
    assert (contingency_table.values >= 5).all(), \
        "FAIL PST-009-T9.5: All contingency cells must be >= 5 for chi-square validity"
```

### Definition of Done — PST-009
```
✅ contingency_table constructed as 2×2 (year × LLM-related: True/False)
✅ All 4 contingency cells >= 5 (or fallback skill used with WARN payload)
✅ chi2_stat, p_value, dof, conclusion, interpretation all printed in notebook
✅ conclusion is exactly "REJECT H₀" or "FAIL TO REJECT H₀" (not ambiguous text)
✅ Markdown cell contains: null hypothesis, alpha, test choice, and plain-English conclusion
✅ All 5 unit tests pass
```

---
---

## PST-011 — Skill Gap Advisor — Groq Integration

```
TICKET ID:     PST-011
FEATURE:       LLM-powered skill gap analysis using Groq API
FILE SCOPE:    src/skill_gap_advisor.py  (CREATE NEW)
PRIORITY:      P2
DEPENDS ON:    PST-006 (top_rising_skills available)
```

### Prompt Contract (FROZEN)
```python
SYSTEM_PROMPT = """You are a Data Science career advisor with deep knowledge of the
current AI and ML job market. You give specific, honest, actionable advice.
You NEVER recommend skills that are not in the provided trending skills list.
You NEVER fabricate job market statistics."""

USER_PROMPT_TEMPLATE = """
A candidate's current skills: {user_skills_str}
Top trending skills in the 2024-2026 job market (from real dataset analysis): {trending_skills_str}

Identify the candidate's top 3 skill gaps from the trending list.
For each gap, explain in one sentence why it matters in the current market.
End with one learning priority recommendation.
Keep total response under 150 words.
"""
```

### Input Validation Contract
```python
# Valid input: comma-separated string of recognizable skills
# Invalid inputs and their required responses:

EMPTY_INPUT → return "Please enter at least one skill to analyze."
ALL_UNRECOGNIZED → return "No recognizable skills found. Try: Python, SQL, Tableau, Machine Learning"
INPUT_TOO_LONG (>500 chars) → truncate to first 500 chars, log warning, proceed
```

### API Call Contract
```python
# Model: "llama-3.3-70b-versatile"
# max_tokens: 300
# temperature: 0.3  (low — we want consistent, factual advice)
# Retry policy: 1 automatic retry after 60s wait on RateLimitError
# On second failure: return "Skill Gap Advisor temporarily unavailable. Try again shortly."
```

### Unit Test Block — PST-011
```python
def test_empty_input_returns_prompt():
    result = get_skill_gap_advice("", trending_skills)
    assert "Please enter" in result, \
        "FAIL PST-011-T11.1: Empty input must return prompt string, not API call"

def test_unrecognized_input_returns_guidance():
    result = get_skill_gap_advice("xyzabc123", trending_skills)
    assert "recognizable" in result.lower() or "try:" in result.lower(), \
        "FAIL PST-011-T11.2: Unrecognized input must return guidance string"

def test_valid_input_returns_non_empty_string():
    # Requires GROQ_API_KEY set in environment
    result = get_skill_gap_advice("Python, Excel, Pandas", trending_skills)
    assert isinstance(result, str) and len(result) > 50, \
        "FAIL PST-011-T11.3: Valid input must return non-empty LLM response"

def test_api_key_missing_raises_environment_error():
    import os
    original = os.environ.pop("GROQ_API_KEY", None)
    with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
        _initialize_groq_client()
    if original: os.environ["GROQ_API_KEY"] = original
```

### Definition of Done — PST-011
```
✅ src/skill_gap_advisor.py created with validate_user_input(), get_skill_gap_advice(), _initialize_groq_client()
✅ SYSTEM_PROMPT and USER_PROMPT_TEMPLATE match frozen contract exactly
✅ temperature=0.3 and max_tokens=300 used in API call
✅ Empty and unrecognized inputs handled without API call being made
✅ RateLimitError triggers 60s wait + 1 retry before fallback message
✅ All 4 unit tests pass
✅ GROQ_API_KEY never hardcoded — always read from os.environ or st.secrets
```

---
---

## PST-007 — Co-occurrence Matrix Builder

```
TICKET ID:     PST-007
FEATURE:       Build skill co-occurrence matrix and render heatmap
FILE SCOPE:    notebooks/03_eda_analysis.ipynb (Section 3)
               src/analysis.py  (EXTEND)
PRIORITY:      P1
DEPENDS ON:    PST-004
```

### Localized Description
The agent computes a pairwise co-occurrence matrix showing how often any two
skills appear together in the same job posting. Co-occurrence is computed at
the **job posting level** — not the long-format level. The agent must
reconstruct the wide-format skills list per job posting from the long-format
DataFrame, then iterate skill pairs using `itertools.combinations`. The output
matrix must be symmetric, square, and zero-diagonal.

### Computation Contract
```python
# Input: df_primary — wide-format DataFrame with 'skills_found' as list[str] per row
# Step 1: Filter to rows with >= 2 skills
# Step 2: Enumerate all unique pairs per row using combinations(sorted(skills), 2)
# Step 3: Count pair frequencies using collections.Counter
# Step 4: Build symmetric NxN matrix for top N skills by frequency

# Agent must produce these exact variables:
co_occur: Counter                  # {("Python", "SQL"): 3421, ...}
top_n_cooccur: int = 15            # Matrix built for top 15 skills only
co_matrix: pd.DataFrame            # shape (15, 15), index == columns == top_15_skill_names
                                   # diagonal must be 0
                                   # co_matrix.loc[A, B] == co_matrix.loc[B, A] (symmetric)
top_pair: tuple[str, str]          # Most frequently co-occurring pair
top_pair_count: int                # Count for top_pair
```

### Exact Failure Payloads

**Failure Payload M — Fewer Than 5 Co-occurring Pairs Found:**
```python
{
  "ticket": "PST-007",
  "error_type": "InsufficientCooccurrenceError",
  "pairs_found": "<n>",
  "message": "Too few skill pairs found. Most job postings may list only one skill.",
  "recovery": "Check df_primary['skills_found'].apply(len).describe() — if median is 1, expand skill_taxonomy.json with more entries.",
  "agent_action": "HALT"
}
```

**Failure Payload N — Non-Symmetric Matrix Detected:**
```python
{
  "ticket": "PST-007",
  "error_type": "MatrixSymmetryError",
  "message": "co_matrix is not symmetric. Pair counting logic has a directional bug.",
  "recovery": "Verify combinations() is used with sorted() to enforce canonical pair order.",
  "agent_action": "FIX and recompute"
}
```

### Implementation Contract
```python
# src/analysis.py — Add to existing file:

from itertools import combinations
from collections import Counter

def build_cooccurrence(df_wide: pd.DataFrame,
                       skills_col: str = "skills_found",
                       top_n: int = 15) -> tuple[Counter, pd.DataFrame]:
    """
    Computes pairwise skill co-occurrence from wide-format DataFrame.
    Args:
        df_wide: Wide-format DataFrame with skills_found as list[str]
        skills_col: Column containing skill lists
        top_n: Number of top skills to include in matrix
    Returns:
        (co_occur Counter, co_matrix DataFrame)
    Raises:
        SystemExit(1) with Payload M if len(co_occur) < 5
        SystemExit(1) with Payload N if matrix is not symmetric
    """

def validate_matrix_symmetry(co_matrix: pd.DataFrame) -> bool:
    """
    Returns True if co_matrix equals its transpose element-wise.
    Returns False otherwise.
    """

def get_top_pair(co_occur: Counter) -> tuple[tuple[str, str], int]:
    """
    Returns ((skill_a, skill_b), count) for the most common pair.
    """
```

### Chart Contract
```python
# Seaborn heatmap:
# Data: co_matrix (15×15)
# cmap: "Blues"
# annot: True (show counts in cells)
# fmt: "d" (integer format)
# figsize: (14, 12)
# Title: f"'{top_pair[0]}' + '{top_pair[1]}' Is the Most Common Skill Combo
#          ({top_pair_count:,} Co-occurrences)"
# Export: "assets/charts/03_skill_cooccurrence.png", dpi=150
```

### Unit Test Block — PST-007
```python
# tests/test_pst007_cooccurrence.py

import pytest
import pandas as pd
from collections import Counter
from src.analysis import build_cooccurrence, validate_matrix_symmetry, get_top_pair

SAMPLE_WIDE = pd.DataFrame({
    "skills_found": [
        ["Python", "SQL", "Pandas"],
        ["Python", "Tableau"],
        ["SQL", "Power BI", "Python"],
        ["Machine Learning", "Python", "SQL"]
    ]
})

# --- Test 7.1: Counter has entries ---
def test_cooccurrence_counter_non_empty():
    co_occur, _ = build_cooccurrence(SAMPLE_WIDE)
    assert len(co_occur) > 0, \
        "FAIL PST-007-T7.1: co_occur Counter must not be empty"

# --- Test 7.2: Known pair counted correctly ---
def test_known_pair_count():
    co_occur, _ = build_cooccurrence(SAMPLE_WIDE)
    # Python + SQL appear together in rows 0, 2, 3 → count = 3
    python_sql = co_occur.get(("Python", "SQL"), co_occur.get(("SQL", "Python"), 0))
    assert python_sql == 3, \
        f"FAIL PST-007-T7.2: Python+SQL should co-occur 3 times, got {python_sql}"

# --- Test 7.3: Matrix is symmetric ---
def test_matrix_is_symmetric():
    _, co_matrix = build_cooccurrence(SAMPLE_WIDE)
    assert validate_matrix_symmetry(co_matrix), \
        "FAIL PST-007-T7.3: co_matrix must be symmetric (co_matrix == co_matrix.T)"

# --- Test 7.4: Matrix diagonal is zero ---
def test_matrix_diagonal_is_zero():
    _, co_matrix = build_cooccurrence(SAMPLE_WIDE)
    import numpy as np
    diag_vals = np.diag(co_matrix.values)
    assert (diag_vals == 0).all(), \
        "FAIL PST-007-T7.4: Diagonal of co_matrix must be all zeros (skill with itself)"

# --- Test 7.5: Matrix shape is (top_n x top_n) ---
def test_matrix_shape():
    _, co_matrix = build_cooccurrence(SAMPLE_WIDE, top_n=3)
    assert co_matrix.shape == (3, 3), \
        f"FAIL PST-007-T7.5: Matrix shape should be (3,3) for top_n=3, got {co_matrix.shape}"

# --- Test 7.6: get_top_pair returns valid tuple ---
def test_get_top_pair():
    co_occur, _ = build_cooccurrence(SAMPLE_WIDE)
    pair, count = get_top_pair(co_occur)
    assert isinstance(pair, tuple) and len(pair) == 2, \
        "FAIL PST-007-T7.6: get_top_pair must return ((str, str), int)"
    assert isinstance(count, int) and count > 0, \
        "FAIL PST-007-T7.6: top pair count must be a positive int"
```

### Definition of Done — PST-007
```
✅ build_cooccurrence() added to src/analysis.py
✅ co_occur Counter has entries for all observed skill pairs
✅ co_matrix is (15×15), symmetric, zero-diagonal
✅ co_matrix index == co_matrix columns (same skill names both axes)
✅ top_pair and top_pair_count computed from actual Counter (not hardcoded)
✅ Chart title embeds actual top_pair skill names and actual count
✅ assets/charts/03_skill_cooccurrence.png exported at 150 DPI
✅ All 6 unit tests pass
```

---
---

## PST-008 — Experience-Level Cross Analysis

```
TICKET ID:     PST-008
FEATURE:       Cross-tabulate skill demand by experience level and render grouped bar chart
FILE SCOPE:    notebooks/03_eda_analysis.ipynb (Section 4)
               src/analysis.py  (EXTEND)
PRIORITY:      P1
DEPENDS ON:    PST-004
```

### Localized Description
The agent builds a cross-tabulation of skills × experience level to identify
which skills are fresher-friendly versus senior-only. The agent must normalize
the crosstab to proportions (not raw counts) within each experience level, so
that levels with different sample sizes are fairly comparable. A minimum of 3
distinct experience levels must be present in the data for the analysis to
be valid.

### Computation Contract
```python
# Experience level standardization map (agent must apply before crosstab):
EXP_LEVEL_MAP = {
    "EN": "Entry-Level",
    "MI": "Mid-Level",
    "SE": "Senior",
    "EX": "Executive",
    "Not Specified": "Not Specified"
}

# Agent must produce:
exp_counts: pd.Series            # Count of rows per experience level (to show sample sizes)
exp_levels_present: list[str]    # Distinct levels in dataset (must have >= 3)
crosstab_raw: pd.DataFrame       # pd.crosstab(experience_level, skills_found)
crosstab_pct: pd.DataFrame       # crosstab_raw.div(crosstab_raw.sum(axis=1), axis=0) * 100
                                 # Rows: experience levels | Columns: top 10 skills by total
top_fresher_skill: str           # Skill with highest pct in "Entry-Level" row
top_senior_skill: str            # Skill with highest pct in "Senior" row
```

### Exact Failure Payloads

**Failure Payload O — Fewer Than 3 Experience Levels:**
```python
{
  "ticket": "PST-008",
  "error_type": "InsufficientExperienceLevelsError",
  "levels_found": "<list of distinct levels>",
  "minimum_required": 3,
  "message": "Fewer than 3 experience levels in dataset. Cross-analysis will be misleading.",
  "recovery": "Check experience_level column after cleaning. Verify PST-002 fill logic ran correctly.",
  "agent_action": "WARN — proceed with available levels but add disclaimer markdown"
}
```

**Failure Payload P — Crosstab Rows Don't Sum to 100%:**
```python
{
  "ticket": "PST-008",
  "error_type": "NormalizationError",
  "row_sums": "<list of row totals from crosstab_pct>",
  "message": "crosstab_pct rows do not sum to 100. Normalization step failed.",
  "recovery": "Re-apply: crosstab_pct = crosstab_raw.div(crosstab_raw.sum(axis=1), axis=0) * 100",
  "agent_action": "FIX and recompute"
}
```

### Implementation Contract
```python
# src/analysis.py — Add to existing file:

def standardize_experience_levels(df: pd.DataFrame,
                                   col: str = "experience_level",
                                   level_map: dict = EXP_LEVEL_MAP) -> pd.DataFrame:
    """
    Maps coded experience levels to human-readable labels.
    Unmapped values retained as-is.
    Returns: DataFrame with experience_level column relabeled.
    """

def build_experience_crosstab(df_long: pd.DataFrame,
                               exp_col: str = "experience_level",
                               skill_col: str = "skills_found",
                               top_n_skills: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Builds raw and percentage crosstabs for top N skills × experience levels.
    Validates: >= 3 distinct experience levels (Payload O on failure).
    Validates: crosstab_pct rows sum to ~100% within ±0.1 tolerance (Payload P on failure).
    Returns: (crosstab_raw, crosstab_pct)
    """

def get_level_champion_skills(crosstab_pct: pd.DataFrame) -> dict[str, str]:
    """
    Returns {experience_level: top_skill} for each row in crosstab_pct.
    Example: {"Entry-Level": "Python", "Senior": "Spark"}
    """
```

### Chart Contract
```python
# Matplotlib grouped bar chart:
# Data: crosstab_pct (top 10 skills, all experience levels)
# figsize: (16, 8)
# legend: experience levels
# xlabel: "Skill"
# ylabel: "% of Job Postings at This Level"
# Title: f"'{top_fresher_skill}' Dominates Entry-Level, '{top_senior_skill}' Rises at Senior Level"
# Export: "assets/charts/04_skill_by_experience.png", dpi=150
```

### Unit Test Block — PST-008
```python
# tests/test_pst008_experience.py

import pytest
import pandas as pd
import numpy as np
from src.analysis import (
    standardize_experience_levels, build_experience_crosstab,
    get_level_champion_skills
)

SAMPLE_LONG = pd.DataFrame({
    "skills_found": ["Python", "SQL", "Python", "Spark", "Python",
                     "SQL", "Tableau", "Python", "SQL", "Spark"],
    "experience_level": ["EN", "EN", "MI", "MI", "SE",
                          "SE", "EN", "EX", "EX", "SE"]
})

# --- Test 8.1: Experience level standardization applied ---
def test_exp_level_standardized():
    result = standardize_experience_levels(SAMPLE_LONG.copy())
    assert "Entry-Level" in result['experience_level'].values, \
        "FAIL PST-008-T8.1: 'EN' must map to 'Entry-Level'"
    assert "EN" not in result['experience_level'].values, \
        "FAIL PST-008-T8.1: Coded 'EN' must not remain after standardization"

# --- Test 8.2: crosstab_pct rows sum to 100 ---
def test_crosstab_rows_sum_to_100():
    df = standardize_experience_levels(SAMPLE_LONG.copy())
    _, crosstab_pct = build_experience_crosstab(df)
    row_sums = crosstab_pct.sum(axis=1)
    assert (row_sums - 100).abs().max() < 0.1, \
        f"FAIL PST-008-T8.2: crosstab_pct rows must sum to ~100%, got: {row_sums.tolist()}"

# --- Test 8.3: crosstab_raw values are integers (counts) ---
def test_crosstab_raw_is_integer():
    df = standardize_experience_levels(SAMPLE_LONG.copy())
    crosstab_raw, _ = build_experience_crosstab(df)
    assert crosstab_raw.dtypes.apply(lambda t: np.issubdtype(t, np.integer)).all(), \
        "FAIL PST-008-T8.3: crosstab_raw must contain integer counts"

# --- Test 8.4: get_level_champion_skills returns dict ---
def test_champion_skills_dict():
    df = standardize_experience_levels(SAMPLE_LONG.copy())
    _, crosstab_pct = build_experience_crosstab(df)
    champions = get_level_champion_skills(crosstab_pct)
    assert isinstance(champions, dict), \
        "FAIL PST-008-T8.4: get_level_champion_skills must return a dict"
    assert all(isinstance(v, str) for v in champions.values()), \
        "FAIL PST-008-T8.4: All champion skill values must be strings"

# --- Test 8.5: top_fresher_skill and top_senior_skill are different variables ---
def test_top_skills_are_distinct_extractions():
    df = standardize_experience_levels(SAMPLE_LONG.copy())
    _, crosstab_pct = build_experience_crosstab(df)
    champions = get_level_champion_skills(crosstab_pct)
    # Both must exist (no KeyError)
    assert "Entry-Level" in champions, \
        "FAIL PST-008-T8.5: champions must contain 'Entry-Level' key"
    assert "Senior" in champions, \
        "FAIL PST-008-T8.5: champions must contain 'Senior' key"
```

### Definition of Done — PST-008
```
✅ standardize_experience_levels() applied to df_long before crosstab
✅ build_experience_crosstab() validates >= 3 distinct levels
✅ crosstab_pct rows each sum to 100% (±0.1 tolerance)
✅ top_fresher_skill and top_senior_skill computed from actual data
✅ Chart title embeds actual skill names from champion computation
✅ assets/charts/04_skill_by_experience.png exported at 150 DPI
✅ Markdown cell interprets which skills are "fresher-accessible" vs "senior-expected"
✅ All 5 unit tests pass
```

---
---

## PST-010 — Visualization Export Pipeline

```
TICKET ID:     PST-010
FEATURE:       Finalize all charts and export to canonical PNG paths
FILE SCOPE:    notebooks/04_visualization_report.ipynb  (CREATE NEW)
               src/viz.py  (CREATE NEW)
               assets/charts/  (POPULATE)
PRIORITY:      P2
DEPENDS ON:    PST-005, PST-006, PST-007, PST-008, PST-009
```

### Localized Description
The agent creates a dedicated visualization notebook (`04_visualization_report.ipynb`)
that imports all computed variables from the analysis notebooks and produces
publication-ready chart exports. This notebook is the single source for all
chart artifacts. Every chart must pass the Title Integrity rule (G-5): titles
contain real computed values, never placeholders. An additional Word Cloud chart
is built here as the fifth artifact.

### Canonical Export Manifest
```
# Agent must produce ALL 5 files at exactly these paths:
assets/charts/01_skill_frequency.png       ← From PST-005
assets/charts/02_skill_trend.png           ← From PST-006
assets/charts/02_skill_trend.html          ← Plotly interactive version
assets/charts/03_skill_cooccurrence.png    ← From PST-007
assets/charts/04_skill_by_experience.png   ← From PST-008
assets/charts/05_skill_wordcloud.png       ← NEW in PST-010
```

### Word Cloud Contract (New in PST-010)
```python
# Input: df_exploded['skills_found'] — all skill mentions, weighted by frequency
# Weights: skill_counts dict {skill: mention_count} from PST-005
# Agent must use WeightedWordCloud approach (frequencies= param)

from wordcloud import WordCloud

skill_freq_dict: dict[str, int]    # {skill_name: total_mention_count}
# Filter: only include top 40 skills to avoid clutter

wc = WordCloud(
    width=1600,
    height=800,
    background_color="white",
    colormap="Blues",
    max_words=40,
    prefer_horizontal=0.9
).generate_from_frequencies(skill_freq_dict)

# Title: "The Data Science Skill Landscape in 2026: A Frequency-Weighted View"
# Export: "assets/charts/05_skill_wordcloud.png", dpi=150
```

### Chart Style Standards (Apply to All 5 Charts)
```python
CHART_STANDARDS = {
    "dpi": 150,
    "bbox_inches": "tight",
    "font_family": "sans-serif",
    "title_fontsize": 14,
    "axis_label_fontsize": 11,
    "tick_fontsize": 9,
    "seaborn_theme": "whitegrid",
    "plotly_template": "plotly_white",
    "figure_facecolor": "white"
}
# Agent must apply sns.set_theme(style="whitegrid") at top of notebook
# Agent must set plt.rcParams["figure.facecolor"] = "white"
```

### Exact Failure Payloads

**Failure Payload Q — PNG Export File Missing After savefig:**
```python
{
  "ticket": "PST-010",
  "error_type": "ExportFailureError",
  "expected_path": "<path>",
  "message": "savefig() completed without error but file not found on disk.",
  "recovery": "Verify os.makedirs('assets/charts', exist_ok=True) ran before savefig. Check working directory with os.getcwd().",
  "agent_action": "FIX path and re-export"
}
```

**Failure Payload R — Word Cloud Input is Empty:**
```python
{
  "ticket": "PST-010",
  "error_type": "WordCloudEmptyInputError",
  "skill_freq_dict_length": 0,
  "message": "skill_freq_dict is empty. PST-005 skill_counts may not be loaded correctly.",
  "recovery": "Re-import or recompute skill_counts from primary_skills_long.csv before running PST-010.",
  "agent_action": "HALT"
}
```

### Implementation Contract
```python
# src/viz.py

import os
import matplotlib.pyplot as plt
import seaborn as sns

def apply_chart_standards() -> None:
    """
    Sets global matplotlib and seaborn style standards.
    Must be called once at top of 04_visualization_report.ipynb.
    """

def export_figure(fig: plt.Figure,
                  path: str,
                  dpi: int = 150) -> None:
    """
    Saves matplotlib figure to path with existence check.
    Creates parent directory if missing (os.makedirs, exist_ok=True).
    Verifies file exists after save — prints Payload Q and halts if missing.
    Prints: "[PST-010] ✅ Exported: <path> (<file_size_kb> KB)"
    """

def export_plotly(fig,
                  html_path: str,
                  png_path: str) -> None:
    """
    Saves Plotly figure to both HTML and PNG formats.
    HTML: fig.write_html(html_path)
    PNG:  fig.write_image(png_path, width=1400, height=700, scale=2)
    Verifies both files exist after save.
    """

def build_wordcloud(skill_freq_dict: dict[str, int],
                    top_n: int = 40) -> plt.Figure:
    """
    Builds and returns a matplotlib Figure containing the word cloud.
    On empty dict: prints Payload R and calls sys.exit(1).
    """
```

### Unit Test Block — PST-010
```python
# tests/test_pst010_exports.py

import os
import pytest

REQUIRED_EXPORTS = [
    "assets/charts/01_skill_frequency.png",
    "assets/charts/02_skill_trend.png",
    "assets/charts/02_skill_trend.html",
    "assets/charts/03_skill_cooccurrence.png",
    "assets/charts/04_skill_by_experience.png",
    "assets/charts/05_skill_wordcloud.png"
]

# --- Test 10.1: All 6 export files exist ---
@pytest.mark.parametrize("path", REQUIRED_EXPORTS)
def test_export_file_exists(path):
    assert os.path.exists(path), \
        f"FAIL PST-010-T10.1: Required export file not found: {path}"

# --- Test 10.2: PNG files are non-zero in size ---
@pytest.mark.parametrize("path", [p for p in REQUIRED_EXPORTS if p.endswith(".png")])
def test_png_file_non_empty(path):
    size = os.path.getsize(path)
    assert size > 5000, \
        f"FAIL PST-010-T10.2: PNG file too small ({size} bytes) — likely blank: {path}"

# --- Test 10.3: HTML file contains Plotly signature ---
def test_html_contains_plotly():
    html_path = "assets/charts/02_skill_trend.html"
    with open(html_path, "r") as f:
        content = f.read()
    assert "plotly" in content.lower(), \
        "FAIL PST-010-T10.3: Trend HTML file must contain Plotly chart markup"

# --- Test 10.4: export_figure raises on empty dict for wordcloud ---
def test_wordcloud_empty_input_exits():
    from src.viz import build_wordcloud
    with pytest.raises(SystemExit):
        build_wordcloud({})

# --- Test 10.5: No chart title contains placeholder text ---
def test_no_placeholder_titles():
    # Manual review gate — agent must confirm before closing ticket:
    placeholders = ["[skill]", "X%", "[INSERT", "TODO", "placeholder"]
    for path in REQUIRED_EXPORTS:
        if path.endswith(".html"):
            with open(path, "r") as f:
                content = f.read()
            for p in placeholders:
                assert p not in content, \
                    f"FAIL PST-010-T10.5: Placeholder '{p}' found in {path}"
```

### Definition of Done — PST-010
```
✅ src/viz.py created with apply_chart_standards(), export_figure(), export_plotly(), build_wordcloud()
✅ 04_visualization_report.ipynb created and calls apply_chart_standards() at top
✅ All 6 canonical export files exist at exact paths in EXPORT MANIFEST
✅ All PNG files are > 5KB (non-blank)
✅ HTML file contains valid Plotly markup
✅ Word cloud uses generate_from_frequencies() with skill_freq_dict (not raw text)
✅ No placeholder text in any chart title
✅ All 5 unit tests pass
```

---
---

## PST-012 — Streamlit App Scaffold

```
TICKET ID:     PST-012
FEATURE:       Build 4-panel interactive Streamlit app
FILE SCOPE:    app.py  (CREATE NEW)
               .streamlit/config.toml  (CREATE NEW)
               .streamlit/secrets.toml  (CREATE NEW — gitignored)
PRIORITY:      P2
DEPENDS ON:    PST-010 (charts available), PST-011 (advisor available)
```

### Localized Description
The agent builds a multi-tab Streamlit application with 4 distinct panels.
All data loading uses `@st.cache_data` to avoid reloading on each interaction.
The Groq API call in Panel 4 must run only when the user explicitly submits
input — never on page load. All panels must render without error on an empty
cache state (first load from CSV) and also on a warm cache state.

### Panel Contract (4 Panels — All Required)

**Panel 1 — Overview**
```python
# Tab label: "📊 Overview"
# Contents:
#   Row 1: 3 KPI metric cards using st.metric():
#     - "Total Job Postings Analyzed": df_primary['job_title'].count() formatted with commas
#     - "Unique Skills Tracked": len(taxonomy_flat) as integer
#     - "Dataset Coverage": "2020 – 2026"
#   Row 2: Top 20 skills horizontal bar chart (static Plotly from PST-005)
#   Row 3: Markdown insight sentence (from PST-005 analysis)
```

**Panel 2 — Trend Explorer**
```python
# Tab label: "📈 Skill Trends"
# Contents:
#   st.multiselect("Select skills to compare:", options=top_20_skills, default=top_5_skills)
#   Date range slider: st.slider("Year range:", min=2020, max=2026, value=(2020, 2026))
#   Plotly multi-line chart filtered by selected skills and year range
#   → Chart updates reactively on selection change (Streamlit re-run handles this)
```

**Panel 3 — Co-occurrence Heatmap**
```python
# Tab label: "🔥 Skill Combos"
# Contents:
#   st.info() box explaining what co-occurrence means (1–2 sentences)
#   Static Plotly heatmap of co_matrix (top 15 skills)
#   st.caption() with top pair insight: "'{pair[0]}' + '{pair[1]}' co-occur {count:,} times"
```

**Panel 4 — Skill Gap Advisor**
```python
# Tab label: "🤖 Skill Gap Advisor"
# Contents:
#   st.text_area("Enter your current skills (comma-separated):", height=100)
#   st.button("Analyse My Gaps")
#   On button click ONLY (not on page load):
#     → Call validate_user_input() from PST-011
#     → If valid: call get_skill_gap_advice() with st.spinner("Analysing...")
#     → Display response in st.success() box
#     → If invalid: display error in st.warning() box
#   st.caption("Powered by Groq API · LLaMA 3.3 70B · Based on real 2020–2026 job market data")
```

### Config Contract
```toml
# .streamlit/config.toml
[theme]
primaryColor = "#2563EB"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F1F5F9"
textColor = "#1E293B"
font = "sans serif"

[server]
headless = true
```

```toml
# .streamlit/secrets.toml  (GITIGNORED — never commit)
GROQ_API_KEY = "gsk_..."
```

### Exact Failure Payloads

**Failure Payload S — Data File Missing on App Start:**
```python
# In app.py, wrapped around @st.cache_data load function:
{
  "ticket": "PST-012",
  "error_type": "AppDataNotFoundError",
  "missing_file": "data/clean/primary_skills_long.csv",
  "message": "App cannot start without clean data. Run notebooks 01–03 first.",
  "ui_action": "st.error('Data file not found. Run data pipeline first.') + st.stop()"
}
```

**Failure Payload T — Panel 4 API Call on Page Load:**
```python
{
  "ticket": "PST-012",
  "error_type": "UnguardedAPICallError",
  "location": "Panel 4 — Skill Gap Advisor",
  "message": "Groq API called without user button click. This wastes quota and adds latency.",
  "recovery": "Wrap all API calls in: if st.button('Analyse My Gaps'): ...",
  "agent_action": "FIX before deployment"
}
```

### Implementation Contract
```python
# app.py — Top-level structure the agent must follow:

import streamlit as st
import pandas as pd
import plotly.express as px
from src.skill_extractor import load_taxonomy, flatten_taxonomy
from src.skill_gap_advisor import validate_user_input, get_skill_gap_advice

st.set_page_config(
    page_title="Skill Trend Analysis",
    page_icon="📊",
    layout="wide"
)

@st.cache_data
def load_data() -> pd.DataFrame:
    """Load primary_skills_long.csv with error handling (Payload S)."""

@st.cache_data
def load_taxonomy_cached() -> dict:
    """Load skill taxonomy JSON."""

# --- Tab scaffold (agent must use exactly these tab labels) ---
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Overview",
    "📈 Skill Trends",
    "🔥 Skill Combos",
    "🤖 Skill Gap Advisor"
])

with tab1: render_overview(df, taxonomy)
with tab2: render_trends(df)
with tab3: render_heatmap(df)
with tab4: render_gap_advisor(df)
```

### Unit Test Block — PST-012
```python
# tests/test_pst012_app.py

# Note: Streamlit apps are tested using subprocess launch + availability check
# and logic-level unit tests on underlying functions

import os
import subprocess
import time
import requests
import pandas as pd

# --- Test 12.1: app.py exists ---
def test_app_file_exists():
    assert os.path.exists("app.py"), \
        "FAIL PST-012-T12.1: app.py not found in repo root"

# --- Test 12.2: app.py imports without error ---
def test_app_imports():
    result = subprocess.run(
        ["python", "-c", "import app"],
        capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, \
        f"FAIL PST-012-T12.2: app.py has import errors:\n{result.stderr}"

# --- Test 12.3: config.toml exists ---
def test_config_toml_exists():
    assert os.path.exists(".streamlit/config.toml"), \
        "FAIL PST-012-T12.3: .streamlit/config.toml not found"

# --- Test 12.4: secrets.toml is gitignored ---
def test_secrets_gitignored():
    with open(".gitignore", "r") as f:
        gitignore = f.read()
    assert "secrets.toml" in gitignore or ".streamlit/secrets.toml" in gitignore, \
        "FAIL PST-012-T12.4: secrets.toml must be listed in .gitignore"

# --- Test 12.5: Panel 4 API not called on cold load (logic guard check) ---
def test_api_guarded_by_button():
    with open("app.py", "r") as f:
        content = f.read()
    # Verify get_skill_gap_advice is only called inside an if-button block
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "get_skill_gap_advice" in line:
            context = "\n".join(lines[max(0, i-5):i])
            assert "st.button" in context or "if submitted" in context, \
                f"FAIL PST-012-T12.5: get_skill_gap_advice at line {i+1} not guarded by button check"
```

### Definition of Done — PST-012
```
✅ app.py created with exactly 4 tabs using specified labels
✅ @st.cache_data applied to load_data() and load_taxonomy_cached()
✅ KPI metrics display real computed values (not hardcoded strings)
✅ Panel 2 multiselect and year slider update chart reactively
✅ Panel 4 API call strictly inside if st.button(...): block
✅ .streamlit/config.toml created with theme colors
✅ .streamlit/secrets.toml in .gitignore
✅ st.stop() called after st.error() if data file missing
✅ All 5 unit tests pass
✅ streamlit run app.py launches without traceback at localhost:8501
```

---
---

## PST-013 — Streamlit Cloud Deployment

```
TICKET ID:     PST-013
FEATURE:       Deploy app.py to Streamlit Cloud with live public URL
FILE SCOPE:    requirements.txt  (FINALIZE)
               GitHub repo main branch  (FINAL PUSH)
               Streamlit Cloud dashboard  (CONFIGURE)
PRIORITY:      P2
DEPENDS ON:    PST-012
```

### Localized Description
The agent prepares the repository for cloud deployment by finalizing
`requirements.txt`, pushing the clean state to GitHub main, connecting the
repo to Streamlit Cloud, and configuring secrets. The agent must verify
the live URL functions correctly in an incognito browser session before
marking this ticket RESOLVED.

### Requirements.txt Contract (EXACT — no version wildcards)
```
# requirements.txt — Agent must include ALL of these:
pandas>=1.5.0
numpy>=1.23.0
matplotlib>=3.5.0
seaborn>=0.12.0
plotly>=5.10.0
wordcloud>=1.9.0
groq>=0.4.0
scipy>=1.9.0
streamlit>=1.28.0
kaleido>=0.2.1
```
```
# kaleido is REQUIRED for Plotly static PNG export (fig.write_image)
# Missing kaleido is the most common Streamlit Cloud deployment failure
# for Plotly-heavy apps — agent must verify it is present
```

### Pre-Deployment Checklist Contract
```
AGENT MUST VERIFY BEFORE PUSHING TO MAIN:

[ ] requirements.txt includes kaleido
[ ] .gitignore excludes: data/raw/, *.csv (files >10MB), .streamlit/secrets.toml
[ ] data/clean/primary_skills_long.csv is committed (it's the app's data source)
    → Verify: git ls-files data/clean/ shows the CSV
[ ] No hardcoded API keys anywhere in app.py or src/*.py
    → Verify: grep -r "gsk_" . returns no results
[ ] All imports in app.py resolve against requirements.txt
[ ] GROQ_API_KEY is set in Streamlit Cloud Secrets dashboard
    → Path: Streamlit Cloud → App Settings → Secrets → Add GROQ_API_KEY
```

### Exact Failure Payloads

**Failure Payload U — kaleido Missing on Cloud:**
```python
{
  "ticket": "PST-013",
  "error_type": "KaleidoMissingError",
  "symptom": "ValueError: install kaleido or orca on Streamlit Cloud logs",
  "message": "Plotly PNG export fails without kaleido. App will crash on Panel 2 chart.",
  "recovery": "Add 'kaleido>=0.2.1' to requirements.txt and redeploy.",
  "agent_action": "FIX requirements.txt + trigger redeploy"
}
```

**Failure Payload V — API Key Not Found on Live App:**
```python
{
  "ticket": "PST-013",
  "error_type": "LiveAPIKeyError",
  "symptom": "Panel 4 shows: 'Skill Gap Advisor temporarily unavailable'",
  "message": "GROQ_API_KEY not configured in Streamlit Cloud Secrets.",
  "recovery": "Streamlit Cloud dashboard → App → Settings → Secrets → paste key.",
  "agent_action": "Configure secret and hard-refresh the live URL"
}
```

### Deployment Verification Protocol
```
POST-DEPLOYMENT CHECKS (agent must run all 4 before closing ticket):

CHECK 1: Open live URL in incognito browser
  → PASS: App title "Skill Trend Analysis" visible within 30 seconds
  → FAIL: 504, 404, or infinite spinner → check Streamlit Cloud logs

CHECK 2: Verify KPI cards show real numbers (not "None" or "0")
  → PASS: Three metrics display non-zero values
  → FAIL: "None" visible → data CSV not committed to repo

CHECK 3: Verify skill trend chart loads in Panel 2
  → PASS: Multi-line chart renders with at least 3 skill lines
  → FAIL: Blank chart → kaleido missing or trend_df empty

CHECK 4: Verify Skill Gap Advisor responds (Panel 4)
  → Input: "Python, SQL, Excel"
  → PASS: LLM response appears within 15 seconds
  → FAIL: Error message → check GROQ_API_KEY in Streamlit Secrets
```

### Unit Test Block — PST-013
```python
# tests/test_pst013_deployment.py

import os
import subprocess

# --- Test 13.1: requirements.txt contains kaleido ---
def test_requirements_has_kaleido():
    with open("requirements.txt", "r") as f:
        content = f.read()
    assert "kaleido" in content, \
        "FAIL PST-013-T13.1: kaleido missing from requirements.txt — Plotly PNG export will fail on cloud"

# --- Test 13.2: No hardcoded API keys in source files ---
def test_no_hardcoded_api_keys():
    result = subprocess.run(
        ["grep", "-r", "gsk_", "src/", "app.py"],
        capture_output=True, text=True
    )
    assert result.returncode != 0 or result.stdout.strip() == "", \
        f"FAIL PST-013-T13.2: Hardcoded Groq API key found:\n{result.stdout}"

# --- Test 13.3: data/clean CSV committed to git ---
def test_clean_data_in_git():
    result = subprocess.run(
        ["git", "ls-files", "data/clean/primary_skills_long.csv"],
        capture_output=True, text=True
    )
    assert "primary_skills_long.csv" in result.stdout, \
        "FAIL PST-013-T13.3: primary_skills_long.csv not committed to git — app will crash on cloud"

# --- Test 13.4: secrets.toml not in git ---
def test_secrets_not_committed():
    result = subprocess.run(
        ["git", "ls-files", ".streamlit/secrets.toml"],
        capture_output=True, text=True
    )
    assert result.stdout.strip() == "", \
        "FAIL PST-013-T13.4: secrets.toml IS committed to git — API key is exposed. Remove immediately."

# --- Test 13.5: All requirements installable (dry run) ---
def test_requirements_installable():
    result = subprocess.run(
        ["pip", "install", "--dry-run", "-r", "requirements.txt"],
        capture_output=True, text=True
    )
    assert result.returncode == 0, \
        f"FAIL PST-013-T13.5: requirements.txt has unresolvable packages:\n{result.stderr}"
```

### Definition of Done — PST-013
```
✅ requirements.txt includes all 10 packages including kaleido
✅ All 5 pre-deployment checklist items verified
✅ No hardcoded API keys in any committed file
✅ data/clean/primary_skills_long.csv committed and tracked by git
✅ GROQ_API_KEY set in Streamlit Cloud Secrets dashboard
✅ All 4 post-deployment checks pass
✅ Live URL recorded in MISSION_PLAN.md Step 8 entry
✅ All 5 unit tests pass
```

---
---

## PST-014 — Power BI Dashboard Export

```
TICKET ID:     PST-014
FEATURE:       Build Power BI dashboard with 4 visuals and export as PDF
FILE SCOPE:    dashboards/skill_trend_powerbi.pbix  (CREATE)
               dashboards/skill_trend_dashboard.pdf  (EXPORT)
PRIORITY:      P3
DEPENDS ON:    PST-004 (primary_skills_long.csv available)
NOTE:          This ticket is executed manually — no Python agent action.
               The agent's role is to verify the output files exist and meet spec.
```

### Localized Description
The developer imports `primary_skills_long.csv` into Power BI Desktop and
builds a 4-visual dashboard using only drag-and-drop features. No DAX
measures are required beyond simple aggregations. This ticket is a manual
execution ticket — the agent verifies the output artifacts post-build using
file existence and PDF content checks.

### Visual Contract (4 Visuals — All Required)

```
VISUAL 1 — Skill Frequency Bar Chart
  Type:       Clustered Bar Chart
  X-axis:     skills_found
  Y-axis:     Count of skills_found (aggregation: Count)
  Sort:       Descending by count
  Filter:     Top 20 skills by count
  Title:      "Top 20 Most In-Demand Skills (2020–2026)"

VISUAL 2 — Skill Trend Line Chart
  Type:       Line Chart
  X-axis:     year (integer, treated as continuous)
  Y-axis:     Count of skills_found
  Legend:     skills_found (filter to top 5 by total)
  Title:      "Skill Demand Trend by Year (Top 5 Skills)"

VISUAL 3 — Skill by Experience Level Matrix
  Type:       Matrix Visual
  Rows:       experience_level
  Columns:    skills_found (top 10)
  Values:     Count of skills_found
  Title:      "Skill Demand by Experience Level"

VISUAL 4 — KPI Cards (3 Cards in One Row)
  Card A:     Total Rows = COUNT(skills_found)
  Card B:     Unique Skills = DISTINCTCOUNT(skills_found)
  Card C:     Year Span — Text card: "2020 – 2026"
```

### Slicer Contract
```
SLICER 1 — Year Slicer
  Field:      year
  Type:       Between (range slider)
  Placement:  Top of report canvas
  All 3 chart visuals must respond to this slicer.
  KPI Cards are exempt from slicer (show total regardless).
```

### Export Contract
```
PDF Export:
  File path: dashboards/skill_trend_dashboard.pdf
  Pages: 1 (single-page dashboard)
  Method: Power BI Desktop → File → Export → Export to PDF

PBIX Save:
  File path: dashboards/skill_trend_powerbi.pbix
  Must be saveable and reopenable without data refresh errors
```

### Exact Failure Payloads

**Failure Payload W — CSV Import Shows No Data in Power BI:**
```python
{
  "ticket": "PST-014",
  "error_type": "PowerBIImportError",
  "symptom": "Visuals show 'No data' or blank after CSV import",
  "message": "Power BI cannot read the CSV. Likely cause: Period dtype columns (month, quarter) are incompatible.",
  "recovery": "Export a modified CSV with month and quarter as plain strings: df['month'] = df['month'].astype(str)",
  "agent_action": "Create data/clean/primary_skills_powerbi.csv with Period cols converted to string"
}
```

**Failure Payload X — Slicer Does Not Filter Charts:**
```python
{
  "ticket": "PST-014",
  "error_type": "SlicerInteractionError",
  "symptom": "Year slicer moved but charts do not update",
  "message": "Slicer is not connected to visuals. Visual interactions must be enabled.",
  "recovery": "Power BI: Select slicer → Format → Edit Interactions → set all visuals to Filter",
  "agent_action": "Manual fix in Power BI Desktop"
}
```

### Verification Contract (Agent Checks Post-Build)
```python
# tests/test_pst014_powerbi.py

import os

# --- Test 14.1: PBIX file exists ---
def test_pbix_exists():
    assert os.path.exists("dashboards/skill_trend_powerbi.pbix"), \
        "FAIL PST-014-T14.1: Power BI source file (.pbix) not found"

# --- Test 14.2: PDF export exists ---
def test_pdf_exists():
    assert os.path.exists("dashboards/skill_trend_dashboard.pdf"), \
        "FAIL PST-014-T14.2: Power BI PDF export not found"

# --- Test 14.3: PDF is non-zero size ---
def test_pdf_non_empty():
    size = os.path.getsize("dashboards/skill_trend_dashboard.pdf")
    assert size > 50000, \
        f"FAIL PST-014-T14.3: PDF too small ({size} bytes) — likely blank export"

# --- Test 14.4: PowerBI CSV variant exists (Period cols as string) ---
def test_powerbi_csv_exists():
    assert os.path.exists("data/clean/primary_skills_powerbi.csv"), \
        "FAIL PST-014-T14.4: Power BI-compatible CSV missing. Period columns must be cast to str."
```

### Definition of Done — PST-014
```
✅ data/clean/primary_skills_powerbi.csv created (month/quarter as strings)
✅ dashboards/skill_trend_powerbi.pbix created and reopens without errors
✅ Dashboard contains exactly 4 visuals + 1 year slicer
✅ All 3 chart visuals respond to year slicer filter
✅ dashboards/skill_trend_dashboard.pdf exported (>50KB)
✅ All 4 unit tests pass
```

---
---

## PST-015 — README & Portfolio Packaging

```
TICKET ID:     PST-015
FEATURE:       Write README.md and finalize portfolio artifacts
FILE SCOPE:    README.md  (CREATE / FINALIZE)
               PROBLEM_STATEMENT.md  (UPDATE resolution log)
               MISSION_PLAN.md  (UPDATE status dashboard)
               sdn9300.github.io  (EXTERNAL — update portfolio site)
PRIORITY:      P3
DEPENDS ON:    PST-013 (live URL available), PST-014 (PDF available)
```

### Localized Description
The agent writes a recruiter-optimized README.md that embeds real computed
insights from the analysis, links all portfolio artifacts, and passes a
completeness validation scan. The README is the primary signal a hiring
manager sees before clicking into any notebook or live app. Every insight
section must contain an actual numerical finding — not a narrative
description of what the project does.

### README Structure Contract (EXACT — all 8 sections required)

```markdown
# SECTION 1 — Title + Badges
Format:
  # Skill Trend Analysis
  ![Python](badge) ![Streamlit](badge) ![Groq](badge) ![Power BI](badge)
  **Live App:** [skill-trend-analysis.streamlit.app](<URL>)
  **Power BI Dashboard:** [View PDF](dashboards/skill_trend_dashboard.pdf)

# SECTION 2 — One-Line Summary (max 2 sentences)
Rule: Must state the project type (Time Series + NLP) and the core output.
Example:
  "An end-to-end Time Series and NLP analysis of 50,000 AI/DS job postings
  (2020–2026), surfacing which skills are rising, declining, and co-occurring —
  deployed as a live Streamlit app with an LLM-powered Skill Gap Advisor."

# SECTION 3 — 3 Key Insights (REQUIRED: real numbers from actual analysis)
Format:
  ## 🔍 Key Findings
  1. **[Actual Skill Name]** appears in **[X]%** of all job postings,
     making it the single most demanded skill across the entire dataset.
  2. **LLM-related skills** (LLM, RAG, Prompt Engineering) grew **[X]%**
     from 2022 to 2024, confirmed by chi-square test (p = [actual p_value]).
  3. **[Skill A]** + **[Skill B]** is the most common skill combination,
     co-occurring in **[count]** job postings.

Rule: ALL values in brackets must be actual computed values from the analysis.
      Placeholders in final README = VIOLATION of RULE G-5.

# SECTION 4 — Tech Stack
Format: Grouped by function (Language / Libraries / Visualization / GenAI / Deployment)
Must include: Python · Pandas · Plotly · Seaborn · SciPy · Groq API · Streamlit · Power BI

# SECTION 5 — Project Structure
Include: Canonical folder tree from ARCHITECTURE.md (copy verbatim)

# SECTION 6 — How to Run Locally
Must include:
  git clone ...
  pip install -r requirements.txt
  # Set API key:
  export GROQ_API_KEY="your_key_here"
  streamlit run app.py

# SECTION 7 — Screenshots (minimum 3 images)
Must link to:
  assets/charts/01_skill_frequency.png
  assets/charts/02_skill_trend.png
  assets/charts/05_skill_wordcloud.png

# SECTION 8 — About the Author
Format:
  **Soumyadeep Nath** | Kolkata, India
  M.A. English Literature (First Division), Presidency University
  Executive PG Programme in Data Science & AI, IIT Roorkee (In Progress)
  [Portfolio](https://sdn9300.github.io) · [GitHub](https://github.com/sdn9300) ·
  [LinkedIn](https://linkedin.com/in/soumyadeep-nath-941780250)
```

### Exact Failure Payloads

**Failure Payload Y — README Contains Placeholder Values:**
```python
{
  "ticket": "PST-015",
  "error_type": "PlaceholderIntegrityError",
  "placeholders_found": ["[X]%", "[actual p_value]", "[Actual Skill Name]"],
  "message": "README published with unfilled placeholder values. Violates RULE G-5.",
  "recovery": "Run the full analysis pipeline. Extract real values from computed variables. Replace all brackets.",
  "agent_action": "FIX before any LinkedIn or portfolio publish"
}
```

**Failure Payload Z — Missing Required README Section:**
```python
{
  "ticket": "PST-015",
  "error_type": "READMEIncompletenessError",
  "missing_sections": ["<section names>"],
  "message": "README missing one or more of the 8 required sections.",
  "recovery": "Add each missing section using the structure contract in PST-015.",
  "agent_action": "FIX and re-validate"
}
```

### LinkedIn Post Contract
```
# Post must follow this exact structure:

🔍 I analyzed 50,000 AI & Data Science job postings (2020–2026)
to find which skills are actually trending — and built a live tool to show it.

📊 3 things I found that surprised me:
1. [REAL FINDING WITH NUMBER from PST-005]
2. [REAL FINDING WITH NUMBER from PST-006]
3. [REAL FINDING WITH NUMBER from PST-007]

⚙️ Built with:
Python · Pandas · Plotly · Groq API (LLaMA 3.3 70B) · Streamlit · Power BI

🔗 Live app: [URL from PST-013]
📁 GitHub: github.com/sdn9300/skill-trend-analysis

What skill surprised you most? 👇

#DataScience #Python #AI #MachineLearning #CareerAdvice #PortfolioProject
```

### Unit Test Block — PST-015
```python
# tests/test_pst015_readme.py

import os
import re

with open("README.md", "r") as f:
    readme = f.read()

REQUIRED_SECTIONS = [
    "Key Findings",
    "Tech Stack",
    "Project Structure",
    "How to Run",
    "Screenshots",
    "Soumyadeep Nath"
]

REQUIRED_LINKS = [
    "streamlit.app",
    "skill_trend_dashboard.pdf",
    "github.com/sdn9300",
    "sdn9300.github.io"
]

REQUIRED_BADGES = ["Python", "Streamlit", "Groq", "Power BI"]

PLACEHOLDER_PATTERNS = [
    r"\[X\]%",
    r"\[actual p_value\]",
    r"\[Actual Skill Name\]",
    r"\[INSERT",
    r"TODO",
    r"\[count\]"
]

# --- Test 15.1: All 6 required sections present ---
def test_required_sections():
    for section in REQUIRED_SECTIONS:
        assert section in readme, \
            f"FAIL PST-015-T15.1: Required section '{section}' missing from README"

# --- Test 15.2: All required links present ---
def test_required_links():
    for link in REQUIRED_LINKS:
        assert link in readme, \
            f"FAIL PST-015-T15.2: Required link '{link}' missing from README"

# --- Test 15.3: No placeholder patterns remain ---
def test_no_placeholders():
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, readme)
        assert len(matches) == 0, \
            f"FAIL PST-015-T15.3: Placeholder pattern '{pattern}' found in README — fill with real values"

# --- Test 15.4: Key Findings section contains at least one number ---
def test_findings_contain_numbers():
    findings_idx = readme.find("Key Findings")
    findings_section = readme[findings_idx:findings_idx+800]
    numbers = re.findall(r'\d+\.?\d*%|\d{3,}', findings_section)
    assert len(numbers) >= 3, \
        f"FAIL PST-015-T15.4: Key Findings must contain at least 3 real numerical values, found: {numbers}"

# --- Test 15.5: Screenshot images linked and files exist ---
def test_screenshot_files_exist():
    img_refs = re.findall(r'assets/charts/\S+\.png', readme)
    assert len(img_refs) >= 3, \
        "FAIL PST-015-T15.5: README must reference at least 3 chart PNG files"
    for img in img_refs:
        assert os.path.exists(img), \
            f"FAIL PST-015-T15.5: Linked image not found on disk: {img}"

# --- Test 15.6: Resolution log updated in PROBLEM_STATEMENT.md ---
def test_resolution_log_has_entries():
    with open("PROBLEM_STATEMENT.md", "r") as f:
        ps_content = f.read()
    # At least PST-001 should be resolved by now
    resolved_count = ps_content.count("RESOLVED") + \
                     sum(1 for line in ps_content.split("\n")
                         if "PST-" in line and "—" not in line.split("|")[-2])
    # Manual check gate — agent confirms log has been updated
    assert "PST-015" in ps_content, \
        "FAIL PST-015-T15.6: PST-015 entry not found in PROBLEM_STATEMENT.md"
```

### Definition of Done — PST-015
```
✅ README.md contains all 8 required sections
✅ Key Findings section has 3 insights with real numbers (no placeholders)
✅ p-value from PST-009 cited verbatim in Finding 2
✅ Top co-occurring pair from PST-007 cited in Finding 3
✅ All 4 required links present and functional
✅ Minimum 3 screenshot PNGs linked and files exist on disk
✅ MISSION_PLAN.md status dashboard updated to show all steps COMPLETE
✅ TICKET RESOLUTION LOG (bottom of this file) updated with all PST entries
✅ LinkedIn post draft written and saved to docs/linkedin_post_draft.txt
✅ Portfolio site sdn9300.github.io updated with project card linking to live app
✅ All 6 unit tests pass
✅ No placeholder patterns in README (RULE G-5 verified)
```

---
---

## GLOBAL AGENT RULES (Apply to ALL Tickets)

```
RULE G-1 — SEQUENTIAL RESOLUTION:
  Tickets marked P0 must be fully resolved (all DoD items ✅) before
  any P1 ticket begins. P1 before P2. P2 before P3.

RULE G-2 — NO INLINE IMPLEMENTATION:
  All reusable logic lives in src/*.py files.
  Notebooks call src functions — they do NOT re-implement logic inline.

RULE G-3 — FAILURE PAYLOAD FIDELITY:
  When an agent prints a Failure Payload, it must print the complete dict
  (not a summary), then call sys.exit(1) for HALT actions.

RULE G-4 — TEST-BEFORE-COMMIT:
  Every ticket's unit test block must pass before the implementing file
  is committed to GitHub. Broken tests are not committed.

RULE G-5 — TITLE INTEGRITY:
  Chart titles and README insights must embed actual computed values.
  Placeholders like "X%" or "[skill]" in the final committed version = VIOLATION.

RULE G-6 — TAXONOMY IS THE BOUNDARY:
  The agent must NEVER invent skill names outside skill_taxonomy.json.
  The LLM in PST-011 must NEVER recommend skills not in the trending list.

RULE G-7 — NO FABRICATED METRICS:
  If a computation returns 0, NaN, or an unexpected result, the agent
  HALTS with a Failure Payload. It does NOT substitute a made-up value.
```

---

## TICKET RESOLUTION LOG

| Ticket | Resolved Date | PR / Commit | All Tests ✅ | Committed By |
|---|---|---|---|---|
| PST-001 | — | — | — | — |
| PST-002 | — | — | — | — |
| PST-003 | — | — | — | — |
| PST-004 | — | — | — | — |
| PST-005 | — | — | — | — |
| PST-006 | — | — | — | — |
| PST-007 | — | — | — | — |
| PST-008 | — | — | — | — |
| PST-009 | — | — | — | — |
| PST-010 | — | — | — | — |
| PST-011 | — | — | — | — |
| PST-012 | — | — | — | — |
| PST-013 | — | — | — | — |
| PST-014 | — | — | — | — |
| PST-015 | — | — | — | — |

*Agent updates this table when a ticket reaches RESOLVED status.*
*A ticket is RESOLVED only when its DoD checklist is 100% complete.*

---

## IMPLEMENTATION RESOLUTION SNAPSHOT

| Phase | Status | Notes |
|---|---|---|
| Phase 0 | Complete | Problem framing and research questions locked |
| Phase 1 | Complete | Raw dataset acquisition and inspection completed |
| Phase 2 | Complete | Cleaning pipeline and clean CSV outputs completed |
| Phase 3 | Complete | EDA notebook and reusable analysis helpers completed |
| Phase 4 | Complete | Publication-ready chart exports completed |
| Phase 5 | Complete | Groq-based skill gap advisor completed |
| Phase 6 | Complete | Streamlit app implemented and branded as Future Fit |
| Phase 7 | Complete | README, architecture, mission plan, and LinkedIn draft completed |
