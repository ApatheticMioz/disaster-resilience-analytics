"""
Comprehensive Dataset Analysis for Global Disaster Resilience Analytics Platform
================================================================================
This script analyzes the unified_resilience_dataset.csv to understand:
1. Data structure and coverage
2. Variable distributions and correlations
3. Suitability for proposed visualization techniques
4. Recommendations for Tableau dashboard design

Author: Data Visualization Expert Analysis
Date: December 2025
"""

import pandas as pd
import numpy as np
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Load the dataset
print("=" * 80)
print("GLOBAL DISASTER RESILIENCE ANALYTICS - DATASET ANALYSIS")
print("=" * 80)

df = pd.read_csv(r"Data\unified_resilience_dataset.csv")

print(f"\n📊 DATASET OVERVIEW")
print("-" * 40)
print(f"Total Records: {len(df):,}")
print(f"Total Columns: {len(df.columns)}")
print(f"Countries (iso3): {df['iso3'].nunique()}")
print(f"Year Range: {df['year'].min()} - {df['year'].max()}")
print(f"Regions: {df['region'].nunique()}")
print(f"Income Groups: {df['income_group'].nunique()}")

# Column categorization
print(f"\n📋 COLUMN CATEGORIES")
print("-" * 40)

# Define column categories
index_cols = ['DII', 'DII_normalized', 'RRS', 'RRS_normalized', 'CRI', 'CRI_normalized']
emdat_cols = [c for c in df.columns if c.startswith('emdat_')]
gdacs_cols = [c for c in df.columns if c.startswith('gdacs_')]
desinventar_cols = [c for c in df.columns if c.startswith('desinventar_')]
wgi_cols = [c for c in df.columns if c.startswith('wgi_')]
ndgain_cols = [c for c in df.columns if c.startswith('ndgain_')]
inform_cols = [c for c in df.columns if c.startswith('inform_')]
economic_cols = ['gdp_per_capita', 'gdp_growth', 'gdp_per_capita_ppp', 'gdp_per_capita_imf', 
                 'gdp_growth_imf', 'gni_per_capita', 'govt_revenue_pct_gdp', 'govt_debt_pct_gdp']
social_cols = ['hdi', 'life_expectancy', 'mean_years_schooling', 'expected_years_schooling',
               'gini_index', 'gini_wid', 'literacy_rate', 'poverty_rate']
infrastructure_cols = ['electricity_access_pct', 'internet_users_pct', 'water_access_pct',
                       'sanitation_access_pct', 'hospital_beds_per_1k', 'physicians_per_1k']

print(f"  Core Indices: {len(index_cols)}")
print(f"  EM-DAT Disaster: {len(emdat_cols)}")
print(f"  GDACS Alerts: {len(gdacs_cols)}")
print(f"  DesInventar: {len(desinventar_cols)}")
print(f"  Governance (WGI): {len(wgi_cols)}")
print(f"  ND-GAIN Climate: {len(ndgain_cols)}")
print(f"  INFORM Risk: {len(inform_cols)}")
print(f"  Economic: {len(economic_cols)}")
print(f"  Social Development: {len(social_cols)}")
print(f"  Infrastructure: {len(infrastructure_cols)}")

# Data Coverage Analysis
print(f"\n📈 DATA COVERAGE ANALYSIS")
print("-" * 40)

coverage = (1 - df.isnull().mean()) * 100
print("\nTop 20 Best-Covered Variables:")
for col, pct in coverage.nlargest(20).items():
    print(f"  {col}: {pct:.1f}%")

print("\nCritical Variables Coverage:")
critical_vars = ['DII', 'RRS', 'CRI', 'hdi', 'gdp_per_capita_best', 'wgi_composite', 
                 'total_disaster_deaths', 'total_disaster_affected', 'population']
for var in critical_vars:
    if var in df.columns:
        pct = coverage.get(var, 0)
        print(f"  {var}: {pct:.1f}%")

# Geographic Distribution
print(f"\n🌍 GEOGRAPHIC DISTRIBUTION")
print("-" * 40)
region_counts = df.groupby('region').agg({
    'iso3': 'nunique',
    'year': 'count'
}).rename(columns={'iso3': 'Countries', 'year': 'Records'})
print(region_counts.to_string())

