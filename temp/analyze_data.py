
import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv('Data/unified_resilience_dataset.csv')

# 1. Verify Data Sparsity for Africa in early 2000s
africa_early = df[(df['region'] == 'Africa') & (df['year'] <= 2005)]
missing_counts = africa_early.isnull().sum()
total_rows = len(africa_early)
print("--- Data Sparsity in Africa (2000-2005) ---")
print(f"Total rows: {total_rows}")
print("Missing values for key columns:")
print(missing_counts[['wgi_composite', 'hdi', 'gdp_per_capita', 'emdat_deaths']].sort_values(ascending=False))

# 2. Correlations
# Filter for recent years for better analysis or use all? Using all for general trend.
# Drop NaNs for correlation
corr_df = df[['CRI', 'RRS', 'gdp_per_capita', 'wgi_composite', 'hdi']].dropna()
print("\n--- Correlations ---")
print(corr_df.corr()[['CRI', 'RRS']])

# 3. Identify Paradox Countries (High GDP, Low Resilience vs Low GDP, High Resilience)
# We'll look at 2023 (or latest available)
latest_df = df[df['year'] == 2023].copy()

# Normalize ranks
latest_df['gdp_rank'] = latest_df['gdp_per_capita'].rank(ascending=False)
latest_df['cri_rank'] = latest_df['CRI'].rank(ascending=False)
latest_df['wgi_rank'] = latest_df['wgi_composite'].rank(ascending=False)

# Paradox: High Wealth (Top 50 GDP) but Low Resilience (Bottom 50 CRI)
rich_fragile = latest_df[(latest_df['gdp_rank'] <= 50) & (latest_df['cri_rank'] > 100)]
print("\n--- Rich but Fragile (High GDP, Low CRI) ---")
print(rich_fragile[['iso3', 'gdp_per_capita', 'CRI', 'wgi_composite']])

# Paradox: Low Wealth (Bottom 100 GDP) but High Resilience (Top 50 CRI)
poor_resilient = latest_df[(latest_df['gdp_rank'] > 100) & (latest_df['cri_rank'] <= 50)]
print("\n--- Poor but Resilient (Low GDP, High CRI) ---")
print(poor_resilient[['iso3', 'gdp_per_capita', 'CRI', 'wgi_composite']])

