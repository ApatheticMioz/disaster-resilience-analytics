"""
Data Quality Diagnostics and Validation Report
===============================================
Generates:
1. coverage_matrix.csv - Variable-level coverage statistics
2. validation_report.txt - Detailed validation report
3. Prints DesInventar country mapping issues
4. Analyzes Gini coverage for interpolation decision
"""

import pandas as pd
import numpy as np
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict
from datetime import datetime

DATA_DIR = Path("Data")
OUTPUT_DIR = DATA_DIR

print("=" * 70)
print("DATA QUALITY DIAGNOSTICS")
print("=" * 70)

# ============================================================================
# 1. DESINVENTAR COUNTRY MAPPING ANALYSIS
# ============================================================================
print("\n" + "=" * 70)
print("1. DESINVENTAR COUNTRY MAPPING ANALYSIS")
print("=" * 70)

desinventar_dir = DATA_DIR / "desinventarSandai"
zip_files = list(desinventar_dir.glob("*.zip"))

# Extract unique level0 values
level0_values = defaultdict(set)
country_codes_from_filename = {}

for zip_file in zip_files:
    filename_parts = zip_file.stem.split('_')
    country_code = filename_parts[-1].upper()
    country_codes_from_filename[zip_file.name] = country_code
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as z:
            xml_files = [n for n in z.namelist() if n.endswith('.xml')]
            for xml_file in xml_files:
                with z.open(xml_file) as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    
                    # Get level0 values from lev0 section (country/region names)
                    lev0 = root.find('lev0')
                    if lev0 is not None:
                        for tr in lev0.findall('TR'):
                            nombre = tr.find('nombre')
                            if nombre is not None and nombre.text:
                                level0_values[country_code].add(nombre.text)
    except:
        continue

print("\nDesInventar ZIP files and extracted country codes:")
print("-" * 50)

# Known problematic codes
problematic_codes = []
import pycountry
valid_iso3 = set(c.alpha_3 for c in pycountry.countries)

for filename, code in sorted(country_codes_from_filename.items()):
    if code not in valid_iso3:
        problematic_codes.append((filename, code, list(level0_values.get(code, ['Unknown']))[:3]))
        
print(f"\nTotal ZIP files: {len(zip_files)}")
print(f"Problematic codes (not standard ISO3): {len(problematic_codes)}")
print("\nFiles with non-standard codes:")
for filename, code, names in problematic_codes:
    print(f"  {filename}")
    print(f"    Code: {code}")
    print(f"    Regions: {names}")

# Suggested mapping
suggested_mapping = {
    'AR2': ('ARM', 'Armenia'),
    'NG_OY': ('NGA', 'Nigeria - Oyo State'),
    'LAO2': ('LAO', 'Laos'),
    'PAC': ('PCN', 'Pacific Islands (aggregate)'),
    'XKX': ('XKX', 'Kosovo (non-standard but commonly used)'),
}

print("\nSuggested manual mappings:")
for code, (iso3, desc) in suggested_mapping.items():
    print(f"  {code} -> {iso3} ({desc})")

# ============================================================================
# 2. LOAD UNIFIED DATASET AND GENERATE COVERAGE MATRIX
# ============================================================================
print("\n" + "=" * 70)
print("2. COVERAGE MATRIX GENERATION")
print("=" * 70)

unified_file = DATA_DIR / "unified_resilience_dataset.csv"
if unified_file.exists():
    df = pd.read_csv(unified_file)
    print(f"\nLoaded unified dataset: {df.shape}")
else:
    print("ERROR: unified_resilience_dataset.csv not found. Running main script first...")
    import subprocess
    subprocess.run(['D:/Work/Semester5/DAV/Project/.venv/Scripts/python.exe', 
                   'D:/Work/Semester5/DAV/Project/build_unified_dataset.py'])
    df = pd.read_csv(unified_file)

# Generate coverage matrix
coverage_data = []
for col in df.columns:
    if col in ['iso3', 'year']:
        continue
    
    non_null = df[col].notna().sum()
    total = len(df)
    
    # Get year range for non-null values
    non_null_df = df[df[col].notna()]
    if len(non_null_df) > 0:
        year_min = non_null_df['year'].min()
        year_max = non_null_df['year'].max()
        countries_covered = non_null_df['iso3'].nunique()
    else:
        year_min = year_max = np.nan
        countries_covered = 0
    
    coverage_data.append({
        'variable': col,
        'total_obs': total,
        'non_null_obs': non_null,
        'coverage_pct': round(non_null / total * 100, 2),
        'countries_covered': countries_covered,
        'year_min': year_min,
        'year_max': year_max
    })

