"""
Verification Script for Report Claims
======================================
This script verifies all numerical claims made in the LaTeX report
against the actual data in unified_resilience_dataset.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scipy import stats

# Load data
DATA_PATH = Path("d:/Work/Semester5/DAV/Project/Data/unified_resilience_dataset.csv")
df = pd.read_csv(DATA_PATH)

print("=" * 80)
print("REPORT CLAIM VERIFICATION")
print("=" * 80)

# Basic dataset info
print(f"\n1. DATASET OVERVIEW")
print(f"   Total rows: {len(df)}")
print(f"   Total columns: {len(df.columns)}")
print(f"   Unique countries: {df['iso3'].nunique()}")
print(f"   Year range: {df['year'].min()} - {df['year'].max()}")
print(f"   Expected: 192 countries, 2000-2024, ~4608 records")

# Check key columns
print(f"\n2. KEY COLUMNS PRESENT")
key_cols = ['iso3', 'year', 'region', 'CRI', 'CRI_normalized', 'DII', 'DII_normalized', 
            'RRS', 'RRS_normalized', 'wgi_composite', 'hdi', 'gdp_per_capita_best']
for col in key_cols:
    exists = col in df.columns
    coverage = (df[col].notna().sum() / len(df) * 100) if exists else 0
    print(f"   {col}: {'✓' if exists else '✗'} ({coverage:.1f}% coverage)")

# CLAIM: "Correlation between CRI and WGI is 0.78"
# CLAIM: "Correlation between CRI and GDP is 0.75"
print(f"\n3. CORRELATION CLAIMS")
if 'CRI_normalized' in df.columns and 'wgi_composite' in df.columns:
    # Use CRI_normalized for correlations
    mask_cri_wgi = df['CRI_normalized'].notna() & df['wgi_composite'].notna()
    corr_cri_wgi = df.loc[mask_cri_wgi, 'CRI_normalized'].corr(df.loc[mask_cri_wgi, 'wgi_composite'])
    print(f"   CRI vs WGI Composite correlation: {corr_cri_wgi:.4f}")
    print(f"   Report claims: 0.78")
    
if 'CRI_normalized' in df.columns and 'gdp_per_capita_best' in df.columns:
    mask_cri_gdp = df['CRI_normalized'].notna() & df['gdp_per_capita_best'].notna()
    corr_cri_gdp = df.loc[mask_cri_gdp, 'CRI_normalized'].corr(df.loc[mask_cri_gdp, 'gdp_per_capita_best'])
    print(f"   CRI vs GDP per capita correlation: {corr_cri_gdp:.4f}")
    # Also try log GDP
    df['log_gdp'] = np.log1p(df['gdp_per_capita_best'])
    mask_log = df['CRI_normalized'].notna() & df['log_gdp'].notna()
    corr_cri_log_gdp = df.loc[mask_log, 'CRI_normalized'].corr(df.loc[mask_log, 'log_gdp'])
    print(f"   CRI vs Log(GDP) correlation: {corr_cri_log_gdp:.4f}")
    print(f"   Report claims: 0.75")

# Also check RRS correlations
if 'RRS_normalized' in df.columns:
    print(f"\n   RRS correlations:")
    if 'wgi_composite' in df.columns:
        mask = df['RRS_normalized'].notna() & df['wgi_composite'].notna()
        corr = df.loc[mask, 'RRS_normalized'].corr(df.loc[mask, 'wgi_composite'])
        print(f"   RRS vs WGI: {corr:.4f}")
    if 'gdp_per_capita_best' in df.columns:
        mask = df['RRS_normalized'].notna() & df['gdp_per_capita_best'].notna()
        corr = df.loc[mask, 'RRS_normalized'].corr(df.loc[mask, 'gdp_per_capita_best'])
        print(f"   RRS vs GDP: {corr:.4f}")

# Check for specific countries mentioned (Guyana, Cabo Verde)
print(f"\n4. COUNTRY-SPECIFIC CLAIMS")

# Guyana (GUY)
if 'GUY' in df['iso3'].values:
    guy_2023 = df[(df['iso3'] == 'GUY') & (df['year'] == 2023)]
    if len(guy_2023) > 0:
        print(f"\n   GUYANA (2023):")
        for col in ['gdp_per_capita_best', 'CRI_normalized', 'wgi_composite', 'CRI']:
            if col in df.columns:
                val = guy_2023[col].values[0]
                print(f"      {col}: {val}")
        print(f"   Report claims: GDP ~$23k, CRI 0.40, WGI -0.25")
    else:
        # Get most recent year
        guy_recent = df[df['iso3'] == 'GUY'].sort_values('year', ascending=False).head(1)
        if len(guy_recent) > 0:
            print(f"\n   GUYANA (most recent: {guy_recent['year'].values[0]}):")
            for col in ['gdp_per_capita_best', 'CRI_normalized', 'wgi_composite']:
                if col in df.columns:
                    val = guy_recent[col].values[0]
                    print(f"      {col}: {val}")

# Cabo Verde (CPV)
if 'CPV' in df['iso3'].values:
    cpv_2023 = df[(df['iso3'] == 'CPV') & (df['year'] == 2023)]
    if len(cpv_2023) > 0:
        print(f"\n   CABO VERDE (2023):")
        for col in ['gdp_per_capita_best', 'CRI_normalized', 'wgi_composite', 'CRI']:
            if col in df.columns:
                val = cpv_2023[col].values[0]
                print(f"      {col}: {val}")
        print(f"   Report claims: GDP ~$4k, CRI 0.91, WGI +0.58")
    else:
        cpv_recent = df[df['iso3'] == 'CPV'].sort_values('year', ascending=False).head(1)
        if len(cpv_recent) > 0:
            print(f"\n   CABO VERDE (most recent: {cpv_recent['year'].values[0]}):")
            for col in ['gdp_per_capita_best', 'CRI_normalized', 'wgi_composite']:
                if col in df.columns:
                    val = cpv_recent[col].values[0]
                    print(f"      {col}: {val}")

# Missing data analysis
print(f"\n5. MISSING DATA CLAIMS")
print(f"   Report claims: 60+ missing emdat_deaths, 58 missing wgi_composite for Africa 2000-2005")

# Check actual missing data for Africa 2000-2005
if 'region' in df.columns:
    africa_early = df[(df['region'] == 'Africa') & (df['year'].between(2000, 2005))]
    print(f"\n   Africa 2000-2005:")
    print(f"   Total country-years: {len(africa_early)}")
    
    for col in ['emdat_deaths', 'wgi_composite', 'hdi']:
        if col in df.columns:
            missing = africa_early[col].isna().sum()
            total = len(africa_early)
            print(f"   {col} missing: {missing}/{total} ({missing/total*100:.1f}%)")

# Check IterativeImputer claim
print(f"\n6. IMPUTATION METHOD")
print(f"   Report claims: sklearn.impute.IterativeImputer used")
print(f"   Code actually uses: Linear interpolation within country groups")
print(f"   (See build_unified_dataset.py line ~175: interpolate_within_country function)")

# Check DII formula
print(f"\n7. DII FORMULA VERIFICATION")
print(f"   Report formula: DII = ((F + 4×Ap) / GDP_pc) × S")
print(f"   Code formula: DII = (fatalities_per_million + 4×affected_pct) / GDP_pc × severity")
print(f"   Note: 'S' (Severity) comes from GDACS alert scores")

# Check what severity column exists
severity_cols = [c for c in df.columns if 'severity' in c.lower() or 'alert' in c.lower()]
print(f"   Severity-related columns found: {severity_cols}")

# Check RRS formula
print(f"\n8. RRS FORMULA VERIFICATION")
print(f"   Report formula: RRS = (ΔGDP_growth + HDI + Gov) / T_recovery")
print(f"   Code formula:")
print(f"   - GDP growth change: year-over-year diff of gdp_growth_best")
print(f"   - HDI: normalized to 0-1")
print(f"   - Gov: wgi_composite, normalized to 0-1")
print(f"   - Recovery_factor: 1 + log(1 + disaster_events)/3")

# Check CRI formula
print(f"\n9. CRI FORMULA VERIFICATION")
print(f"   Report doesn't explain CRI formula clearly")
print(f"   Code formula: CRI = Adaptive_Capacity / (Exposure + Vulnerability + 0.001)")
print(f"   - Adaptive Capacity: ndgain_readiness (or inform_coping inverted)")
print(f"   - Exposure: inform_hazard (or normalized disaster count)")
print(f"   - Vulnerability: ndgain_vulnerability (or inform_vulnerability)")

# Check the actual index statistics
print(f"\n10. INDEX STATISTICS")
for idx in ['DII', 'DII_normalized', 'RRS', 'RRS_normalized', 'CRI', 'CRI_normalized']:
    if idx in df.columns:
        print(f"\n   {idx}:")
        print(f"      Mean: {df[idx].mean():.4f}")
        print(f"      Std:  {df[idx].std():.4f}")
        print(f"      Min:  {df[idx].min():.4f}")
        print(f"      Max:  {df[idx].max():.4f}")
        print(f"      Coverage: {df[idx].notna().sum()}/{len(df)} ({df[idx].notna().sum()/len(df)*100:.1f}%)")

# Regional analysis for temporal evolution claims
print(f"\n11. TEMPORAL EVOLUTION BY REGION")
if 'region' in df.columns and 'ndgain_vulnerability' in df.columns and 'ndgain_readiness' in df.columns:
    for region in df['region'].dropna().unique():
        region_df = df[df['region'] == region]
        
        early = region_df[region_df['year'].between(2000, 2005)]
        late = region_df[region_df['year'].between(2018, 2023)]
        
        vuln_early = early['ndgain_vulnerability'].mean()
        vuln_late = late['ndgain_vulnerability'].mean()
        
        read_early = early['ndgain_readiness'].mean()
        read_late = late['ndgain_readiness'].mean()
        
        gap_early = read_early - vuln_early if pd.notna(read_early) and pd.notna(vuln_early) else np.nan
        gap_late = read_late - vuln_late if pd.notna(read_late) and pd.notna(vuln_late) else np.nan
        
        print(f"\n   {region}:")
        print(f"      Readiness 2000-05: {read_early:.3f}, 2018-23: {read_late:.3f}")
        print(f"      Vulnerability 2000-05: {vuln_early:.3f}, 2018-23: {vuln_late:.3f}")
        print(f"      Gap (R-V) 2000-05: {gap_early:.3f}, 2018-23: {gap_late:.3f}")

# Find interesting paradox examples
print(f"\n12. FINDING REAL PARADOX EXAMPLES")
recent = df[df['year'] == df['year'].max()].copy()

# High GDP but low CRI
if 'gdp_per_capita_best' in recent.columns and 'CRI_normalized' in recent.columns:
    recent['gdp_rank'] = recent['gdp_per_capita_best'].rank(pct=True)
    recent['cri_rank'] = recent['CRI_normalized'].rank(pct=True)
    
    # Rich but fragile: high GDP rank, low CRI rank
    rich_fragile = recent[(recent['gdp_rank'] > 0.7) & (recent['cri_rank'] < 0.4)]
    print(f"\n   Rich but Fragile (GDP top 30%, CRI bottom 40%):")
    for _, row in rich_fragile.nlargest(5, 'gdp_per_capita_best').iterrows():
        print(f"      {row['iso3']}: GDP ${row['gdp_per_capita_best']:,.0f}, CRI {row['CRI_normalized']:.1f}, WGI {row.get('wgi_composite', 'N/A')}")
    
    # Poor but resilient: low GDP rank, high CRI rank  
    poor_resilient = recent[(recent['gdp_rank'] < 0.4) & (recent['cri_rank'] > 0.6)]
    print(f"\n   Poor but Resilient (GDP bottom 40%, CRI top 40%):")
    for _, row in poor_resilient.nlargest(5, 'CRI_normalized').iterrows():
        print(f"      {row['iso3']}: GDP ${row['gdp_per_capita_best']:,.0f}, CRI {row['CRI_normalized']:.1f}, WGI {row.get('wgi_composite', 'N/A')}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
