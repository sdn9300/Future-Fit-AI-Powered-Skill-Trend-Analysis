import pandas as pd
from pathlib import Path
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder
import ast
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ONEHOT_PATH = PROJECT_ROOT / "data" / "clean" / "primary_onehot.csv"
RAW_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "skills_demand.csv"
WIDE_INPUT_PATH = PROJECT_ROOT / "data" / "clean" / "primary_wide.csv"

def regenerate_onehot(top_n=30):
    print(f"\n--- Regenerating One-Hot Matrix with TOP {top_n} skills ---")
    skills = pd.read_csv(RAW_INPUT_PATH)
    top_skills = skills['skill'].value_counts().head(top_n).index.tolist()
    
    df_wide = pd.read_csv(WIDE_INPUT_PATH)
    df_wide['skills_found'] = df_wide['skills_found'].apply(ast.literal_eval)
    
    df_wide['skills_filtered'] = df_wide['skills_found'].apply(
        lambda x: [s for s in x if s in top_skills]
    )
    
    df_wide = df_wide[df_wide['skills_filtered'].apply(len) >= 2]
    
    te = TransactionEncoder()
    onehot = te.fit(df_wide['skills_filtered']).transform(df_wide['skills_filtered'])
    onehot_df = pd.DataFrame(onehot, columns=te.columns_)
    
    # Confirm no column is entirely 0
    zero_cols = [col for col in onehot_df.columns if onehot_df[col].sum() == 0]
    if zero_cols:
        print(f"Dropping entirely 0 columns: {zero_cols}")
        onehot_df = onehot_df.drop(columns=zero_cols)
        
    onehot_df.to_csv(ONEHOT_PATH, index=False)
    print(f"Saved new one-hot encoded matrix to {ONEHOT_PATH}. Shape: {onehot_df.shape}")
    return onehot_df

def run_analysis():
    # Load existing one-hot DF
    if ONEHOT_PATH.exists():
        print(f"Loading existing one-hot data from {ONEHOT_PATH}...")
        onehot_df = pd.read_csv(ONEHOT_PATH)
    else:
        onehot_df = regenerate_onehot(top_n=30)
    
    # Convert all columns to boolean as required by mlxtend >= 0.17.0
    onehot_df = onehot_df.astype(bool)
    
    print("Running Apriori with min_support=0.05...")
    frequent_itemsets = apriori(onehot_df, min_support=0.05, use_colnames=True)
    print("Frequent itemsets found at 0.05 support:", len(frequent_itemsets))
    
    if len(frequent_itemsets) == 0:
        print("Empty frequent itemsets at 0.05 support. Retrying with min_support=0.03...")
        frequent_itemsets = apriori(onehot_df, min_support=0.03, use_colnames=True)
        print("Retried at 0.03 — found:", len(frequent_itemsets))
        
        if len(frequent_itemsets) == 0:
            print("Still 0 frequent itemsets. Reducing TOP_30 to TOP_15 and rerunning...")
            # Regenerate with top 15 skills
            onehot_df = regenerate_onehot(top_n=15)
            onehot_df = onehot_df.astype(bool)
            
            print("Running Apriori again on TOP_15 data with min_support=0.05...")
            frequent_itemsets = apriori(onehot_df, min_support=0.05, use_colnames=True)
            print("Frequent itemsets found at 0.05 support:", len(frequent_itemsets))
            
            if len(frequent_itemsets) == 0:
                print("Retrying TOP_15 data with min_support=0.03...")
                frequent_itemsets = apriori(onehot_df, min_support=0.03, use_colnames=True)
                print("Retried TOP_15 at 0.03 — found:", len(frequent_itemsets))

    if len(frequent_itemsets) > 0:
        print("\nFrequent Itemsets:\n", frequent_itemsets.sort_values(by="support", ascending=False).head(20))
        
        # Generate association rules
        print("\nGenerating association rules with confidence threshold 0.1...")
        try:
            rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.1, num_itemsets=len(frequent_itemsets))
            print(f"Generated {len(rules)} association rules.")
            if len(rules) > 0:
                print("\nTop 10 Association Rules (by lift):\n", rules.sort_values(by="lift", ascending=False).head(10))
        except TypeError:
            # Handle different versions of mlxtend association_rules parameters
            try:
                rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.1)
                print(f"Generated {len(rules)} association rules.")
                if len(rules) > 0:
                    print("\nTop 10 Association Rules (by lift):\n", rules.sort_values(by="lift", ascending=False).head(10))
            except Exception as e:
                print(f"Could not generate association rules: {e}")
        except Exception as e:
            print(f"Could not generate association rules: {e}")

if __name__ == "__main__":
    run_analysis()
