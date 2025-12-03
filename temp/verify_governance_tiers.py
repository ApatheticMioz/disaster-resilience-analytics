"""
Additional verification for governance tier analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Load data
DATA_PATH = Path("d:/Work/Semester5/DAV/Project/Data/unified_resilience_dataset.csv")
df = pd.read_csv(DATA_PATH)

print("=" * 80)
print("GOVERNANCE TIER ANALYSIS")
print("=" * 80)

# Create governance tiers
def assign_tier(wgi):
    if pd.isna(wgi):
        return 'Unknown'
    elif wgi >= 1.0:
        return 'Excellent'
    elif wgi >= 0.0:
        return 'Good'
    elif wgi >= -0.5:
        return 'Weak'
    else:
        return 'Failed'

df['governance_tier'] = df['wgi_composite'].apply(assign_tier)

# Get stats by tier
print("\nCRI_normalized by Governance Tier:")
for tier in ['Excellent', 'Good', 'Weak', 'Failed']:
    tier_data = df[df['governance_tier'] == tier]['CRI_normalized']
    print(f"   {tier}: Mean={tier_data.mean():.2f}, Median={tier_data.median():.2f}, n={len(tier_data)}")

print("\nRRS_normalized by Governance Tier:")
for tier in ['Excellent', 'Good', 'Weak', 'Failed']:
    tier_data = df[df['governance_tier'] == tier]['RRS_normalized']
    print(f"   {tier}: Mean={tier_data.mean():.2f}, Median={tier_data.median():.2f}")

# Check at equal GDP levels
print("\n" + "=" * 80)
print("GOVERNANCE PREMIUM AT EQUAL GDP")
print("=" * 80)

# Create GDP bands
df['gdp_band'] = pd.qcut(df['gdp_per_capita_best'].dropna(), q=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])

print("\nCRI by GDP band and Governance Tier:")
for gdp_band in ['Very Low', 'Low', 'Medium', 'High', 'Very High']:
    print(f"\n{gdp_band} GDP:")
    band_data = df[df['gdp_band'] == gdp_band]
    for tier in ['Excellent', 'Good', 'Weak', 'Failed']:
        tier_data = band_data[band_data['governance_tier'] == tier]['CRI_normalized']
        if len(tier_data) > 0:
            print(f"   {tier}: Mean={tier_data.mean():.2f}, n={len(tier_data)}")

# Calculate the "34% higher" claim
print("\n" + "=" * 80)
print("VALIDATING THE '34% HIGHER' CLAIM")
print("=" * 80)

# Compare Excellent vs Failed at similar GDP
excellent_cri = df[df['governance_tier'] == 'Excellent']['CRI_normalized'].mean()
failed_cri = df[df['governance_tier'] == 'Failed']['CRI_normalized'].mean()

print(f"\nOverall:")
print(f"   Excellent governance mean CRI: {excellent_cri:.2f}")
print(f"   Failed governance mean CRI: {failed_cri:.2f}")
print(f"   Ratio (Excellent/Failed): {excellent_cri/failed_cri:.2f}x")
print(f"   Percentage difference: {((excellent_cri - failed_cri)/failed_cri)*100:.1f}%")

# Check at medium GDP band specifically
medium_data = df[df['gdp_band'] == 'Medium']
medium_excellent = medium_data[medium_data['governance_tier'] == 'Excellent']['CRI_normalized']
medium_failed = medium_data[medium_data['governance_tier'] == 'Failed']['CRI_normalized']

if len(medium_excellent) > 0 and len(medium_failed) > 0:
    print(f"\nAt Medium GDP level:")
    print(f"   Excellent governance mean CRI: {medium_excellent.mean():.2f} (n={len(medium_excellent)})")
    print(f"   Failed governance mean CRI: {medium_failed.mean():.2f} (n={len(medium_failed)})")
    print(f"   Percentage difference: {((medium_excellent.mean() - medium_failed.mean())/medium_failed.mean())*100:.1f}%")

# Check index distributions
print("\n" + "=" * 80)
print("INDEX DISTRIBUTIONS")
print("=" * 80)

for idx in ['CRI_normalized', 'DII_normalized', 'RRS_normalized']:
    data = df[idx].dropna()
    print(f"\n{idx}:")
    print(f"   Min: {data.min():.2f}")
    print(f"   Q1: {data.quantile(0.25):.2f}")
    print(f"   Median: {data.median():.2f}")
    print(f"   Q3: {data.quantile(0.75):.2f}")
    print(f"   Max: {data.max():.2f}")
    print(f"   Mean: {data.mean():.2f}")
    print(f"   Std: {data.std():.2f}")

# Top resilient countries in 2023
print("\n" + "=" * 80)
print("TOP 10 MOST RESILIENT COUNTRIES (2023)")
print("=" * 80)

recent = df[df['year'] == 2023].sort_values('CRI_normalized', ascending=False)
for i, (_, row) in enumerate(recent.head(10).iterrows(), 1):
    gdp = row['gdp_per_capita_best']
    wgi = row['wgi_composite']
    print(f"{i:2}. {row['iso3']}: CRI={row['CRI_normalized']:.1f}, GDP=${gdp:,.0f}, WGI={wgi:.2f}")

# Bottom 10
print("\n" + "=" * 80)
print("BOTTOM 10 LEAST RESILIENT COUNTRIES (2023)")
print("=" * 80)

for i, (_, row) in enumerate(recent.tail(10).iterrows(), 1):
    gdp = row['gdp_per_capita_best']
    wgi = row['wgi_composite']
    print(f"{i:2}. {row['iso3']}: CRI={row['CRI_normalized']:.1f}, GDP=${gdp:,.0f}, WGI={wgi:.2f}")

print("\n" + "=" * 80)
