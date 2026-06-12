import pandas as pd
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "clean" / "primary_skills_long.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "clean" / "primary_skills_powerbi.csv"

print("Loading data from:", INPUT_PATH)
df = pd.read_csv(INPUT_PATH)

# Convert any Period columns to plain text
for col in ['month', 'quarter']:
    if col in df.columns:
        df[col] = df[col].astype(str)

# Fill any remaining blanks so Power BI doesn't show errors
df['posted_year'] = df['posted_year'].fillna('Not Specified')
df['experience_level'] = df['experience_level'].fillna('Not Specified')

# Ensure directories exist
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(OUTPUT_PATH, index=False)
print("Saved:", df.shape)
print("Columns:", df.columns.tolist())