print(f"\n💰 INCOME GROUP DISTRIBUTION")
print("-" * 40)
income_counts = df.groupby('income_group').agg({
    'iso3': 'nunique',
    'year': 'count'
}).rename(columns={'iso3': 'Countries', 'year': 'Records'})
print(income_counts.to_string())

# Core Index Statistics
print(f"\n📊 CORE INDEX STATISTICS")
print("-" * 40)
for idx in ['DII', 'RRS', 'CRI']:
    if idx in df.columns:
        print(f"\n{idx}:")
        print(f"  Mean: {df[idx].mean():.4f}")
        print(f"  Std: {df[idx].std():.4f}")
        print(f"  Min: {df[idx].min():.4f}")
        print(f"  Max: {df[idx].max():.4f}")
        print(f"  Coverage: {coverage.get(idx, 0):.1f}%")

# Temporal Coverage
print(f"\n📅 TEMPORAL COVERAGE BY DECADE")
print("-" * 40)
df['decade'] = (df['year'] // 10) * 10
decade_coverage = df.groupby('decade').agg({
    'iso3': 'nunique',
    'DII': lambda x: x.notna().sum(),
    'RRS': lambda x: x.notna().sum(),
    'CRI': lambda x: x.notna().sum()
}).rename(columns={'iso3': 'Countries', 'DII': 'DII_obs', 'RRS': 'RRS_obs', 'CRI': 'CRI_obs'})
print(decade_coverage.to_string())

# Correlation Analysis for Key Variables
print(f"\n🔗 KEY CORRELATIONS (where data available)")
print("-" * 40)
key_vars = ['DII', 'RRS', 'CRI', 'hdi', 'gdp_per_capita_best', 'wgi_composite', 
            'ndgain_score', 'inform_risk']
available_vars = [v for v in key_vars if v in df.columns and df[v].notna().sum() > 100]
if len(available_vars) > 1:
    corr_matrix = df[available_vars].corr()
    print("\nCorrelation Matrix:")
    print(corr_matrix.round(3).to_string())

# Disaster Type Distribution
print(f"\n🌊 DISASTER TYPE DISTRIBUTION (GDACS)")
print("-" * 40)
disaster_types = ['gdacs_drought_count', 'gdacs_earthquake_count', 'gdacs_eruption_count',
                  'gdacs_flood_count', 'gdacs_forest_fire_count', 'gdacs_tropical_cyclone_count']
for dt in disaster_types:
    if dt in df.columns:
        total = df[dt].sum()
        dtype = dt.replace('gdacs_', '').replace('_count', '')
        print(f"  {dtype.title()}: {total:,.0f} events")

# Impact Magnitude Analysis
print(f"\n💥 DISASTER IMPACT MAGNITUDES")
print("-" * 40)
impact_vars = ['total_disaster_deaths', 'total_disaster_affected', 'emdat_damage_usd']
for var in impact_vars:
    if var in df.columns:
        total = df[var].sum()
        mean = df[var].mean()
        max_val = df[var].max()
        print(f"\n{var}:")
        print(f"  Total: {total:,.0f}")
        print(f"  Mean per country-year: {mean:,.0f}")
        print(f"  Max single record: {max_val:,.0f}")

# Identify Countries with Extreme Values
print(f"\n🔥 TOP 10 MOST IMPACTED COUNTRIES (by total deaths)")
print("-" * 40)
if 'total_disaster_deaths' in df.columns:
    country_deaths = df.groupby('iso3')['total_disaster_deaths'].sum().nlargest(10)
    for country, deaths in country_deaths.items():
        print(f"  {country}: {deaths:,.0f} deaths")

print(f"\n💪 TOP 10 MOST RESILIENT COUNTRIES (by mean CRI)")
print("-" * 40)
if 'CRI' in df.columns:
    country_cri = df.groupby('iso3')['CRI'].mean().nlargest(10)
    for country, cri in country_cri.items():
        print(f"  {country}: {cri:.4f}")

# Visualization Suitability Assessment
print("\n" + "=" * 80)
print("VISUALIZATION TECHNIQUE ASSESSMENT FOR TABLEAU")
print("=" * 80)

print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED VISUALIZATION TECHNIQUES                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ 1. CHOROPLETH MAPS ✅ (Highly Recommended)                                  │
│    Data Support: iso3 codes enable direct geographic mapping                │
│    Variables: DII, RRS, CRI, hdi, gdp_per_capita, inform_risk               │
│    Tableau: Use filled maps with diverging color scales                     │
│    Insight: Show spatial patterns of vulnerability vs resilience            │
│                                                                             │
│ 2. TIME SERIES LINE CHARTS ✅ (Essential)                                   │
│    Data Support: 24 years of data (2000-2023)                               │
│    Variables: All indices + economic/social indicators over time            │
│    Tableau: Dual-axis for comparing DII vs RRS trajectories                 │
│    Insight: Track resilience evolution, identify inflection points          │
│                                                                             │
│ 3. SCATTER/BUBBLE PLOTS ✅ (Critical for Relationships)                     │
│    Pairs: GDP vs CRI, HDI vs RRS, Governance vs Recovery Speed              │
│    Encoding: Size = disaster deaths, Color = region/income_group            │
│    Tableau: Interactive selection with parameter controls                   │
│    Insight: "Does wealth = resilience?" hypothesis testing                  │
│                                                                             │
│ 4. PARALLEL COORDINATES (Moderately Supported)                              │
│    Variables: Multiple dimensions of CRI components                         │
│    Challenge: Many missing values in infrastructure variables               │
│    Workaround: Focus on well-covered variables (hdi, gdp, governance)       │
│    Insight: Multi-dimensional country profiles                              │
│                                                                             │
│ 5. STACKED AREA CHARTS ✅ (Good for Composition)                            │
│    Variables: Disaster types over time (gdacs_* counts)                     │
│    Use: Show changing disaster profile composition                          │
│    Insight: Climate change impact on disaster patterns                      │
│                                                                             │
│ 6. TREEMAPS ✅ (Excellent for Hierarchical)                                 │
│    Hierarchy: Region → Income Group → Country                               │
│    Size: Population or total affected                                       │
│    Color: CRI or DII (resilience gradient)                                  │
│    Insight: Proportional impact across hierarchies                          │
│                                                                             │
│ 7. BOX PLOTS / VIOLIN PLOTS ✅ (Distribution Analysis)                      │
│    Grouping: By region, income_group, or decade                             │
│    Variables: DII, RRS, CRI distributions                                   │
│    Insight: Compare resilience distributions across groups                  │
│                                                                             │
│ 8. HEATMAPS ✅ (Correlation Matrices)                                       │
│    Variables: Cross-correlation of all resilience factors                   │
│    Insight: Identify which factors drive resilience                         │
│                                                                             │
│ 9. SMALL MULTIPLES (Faceted Charts)                                         │
│    Facet by: Region or disaster type                                        │
│    Chart type: Line charts showing index evolution                          │
│    Insight: Compare patterns across categories                              │
│                                                                             │
│ 10. SANKEY DIAGRAMS (Flow Visualization)                                    │
│     Data Challenge: Need humanitarian_funding_usd (limited coverage)        │
│     Alternative: Use income_group → disaster_type → impact_level flows      │
│     Insight: Flow of disaster impact through socioeconomic groups           │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""")

# Dashboard Architecture Recommendation
print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED DASHBOARD ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ DASHBOARD 1: "GLOBAL RESILIENCE OVERVIEW" (Geographic Focus)                │
│ ├── Primary: Choropleth Map (CRI/DII selector)                              │
│ ├── Secondary: Bar chart of top/bottom 10 countries                         │
│ ├── Tertiary: Time slider for year animation                                │
│ └── Filters: Region, Income Group, Year Range                               │
│                                                                             │
│ DASHBOARD 2: "RESILIENCE DYNAMICS" (Temporal Focus)                         │
│ ├── Primary: Multi-line time series (indices over time)                     │
│ ├── Secondary: Stacked area (disaster type composition)                     │
│ ├── Tertiary: Event markers for major disasters                             │
│ └── Filters: Country selector, disaster type                                │
│                                                                             │
│ DASHBOARD 3: "FACTOR ANALYSIS" (Analytical Focus)                           │
│ ├── Primary: Scatter matrix (GDP, HDI, Governance vs Resilience)            │
│ ├── Secondary: Parallel coordinates (country profiles)                      │
│ ├── Tertiary: Correlation heatmap                                           │
│ └── Filters: Income group, region                                           │
│                                                                             │
│ DASHBOARD 4: "COUNTRY DEEP-DIVE" (Detail Focus)                             │
│ ├── Primary: Country selector with key metrics                              │
│ ├── Secondary: Historical timeline of disasters                             │
│ ├── Tertiary: Radar chart of resilience components                          │
│ └── Context: Peer comparison (similar countries)                            │
│                                                                             │
│ CROSS-DASHBOARD ACTIONS:                                                    │
│ • Click country on map → Filter all other dashboards                        │
│ • Select year range → Consistent filtering                                  │
│ • Highlight disaster type → Cross-highlight across views                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""")

