import pandas as pd
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "skills_demand.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "clean" / "primary_wide.csv"

print("Loading data from:", INPUT_PATH)
skills = pd.read_csv(INPUT_PATH)

# Group by job_id → list of skills per job
print("Grouping by job_id...")
df_wide = skills.groupby('job_id')['skill'].apply(list).reset_index()
df_wide.columns = ['job_id', 'skills_found']

print("Total jobs:", df_wide.shape[0])
print("Avg skills per job:", df_wide['skills_found'].apply(len).mean())

# Filter out jobs with only 1 skill (MBA needs >= 2 items per "basket")
print("Filtering jobs with >= 2 skills...")
df_wide = df_wide[df_wide['skills_found'].apply(len) >= 2]
print("Jobs with >= 2 skills:", df_wide.shape[0])

# Ensure directories exist
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

df_wide.to_csv(OUTPUT_PATH, index=False)
print("Saved:", df_wide.shape)
