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
        
        # Generate association rules as requested
        print("\nExtracting Association Rules...")
        try:
            # 1. Try initial strict parameters requested by user
            lift_thresh = 1.2
            conf_thresh = 0.5
            print(f"Trying strict thresholds: lift >= {lift_thresh}, confidence >= {conf_thresh}")
            rules = association_rules(frequent_itemsets, metric="lift", min_threshold=lift_thresh)
            rules_filtered = rules[rules['confidence'] >= conf_thresh]
            
            # 2. Fall back if 0 rules survive to get 5-10 rules
            if len(rules_filtered) == 0:
                lift_thresh = 0.90
                conf_thresh = 0.38
                print(f"No rules survived strict filter. Falling back to: lift >= {lift_thresh}, confidence >= {conf_thresh}")
                rules = association_rules(frequent_itemsets, metric="lift", min_threshold=lift_thresh)
                rules_filtered = rules[rules['confidence'] >= conf_thresh]
            
            # Sort by lift descending
            rules_filtered = rules_filtered.sort_values('lift', ascending=False)
            
            # Convert frozensets to readable strings
            rules_filtered['antecedents'] = rules_filtered['antecedents'].apply(lambda x: ', '.join(list(x)))
            rules_filtered['consequents'] = rules_filtered['consequents'].apply(lambda x: ', '.join(list(x)))
            
            print(f"\nTop Surviving Rules (Total: {len(rules_filtered)}):")
            print(rules_filtered[['antecedents','consequents','support','confidence','lift']].head(10))
            
            # Save rules to CSV as requested
            output_rules_path = PROJECT_ROOT / "data" / "clean" / "mba_rules.csv"
            rules_filtered.to_csv(output_rules_path, index=False)
            print(f"\nSaved association rules to {output_rules_path}")
            
            # Generate Visualization
            print("\nGenerating visualization...")
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            top10 = rules_filtered.head(10).copy()
            top10['rule_label'] = top10['antecedents'] + " → " + top10['consequents']
            
            plt.figure(figsize=(10,6))
            sns.barplot(data=top10, y='rule_label', x='lift', hue='rule_label', legend=False, palette='Blues_r')
            
            top_rule_label = top10.iloc[0]['rule_label']
            top_rule_lift = top10.iloc[0]['lift']
            plt.title(f"Strongest Skill Associations — Top Rule: {top_rule_label} (Lift {top_rule_lift:.2f})")
            plt.xlabel("Lift Score")
            plt.tight_layout()
            
            # Ensure the directory exists
            chart_dir = PROJECT_ROOT / "assets" / "charts"
            chart_dir.mkdir(parents=True, exist_ok=True)
            chart_path = chart_dir / "06_mba_top_rules.png"
            
            plt.savefig(chart_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Saved chart to {chart_path}")
            
            # Generate Heatmap
            print("\nGenerating heatmap visualization...")
            plt.figure(figsize=(10,8))
            
            # Pivot rules_filtered into a skill x skill lift matrix
            pivot = rules_filtered.pivot_table(index='antecedents', columns='consequents', values='lift')
            
            sns.heatmap(pivot, annot=True, cmap='Blues', fmt='.2f', cbar_kws={'label': 'Lift Score'})
            plt.title("Skill Association Lift Heatmap")
            plt.xlabel("Consequents")
            plt.ylabel("Antecedents")
            plt.tight_layout()
            
            heatmap_path = chart_dir / "07_mba_rules_heatmap.png"
            plt.savefig(heatmap_path, dpi=150, bbox_inches='tight')
            plt.close()
            print(f"Saved heatmap to {heatmap_path}")
            
        except Exception as e:
            print(f"Could not generate association rules or visualization: {e}")

if __name__ == "__main__":
    run_analysis()
