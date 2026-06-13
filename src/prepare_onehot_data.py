import pandas as pd
from pathlib import Path
from mlxtend.preprocessing import TransactionEncoder
import ast

# Setup paths
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "skills_demand.csv"
WIDE_INPUT_PATH = PROJECT_ROOT / "data" / "clean" / "primary_wide.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "clean" / "primary_onehot.csv"

print("Loading raw data to calculate top 30 skills...")
skills = pd.read_csv(RAW_INPUT_PATH)
top_30 = skills['skill'].value_counts().head(30).index.tolist()

print("Loading wide data...")
df_wide = pd.read_csv(WIDE_INPUT_PATH)
# Convert string representation of lists back to actual lists
df_wide['skills_found'] = df_wide['skills_found'].apply(ast.literal_eval)

print("Filtering for top 30 skills...")
df_wide['skills_filtered'] = df_wide['skills_found'].apply(
    lambda x: [s for s in x if s in top_30]
)

print("Filtering jobs with >= 2 filtered skills...")
df_wide = df_wide[df_wide['skills_filtered'].apply(len) >= 2]

print("Applying TransactionEncoder...")
te = TransactionEncoder()
onehot = te.fit(df_wide['skills_filtered']).transform(df_wide['skills_filtered'])
onehot_df = pd.DataFrame(onehot, columns=te.columns_)

print("Initial Matrix shape:", onehot_df.shape)
print("All values 0/1?", onehot_df.isin([0,1]).all().all())

# Confirm no column is entirely 0
zero_cols = [col for col in onehot_df.columns if onehot_df[col].sum() == 0]
if zero_cols:
    print(f"Dropping entirely 0 columns: {zero_cols}")
    onehot_df = onehot_df.drop(columns=zero_cols)
else:
    print("No columns are entirely 0.")

print("Final Matrix shape:", onehot_df.shape)

onehot_df.to_csv(OUTPUT_PATH, index=False)
print(f"Saved one-hot encoded matrix to {OUTPUT_PATH}")
