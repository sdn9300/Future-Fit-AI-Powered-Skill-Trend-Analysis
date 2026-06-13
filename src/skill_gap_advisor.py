from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from groq import Groq
    from groq import RateLimitError
except Exception:  # pragma: no cover - optional dependency import guard
    Groq = None  # type: ignore[assignment]
    RateLimitError = Exception  # type: ignore[assignment]


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRIMARY_CLEAN_PATH = PROJECT_ROOT / "data" / "clean" / "primary_skills_long.csv"

DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
DEFAULT_SYSTEM_PROMPT = (
    "You are a career advisor specializing in Data Science job market trends. "
    "Write concise, practical advice that helps a learner prioritize next steps."
)

TRIVIAL_INPUTS = {
    "",
    "n/a",
    "na",
    "none",
    "null",
    "asdfghjkl",
    "qwerty",
    "i know everything",
}

COMMON_SKILL_ALIASES = {
    "scikit learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "power bi": "power bi",
    "excel": "excel",
    "powerpoint": "powerpoint",
    "cuda": "cuda",
    "tensorflow": "tensorflow",
    "pytorch": "pytorch",
    "python": "python",
    "sql": "sql",
    "pandas": "pandas",
}

PRIMARY_TREND_SKILLS = [
    "aws",
    "gcp",
    "tensorflow",
    "azure",
    "scikit-learn",
    "nlp",
    "python",
    "sql",
    "computer vision",
    "r",
    "pytorch",
]


@dataclass(frozen=True)
class SkillGapContext:
    user_skills: list[str]
    trending_skills: list[str]
    matched_skills: list[str]
    missing_trending_skills: list[str]
    priority_skills: list[str]


def _load_primary_clean() -> pd.DataFrame:
    if not PRIMARY_CLEAN_PATH.exists():
        raise FileNotFoundError(
            f"Primary clean dataset not found at {PRIMARY_CLEAN_PATH}. "
            "Run Phase 2 before using the skill gap advisor."
        )
    df = pd.read_csv(PRIMARY_CLEAN_PATH)
    if "skill" in df.columns:
        df["skill"] = df["skill"].astype("string").str.strip().str.lower()
    if "posted_year" in df.columns:
        df["posted_year"] = pd.to_numeric(df["posted_year"], errors="coerce")
    return df


def _canonicalize_skill(token: str) -> str:
    cleaned = re.sub(r"\s+", " ", token.strip())
    lower = cleaned.lower()
    if lower in COMMON_SKILL_ALIASES:
        return COMMON_SKILL_ALIASES[lower]
    if lower in {"aws", "gcp", "sql", "nlp", "llm", "rag", "cuda"}:
        return lower
    if lower in {"python", "pandas", "azure", "tensorflow", "pytorch"}:
        return lower
    if lower == "computer vision":
        return "computer vision"
    if lower == "scikit-learn" or lower == "scikit learn":
        return "scikit-learn"
    return cleaned


def _looks_like_valid_skill_phrase(token: str) -> bool:
    token = token.strip()
    if not token:
        return False
    if token.lower() in TRIVIAL_INPUTS:
        return False
    if len(token) < 2:
        return False
    if not re.search(r"[a-zA-Z]", token):
        return False
    if token.lower() in {"i know everything", "i know all"}:
        return False
    # Reject clearly non-skill filler that has no meaningful technical keyword shape.
    if len(token.split()) > 5 and not re.search(r"(python|sql|excel|power|data|cloud|ml|ai|tableau|pandas|tensorflow|pytorch|azure|aws|gcp)", token, re.I):
        return False
    return True


def validate_user_input(user_input: str) -> tuple[bool, list[str] | str]:
    """
    Validate a comma-separated skill list.

    Returns:
        (True, cleaned_skills) on success
        (False, error_message) on invalid input
    """
    if user_input is None:
        return False, "Please enter at least one skill, for example: Python, SQL, Tableau."

    raw = user_input.strip()
    if not raw or raw.lower() in TRIVIAL_INPUTS:
        return False, "Please enter at least one recognizable skill, for example: Python, SQL, Tableau."

    tokens = [part.strip() for part in raw.split(",") if part.strip()]
    if not tokens:
        return False, "Please enter at least one recognizable skill, for example: Python, SQL, Tableau."

    cleaned: list[str] = []
    for token in tokens:
        if not _looks_like_valid_skill_phrase(token):
            continue
        canonical = _canonicalize_skill(token)
        if canonical not in cleaned:
            cleaned.append(canonical)

    if not cleaned:
        return False, "No recognizable skills found. Please enter skills like: Python, SQL, Tableau."

    return True, cleaned