coverage_df = pd.DataFrame(coverage_data)
coverage_df = coverage_df.sort_values('coverage_pct', ascending=False)

# Save coverage matrix
coverage_file = OUTPUT_DIR / "coverage_matrix.csv"
coverage_df.to_csv(coverage_file, index=False)
print(f"\nSaved coverage matrix to: {coverage_file}")

print("\nCoverage Summary:")
print(coverage_df.to_string(index=False))

# ============================================================================
# 3. GINI INDEX ANALYSIS
# ============================================================================
print("\n" + "=" * 70)
print("3. GINI INDEX COVERAGE ANALYSIS")
print("=" * 70)

if 'gini_index' in df.columns:
    gini_coverage = df['gini_index'].notna().sum() / len(df) * 100
    gini_countries = df[df['gini_index'].notna()]['iso3'].nunique()
    gini_years = df[df['gini_index'].notna()]['year'].value_counts().sort_index()
    
    print(f"\nGini Index Coverage: {gini_coverage:.1f}%")
    print(f"Countries with Gini data: {gini_countries}")
    print(f"\nGini observations by year:")
    print(gini_years.to_string())
    
    # Analyze sparsity per country
    gini_per_country = df.groupby('iso3')['gini_index'].apply(lambda x: x.notna().sum())
    countries_with_gini = (gini_per_country > 0).sum()
    avg_years_per_country = gini_per_country[gini_per_country > 0].mean()
    
    print(f"\n{countries_with_gini} countries have at least one Gini observation")
    print(f"Average Gini observations per country: {avg_years_per_country:.1f} years")
    
    # Recommendation
    print("\n" + "-" * 50)
    print("GINI INTERPOLATION RECOMMENDATION:")
    print("-" * 50)
    if gini_coverage < 20:
        print("Coverage is LOW (<20%). Options:")
        print("  1. INTERPOLATE within countries (forward-fill + backward-fill)")
        print("     - Pros: Preserves country-level variation")
        print("     - Cons: May mask actual changes")
        print("  2. DROP the variable entirely")
        print("     - Pros: Cleaner dataset, no artificial data")
        print("     - Cons: Lose inequality information")
        print("  3. KEEP AS-IS for analyses that can handle missing data")
        print("\n  RECOMMENDED: Option 1 (Interpolate) if inequality is critical")
        print("               Option 3 (Keep as-is) if using models that handle NaN")
    else:
        print(f"Coverage is acceptable ({gini_coverage:.1f}%). Keep as-is or interpolate.")

# ============================================================================
# 4. VALIDATION REPORT
# ============================================================================
print("\n" + "=" * 70)
print("4. GENERATING VALIDATION REPORT")
print("=" * 70)

report_lines = []
report_lines.append("=" * 70)
report_lines.append("UNIFIED RESILIENCE DATASET - VALIDATION REPORT")
report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append("=" * 70)

# 4a. Dataset overview
report_lines.append("\n\n1. DATASET OVERVIEW")
report_lines.append("-" * 50)
report_lines.append(f"Total rows: {len(df)}")
report_lines.append(f"Total columns: {len(df.columns)}")
report_lines.append(f"Countries: {df['iso3'].nunique()}")
report_lines.append(f"Year range: {df['year'].min()} - {df['year'].max()}")

# 4b. Source row counts (before/after merge)
report_lines.append("\n\n2. SOURCE DATA ROW COUNTS")
report_lines.append("-" * 50)
report_lines.append("Note: 'Before merge' counts are from individual source processing")
report_lines.append("      'After merge' counts show how many rows have data for each source")

