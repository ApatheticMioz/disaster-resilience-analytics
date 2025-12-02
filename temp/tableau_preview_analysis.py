"""
Tableau Sheet Preview Analysis
==============================
Analyzes the actual data to preview what each sheet will look like
and identify potential issues before Tableau implementation.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load the dataset
df = pd.read_csv('../Data/unified_resilience_dataset.csv')

print("=" * 80)
print("TABLEAU SHEET PREVIEW ANALYSIS")
print("=" * 80)
print(f"Dataset: {len(df)} rows, {len(df.columns)} columns")
print(f"Countries: {df['iso3'].nunique()}")
print(f"Years: {df['year'].min()} - {df['year'].max()}")

# Use latest year for most analyses
latest_year = df['year'].max()
df_latest = df[df['year'] == latest_year].copy()
print(f"\nLatest year ({latest_year}): {len(df_latest)} countries")

# ============================================================================
# SHEET 1 ANALYSIS: Global Map
# ============================================================================
print("\n" + "=" * 80)
print("SHEET 1: GLOBAL RESILIENCE MAP")
print("=" * 80)

print("\n📊 CRI_normalized Distribution (for color encoding):")
cri_stats = df_latest['CRI_normalized'].describe()
print(cri_stats)

print("\n📊 CRI by Quintile:")
df_latest['CRI_quintile'] = pd.qcut(df_latest['CRI_normalized'], 5, labels=['0-20%', '20-40%', '40-60%', '60-80%', '80-100%'])
print(df_latest['CRI_quintile'].value_counts().sort_index())

print("\n📊 total_disaster_deaths Distribution (for size encoding):")
deaths_stats = df_latest['total_disaster_deaths'].describe()
print(deaths_stats)

# Check if deaths are heavily skewed
print(f"\n⚠️ ISSUE CHECK - Deaths Skewness:")
print(f"   Max deaths: {df_latest['total_disaster_deaths'].max():,.0f}")
print(f"   Median deaths: {df_latest['total_disaster_deaths'].median():,.0f}")
print(f"   Mean deaths: {df_latest['total_disaster_deaths'].mean():,.0f}")
print(f"   Countries with 0 deaths: {(df_latest['total_disaster_deaths'] == 0).sum()}")
print(f"   Countries with >1000 deaths: {(df_latest['total_disaster_deaths'] > 1000).sum()}")

print("\n💡 RECOMMENDATION for Sheet 1:")
print("   - Size mark on filled map WON'T WORK as intended")
print("   - Option A: Use dual-axis map (filled + symbol layer)")
print("   - Option B: Just use filled map with CRI color only")
print("   - Option C: Add death count to tooltip, not visual encoding")

# ============================================================================
# SHEET 2 ANALYSIS: Resilience Quadrant Matrix
# ============================================================================
print("\n" + "=" * 80)
print("SHEET 2: RESILIENCE QUADRANT MATRIX")
print("=" * 80)

print("\n📊 DII_normalized Distribution:")
dii_stats = df_latest['DII_normalized'].describe()
print(dii_stats)

print("\n📊 RRS_normalized Distribution:")
rrs_stats = df_latest['RRS_normalized'].describe()
print(rrs_stats)

# Calculate medians for reference lines
dii_median = df_latest['DII_normalized'].median()
rrs_median = df_latest['RRS_normalized'].median()

print(f"\n📍 QUADRANT REFERENCE LINES:")
print(f"   DII Median (X-axis): {dii_median:.2f}")
print(f"   RRS Median (Y-axis): {rrs_median:.2f}")

# Check quadrant distribution
df_latest['quadrant'] = 'Unknown'
df_latest.loc[(df_latest['DII_normalized'] < dii_median) & (df_latest['RRS_normalized'] >= rrs_median), 'quadrant'] = 'Bulletproof'
df_latest.loc[(df_latest['DII_normalized'] >= dii_median) & (df_latest['RRS_normalized'] >= rrs_median), 'quadrant'] = 'Fighters'
df_latest.loc[(df_latest['DII_normalized'] >= dii_median) & (df_latest['RRS_normalized'] < rrs_median), 'quadrant'] = 'Fragile'
df_latest.loc[(df_latest['DII_normalized'] < dii_median) & (df_latest['RRS_normalized'] < rrs_median), 'quadrant'] = 'At Risk'

print("\n📊 Quadrant Distribution:")
print(df_latest['quadrant'].value_counts())

print("\n⚠️ ISSUE CHECK - DII Distribution:")
print(f"   DII Median: {dii_median:.2f}")
print(f"   DII at 25th percentile: {df_latest['DII_normalized'].quantile(0.25):.2f}")
print(f"   DII at 75th percentile: {df_latest['DII_normalized'].quantile(0.75):.2f}")
print(f"   Countries with DII < 1: {(df_latest['DII_normalized'] < 1).sum()}")
print(f"   Countries with DII > 10: {(df_latest['DII_normalized'] > 10).sum()}")

if dii_median < 5:
    print("\n   ❌ PROBLEM: DII median is very low - most countries clustered near 0")
    print("   This will make the left quadrants (Bulletproof, At Risk) very crowded")
    print("   and the right quadrants (Fighters, Fragile) very sparse")

print("\n💡 ALTERNATIVE APPROACHES for Sheet 2:")
print("   Option A: Use LOG scale for DII (spreads out the distribution)")
print("   Option B: Use DII percentile rank instead of raw value")
print("   Option C: Use different X-axis variable (inform_hazard, total_disaster_events)")

# Check alternative X-axis candidates
print("\n📊 Alternative X-axis candidates:")
for col in ['total_disaster_events', 'inform_hazard', 'inform_risk', 'DII']:
    if col in df_latest.columns:
        valid = df_latest[col].notna()
        if valid.sum() > 0:
            print(f"   {col}: median={df_latest.loc[valid, col].median():.2f}, "
                  f"range=[{df_latest.loc[valid, col].min():.2f}, {df_latest.loc[valid, col].max():.2f}], "
                  f"coverage={valid.sum()}")

# ============================================================================
# SHEET 3 ANALYSIS: Timeline by Region
# ============================================================================
print("\n" + "=" * 80)
print("SHEET 3: RESILIENCE EVOLUTION TIMELINE")
print("=" * 80)

# Calculate regional averages over time
regional_cri = df.groupby(['year', 'region'])['CRI_normalized'].mean().reset_index()
regional_pivot = regional_cri.pivot(index='year', columns='region', values='CRI_normalized')

print("\n📊 CRI by Region Over Time:")
print(regional_pivot.round(2))

print("\n📊 Regional Trends (First vs Last Year):")
for region in regional_pivot.columns:
    first_val = regional_pivot[region].iloc[0]
    last_val = regional_pivot[region].iloc[-1]
    change = last_val - first_val
    pct_change = (change / first_val) * 100 if first_val > 0 else 0
    print(f"   {region}: {first_val:.1f} → {last_val:.1f} (Δ {change:+.1f}, {pct_change:+.1f}%)")

print("\n📊 Key Event Years - Regional CRI:")
key_years = [2004, 2008, 2010, 2011, 2020]
for year in key_years:
    if year in regional_pivot.index:
        prev_year = year - 1 if year - 1 in regional_pivot.index else None
        print(f"\n   {year}:")
        for region in regional_pivot.columns:
            curr = regional_pivot.loc[year, region]
            if prev_year:
                prev = regional_pivot.loc[prev_year, region]
                diff = curr - prev
                print(f"      {region}: {curr:.1f} (Δ {diff:+.1f} from {prev_year})")
            else:
                print(f"      {region}: {curr:.1f}")

print("\n⚠️ ISSUE CHECK - Timeline Visibility:")
cri_range = regional_pivot.max().max() - regional_pivot.min().min()
print(f"   Total CRI range across all regions/years: {cri_range:.1f}")
print(f"   Min CRI: {regional_pivot.min().min():.1f}")
print(f"   Max CRI: {regional_pivot.max().max():.1f}")

if cri_range < 20:
    print("\n   ⚠️ WARNING: Small range - lines may appear flat")
    print("   Consider: Adjusted Y-axis range, or showing absolute values")

# ============================================================================
# SHEET 4 ANALYSIS: Governance vs Wealth
# ============================================================================
print("\n" + "=" * 80)
print("SHEET 4: GOVERNANCE VS RESILIENCE")
print("=" * 80)

print("\n📊 wgi_composite Distribution:")
wgi_stats = df_latest['wgi_composite'].describe()
print(wgi_stats)

print("\n📊 Correlation Analysis:")
correlations = {
    'CRI vs WGI (Governance)': df_latest[['CRI_normalized', 'wgi_composite']].corr().iloc[0, 1],
    'CRI vs GDP per capita': df_latest[['CRI_normalized', 'gdp_per_capita_best']].corr().iloc[0, 1],
    'CRI vs HDI': df_latest[['CRI_normalized', 'hdi']].corr().iloc[0, 1],
}
for name, corr in correlations.items():
    print(f"   {name}: r = {corr:.3f} (R² = {corr**2:.3f})")

print("\n📊 Key Comparison Countries:")
comparison_pairs = [
    ('CHL', 'VEN', 'Chile vs Venezuela'),
    ('RWA', 'GNQ', 'Rwanda vs Eq. Guinea'),
    ('BWA', 'LBY', 'Botswana vs Libya'),
    ('JPN', 'HTI', 'Japan vs Haiti'),
]

for iso1, iso2, label in comparison_pairs:
    c1 = df_latest[df_latest['iso3'] == iso1]
    c2 = df_latest[df_latest['iso3'] == iso2]
    if len(c1) > 0 and len(c2) > 0:
        print(f"\n   {label}:")
        print(f"      {iso1}: CRI={c1['CRI_normalized'].values[0]:.1f}, WGI={c1['wgi_composite'].values[0]:.2f}, GDP=${c1['gdp_per_capita_best'].values[0]:,.0f}")
        print(f"      {iso2}: CRI={c2['CRI_normalized'].values[0]:.1f}, WGI={c2['wgi_composite'].values[0]:.2f}, GDP=${c2['gdp_per_capita_best'].values[0]:,.0f}")

# ============================================================================
# VISUALIZATION PREVIEWS
# ============================================================================
print("\n" + "=" * 80)
print("GENERATING PREVIEW PLOTS...")
print("=" * 80)

fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# Sheet 1 Preview: CRI Distribution (histogram since we can't do map in matplotlib)
ax1 = axes[0, 0]
ax1.hist(df_latest['CRI_normalized'].dropna(), bins=20, color='steelblue', edgecolor='white')
ax1.axvline(df_latest['CRI_normalized'].median(), color='red', linestyle='--', label=f'Median: {df_latest["CRI_normalized"].median():.1f}')
ax1.set_xlabel('CRI Normalized')
ax1.set_ylabel('Number of Countries')
ax1.set_title('Sheet 1 Preview: CRI Distribution (2023)\n[Map will show this as color gradient]')
ax1.legend()

# Sheet 2 Preview: Quadrant Scatter
ax2 = axes[0, 1]
colors = {'Africa': '#e15759', 'Americas': '#4e79a7', 'Asia': '#f28e2b', 'Europe': '#76b7b2', 'Oceania': '#59a14f'}
for region in df_latest['region'].dropna().unique():
    mask = df_latest['region'] == region
    ax2.scatter(df_latest.loc[mask, 'DII_normalized'], 
                df_latest.loc[mask, 'RRS_normalized'],
                c=colors.get(region, 'gray'),
                label=region, alpha=0.7, s=50)
ax2.axvline(dii_median, color='gray', linestyle='--', alpha=0.5)
ax2.axhline(rrs_median, color='gray', linestyle='--', alpha=0.5)
ax2.set_xlabel('DII Normalized (Impact)')
ax2.set_ylabel('RRS Normalized (Recovery)')
ax2.set_title(f'Sheet 2 Preview: Quadrant Matrix\nDII Median={dii_median:.1f}, RRS Median={rrs_median:.1f}')
ax2.legend(loc='upper right', fontsize=8)
# Add quadrant labels
ax2.text(dii_median/2, rrs_median + (100-rrs_median)/2, 'BULLETPROOF', ha='center', fontsize=9, alpha=0.5)
ax2.text(dii_median + (100-dii_median)/2, rrs_median + (100-rrs_median)/2, 'FIGHTERS', ha='center', fontsize=9, alpha=0.5)
ax2.text(dii_median + (100-dii_median)/2, rrs_median/2, 'FRAGILE', ha='center', fontsize=9, alpha=0.5)
ax2.text(dii_median/2, rrs_median/2, 'AT RISK', ha='center', fontsize=9, alpha=0.5)

# Sheet 3 Preview: Timeline by Region
ax3 = axes[1, 0]
for region in regional_pivot.columns:
    ax3.plot(regional_pivot.index, regional_pivot[region], 
             color=colors.get(region, 'gray'), label=region, linewidth=2)
# Add event markers
events = {2004: 'Tsunami', 2010: 'Haiti', 2011: 'Japan', 2020: 'COVID'}
for year, label in events.items():
    if year in regional_pivot.index:
        ax3.axvline(year, color='red', linestyle=':', alpha=0.5)
        ax3.text(year, ax3.get_ylim()[1], label, rotation=90, va='top', fontsize=8, alpha=0.7)
ax3.set_xlabel('Year')
ax3.set_ylabel('Average CRI Normalized')
ax3.set_title('Sheet 3 Preview: Resilience Timeline by Region')
ax3.legend(loc='lower right', fontsize=8)
ax3.set_xlim(2000, 2023)

# Sheet 4 Preview: Governance vs CRI
ax4 = axes[1, 1]
for income in ['Low', 'Lower-middle', 'Upper-middle', 'High']:
    mask = df_latest['income_group'] == income
    ax4.scatter(df_latest.loc[mask, 'wgi_composite'], 
                df_latest.loc[mask, 'CRI_normalized'],
                label=income, alpha=0.6, s=40)
# Add trend line
valid = df_latest[['wgi_composite', 'CRI_normalized']].dropna()
z = np.polyfit(valid['wgi_composite'], valid['CRI_normalized'], 1)
p = np.poly1d(z)
x_line = np.linspace(valid['wgi_composite'].min(), valid['wgi_composite'].max(), 100)
ax4.plot(x_line, p(x_line), 'r--', alpha=0.8, label=f'Trend (R²={correlations["CRI vs WGI (Governance)"]**2:.2f})')
ax4.set_xlabel('WGI Composite (Governance)')
ax4.set_ylabel('CRI Normalized')
ax4.set_title('Sheet 4 Preview: Governance vs Resilience')
ax4.legend(loc='lower right', fontsize=8)

plt.tight_layout()
plt.savefig('tableau_preview_plots.png', dpi=150, bbox_inches='tight')
print(f"\n✅ Saved preview plots to: tableau_preview_plots.png")

# ============================================================================
# FINAL RECOMMENDATIONS
# ============================================================================
print("\n" + "=" * 80)
print("FINAL RECOMMENDATIONS")
print("=" * 80)

print("""
📋 SHEET 1 (Map):
   ✗ REMOVE size encoding (doesn't work with filled maps)
   ✓ Use only CRI_normalized for color (Red-Yellow-Green)
   ✓ Put disaster deaths in tooltip instead
   ✓ Consider dual-layer map if deaths visualization is critical

📋 SHEET 2 (Quadrant):
   ⚠️ DII_normalized median is very low ({:.1f}) - data is right-skewed
   OPTIONS:
   A) Use LOG(DII_normalized + 1) for X-axis → spreads distribution
   B) Use PERCENTILE rank of DII → guarantees 50/50 split
   C) Use total_disaster_events or inform_risk instead
   D) Accept uneven quadrants (most countries are low-impact)
   
   RECOMMENDED: Option D (accept reality) or Option C (use inform_risk)
   
📋 SHEET 3 (Timeline):
   ✓ Regional lines look good and show differentiation
   ✓ Europe consistently highest, Africa lowest
   ⚠️ Y-axis range is narrow ({:.1f} to {:.1f}) - lines may appear flat
   ✓ Set Y-axis to fixed range (20-70) for better visibility
   ✓ Event annotations (2004, 2010, 2011, 2020) will add context

📋 SHEET 4 (Governance):
   ✓ Strong correlation visible (R² = {:.2f})
   ✓ Income group coloring shows wealth isn't deterministic
   ✓ Trend line will tell the story effectively
""".format(
    dii_median,
    regional_pivot.min().min(),
    regional_pivot.max().max(),
    correlations["CRI vs WGI (Governance)"]**2
))

plt.show()