def get_trending_skills(df_exploded: pd.DataFrame, top_n: int = 20) -> list[str]:
    """
    Return the top trending skills from an analyzed dataset.

    The implementation favors the most recent annual share and the change
    between the first and last observed year when `posted_year` is available.
    """
    if df_exploded is None or df_exploded.empty:
        return PRIMARY_TREND_SKILLS[:top_n]

    if "skill" not in df_exploded.columns:
        raise ValueError("Expected a `skill` column in the analyzed dataset.")

    skills = df_exploded.copy()
    skills["skill"] = skills["skill"].astype("string").str.strip().str.lower()

    if "posted_year" not in skills.columns or skills["posted_year"].dropna().empty:
        ranked = skills["skill"].value_counts().head(top_n).index.tolist()
        return ranked

    skills["posted_year"] = pd.to_numeric(skills["posted_year"], errors="coerce")
    skills = skills.dropna(subset=["posted_year"])
    if skills.empty:
        ranked = skills["skill"].value_counts().head(top_n).index.tolist()
        return ranked

    year_totals = skills.groupby("posted_year").size().rename("year_total").reset_index()
    annual = skills.groupby(["posted_year", "skill"]).size().rename("mentions").reset_index()
    annual = annual.merge(year_totals, on="posted_year", how="left")
    annual["share"] = annual["mentions"] / annual["year_total"]

    first_year = int(annual["posted_year"].min())
    last_year = int(annual["posted_year"].max())
    trend = annual.pivot(index="skill", columns="posted_year", values="share").fillna(0.0)
    trend["share_change"] = trend.get(last_year, 0.0) - trend.get(first_year, 0.0)
    trend["recent_share"] = trend[[c for c in trend.columns if isinstance(c, (int, float)) and c >= last_year - 2]].mean(axis=1)
    trend["overall_mentions"] = skills["skill"].value_counts(normalize=True)
    trend["score"] = (
        trend["recent_share"].fillna(0.0) * 0.55
        + trend["share_change"].fillna(0.0).clip(lower=0.0) * 0.30
        + trend["overall_mentions"].fillna(0.0) * 0.15
    )
    ranked = trend.sort_values("score", ascending=False).head(top_n).index.tolist()
    return ranked


def _build_skill_gap_context(user_skills: list[str], trending_skills: list[str]) -> SkillGapContext:
    normalized_user = [_canonicalize_skill(skill) for skill in user_skills]
    normalized_trending = [_canonicalize_skill(skill) for skill in trending_skills]

    matched = []
    def _skills_match(a: str, b: str) -> bool:
        a_clean = a.lower().strip()
        b_clean = b.lower().strip()
        if len(a_clean) < 3 or len(b_clean) < 3:
            return a_clean == b_clean
        return a_clean == b_clean or a_clean in b_clean or b_clean in a_clean

    for skill in normalized_user:
        for trending in normalized_trending:
            if _skills_match(skill, trending):
                matched.append(skill)
                break

    missing = [skill for skill in normalized_trending if skill.lower() not in {s.lower() for s in matched}]
    priority = missing[:5]
    return SkillGapContext(
        user_skills=normalized_user,
        trending_skills=normalized_trending,
        matched_skills=matched,
        missing_trending_skills=missing,
        priority_skills=priority,
    )


def _format_user_prompt(context: SkillGapContext, concise: bool = False) -> str:
    if concise:
        return (
            f"My current skills are: {', '.join(context.user_skills)}.\n"
            f"Top trending skills are: {', '.join(context.trending_skills)}.\n"
            "Tell me my main gaps and what to learn next in 3-5 short bullets."
        )
    return (
        f"My current skills are: {', '.join(context.user_skills)}.\n"
        f"Top trending skills in 2024-2026 are: {', '.join(context.trending_skills)}.\n"
        "Identify my skill gaps and explain concisely what I should prioritize learning.\n"
        f"Focus on these priority gaps first: {', '.join(context.priority_skills) if context.priority_skills else 'the most relevant trending skills'}."
    )


def _format_offline_advice(context: SkillGapContext) -> str:
    if not context.user_skills:
        return "Please enter at least one skill so I can assess your gap."

    if not context.matched_skills:
        return (
            "Your profile does not overlap with the current trending stack yet. "
            f"Start with {', '.join(context.priority_skills[:3]) if context.priority_skills else ', '.join(context.trending_skills[:3])}, "
            "then add Python and SQL as a foundation for data workflows."
        )

    missing = context.priority_skills[:4]
    if not missing:
        return (
            "You already cover most of the current trend stack. "
            "Next, deepen your portfolio with project work, deployment practice, and interview-ready case studies."
        )

    return (
        f"You already have {', '.join(context.matched_skills[:3])}. "
        f"The biggest gaps are {', '.join(missing)}. "
        "Prioritize the missing cloud and ML tools first, then practice one end-to-end project that combines data prep, modeling, and deployment."
    )