source_indicators = {
    'ND-GAIN': ['ndgain_score', 'ndgain_readiness', 'ndgain_vulnerability'],
    'Nighttime Lights': ['ntl_radiance'],
    'GDACS': ['disaster_count', 'disaster_deaths'],
    'IMF WEO': ['gdp_growth_imf', 'gdp_per_capita_imf', 'inflation_rate'],
    'World Bank WDI': ['gdp_growth', 'gdp_per_capita', 'gini_index', 'population'],
    'HDR': ['hdi'],
    'WGI': ['wgi_voice_accountability', 'wgi_rule_of_law', 'wgi_gov_effectiveness'],
    'INFORM Risk': ['inform_risk', 'inform_hazard', 'inform_vulnerability'],
    'FTS': ['humanitarian_funding_usd'],
    'DesInventar': ['desinventar_events', 'desinventar_deaths'],
}

for source, indicators in source_indicators.items():
    available_indicators = [i for i in indicators if i in df.columns]
    if available_indicators:
        # Count rows where at least one indicator is non-null
        mask = df[available_indicators].notna().any(axis=1)
        rows_with_data = mask.sum()
        countries_with_data = df[mask]['iso3'].nunique()
        report_lines.append(f"\n{source}:")
        report_lines.append(f"  Rows with data: {rows_with_data}")
        report_lines.append(f"  Countries with data: {countries_with_data}")
    else:
        report_lines.append(f"\n{source}: No indicators found in final dataset")

# 4c. Countries in sources but missing from final
report_lines.append("\n\n3. COUNTRY COVERAGE BY SOURCE")
report_lines.append("-" * 50)

final_countries = set(df['iso3'].unique())
report_lines.append(f"Countries in final dataset: {len(final_countries)}")

# 4d. Years with <50% coverage for critical variables
report_lines.append("\n\n4. YEARS WITH LOW COVERAGE (<50%)")
report_lines.append("-" * 50)

critical_vars = ['ndgain_score', 'gdp_per_capita', 'hdi', 'inform_risk', 'disaster_count']
critical_vars = [v for v in critical_vars if v in df.columns]

for var in critical_vars:
    yearly_coverage = df.groupby('year')[var].apply(lambda x: x.notna().sum() / len(x) * 100)
    low_coverage_years = yearly_coverage[yearly_coverage < 50]
    
    report_lines.append(f"\n{var}:")
    if len(low_coverage_years) > 0:
        report_lines.append(f"  Years with <50% coverage: {list(low_coverage_years.index)}")
        report_lines.append(f"  Coverage in those years: {[f'{y:.0f}%' for y in low_coverage_years.values]}")
    else:
        report_lines.append(f"  All years have >=50% coverage")

# 4e. Missing value summary
report_lines.append("\n\n5. MISSING VALUE SUMMARY")
report_lines.append("-" * 50)
missing_pct = (df.isnull().sum() / len(df) * 100).sort_values(ascending=False)
report_lines.append("\nVariables by missing %:")
for var, pct in missing_pct.items():
    if var not in ['iso3', 'year']:
        report_lines.append(f"  {var}: {pct:.1f}% missing")

# 4f. Data quality flags
report_lines.append("\n\n6. DATA QUALITY FLAGS")
report_lines.append("-" * 50)

# Check for duplicate (iso3, year) combinations
duplicates = df.duplicated(subset=['iso3', 'year'], keep=False)
dup_count = df.duplicated(subset=['iso3', 'year'], keep='first').sum()
if dup_count > 0:
    report_lines.append(f"WARNING: {dup_count} duplicate (iso3, year) rows found")
else:
    report_lines.append("OK: No duplicate (iso3, year) combinations")

# Check for invalid ISO3 codes
invalid_iso3 = df[~df['iso3'].isin(valid_iso3)]['iso3'].unique()
if len(invalid_iso3) > 0:
    report_lines.append(f"NOTE: {len(invalid_iso3)} non-standard ISO3 codes (may be territories/regions):")
    report_lines.append(f"      {list(invalid_iso3)}")
else:
    report_lines.append("OK: All ISO3 codes are standard")

# Check year coverage
expected_years = set(range(2000, 2024))
actual_years = set(df['year'].unique())
missing_years = expected_years - actual_years
if missing_years:
    report_lines.append(f"WARNING: Missing years in dataset: {sorted(missing_years)}")
else:
    report_lines.append("OK: All expected years (2000-2023) present")

# Save validation report
report_file = OUTPUT_DIR / "validation_report.txt"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))

print(f"\nSaved validation report to: {report_file}")

# Print report to console
print("\n" + "\n".join(report_lines))

print("\n" + "=" * 70)
print("DIAGNOSTICS COMPLETE")
print("=" * 70)
