# Pipeline Decisions

## Dataset Join Limitation & Resolution

ai_jobs.csv and skills_demand.csv share a job_id column but only ~15%
of IDs match across the two files. Root cause: ID format divergence
between source files from the dataset publisher.

Resolution: Left join preserves all 224,605 skill rows. Temporal
analysis (trend charts, hypothesis testing, forecasting) uses only
the ~33,000 rows with verified posted_year. Frequency and association
analysis uses the full 224,605 rows. No year data was imputed or fabricated.