def get_skill_gap_advice(
    user_skills: list[str],
    trending_skills: list[str],
    *,
    client: Any | None = None,
    model: str | None = None,
    max_retries: int = 1,
    mba_rules: Any = None,
) -> str:
    """
    Call Groq API with a structured prompt and return concise career guidance.

    Raises:
        EnvironmentError: if GROQ_API_KEY is missing
        RuntimeError: if the API call fails after the configured retry
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. Add it to your environment or Streamlit secrets before calling the live advisor."
        )

    if client is None:
        if Groq is None:
            raise RuntimeError("groq package is unavailable in this environment.")
        client = Groq(api_key=api_key)

    active_model = model or DEFAULT_GROQ_MODEL
    context = _build_skill_gap_context(user_skills, trending_skills)
    
    # Process market basket association insight
    mba_context = ""
    if mba_rules is not None and not mba_rules.empty:
        user_skills_lower = [s.lower().strip() for s in user_skills]
        relevant = mba_rules[mba_rules['antecedents'].str.lower().isin(user_skills_lower)]
        if len(relevant) > 0:
            top_rule = relevant.iloc[0]
            mba_context = (f"\nAssociation insight: Jobs requiring "
                            f"{top_rule['antecedents']} also require "
                            f"{top_rule['consequents']} with "
                            f"{top_rule['confidence']*100:.0f}% confidence.")

    prompts = [
        _format_user_prompt(context, concise=False),
        _format_user_prompt(context, concise=True),
    ]
    if mba_context:
        prompts = [p + "\n" + mba_context for p in prompts]

    last_error: Exception | None = None
    for attempt in range(max_retries + 1):
        prompt = prompts[min(attempt, len(prompts) - 1)]
        try:
            response = client.chat.completions.create(
                model=active_model,
                messages=[
                    {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.4,
                max_tokens=300,
            )
            content = getattr(response.choices[0].message, "content", None)
            if content and len(content.strip()) >= 10:
                return content.strip()
            last_error = RuntimeError("LLM returned an empty or truncated response.")
        except RateLimitError as exc:
            last_error = exc
            if attempt < max_retries:
                time.sleep(60)
                continue
        except Exception as exc:  # pragma: no cover - live API branch
            last_error = exc
            if attempt < max_retries:
                continue

    raise RuntimeError(f"Groq API call failed after retry: {last_error}")


def generate_skill_gap_preview(
    user_skills: list[str],
    trending_skills: list[str],
    mba_rules: Any = None,
) -> str:
    """
    Deterministic offline preview used for local smoke tests when no API key is available.
    """
    context = _build_skill_gap_context(user_skills, trending_skills)
    advice = _format_offline_advice(context)
    
    # Process market basket association insight
    if mba_rules is not None and not mba_rules.empty:
        user_skills_lower = [s.lower().strip() for s in user_skills]
        relevant = mba_rules[mba_rules['antecedents'].str.lower().isin(user_skills_lower)]
        if len(relevant) > 0:
            top_rule = relevant.iloc[0]
            mba_context = (f"\nAssociation insight: Jobs requiring "
                            f"{top_rule['antecedents']} also require "
                            f"{top_rule['consequents']} with "
                            f"{top_rule['confidence']*100:.0f}% confidence.")
            advice += "\n" + mba_context
            
    return advice


def run_phase5_smoke_tests(df_exploded: pd.DataFrame | None = None) -> list[dict[str, Any]]:
    """
    Execute the five plan-required smoke tests.

    This function uses the live API when GROQ_API_KEY is available; otherwise it
    falls back to a deterministic preview so the workflow can still be verified
    locally without network access.
    """
    if df_exploded is None:
        try:
            df_exploded = _load_primary_clean()
        except Exception:
            df_exploded = pd.DataFrame({"skill": PRIMARY_TREND_SKILLS})

    trending_skills = get_trending_skills(df_exploded, top_n=20)
    tests = [
        "Python, SQL, Pandas",
        "Excel, PowerPoint",
        "TensorFlow, PyTorch, CUDA",
        "",
        "asdfghjkl",
    ]

    use_live_api = bool(os.getenv("GROQ_API_KEY"))
    results: list[dict[str, Any]] = []
    for idx, raw_input in enumerate(tests, start=1):
        valid, parsed = validate_user_input(raw_input)
        record: dict[str, Any] = {"test": idx, "input": raw_input, "valid": valid}
        if not valid:
            record["result"] = parsed
            record["mode"] = "validation-error"
            results.append(record)
            continue

        assert isinstance(parsed, list)
        if use_live_api:
            try:
                record["result"] = get_skill_gap_advice(parsed, trending_skills)
                record["mode"] = "live"
            except Exception as exc:
                record["result"] = f"Live API unavailable for smoke test: {exc}"
                record["mode"] = "fallback"
        else:
            record["result"] = generate_skill_gap_preview(parsed, trending_skills)
            record["mode"] = "offline-preview"

        results.append(record)

    return results


def main() -> None:
    df = None
    try:
        df = _load_primary_clean()
    except Exception as exc:
        print(f"Could not load primary dataset: {exc}")

    trending = get_trending_skills(df if df is not None else pd.DataFrame(), top_n=20)
    print("Trending skills:", trending)
    print()
    print("Smoke tests:")
    for item in run_phase5_smoke_tests(df):
        print(f"- Test {item['test']}: {item['input']!r}")
        print(f"  valid={item['valid']}")
        print(f"  result={item['result']}")


if __name__ == "__main__":
    main()
