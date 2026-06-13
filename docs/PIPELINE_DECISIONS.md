# Pipeline Decisions

This document details key architectural decisions, analytical methodologies, and limitations of the skill trend analysis pipeline.

## Forecasting Methodology & Limitations

Forecasting uses ONLY the ~33,000 rows with a verified posted_year
(2020–2026) — 7 annual data points per skill at most.

Given this data depth, a tiered approach was used:
- Skills with ≥5 years of data: Prophet (yearly frequency, 80% CI)
- If Prophet's confidence interval exceeds 1.5x the predicted value
  (signal of unreliable fit at low N): fallback to simple linear
  trend extrapolation
- Skills with <5 years of data: excluded from forecasting entirely

This is a directional indicator for 2027, not a precise prediction.
No monthly or quarterly forecasting was performed — the source data
does not contain sub-annual date granularity.
