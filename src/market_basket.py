"""
market_basket.py
================
Reusable Market Basket Analysis (Apriori) pipeline for skill co-occurrence mining.

Public API
----------
run_mba_pipeline(raw_path, wide_path, onehot_path, top_n=30)
    -> (frequent_itemsets, rules)  # both pd.DataFrames

load_mba_rules(path)
    -> pd.DataFrame
"""

from __future__ import annotations

import ast
from pathlib import Path

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_MIN_SUPPORT: float = 0.05
FALLBACK_MIN_SUPPORT: float = 0.03
DEFAULT_LIFT_THRESHOLD: float = 1.2
FALLBACK_LIFT_THRESHOLD: float = 0.90
DEFAULT_CONF_THRESHOLD: float = 0.50
FALLBACK_CONF_THRESHOLD: float = 0.38
DEFAULT_TOP_N: int = 30
FALLBACK_TOP_N: int = 15


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_onehot(raw_path: Path, wide_path: Path, top_n: int = DEFAULT_TOP_N) -> pd.DataFrame:
    """Build a boolean one-hot skill matrix from raw + wide data."""
    skills = pd.read_csv(raw_path)
    top_skills = skills["skill"].value_counts().head(top_n).index.tolist()

    df_wide = pd.read_csv(wide_path)
    df_wide["skills_found"] = df_wide["skills_found"].apply(ast.literal_eval)
    df_wide["skills_filtered"] = df_wide["skills_found"].apply(
        lambda x: [s for s in x if s in top_skills]
    )
    df_wide = df_wide[df_wide["skills_filtered"].apply(len) >= 2]

    te = TransactionEncoder()
    onehot = te.fit(df_wide["skills_filtered"]).transform(df_wide["skills_filtered"])
    onehot_df = pd.DataFrame(onehot, columns=te.columns_)

    zero_cols = [col for col in onehot_df.columns if onehot_df[col].sum() == 0]
    if zero_cols:
        onehot_df = onehot_df.drop(columns=zero_cols)

    return onehot_df


def _run_apriori(onehot_df: pd.DataFrame) -> pd.DataFrame:
    """Run Apriori with automatic support fallback."""
    for support in (DEFAULT_MIN_SUPPORT, FALLBACK_MIN_SUPPORT):
        itemsets = apriori(onehot_df, min_support=support, use_colnames=True)
        if len(itemsets) > 0:
            print(f"[MBA] Apriori found {len(itemsets)} itemsets at support={support}")
            return itemsets
    raise RuntimeError(
        "Apriori returned 0 frequent itemsets at all support thresholds. "
        "Check your dataset for sufficient transactions."
    )


def _extract_rules(itemsets: pd.DataFrame) -> pd.DataFrame:
    """
    Extract and filter association rules with automatic lift/confidence fallback.
    Converts frozensets to readable strings.
    """
    for lift_thresh, conf_thresh in (
        (DEFAULT_LIFT_THRESHOLD, DEFAULT_CONF_THRESHOLD),
        (FALLBACK_LIFT_THRESHOLD, FALLBACK_CONF_THRESHOLD),
    ):
        rules = association_rules(itemsets, metric="lift", min_threshold=lift_thresh)
        filtered = rules[rules["confidence"] >= conf_thresh].sort_values("lift", ascending=False)
        if len(filtered) > 0:
            print(
                f"[MBA] {len(filtered)} rules survived "
                f"(lift>={lift_thresh}, confidence>={conf_thresh})"
            )
            filtered = filtered.copy()
            filtered["antecedents"] = filtered["antecedents"].apply(lambda x: ", ".join(sorted(x)))
            filtered["consequents"] = filtered["consequents"].apply(lambda x: ", ".join(sorted(x)))
            return filtered.reset_index(drop=True)

    print("[MBA] No rules survived any threshold combination — returning empty DataFrame.")
    return pd.DataFrame(columns=["antecedents", "consequents", "support", "confidence", "lift"])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_mba_pipeline(
    raw_path: Path,
    wide_path: Path,
    onehot_path: Path | None = None,
    top_n: int = DEFAULT_TOP_N,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    End-to-end Market Basket Analysis pipeline.

    Parameters
    ----------
    raw_path   : Path to raw skills_demand.csv
    wide_path  : Path to primary_wide.csv (one row per job, skill lists)
    onehot_path: If provided, try loading cached one-hot matrix first; fall back to
                 rebuilding from raw + wide data if the file is missing.
    top_n      : Cap skills matrix to top-N skills. Retries with FALLBACK_TOP_N if needed.

    Returns
    -------
    (frequent_itemsets, rules) — both pd.DataFrames ready for Streamlit/Power BI.
    """
    # Load or build one-hot matrix
    if onehot_path and onehot_path.exists():
        print(f"[MBA] Loading cached one-hot matrix from {onehot_path}")
        onehot_df = pd.read_csv(onehot_path).astype(bool)
    else:
        print(f"[MBA] Building one-hot matrix (top_n={top_n}) …")
        onehot_df = _build_onehot(raw_path, wide_path, top_n=top_n).astype(bool)
        if onehot_path:
            onehot_df.to_csv(onehot_path, index=False)
            print(f"[MBA] Cached one-hot matrix to {onehot_path}")

    # Apriori — retry with smaller skill set if no itemsets found
    try:
        itemsets = _run_apriori(onehot_df)
    except RuntimeError:
        print(f"[MBA] Retrying pipeline with top_n={FALLBACK_TOP_N} …")
        onehot_df = _build_onehot(raw_path, wide_path, top_n=FALLBACK_TOP_N).astype(bool)
        if onehot_path:
            onehot_df.to_csv(onehot_path, index=False)
        itemsets = _run_apriori(onehot_df)

    rules = _extract_rules(itemsets)
    return itemsets, rules


def load_mba_rules(path: Path) -> pd.DataFrame:
    """Load pre-computed MBA rules CSV. Returns empty DataFrame if file not found."""
    if not path.exists():
        print(f"[MBA] Rules file not found at {path}. Returning empty DataFrame.")
        return pd.DataFrame(columns=["antecedents", "consequents", "support", "confidence", "lift"])
    return pd.read_csv(path)