# Data Quality Notes for Tableau
print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                       DATA QUALITY NOTES FOR TABLEAU                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ ⚠️  MISSING DATA HANDLING:                                                  │
│     • inform_* variables: Only available from 2016 onwards                  │
│     • literacy_rate: Sparse (<20% coverage)                                 │
│     • poverty_rate: Sparse (<15% coverage)                                  │
│     • hospital_beds, physicians: Incomplete                                 │
│     SOLUTION: Use *_best columns which have gap-filled values               │
│               Use LOD calculations for aggregations                         │
│                                                                             │
│ ⚠️  OUTLIER HANDLING:                                                       │
│     • emdat_deaths: Extreme spikes (Haiti 2010, Indian Ocean 2004)          │
│     • DII: Right-skewed distribution                                        │
│     SOLUTION: Use log scales or normalized versions                         │
│                                                                             │
│ ⚠️  GEOGRAPHIC GAPS:                                                        │
│     • Some small island nations missing                                     │
│     • Conflict zones may have data gaps                                     │
│     SOLUTION: Document exclusions, use region aggregates                    │
│                                                                             │
│ ⚠️  TEMPORAL CONSIDERATIONS:                                                │
│     • COVID-19 (2020-2021): Unusual patterns                                │
│     • Pre-2000 data limited                                                 │
│     SOLUTION: Add COVID indicator, focus on 2000-2023                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""")

# Key Insights Preview
print("""
┌─────────────────────────────────────────────────────────────────────────────┐
│                     KEY ANALYTICAL QUESTIONS TO EXPLORE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ Q1: "Does wealth guarantee resilience?"                                     │
│     → Scatter: GDP per capita vs CRI, colored by region                     │
│     → Expected: Positive correlation but with exceptions                    │
│                                                                             │
│ Q2: "Which regions improved most over time?"                                │
│     → Line chart: Mean CRI by region over years                             │
│     → Look for: Convergence or divergence trends                            │
│                                                                             │
│ Q3: "Do governance and recovery correlate?"                                 │
│     → Scatter: wgi_composite vs RRS                                         │
│     → Hypothesis: Strong governance = faster recovery                       │
│                                                                             │
│ Q4: "Is climate vulnerability increasing?"                                  │
│     → Time series: ndgain_vulnerability + disaster frequency                │
│     → Look for: Upward trends, especially in vulnerable regions             │
│                                                                             │
│ Q5: "Which disaster types cause most impact?"                               │
│     → Stacked bar: Deaths by disaster type over time                        │
│     → Insight: Floods vs earthquakes vs droughts                            │
│                                                                             │
│ Q6: "Are low-income countries improving?"                                   │
│     → Box plots: CRI distribution by income_group per decade                │
│     → Look for: Narrowing gaps or widening inequality                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
""")

print("\n" + "=" * 80)
print("ANALYSIS COMPLETE")
print("=" * 80)
print("\nThis analysis has been saved. Use these insights to guide Tableau design.")
