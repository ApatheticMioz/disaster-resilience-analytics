"""
Global Disaster Resilience Analytics Platform - Data Processing Pipeline
=========================================================================
Comprehensive ETL pipeline for disaster resilience analysis.
Integrates 12+ datasets into unified country-year format (2000-2024).
Calculates derived indices: DII (Disaster Impact Index), RRS (Resilience 
Recovery Score), and CRI (Composite Resilience Index).

Primary Key: (iso3, year)
Output: unified_resilience_dataset.csv

Data Sources:
1. ND-GAIN (Climate Resilience Index) - Spine dataset
2. Harmonized Nighttime Lights (Economic proxy)
3. GDACS (Global Disaster Alerts)
4. EM-DAT (Primary disaster impact - deaths, affected, damages)
5. IMF WEO (Macroeconomic indicators)
6. World Bank WDI (Development indicators)
7. HDR (Human Development Index)
8. WGI (Governance Indicators)
9. INFORM Risk Index (Hazard, Vulnerability, Coping Capacity)
10. FTS (Humanitarian Funding)
11. DesInventar (Granular disaster losses)
12. Barro-Lee (Educational Attainment)
13. WID/Gini (Inequality data)

Author: Data Analytics Team
Version: 2.0
"""

import pandas as pd
import numpy as np
import os
import re
import glob
import zipfile
import warnings
from pathlib import Path
from datetime import datetime

warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Base paths
DATA_DIR = Path("Data")
OUTPUT_FILE = DATA_DIR / "unified_resilience_dataset.csv"
COVERAGE_FILE = DATA_DIR / "coverage_matrix.csv"
VALIDATION_FILE = DATA_DIR / "validation_report.txt"

# Target year range
YEAR_START = 2000
YEAR_END = 2024

# Index calculation parameters
DII_AFFECTED_WEIGHT = 4  # Weight for affected population in DII formula
RECOVERY_WINDOW = 3      # Years to consider for recovery calculation

print("=" * 80)
print("GLOBAL DISASTER RESILIENCE ANALYTICS - DATA PROCESSING PIPELINE v2.0")
print(f"Processing years: {YEAR_START}-{YEAR_END}")
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def standardize_iso3(df, iso_col='iso3'):
    """Standardize ISO3 codes: uppercase, strip whitespace, handle blanks"""
    df = df.copy()
    df[iso_col] = df[iso_col].astype(str).str.strip().str.upper()
    # Replace invalid codes
    invalid_values = ['', 'NAN', 'NONE', '-1', '   ', 'NA', 'NULL', '...']
    df.loc[df[iso_col].isin(invalid_values), iso_col] = np.nan
    return df

def country_name_to_iso3(country_name):
    """Convert country name to ISO3 code using pycountry with extensive mappings"""
    try:
        import pycountry
    except ImportError:
        return None
        
    if pd.isna(country_name) or not country_name:
        return None
    
    # Manual mappings for common variations
    manual_mappings = {
        'BOLIVIA': 'BOL', 'BOLIVIA (PLURINATIONAL STATE OF)': 'BOL',
        'VENEZUELA': 'VEN', 'VENEZUELA (BOLIVARIAN REPUBLIC OF)': 'VEN',
        'IRAN': 'IRN', 'IRAN (ISLAMIC REPUBLIC OF)': 'IRN',
        'TANZANIA': 'TZA', 'UNITED REPUBLIC OF TANZANIA': 'TZA',
        'RUSSIA': 'RUS', 'RUSSIAN FEDERATION': 'RUS',
        'KOREA, REPUBLIC OF': 'KOR', 'SOUTH KOREA': 'KOR',
        'KOREA, DEM. PEOPLE\'S REP.': 'PRK', 'NORTH KOREA': 'PRK',
        'CÔTE D\'IVOIRE': 'CIV', 'IVORY COAST': 'CIV',
        'DEMOCRATIC REPUBLIC OF THE CONGO': 'COD', 'DR CONGO': 'COD', 'DRC': 'COD',
        'REPUBLIC OF THE CONGO': 'COG', 'CONGO': 'COG',
        'UNITED STATES': 'USA', 'UNITED STATES OF AMERICA': 'USA',
        'UNITED KINGDOM': 'GBR', 'UK': 'GBR',
        'VIET NAM': 'VNM', 'VIETNAM': 'VNM',
        'LAO PDR': 'LAO', 'LAOS': 'LAO',
        'SYRIA': 'SYR', 'SYRIAN ARAB REPUBLIC': 'SYR',
        'CZECHIA': 'CZE', 'CZECH REPUBLIC': 'CZE',
        'SLOVAKIA': 'SVK', 'SLOVAK REPUBLIC': 'SVK',
        'MOLDOVA': 'MDA', 'REPUBLIC OF MOLDOVA': 'MDA',
        'HONG KONG': 'HKG', 'HONG KONG SAR': 'HKG',
        'MACAU': 'MAC', 'MACAO': 'MAC',
        'TAIWAN': 'TWN', 'CHINESE TAIPEI': 'TWN',
        'PALESTINE': 'PSE', 'WEST BANK AND GAZA': 'PSE',
        'ESWATINI': 'SWZ', 'SWAZILAND': 'SWZ',
        'MYANMAR': 'MMR', 'BURMA': 'MMR',
        'CABO VERDE': 'CPV', 'CAPE VERDE': 'CPV',
        'TÜRKIYE': 'TUR', 'TURKEY': 'TUR',
    }
    
    name_upper = str(country_name).strip().upper()
    if name_upper in manual_mappings:
        return manual_mappings[name_upper]
    
    try:
        # Try exact match first
        country = pycountry.countries.get(name=country_name)
        if country:
            return country.alpha_3
        # Try fuzzy search
        results = pycountry.countries.search_fuzzy(country_name)
        if results:
            return results[0].alpha_3
    except:
        pass
    return None

def melt_wide_to_long(df, id_col, year_cols, value_name):
    """Melt wide format (years as columns) to long format"""
    df_long = df.melt(
        id_vars=[id_col],
        value_vars=year_cols,
        var_name='year',
        value_name=value_name
    )
    df_long['year'] = pd.to_numeric(df_long['year'], errors='coerce').astype('Int64')
    return df_long

def safe_divide(numerator, denominator, fill_value=np.nan):
    """Safely divide, returning fill_value when denominator is 0 or NaN"""
    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.where(
            (denominator == 0) | pd.isna(denominator),
            fill_value,
            numerator / denominator
        )
    return result

def normalize_0_1(series, invert=False):
    """Normalize a series to 0-1 range, optionally inverting"""
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(0.5, index=series.index)
    normalized = (series - min_val) / (max_val - min_val)
    if invert:
        normalized = 1 - normalized
    return normalized

def interpolate_within_country(df, value_col, group_col='iso3'):
    """Interpolate missing values within each country group"""
    return df.groupby(group_col)[value_col].transform(
        lambda x: x.interpolate(method='linear', limit_direction='both')
    )

# ============================================================================
# 1. PROCESS ND-GAIN DATASETS (SPINE)
# ============================================================================
print("\n" + "=" * 80)
print("[1/13] Processing ND-GAIN datasets (Climate Resilience Index)...")
print("=" * 80)

ndgain_dir = DATA_DIR / "NDGain"
year_cols = [str(y) for y in range(YEAR_START, YEAR_END + 1)]

try:
    gain_df = pd.read_csv(ndgain_dir / "gain" / "gain.csv")
    readiness_df = pd.read_csv(ndgain_dir / "readiness" / "readiness.csv")
    vulnerability_df = pd.read_csv(ndgain_dir / "vulnerability" / "vulnerability.csv")
    
    # Filter year columns that exist
    gain_years = [y for y in year_cols if y in gain_df.columns]
    
    # Melt to long format
    gain_long = melt_wide_to_long(gain_df, 'ISO3', gain_years, 'ndgain_score')
    readiness_long = melt_wide_to_long(readiness_df, 'ISO3', gain_years, 'ndgain_readiness')
    vulnerability_long = melt_wide_to_long(vulnerability_df, 'ISO3', gain_years, 'ndgain_vulnerability')
    
    # Merge ND-GAIN components
    ndgain_final = gain_long.merge(readiness_long, on=['ISO3', 'year'], how='outer')
    ndgain_final = ndgain_final.merge(vulnerability_long, on=['ISO3', 'year'], how='outer')
    ndgain_final = ndgain_final.rename(columns={'ISO3': 'iso3'})
    ndgain_final = standardize_iso3(ndgain_final)
    
    # Also load ND-GAIN sub-indicators if available
    indicators_dir = ndgain_dir / "indicators"
    if indicators_dir.exists():
        # Load food, water, health, infrastructure indicators
        for indicator_name in ['food', 'water', 'health', 'infrastructure']:
            indicator_file = indicators_dir / f"{indicator_name}.csv"
            if indicator_file.exists():
                ind_df = pd.read_csv(indicator_file)
                ind_years = [y for y in year_cols if y in ind_df.columns]
                if ind_years:
                    ind_long = melt_wide_to_long(ind_df, 'ISO3', ind_years, f'ndgain_{indicator_name}')
                    ind_long = ind_long.rename(columns={'ISO3': 'iso3'})
                    ind_long = standardize_iso3(ind_long)
                    ndgain_final = ndgain_final.merge(ind_long, on=['iso3', 'year'], how='left')
    
    print(f"   ✓ ND-GAIN: {len(ndgain_final)} rows, {ndgain_final['iso3'].nunique()} countries")
    print(f"   Year range: {ndgain_final['year'].min()} - {ndgain_final['year'].max()}")
except Exception as e:
    print(f"   ✗ ERROR processing ND-GAIN: {e}")
    ndgain_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 2. PROCESS HARMONIZED NIGHTTIME LIGHTS
# ============================================================================
print("\n" + "-" * 80)
print("[2/13] Processing Harmonized Nighttime Lights (Economic Activity Proxy)...")

ntl_dir = DATA_DIR / "HarmonizedNTL"

try:
    # Load DMSP (annual, 1992-2013)
    dmsp_df = pd.read_csv(ntl_dir / "DMSP-OLS-nighttime-lights-1992to2013-level0.csv")
    dmsp_df = dmsp_df.rename(columns={'iso': 'iso3', 'nlsum': 'ntl_radiance'})
    dmsp_df = dmsp_df[(dmsp_df['year'] >= YEAR_START) & (dmsp_df['year'] <= 2012)]
    
    # Load VIIRS (monthly, 2013-2024)
    viirs_df = pd.read_csv(ntl_dir / "VIIRS-nighttime-lights-2013m1to2024m5-level0.csv")
    viirs_df = viirs_df.rename(columns={'iso': 'iso3', 'nlsum': 'ntl_radiance'})
    
    # Aggregate VIIRS monthly to annual (mean)
    viirs_annual = viirs_df.groupby(['iso3', 'year'])['ntl_radiance'].mean().reset_index()
    viirs_annual = viirs_annual[viirs_annual['year'] <= YEAR_END]
    
    # Combine: Use DMSP for <2013, VIIRS for >=2013
    ntl_final = pd.concat([dmsp_df[['iso3', 'year', 'ntl_radiance']], 
                           viirs_annual], ignore_index=True)
    ntl_final = standardize_iso3(ntl_final)
    
    # Calculate year-over-year NTL growth (economic recovery proxy)
    ntl_final = ntl_final.sort_values(['iso3', 'year'])
    ntl_final['ntl_growth'] = ntl_final.groupby('iso3')['ntl_radiance'].pct_change() * 100
    
    print(f"   ✓ NTL: {len(ntl_final)} rows, {ntl_final['iso3'].nunique()} countries")
    print(f"   DMSP years: 2000-2012, VIIRS years: 2013-{YEAR_END}")
except Exception as e:
    print(f"   ✗ ERROR processing NTL: {e}")
    ntl_final = pd.DataFrame(columns=['iso3', 'year', 'ntl_radiance'])

# ============================================================================
# 3. PROCESS EM-DAT (PRIMARY DISASTER IMPACT DATA)
# ============================================================================
print("\n" + "-" * 80)
print("[3/13] Processing EM-DAT International Disaster Database (Primary Source)...")

emdat_dir = DATA_DIR / "emdat"

try:
    # Find EM-DAT Excel file
    emdat_files = list(emdat_dir.glob("*.xlsx")) + list(emdat_dir.glob("*.xls"))
    
    if emdat_files:
        emdat_file = emdat_files[0]
        print(f"   Loading: {emdat_file.name}")
        
        # Read EM-DAT Excel file
        emdat_df = pd.read_excel(emdat_file, sheet_name=0)
        
        # Standardize column names (EM-DAT uses various formats)
        emdat_df.columns = emdat_df.columns.str.strip()
        
        # Find specific columns - EM-DAT format: ISO, Start Year, Total Deaths, Total Affected, Total Damage Adjusted
        col_mapping = {}
        
        # Map ISO column
        iso_col = next((c for c in emdat_df.columns if c.upper() == 'ISO'), None)
        if iso_col:
            col_mapping[iso_col] = 'iso3'
        
        # Map Year column (prefer Start Year)
        year_col = next((c for c in emdat_df.columns if 'start year' in c.lower()), None)
        if year_col:
            col_mapping[year_col] = 'year'
        
        # Map Total Deaths
        deaths_col = next((c for c in emdat_df.columns if c.lower() == 'total deaths'), None)
        if deaths_col:
            col_mapping[deaths_col] = 'emdat_deaths'
        
        # Map Total Affected  
        affected_col = next((c for c in emdat_df.columns if c.lower() == 'total affected'), None)
        if affected_col:
            col_mapping[affected_col] = 'emdat_affected'
        
        # Map Total Damage Adjusted (prefer adjusted over raw)
        damage_col = next((c for c in emdat_df.columns if 'total damage' in c.lower() and 'adjusted' in c.lower()), None)
        if not damage_col:
            damage_col = next((c for c in emdat_df.columns if 'total damage' in c.lower()), None)
        if damage_col:
            col_mapping[damage_col] = 'emdat_damage_usd'
        
        # Map Disaster Type
        dtype_col = next((c for c in emdat_df.columns if c.lower() == 'disaster type'), None)
        if dtype_col:
            col_mapping[dtype_col] = 'disaster_type'
        
        emdat_df = emdat_df.rename(columns=col_mapping)
        
        if 'iso3' in emdat_df.columns and 'year' in emdat_df.columns:
            # Convert year to numeric
            emdat_df['year'] = pd.to_numeric(emdat_df['year'], errors='coerce')
            
            # Filter to target year range
            emdat_df = emdat_df[(emdat_df['year'] >= YEAR_START) & (emdat_df['year'] <= YEAR_END)]
            
            # Select only the columns we need and ensure no duplicates
            keep_cols = ['iso3', 'year']
            numeric_cols = ['emdat_deaths', 'emdat_affected', 'emdat_damage_usd']
            for col in numeric_cols:
                if col in emdat_df.columns:
                    keep_cols.append(col)
            
            # Keep only needed columns (first instance of each)
            emdat_df = emdat_df.loc[:, ~emdat_df.columns.duplicated()]
            emdat_df = emdat_df[[c for c in keep_cols if c in emdat_df.columns]]
            
            # Ensure numeric columns
            for col in numeric_cols:
                if col in emdat_df.columns:
                    emdat_df[col] = pd.to_numeric(emdat_df[col], errors='coerce').fillna(0)
            
            # Count events by country-year
            event_counts = emdat_df.groupby(['iso3', 'year']).size().reset_index(name='emdat_event_count')
            
            # Aggregate numeric columns by country-year
            agg_cols = [c for c in numeric_cols if c in emdat_df.columns]
            if agg_cols:
                agg_dict = {col: 'sum' for col in agg_cols}
                emdat_agg = emdat_df.groupby(['iso3', 'year'], as_index=False)[agg_cols].sum()
                emdat_agg = emdat_agg.merge(event_counts, on=['iso3', 'year'], how='left')
            else:
                emdat_agg = event_counts
            
            emdat_final = standardize_iso3(emdat_agg)
            emdat_final = emdat_final.dropna(subset=['iso3'])
            
            print(f"   ✓ EM-DAT: {len(emdat_final)} country-years, {emdat_final['iso3'].nunique()} countries")
            if 'emdat_deaths' in emdat_final.columns:
                print(f"   Total deaths recorded: {emdat_final['emdat_deaths'].sum():,.0f}")
            if 'emdat_affected' in emdat_final.columns:
                print(f"   Total affected recorded: {emdat_final['emdat_affected'].sum():,.0f}")
        else:
            print("   ✗ Could not find ISO3 or year columns in EM-DAT")
            emdat_final = pd.DataFrame(columns=['iso3', 'year'])
    else:
        print("   ✗ No EM-DAT Excel files found")
        emdat_final = pd.DataFrame(columns=['iso3', 'year'])
        
except Exception as e:
    print(f"   ✗ ERROR processing EM-DAT: {e}")
    import traceback
    traceback.print_exc()
    emdat_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 4. PROCESS GDACS DISASTER DATA (SECONDARY - SEVERITY SCORES)
# ============================================================================
print("\n" + "-" * 80)
print("[4/13] Processing GDACS Global Disaster Alerts (Severity Scores)...")

gdacs_dir = DATA_DIR / "GDACS" / "Clean"

try:
    gdacs_files = {
        'Earthquake': 'Earthquake_clean.csv',
        'Flood': 'Flood_clean.csv',
        'Drought': 'Drought_clean.csv',
        'Forest_Fire': 'Forest_Fires_clean.csv',
        'Tropical_Cyclone': 'Tropical_Cyclone_clean.csv',
        'Eruption': 'Eruption_clean.csv'
    }
    
    all_disasters = []
    
    for disaster_type, filename in gdacs_files.items():
        filepath = gdacs_dir / filename
        if filepath.exists():
            df = pd.read_csv(filepath)
            
            # Standardize column names (handle case variations)
            df.columns = df.columns.str.lower().str.strip()
            
            # Extract year from fromdate
            if 'fromdate' in df.columns:
                df['year'] = pd.to_datetime(df['fromdate'], errors='coerce').dt.year
            
            # Get ISO3 column
            iso_col = 'iso3' if 'iso3' in df.columns else None
            if iso_col:
                df = df.rename(columns={iso_col: 'iso3'})
            
            df['disaster_type'] = disaster_type
            
            # Select relevant columns
            cols_to_keep = ['iso3', 'year', 'disaster_type', 'alertlevel', 'alertscore']
            
            # Add deaths/displaced/affected if available
            for col in ['death', 'deaths', 'displaced', 'people affected', 'affected', 
                        'exposed population', 'severity', 'magnitude']:
                if col in df.columns:
                    cols_to_keep.append(col)
            
            available_cols = [c for c in cols_to_keep if c in df.columns]
            all_disasters.append(df[available_cols])
    
    # Combine all disaster types
    if all_disasters:
        gdacs_combined = pd.concat(all_disasters, ignore_index=True)
        gdacs_combined = standardize_iso3(gdacs_combined)
        
        # Filter year range
        gdacs_combined = gdacs_combined[(gdacs_combined['year'] >= YEAR_START) & 
                                         (gdacs_combined['year'] <= YEAR_END)]
        
        # Create severity weight from alert level
        alert_weights = {'GREEN': 1, 'ORANGE': 2, 'RED': 3}
        gdacs_combined['severity_weight'] = gdacs_combined['alertlevel'].str.upper().map(alert_weights).fillna(1)
        
        # Count by alert level
        gdacs_combined['is_red_alert'] = (gdacs_combined['alertlevel'].str.upper() == 'RED').astype(int)
        gdacs_combined['is_orange_alert'] = (gdacs_combined['alertlevel'].str.upper() == 'ORANGE').astype(int)
        
        # Aggregate by country-year
        gdacs_agg = gdacs_combined.groupby(['iso3', 'year']).agg({
            'disaster_type': 'count',        # Total disaster events
            'is_red_alert': 'sum',           # Red alert count
            'is_orange_alert': 'sum',        # Orange alert count
            'alertscore': 'mean',            # Average severity
            'severity_weight': 'mean'        # Average severity weight (1-3 scale)
        }).reset_index()
        
        gdacs_agg = gdacs_agg.rename(columns={
            'disaster_type': 'gdacs_disaster_count',
            'is_red_alert': 'gdacs_red_alerts',
            'is_orange_alert': 'gdacs_orange_alerts',
            'alertscore': 'gdacs_avg_alert_score',
            'severity_weight': 'gdacs_severity_weight'
        })
        
        # Get disaster type breakdown
        type_counts = gdacs_combined.groupby(['iso3', 'year', 'disaster_type']).size().unstack(fill_value=0)
        type_counts = type_counts.add_prefix('gdacs_').add_suffix('_count').reset_index()
        type_counts.columns = type_counts.columns.str.lower().str.replace(' ', '_')
        
        gdacs_agg = gdacs_agg.merge(type_counts, on=['iso3', 'year'], how='left')
        
        gdacs_final = gdacs_agg.dropna(subset=['iso3'])
        print(f"   ✓ GDACS: {len(gdacs_final)} country-years, {gdacs_final['iso3'].nunique()} countries")
        print(f"   Disaster types: {list(gdacs_files.keys())}")
    else:
        gdacs_final = pd.DataFrame(columns=['iso3', 'year'])
        print("   ✗ No GDACS files processed")
        
except Exception as e:
    print(f"   ✗ ERROR processing GDACS: {e}")
    import traceback
    traceback.print_exc()
    gdacs_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 5. PROCESS IMF WEO DATA
# ============================================================================
print("\n" + "-" * 80)
print("[5/13] Processing IMF World Economic Outlook...")

weo_dir = DATA_DIR / "IMFWEO"

try:
    # Find the WEO CSV file
    weo_files = list(weo_dir.glob("*.csv"))
    if weo_files:
        weo_df = pd.read_csv(weo_files[0])
        
        # Extract ISO3 from SERIES_CODE (first 3 characters)
        weo_df['iso3'] = weo_df['SERIES_CODE'].str[:3]
        
        # Extract indicator code (between first and second dot)
        weo_df['indicator'] = weo_df['SERIES_CODE'].str.split('.').str[1]
        
        # Target indicators
        target_indicators = {
            'NGDP_RPCH': 'gdp_growth_imf',        # Real GDP growth (%)
            'NGDPDPC': 'gdp_per_capita_imf',     # GDP per capita (current prices USD)
            'PCPIPCH': 'inflation_rate',          # Inflation rate (%)
            'LUR': 'unemployment_rate',           # Unemployment rate (%)
            'LP': 'population_imf',               # Population (millions)
            'GGR_NGDP': 'govt_revenue_pct_gdp',   # Government revenue (% of GDP)
            'GGXWDG_NGDP': 'govt_debt_pct_gdp',   # Government debt (% of GDP)
        }
        
        # Filter for target indicators
        weo_filtered = weo_df[weo_df['indicator'].isin(target_indicators.keys())].copy()
        
        # Get year columns
        year_cols_weo = [str(y) for y in range(YEAR_START, YEAR_END + 1)]
        available_year_cols = [c for c in year_cols_weo if c in weo_filtered.columns]
        
        # Melt to long format
        weo_long = weo_filtered.melt(
            id_vars=['iso3', 'indicator'],
            value_vars=available_year_cols,
            var_name='year',
            value_name='value'
        )
        
        # Clean values (handle empty strings and special characters)
        weo_long['value'] = pd.to_numeric(weo_long['value'], errors='coerce')
        weo_long['year'] = weo_long['year'].astype(int)
        
        # Pivot to wide format
        weo_pivot = weo_long.pivot_table(
            index=['iso3', 'year'],
            columns='indicator',
            values='value'
        ).reset_index()
        
        # Rename columns
        weo_pivot.columns.name = None
        weo_pivot = weo_pivot.rename(columns=target_indicators)
        
        weo_final = standardize_iso3(weo_pivot)
        print(f"   ✓ IMF WEO: {len(weo_final)} rows, {weo_final['iso3'].nunique()} countries")
        print(f"   Indicators: {list(target_indicators.values())}")
    else:
        weo_final = pd.DataFrame(columns=['iso3', 'year'])
        print("   ✗ IMF WEO: No files found")
        
except Exception as e:
    print(f"   ✗ ERROR processing IMF WEO: {e}")
    import traceback
    traceback.print_exc()
    weo_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 6. PROCESS WORLD BANK WDI
# ============================================================================
print("\n" + "-" * 80)
print("[6/13] Processing World Bank WDI (large file, using chunks)...")

wdi_dir = DATA_DIR / "worldBankWDI"
wdi_file = wdi_dir / "WDICSV.csv"

try:
    # Target indicators - comprehensive selection
    target_wdi_indicators = [
        'NY.GDP.MKTP.KD.ZG',    # GDP growth (annual %)
        'NY.GDP.PCAP.KD',       # GDP per capita (constant 2015 US$)
        'NY.GDP.PCAP.PP.KD',    # GDP per capita, PPP (constant 2017 int'l $)
        'SI.POV.GINI',          # Gini Index
        'SI.POV.DDAY',          # Poverty headcount ratio at $2.15/day
        'SH.MED.BEDS.ZS',       # Hospital beds per 1,000
        'SH.MED.PHYS.ZS',       # Physicians per 1,000
        'IT.NET.USER.ZS',       # Internet users (% of population)
        'SE.ADT.LITR.ZS',       # Adult literacy rate
        'SE.SEC.ENRR',          # Secondary school enrollment (gross %)
        'SP.POP.TOTL',          # Total population
        'SP.URB.TOTL.IN.ZS',    # Urban population (%)
        'SH.XPD.CHEX.GD.ZS',    # Health expenditure (% of GDP)
        'EG.ELC.ACCS.ZS',       # Access to electricity (%)
        'SH.STA.BASS.ZS',       # Basic sanitation services (%)
        'SH.H2O.BASW.ZS',       # Basic drinking water services (%)
        'AG.LND.FRST.ZS',       # Forest area (%)
        'EN.ATM.CO2E.PC',       # CO2 emissions per capita
        'IC.BUS.EASE.XQ',       # Ease of doing business score
        'FP.CPI.TOTL.ZG',       # Inflation, consumer prices (annual %)
    ]
    
    indicator_names = {
        'NY.GDP.MKTP.KD.ZG': 'gdp_growth',
        'NY.GDP.PCAP.KD': 'gdp_per_capita',
        'NY.GDP.PCAP.PP.KD': 'gdp_per_capita_ppp',
        'SI.POV.GINI': 'gini_index',
        'SI.POV.DDAY': 'poverty_rate',
        'SH.MED.BEDS.ZS': 'hospital_beds_per_1k',
        'SH.MED.PHYS.ZS': 'physicians_per_1k',
        'IT.NET.USER.ZS': 'internet_users_pct',
        'SE.ADT.LITR.ZS': 'literacy_rate',
        'SE.SEC.ENRR': 'secondary_enrollment',
        'SP.POP.TOTL': 'population',
        'SP.URB.TOTL.IN.ZS': 'urban_population_pct',
        'SH.XPD.CHEX.GD.ZS': 'health_expenditure_pct_gdp',
        'EG.ELC.ACCS.ZS': 'electricity_access_pct',
        'SH.STA.BASS.ZS': 'sanitation_access_pct',
        'SH.H2O.BASW.ZS': 'water_access_pct',
        'AG.LND.FRST.ZS': 'forest_area_pct',
        'EN.ATM.CO2E.PC': 'co2_emissions_per_capita',
        'IC.BUS.EASE.XQ': 'ease_doing_business',
        'FP.CPI.TOTL.ZG': 'inflation_wdi',
    }
    
    # Read in chunks to handle large file
    chunks = []
    chunk_size = 50000
    
    for chunk in pd.read_csv(wdi_file, chunksize=chunk_size, low_memory=False):
        # Filter for target indicators
        filtered = chunk[chunk['Indicator Code'].isin(target_wdi_indicators)]
        if len(filtered) > 0:
            chunks.append(filtered)
    
    if chunks:
        wdi_df = pd.concat(chunks, ignore_index=True)
        
        # Get year columns
        year_cols_wdi = [str(y) for y in range(YEAR_START, YEAR_END + 1)]
        available_years = [c for c in year_cols_wdi if c in wdi_df.columns]
        
        # Melt to long format
        wdi_long = wdi_df.melt(
            id_vars=['Country Code', 'Indicator Code'],
            value_vars=available_years,
            var_name='year',
            value_name='value'
        )
        
        wdi_long['year'] = wdi_long['year'].astype(int)
        wdi_long['value'] = pd.to_numeric(wdi_long['value'], errors='coerce')
        
        # Pivot to wide format
        wdi_pivot = wdi_long.pivot_table(
            index=['Country Code', 'year'],
            columns='Indicator Code',
            values='value'
        ).reset_index()
        
        wdi_pivot.columns.name = None
        wdi_pivot = wdi_pivot.rename(columns={'Country Code': 'iso3'})
        wdi_pivot = wdi_pivot.rename(columns=indicator_names)
        
        wdi_final = standardize_iso3(wdi_pivot)
        print(f"   ✓ WDI: {len(wdi_final)} rows, {wdi_final['iso3'].nunique()} entities")
        print(f"   Indicators loaded: {len([c for c in indicator_names.values() if c in wdi_final.columns])}")
    else:
        wdi_final = pd.DataFrame(columns=['iso3', 'year'])
        print("   ✗ WDI: No matching indicators found")
        
except Exception as e:
    print(f"   ✗ ERROR processing WDI: {e}")
    import traceback
    traceback.print_exc()
    wdi_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 7. PROCESS HDR (Human Development Report)
# ============================================================================
print("\n" + "-" * 80)
print("[7/13] Processing HDR (Human Development Index & Components)...")

hdr_dir = DATA_DIR / "HDR"

try:
    # First try the time-series CSV (preferred)
    hdr_timeseries = hdr_dir / "HDR25_Composite_indices_complete_time_series.csv"
    
    if hdr_timeseries.exists():
        hdr_df = pd.read_csv(hdr_timeseries, encoding='latin-1')
        
        # Get ONLY base HDI year columns (hdi_YYYY format, not hdi_f_YYYY or hdi_m_YYYY)
        hdi_year_cols = [c for c in hdr_df.columns if re.match(r'^hdi_\d{4}$', c)]
        
        # Melt to long format
        hdr_long = hdr_df.melt(
            id_vars=['iso3'],
            value_vars=hdi_year_cols,
            var_name='year_col',
            value_name='hdi'
        )
        
        # Extract year from column name (hdi_2000 -> 2000)
        hdr_long['year'] = hdr_long['year_col'].str.extract(r'(\d{4})').astype(int)
        hdr_long = hdr_long.drop(columns=['year_col'])
        
        # Convert HDI to numeric
        hdr_long['hdi'] = pd.to_numeric(hdr_long['hdi'], errors='coerce')
        
        # Filter to target year range
        hdr_long = hdr_long[(hdr_long['year'] >= YEAR_START) & (hdr_long['year'] <= YEAR_END)]
        
        # Also extract life expectancy (base le_YYYY only)
        le_cols = [c for c in hdr_df.columns if re.match(r'^le_\d{4}$', c)]
        if le_cols:
            le_long = hdr_df.melt(
                id_vars=['iso3'],
                value_vars=le_cols,
                var_name='year_col',
                value_name='life_expectancy'
            )
            le_long['year'] = le_long['year_col'].str.extract(r'(\d{4})').astype(int)
            le_long = le_long.drop(columns=['year_col'])
            le_long['life_expectancy'] = pd.to_numeric(le_long['life_expectancy'], errors='coerce')
            le_long = le_long[(le_long['year'] >= YEAR_START) & (le_long['year'] <= YEAR_END)]
            hdr_long = hdr_long.merge(le_long, on=['iso3', 'year'], how='left')
        
        # Extract expected years of schooling (eys_YYYY)
        eys_cols = [c for c in hdr_df.columns if re.match(r'^eys_\d{4}$', c)]
        if eys_cols:
            eys_long = hdr_df.melt(
                id_vars=['iso3'],
                value_vars=eys_cols,
                var_name='year_col',
                value_name='expected_years_schooling'
            )
            eys_long['year'] = eys_long['year_col'].str.extract(r'(\d{4})').astype(int)
            eys_long = eys_long.drop(columns=['year_col'])
            eys_long['expected_years_schooling'] = pd.to_numeric(eys_long['expected_years_schooling'], errors='coerce')
            eys_long = eys_long[(eys_long['year'] >= YEAR_START) & (eys_long['year'] <= YEAR_END)]
            hdr_long = hdr_long.merge(eys_long, on=['iso3', 'year'], how='left')
        
        # Extract mean years of schooling (mys_YYYY)
        mys_cols = [c for c in hdr_df.columns if re.match(r'^mys_\d{4}$', c)]
        if mys_cols:
            mys_long = hdr_df.melt(
                id_vars=['iso3'],
                value_vars=mys_cols,
                var_name='year_col',
                value_name='mean_years_schooling'
            )
            mys_long['year'] = mys_long['year_col'].str.extract(r'(\d{4})').astype(int)
            mys_long = mys_long.drop(columns=['year_col'])
            mys_long['mean_years_schooling'] = pd.to_numeric(mys_long['mean_years_schooling'], errors='coerce')
            mys_long = mys_long[(mys_long['year'] >= YEAR_START) & (mys_long['year'] <= YEAR_END)]
            hdr_long = hdr_long.merge(mys_long, on=['iso3', 'year'], how='left')
        
        # Extract GNI per capita (gni_pc_YYYY)
        gni_cols = [c for c in hdr_df.columns if re.match(r'^gnipc_\d{4}$', c)]
        if gni_cols:
            gni_long = hdr_df.melt(
                id_vars=['iso3'],
                value_vars=gni_cols,
                var_name='year_col',
                value_name='gni_per_capita'
            )
            gni_long['year'] = gni_long['year_col'].str.extract(r'(\d{4})').astype(int)
            gni_long = gni_long.drop(columns=['year_col'])
            gni_long['gni_per_capita'] = pd.to_numeric(gni_long['gni_per_capita'], errors='coerce')
            gni_long = gni_long[(gni_long['year'] >= YEAR_START) & (gni_long['year'] <= YEAR_END)]
            hdr_long = hdr_long.merge(gni_long, on=['iso3', 'year'], how='left')
        
        hdr_final = standardize_iso3(hdr_long)
        hdr_final = hdr_final.dropna(subset=['iso3'])
        
        print(f"   ✓ HDR: {len(hdr_final)} rows, {hdr_final['iso3'].nunique()} countries")
        print(f"   Year range: {hdr_final['year'].min()} - {hdr_final['year'].max()}")
        print(f"   Components: HDI, Life Expectancy, Years of Schooling, GNI")
    else:
        hdr_final = pd.DataFrame(columns=['iso3', 'year', 'hdi'])
        print("   ✗ HDR time series file not found")
        
except Exception as e:
    print(f"   ✗ ERROR processing HDR: {e}")
    import traceback
    traceback.print_exc()
    hdr_final = pd.DataFrame(columns=['iso3', 'year', 'hdi'])

# ============================================================================
# 8. PROCESS WGI (Worldwide Governance Indicators)
# ============================================================================
print("\n" + "-" * 80)
print("[8/13] Processing WGI (Worldwide Governance Indicators)...")

wgi_dir = DATA_DIR / "WGI"
wgi_file = wgi_dir / "wgidataset.xlsx"

try:
    if wgi_file.exists():
        # WGI is in long format with columns: code, countryname, year, indicator, estimate
        wgi_df = pd.read_excel(wgi_file, sheet_name=0)
        
        # The data has: code (ISO3), year, indicator (cc/ge/pv/rl/rq/va), estimate (score)
        wgi_df = wgi_df.rename(columns={'code': 'iso3'})
        
        # Filter to target years
        wgi_df = wgi_df[(wgi_df['year'] >= YEAR_START) & (wgi_df['year'] <= YEAR_END)]
        
        # Convert estimate to numeric (handle '..' values)
        wgi_df['estimate'] = pd.to_numeric(wgi_df['estimate'], errors='coerce')
        
        # Pivot indicators to columns
        wgi_pivot = wgi_df.pivot_table(
            index=['iso3', 'year'],
            columns='indicator',
            values='estimate'
        ).reset_index()
        
        wgi_pivot.columns.name = None
        
        # Rename governance indicators
        gov_renames = {
            'va': 'wgi_voice_accountability',
            'pv': 'wgi_political_stability',
            'ge': 'wgi_gov_effectiveness',
            'rq': 'wgi_regulatory_quality',
            'rl': 'wgi_rule_of_law',
            'cc': 'wgi_control_corruption'
        }
        wgi_pivot = wgi_pivot.rename(columns=gov_renames)
        
        # Calculate composite governance index (average of all 6 indicators)
        gov_cols = [c for c in gov_renames.values() if c in wgi_pivot.columns]
        if gov_cols:
            wgi_pivot['wgi_composite'] = wgi_pivot[gov_cols].mean(axis=1)
        
        wgi_final = standardize_iso3(wgi_pivot)
        wgi_final = wgi_final.dropna(subset=['iso3'])
        print(f"   ✓ WGI: {len(wgi_final)} rows, {wgi_final['iso3'].nunique()} countries")
        print(f"   Indicators: Voice, Political Stability, Effectiveness, Regulatory, Rule of Law, Corruption")
    else:
        print(f"   ✗ WGI file not found")
        wgi_final = pd.DataFrame(columns=['iso3', 'year'])
        
except Exception as e:
    print(f"   ✗ ERROR processing WGI: {e}")
    import traceback
    traceback.print_exc()
    wgi_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 9. PROCESS INFORM RISK INDEX
# ============================================================================
print("\n" + "-" * 80)
print("[9/13] Processing INFORM Risk Index (Hazard, Vulnerability, Coping)...")

inform_dir = DATA_DIR / "IINFORMRisk"

try:
    # Use the TREND file which has historical data 2015-2024
    trend_file = inform_dir / "INFORM2024_TREND_2015_2024_v70_ALL.xlsx"
    
    if trend_file.exists():
        inform_df = pd.read_excel(trend_file, sheet_name=0)
        
        # Target indicators to extract
        target_indicators = {
            'INFORM': 'inform_risk',
            'HA': 'inform_hazard',
            'VU': 'inform_vulnerability', 
            'CC': 'inform_coping_capacity',
            'HA.NAT': 'inform_natural_hazard',
            'HA.HUM': 'inform_human_hazard',
            'VU.SEV': 'inform_socioeconomic_vulnerability',
            'VU.VGR': 'inform_vulnerable_groups',
            'CC.INF': 'inform_institutional',
            'CC.INS': 'inform_infrastructure'
        }
        
        inform_dfs = []
        
        for indicator_id, col_name in target_indicators.items():
            ind_df = inform_df[inform_df['IndicatorId'] == indicator_id][['Iso3', 'INFORMYear', 'IndicatorScore']].copy()
            if len(ind_df) > 0:
                ind_df.columns = ['iso3', 'year', col_name]
                inform_dfs.append(ind_df)
        
        if inform_dfs:
            # Merge all indicators
            inform_final = inform_dfs[0]
            for df in inform_dfs[1:]:
                inform_final = inform_final.merge(df, on=['iso3', 'year'], how='outer')
            
            # Filter year range
            inform_final = inform_final[(inform_final['year'] >= YEAR_START) & (inform_final['year'] <= YEAR_END)]
            
            inform_final = standardize_iso3(inform_final)
            inform_final = inform_final.dropna(subset=['iso3'])
            
            print(f"   ✓ INFORM: {len(inform_final)} rows, {inform_final['iso3'].nunique()} countries")
            print(f"   Year range: {inform_final['year'].min()} - {inform_final['year'].max()}")
            print(f"   Note: INFORM data only available from 2015 onwards")
        else:
            inform_final = pd.DataFrame(columns=['iso3', 'year'])
    else:
        print(f"   ✗ INFORM TREND file not found")
        inform_final = pd.DataFrame(columns=['iso3', 'year'])
        
except Exception as e:
    print(f"   ✗ ERROR processing INFORM: {e}")
    import traceback
    traceback.print_exc()
    inform_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 10. PROCESS FTS HUMANITARIAN FUNDING
# ============================================================================
print("\n" + "-" * 80)
print("[10/13] Processing FTS Humanitarian Funding Data...")

fts_dir = DATA_DIR / "FTS"

try:
    fts_files = list(fts_dir.glob("*.csv"))
    
    if fts_files:
        fts_all = []
        
        for fts_file in fts_files:
            try:
                # Skip HXL row (row index 1)
                df = pd.read_csv(fts_file, skiprows=[1])
                
                # Use destLocations for recipient countries
                if 'destLocations' in df.columns and 'amountUSD' in df.columns:
                    df_clean = df[['destLocations', 'budgetYear', 'amountUSD']].copy()
                    df_clean = df_clean.dropna(subset=['destLocations', 'amountUSD'])
                    
                    # Handle multi-country destinations (split equally)
                    expanded_rows = []
                    for _, row in df_clean.iterrows():
                        locations = str(row['destLocations']).split(',')
                        locations = [loc.strip() for loc in locations if loc.strip() and len(loc.strip()) == 3]
                        if locations:
                            amount_per_country = row['amountUSD'] / len(locations)
                            for loc in locations:
                                expanded_rows.append({
                                    'iso3': loc,
                                    'year': row['budgetYear'],
                                    'funding_usd': amount_per_country
                                })
                    
                    if expanded_rows:
                        fts_all.append(pd.DataFrame(expanded_rows))
            except Exception as file_error:
                print(f"      Warning: Error reading {fts_file.name}: {file_error}")
                continue
        
        if fts_all:
            fts_combined = pd.concat(fts_all, ignore_index=True)
            
            # Aggregate by country-year
            fts_agg = fts_combined.groupby(['iso3', 'year']).agg({
                'funding_usd': 'sum'
            }).reset_index()
            
            fts_agg = fts_agg.rename(columns={'funding_usd': 'humanitarian_funding_usd'})
            
            # Calculate funding per capita (will be joined later with population)
            fts_final = standardize_iso3(fts_agg)
            fts_final = fts_final[(fts_final['year'] >= YEAR_START) & (fts_final['year'] <= YEAR_END)]
            
            print(f"   ✓ FTS: {len(fts_final)} rows, {fts_final['iso3'].nunique()} countries")
            print(f"   Year range: {fts_final['year'].min()} - {fts_final['year'].max()}")
            print(f"   Total funding: ${fts_final['humanitarian_funding_usd'].sum():,.0f}")
        else:
            fts_final = pd.DataFrame(columns=['iso3', 'year', 'humanitarian_funding_usd'])
    else:
        fts_final = pd.DataFrame(columns=['iso3', 'year', 'humanitarian_funding_usd'])
        print("   ✗ FTS: No files found")
        
except Exception as e:
    print(f"   ✗ ERROR processing FTS: {e}")
    import traceback
    traceback.print_exc()
    fts_final = pd.DataFrame(columns=['iso3', 'year', 'humanitarian_funding_usd'])

# ============================================================================
# 11. PROCESS DESINVENTAR (Disaster Loss Records)
# ============================================================================
print("\n" + "-" * 80)
print("[11/13] Processing DesInventar Disaster Loss Records...")

desinventar_dir = DATA_DIR / "desinventarSandai"

try:
    import xml.etree.ElementTree as ET
    
    # Check for extracted folders first (faster than ZIPs)
    extracted_dir = desinventar_dir / "extracted"
    
    if extracted_dir.exists():
        country_dirs = [d for d in extracted_dir.iterdir() if d.is_dir()]
        print(f"   Found {len(country_dirs)} extracted DesInventar country folders")
        
        desinventar_all = []
        processed_count = 0
        
        # ISO3 code mapping from folder names
        code_mapping = {
            'AGO': 'AGO', 'ALB': 'ALB', 'AR2': 'ARM', 'ARG': 'ARG', 'ATG': 'ATG',
            'BFA': 'BFA', 'BLZ': 'BLZ', 'BOL': 'BOL', 'BRB': 'BRB', 'BTN': 'BTN',
            'CHL': 'CHL', 'COL': 'COL', 'COM': 'COM', 'CRI': 'CRI', 'DJI': 'DJI',
            'DMA': 'DMA', 'DOM': 'DOM', 'ECU': 'ECU', 'EGY': 'EGY', 'ESP': 'ESP',
            'ETH': 'ETH', 'GHA': 'GHA', 'GIN': 'GIN', 'GMB': 'GMB', 'GNB': 'GNB',
            'GNQ': 'GNQ', 'GRD': 'GRD', 'GTM': 'GTM', 'GUY': 'GUY', 'HND': 'HND',
            'IDN': 'IDN', 'IRN': 'IRN', 'JAM': 'JAM', 'JOR': 'JOR', 'KEN': 'KEN',
            'KHM': 'KHM', 'KNA': 'KNA', 'LAO2': 'LAO', 'LBN': 'LBN', 'LBR': 'LBR',
            'LCA': 'LCA', 'MAR': 'MAR', 'MDG': 'MDG', 'MDV': 'MDV', 'MEX': 'MEX',
            'MLI': 'MLI', 'MMR': 'MMR', 'MNE': 'MNE', 'MNG': 'MNG', 'MOZ': 'MOZ',
            'MUS': 'MUS', 'MWI': 'MWI', 'NAM': 'NAM', 'NER': 'NER', 'NG_OY': 'NGA',
            'NIC': 'NIC', 'NPL': 'NPL', 'PAK': 'PAK', 'PAN': 'PAN', 'PER': 'PER',
            'PHL': 'PHL', 'PNG': 'PNG', 'PRY': 'PRY', 'RWA': 'RWA', 'SEN': 'SEN',
            'SLB': 'SLB', 'SLE': 'SLE', 'SLV': 'SLV', 'SRB': 'SRB', 'SUR': 'SUR',
            'SYR': 'SYR', 'TCD': 'TCD', 'TGO': 'TGO', 'TTO': 'TTO', 'TUR': 'TUR',
            'TZA': 'TZA', 'UGA': 'UGA', 'URY': 'URY', 'VCT': 'VCT', 'VEN': 'VEN',
            'VNM': 'VNM', 'VUT': 'VUT', 'YEM': 'YEM', 'ZMB': 'ZMB',
        }
        
        for country_dir in country_dirs:
            try:
                # Extract country code from folder name (DI_export_XXX)
                folder_name = country_dir.name
                if folder_name.startswith('DI_export_'):
                    country_code = folder_name.replace('DI_export_', '').upper()
                else:
                    country_code = folder_name.upper()
                
                country_code = code_mapping.get(country_code, country_code)
                
                # Find XML files in folder
                xml_files = list(country_dir.glob("*.xml"))
                
                for xml_file in xml_files:
                    try:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()
                        
                        # Find fichas (disaster records)
                        fichas = root.find('fichas')
                        if fichas is not None:
                            for record in fichas.findall('TR'):
                                try:
                                    year_elem = record.find('fechano')
                                    year = int(year_elem.text) if year_elem is not None and year_elem.text else None
                                    
                                    if year and YEAR_START <= year <= YEAR_END:
                                        deaths = record.find('muertos')
                                        affected = record.find('afectados')
                                        houses_dest = record.find('vivdest')
                                        houses_dam = record.find('vivafec')
                                        
                                        desinventar_all.append({
                                            'iso3': country_code,
                                            'year': year,
                                            'deaths': int(deaths.text) if deaths is not None and deaths.text else 0,
                                            'affected': int(affected.text) if affected is not None and affected.text else 0,
                                            'houses_destroyed': int(houses_dest.text) if houses_dest is not None and houses_dest.text else 0,
                                            'houses_damaged': int(houses_dam.text) if houses_dam is not None and houses_dam.text else 0,
                                            'event_count': 1
                                        })
                                except:
                                    continue
                            processed_count += 1
                    except ET.ParseError:
                        continue
            except Exception as dir_error:
                continue
        
        if desinventar_all:
            desinventar_df = pd.DataFrame(desinventar_all)
            
            # Aggregate by country-year
            desinventar_agg = desinventar_df.groupby(['iso3', 'year']).agg({
                'event_count': 'sum',
                'deaths': 'sum',
                'affected': 'sum',
                'houses_destroyed': 'sum',
                'houses_damaged': 'sum'
            }).reset_index()
            
            # Rename columns with prefix
            desinventar_agg = desinventar_agg.rename(columns={
                'event_count': 'desinventar_events',
                'deaths': 'desinventar_deaths',
                'affected': 'desinventar_affected',
                'houses_destroyed': 'desinventar_houses_destroyed',
                'houses_damaged': 'desinventar_houses_damaged'
            })
            
            desinventar_final = standardize_iso3(desinventar_agg)
            print(f"   ✓ DesInventar: {len(desinventar_final)} country-years from {processed_count} countries")
            print(f"   Total events: {desinventar_final['desinventar_events'].sum():,}")
        else:
            desinventar_final = pd.DataFrame(columns=['iso3', 'year'])
            print("   ✗ DesInventar: No data extracted")
    else:
        desinventar_final = pd.DataFrame(columns=['iso3', 'year'])
        print("   ✗ DesInventar: Extracted folder not found")
        
except Exception as e:
    print(f"   ✗ ERROR processing DesInventar: {e}")
    import traceback
    traceback.print_exc()
    desinventar_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 12. PROCESS BARRO-LEE EDUCATIONAL ATTAINMENT
# ============================================================================
print("\n" + "-" * 80)
print("[12/13] Processing Barro-Lee Educational Attainment Data...")

barrolee_dir = DATA_DIR / "barrolee"

try:
    barrolee_files = list(barrolee_dir.glob("*.csv"))
    
    if barrolee_files:
        barrolee_df = pd.read_csv(barrolee_files[0])
        
        # Column names: WBcode (ISO3), country, year, various education metrics
        # Key variable: yr_sch (average years of schooling)
        
        if 'WBcode' in barrolee_df.columns:
            barrolee_df = barrolee_df.rename(columns={'WBcode': 'iso3'})
        
        # Select relevant columns
        cols_to_keep = ['iso3', 'year']
        education_cols = {
            'yr_sch': 'years_of_schooling',
            'yr_sch_pri': 'years_primary_schooling',
            'yr_sch_sec': 'years_secondary_schooling', 
            'yr_sch_ter': 'years_tertiary_schooling',
            'lu': 'no_schooling_pct',
            'lp': 'primary_completed_pct',
            'ls': 'secondary_completed_pct',
            'lh': 'tertiary_completed_pct'
        }
        
        for old_col, new_col in education_cols.items():
            if old_col in barrolee_df.columns:
                cols_to_keep.append(old_col)
        
        barrolee_filtered = barrolee_df[cols_to_keep].copy()
        barrolee_filtered = barrolee_filtered.rename(columns=education_cols)
        
        # Filter to target year range (Barro-Lee data is 5-year intervals)
        barrolee_filtered = barrolee_filtered[
            (barrolee_filtered['year'] >= YEAR_START) & 
            (barrolee_filtered['year'] <= YEAR_END)
        ]
        
        barrolee_final = standardize_iso3(barrolee_filtered)
        barrolee_final = barrolee_final.dropna(subset=['iso3'])
        
        print(f"   ✓ Barro-Lee: {len(barrolee_final)} rows, {barrolee_final['iso3'].nunique()} countries")
        print(f"   Year range: {barrolee_final['year'].min()} - {barrolee_final['year'].max()}")
        print(f"   Note: Data at 5-year intervals, will interpolate later")
    else:
        barrolee_final = pd.DataFrame(columns=['iso3', 'year'])
        print("   ✗ Barro-Lee: No files found")
        
except Exception as e:
    print(f"   ✗ ERROR processing Barro-Lee: {e}")
    import traceback
    traceback.print_exc()
    barrolee_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 13. PROCESS GINI INDEX (WID/World Inequality Database)
# ============================================================================
print("\n" + "-" * 80)
print("[13/13] Processing Gini Index Data...")

gini_dir = DATA_DIR / "WDIworld"

try:
    gini_file = gini_dir / "economic-inequality-gini-index.csv"
    
    if gini_file.exists():
        gini_df = pd.read_csv(gini_file)
        
        # Standard format: Entity, Code, Year, Gini coefficient
        if 'Code' in gini_df.columns:
            gini_df = gini_df.rename(columns={'Code': 'iso3', 'Year': 'year'})
        
        # Find Gini column
        gini_col = None
        for col in gini_df.columns:
            if 'gini' in col.lower():
                gini_col = col
                break
        
        if gini_col and 'iso3' in gini_df.columns:
            gini_filtered = gini_df[['iso3', 'year', gini_col]].copy()
            gini_filtered = gini_filtered.rename(columns={gini_col: 'gini_wid'})
            
            # Filter year range
            gini_filtered = gini_filtered[
                (gini_filtered['year'] >= YEAR_START) & 
                (gini_filtered['year'] <= YEAR_END)
            ]
            
            gini_final = standardize_iso3(gini_filtered)
            gini_final = gini_final.dropna(subset=['iso3', 'gini_wid'])
            
            print(f"   ✓ Gini (WID): {len(gini_final)} rows, {gini_final['iso3'].nunique()} countries")
        else:
            gini_final = pd.DataFrame(columns=['iso3', 'year'])
            print("   ✗ Gini: Could not find required columns")
    else:
        gini_final = pd.DataFrame(columns=['iso3', 'year'])
        print("   ✗ Gini file not found")
        
except Exception as e:
    print(f"   ✗ ERROR processing Gini: {e}")
    import traceback
    traceback.print_exc()
    gini_final = pd.DataFrame(columns=['iso3', 'year'])
# ============================================================================
# FINAL MERGE - COMBINE ALL DATASETS
# ============================================================================
print("\n" + "=" * 80)
print("MERGING ALL DATASETS")
print("=" * 80)

# Use ND-GAIN as the spine (most complete country-year coverage)
print(f"\nStarting with ND-GAIN spine: {len(ndgain_final)} rows, {ndgain_final['iso3'].nunique()} countries")
final = ndgain_final.copy()

# Define merge datasets in order of priority/coverage
merge_datasets = [
    (ntl_final, 'Nighttime Lights'),
    (emdat_final, 'EM-DAT Disasters'),
    (gdacs_final, 'GDACS Alerts'),
    (weo_final, 'IMF WEO'),
    (wdi_final, 'World Bank WDI'),
    (hdr_final, 'HDR'),
    (wgi_final, 'WGI Governance'),
    (inform_final, 'INFORM Risk'),
    (fts_final, 'FTS Funding'),
    (desinventar_final, 'DesInventar'),
    (barrolee_final, 'Barro-Lee Education'),
    (gini_final, 'Gini Index'),
]

for df, name in merge_datasets:
    if len(df) > 0 and 'iso3' in df.columns and 'year' in df.columns:
        # Ensure year is int
        df = df.copy()
        df['year'] = pd.to_numeric(df['year'], errors='coerce').astype('Int64')
        
        # Get columns to merge (excluding iso3 and year)
        merge_cols = [c for c in df.columns if c not in ['iso3', 'year']]
        
        if merge_cols:
            before_len = len(final)
            before_cols = len(final.columns)
            final = final.merge(df, on=['iso3', 'year'], how='left')
            print(f"   ✓ Merged {name}: +{len(merge_cols)} columns ({len(final.columns)} total)")
        else:
            print(f"   ○ Skipped {name}: No data columns")
    else:
        print(f"   ○ Skipped {name}: Empty or missing key columns")

# ============================================================================
# POST-PROCESSING & DATA QUALITY IMPROVEMENTS
# ============================================================================
print("\n" + "=" * 80)
print("POST-PROCESSING & DATA QUALITY")
print("=" * 80)

# Filter to target year range
final = final[(final['year'] >= YEAR_START) & (final['year'] <= YEAR_END)]

# Remove rows with no iso3
final = final.dropna(subset=['iso3'])

# Sort by iso3 and year
final = final.sort_values(['iso3', 'year']).reset_index(drop=True)

print(f"\n1. Basic filtering complete: {len(final)} rows")

# ============================================================================
# CONSOLIDATE DISASTER IMPACT DATA
# ============================================================================
print("\n2. Consolidating disaster impact data...")

# Helper function to safely get column as Series (avoids .get() returning int when column missing)
def safe_col(df, col, default=0):
    """Return column if exists, otherwise Series of default values."""
    if col in df.columns:
        return df[col].fillna(default)
    return pd.Series(default, index=df.index)

# Combine deaths from multiple sources (prioritize EM-DAT, then DesInventar)
if 'emdat_deaths' in final.columns or 'desinventar_deaths' in final.columns:
    final['total_disaster_deaths'] = safe_col(final, 'emdat_deaths') + safe_col(final, 'desinventar_deaths')
    print(f"   Combined deaths from EM-DAT and DesInventar")

# Combine affected populations
if 'emdat_affected' in final.columns or 'desinventar_affected' in final.columns:
    final['total_disaster_affected'] = safe_col(final, 'emdat_affected') + safe_col(final, 'desinventar_affected')
    print(f"   Combined affected populations")

# Combine disaster event counts
if 'emdat_event_count' in final.columns or 'desinventar_events' in final.columns or 'gdacs_disaster_count' in final.columns:
    final['total_disaster_events'] = (
        safe_col(final, 'emdat_event_count') + safe_col(final, 'desinventar_events')
    ).astype(int)
    # Use GDACS count as fallback
    final['total_disaster_events'] = final['total_disaster_events'].where(
        final['total_disaster_events'] > 0,
        safe_col(final, 'gdacs_disaster_count')
    )
    print(f"   Combined disaster event counts")

# ============================================================================
# CONSOLIDATE ECONOMIC DATA
# ============================================================================
print("\n3. Consolidating economic indicators...")

# Use best available GDP per capita (prefer WDI constant USD)
if 'gdp_per_capita' in final.columns and 'gdp_per_capita_imf' in final.columns:
    final['gdp_per_capita_best'] = final['gdp_per_capita'].fillna(final['gdp_per_capita_imf'])
    print(f"   Consolidated GDP per capita (WDI primary, IMF secondary)")
elif 'gdp_per_capita' in final.columns:
    final['gdp_per_capita_best'] = final['gdp_per_capita']
elif 'gdp_per_capita_imf' in final.columns:
    final['gdp_per_capita_best'] = final['gdp_per_capita_imf']

# Use best available GDP growth
if 'gdp_growth' in final.columns and 'gdp_growth_imf' in final.columns:
    final['gdp_growth_best'] = final['gdp_growth'].fillna(final['gdp_growth_imf'])
    print(f"   Consolidated GDP growth (WDI primary, IMF secondary)")
elif 'gdp_growth' in final.columns:
    final['gdp_growth_best'] = final['gdp_growth']
elif 'gdp_growth_imf' in final.columns:
    final['gdp_growth_best'] = final['gdp_growth_imf']

# Consolidate Gini (WDI primary, WID secondary)
if 'gini_index' in final.columns and 'gini_wid' in final.columns:
    final['gini_best'] = final['gini_index'].fillna(final['gini_wid'])
    print(f"   Consolidated Gini index (WDI primary, WID secondary)")
elif 'gini_index' in final.columns:
    final['gini_best'] = final['gini_index']
elif 'gini_wid' in final.columns:
    final['gini_best'] = final['gini_wid']

# ============================================================================
# CONSOLIDATE EDUCATION DATA
# ============================================================================
print("\n4. Consolidating education indicators...")

# Use HDR mean years schooling if available, else Barro-Lee
if 'mean_years_schooling' in final.columns and 'years_of_schooling' in final.columns:
    final['education_years_best'] = final['mean_years_schooling'].fillna(final['years_of_schooling'])
    print(f"   Consolidated years of schooling (HDR primary, Barro-Lee secondary)")
elif 'mean_years_schooling' in final.columns:
    final['education_years_best'] = final['mean_years_schooling']
elif 'years_of_schooling' in final.columns:
    final['education_years_best'] = final['years_of_schooling']

# ============================================================================
# CALCULATE DERIVED INDICES
# ============================================================================
print("\n" + "=" * 80)
print("CALCULATING DERIVED RESILIENCE INDICES")
print("=" * 80)

# -----------------------------------------------------------------------------
# DII - DISASTER IMPACT INDEX
# Formula: DII = ((F + 4A) / GDP_pc) × S
# Where: F = Fatalities per million, A = Affected %, S = Severity weight
# -----------------------------------------------------------------------------
print("\n5. Calculating DII (Disaster Impact Index)...")

if 'population' in final.columns:
    # Calculate fatalities per million population
    final['fatalities_per_million'] = safe_divide(
        safe_col(final, 'total_disaster_deaths') * 1_000_000,
        final['population']
    )
    
    # Calculate affected as percentage of population
    final['affected_pct'] = safe_divide(
        safe_col(final, 'total_disaster_affected') * 100,
        final['population']
    )
    
    # Get severity weight (from GDACS or default to 1)
    severity_weight = safe_col(final, 'gdacs_severity_weight', default=1)
    
    # Calculate DII
    gdp_pc = final['gdp_per_capita_best'] if 'gdp_per_capita_best' in final.columns else \
             (final['gdp_per_capita'] if 'gdp_per_capita' in final.columns else pd.Series(np.nan, index=final.index))
    
    final['DII'] = safe_divide(
        (final['fatalities_per_million'].fillna(0) + DII_AFFECTED_WEIGHT * final['affected_pct'].fillna(0)),
        gdp_pc
    ) * severity_weight
    
    # Normalize DII to 0-100 scale (higher = more impact)
    final['DII_normalized'] = normalize_0_1(final['DII'].clip(lower=0)) * 100
    
    print(f"   ✓ DII calculated for {final['DII'].notna().sum()} country-years")
    print(f"   DII range: {final['DII'].min():.4f} - {final['DII'].max():.4f}")
else:
    print("   ✗ Cannot calculate DII: missing population data")

# -----------------------------------------------------------------------------
# RRS - RESILIENCE RECOVERY SCORE
# Formula: RRS = (GDP_growth_change + HDI + GovIndex) / T_recovery
# -----------------------------------------------------------------------------
print("\n6. Calculating RRS (Resilience Recovery Score)...")

# Calculate GDP growth change (year-over-year)
final = final.sort_values(['iso3', 'year'])

# Determine which GDP growth column to use
gdp_growth_col = None
if 'gdp_growth_best' in final.columns:
    gdp_growth_col = 'gdp_growth_best'
elif 'gdp_growth' in final.columns:
    gdp_growth_col = 'gdp_growth'

if gdp_growth_col:
    final['gdp_growth_change'] = final.groupby('iso3')[gdp_growth_col].diff()
else:
    final['gdp_growth_change'] = np.nan

# Normalize components to 0-1 scale
hdi_norm = normalize_0_1(final['hdi'] if 'hdi' in final.columns else pd.Series(np.nan, index=final.index))
gov_col = 'wgi_composite' if 'wgi_composite' in final.columns else ('wgi_gov_effectiveness' if 'wgi_gov_effectiveness' in final.columns else None)
gov_norm = normalize_0_1(final[gov_col] if gov_col else pd.Series(np.nan, index=final.index))
gdp_change_norm = normalize_0_1(final['gdp_growth_change'] if 'gdp_growth_change' in final.columns else pd.Series(np.nan, index=final.index))

# Recovery time estimation (use 3-year rolling window or years since disaster)
# Higher disaster count = longer recovery time
disaster_intensity = safe_col(final, 'total_disaster_events')
recovery_factor = 1 + np.log1p(disaster_intensity) / 3  # Log scale, min 1

# Calculate RRS (higher = better recovery capacity)
final['RRS'] = safe_divide(
    (gdp_change_norm.fillna(0.5) + hdi_norm.fillna(0.5) + gov_norm.fillna(0.5)),
    recovery_factor
)

# Normalize to 0-100 scale
final['RRS_normalized'] = normalize_0_1(final['RRS'].clip(lower=0, upper=5)) * 100

print(f"   ✓ RRS calculated for {final['RRS'].notna().sum()} country-years")
print(f"   RRS range: {final['RRS'].min():.4f} - {final['RRS'].max():.4f}")

# -----------------------------------------------------------------------------
# CRI - COMPOSITE RESILIENCE INDEX
# Formula: CRI = A / (E + V)
# Where: A = Adaptive Capacity, E = Exposure, V = Vulnerability
# -----------------------------------------------------------------------------
print("\n7. Calculating CRI (Composite Resilience Index)...")

# Adaptive Capacity (use ND-GAIN readiness or INFORM coping capacity)
adaptive_capacity = final['ndgain_readiness'] if 'ndgain_readiness' in final.columns else pd.Series(np.nan, index=final.index)
if 'inform_coping_capacity' in final.columns:
    # INFORM coping is inverse (higher = less capacity), so invert
    inform_coping_inverted = 10 - final['inform_coping_capacity'].fillna(5)
    adaptive_capacity = adaptive_capacity.fillna(inform_coping_inverted / 10)

# Exposure (use INFORM hazard or disaster count as proxy)
exposure = final['inform_hazard'] if 'inform_hazard' in final.columns else pd.Series(np.nan, index=final.index)
if exposure.isna().all():
    # Use normalized disaster count as proxy for exposure
    exposure = normalize_0_1(safe_col(final, 'total_disaster_events')) * 10

# Vulnerability (use ND-GAIN or INFORM vulnerability)
vulnerability = final['ndgain_vulnerability'] if 'ndgain_vulnerability' in final.columns else pd.Series(np.nan, index=final.index)
if 'inform_vulnerability' in final.columns:
    vulnerability = vulnerability.fillna(final['inform_vulnerability'] / 10)

# Calculate CRI (add small epsilon to avoid division by zero)
final['CRI'] = safe_divide(
    adaptive_capacity.fillna(0.5),
    (exposure.fillna(5) / 10 + vulnerability.fillna(0.5) + 0.001)
)

# Normalize to 0-100 scale (higher = more resilient)
final['CRI_normalized'] = normalize_0_1(final['CRI'].clip(lower=0, upper=5)) * 100

print(f"   ✓ CRI calculated for {final['CRI'].notna().sum()} country-years")
print(f"   CRI range: {final['CRI'].min():.4f} - {final['CRI'].max():.4f}")

# ============================================================================
# ADD METADATA COLUMNS
# ============================================================================
print("\n8. Adding metadata columns...")

# Add region classification
try:
    import pycountry
    
    # Simple region mapping based on first letter of ISO3 or manual mapping
    region_mapping = {
        'AFG': 'Asia', 'ALB': 'Europe', 'DZA': 'Africa', 'AND': 'Europe', 'AGO': 'Africa',
        'ARG': 'Americas', 'ARM': 'Asia', 'AUS': 'Oceania', 'AUT': 'Europe', 'AZE': 'Asia',
        'BHS': 'Americas', 'BHR': 'Asia', 'BGD': 'Asia', 'BRB': 'Americas', 'BLR': 'Europe',
        'BEL': 'Europe', 'BLZ': 'Americas', 'BEN': 'Africa', 'BTN': 'Asia', 'BOL': 'Americas',
        'BIH': 'Europe', 'BWA': 'Africa', 'BRA': 'Americas', 'BRN': 'Asia', 'BGR': 'Europe',
        'BFA': 'Africa', 'BDI': 'Africa', 'KHM': 'Asia', 'CMR': 'Africa', 'CAN': 'Americas',
        'CPV': 'Africa', 'CAF': 'Africa', 'TCD': 'Africa', 'CHL': 'Americas', 'CHN': 'Asia',
        'COL': 'Americas', 'COM': 'Africa', 'COG': 'Africa', 'COD': 'Africa', 'CRI': 'Americas',
        'CIV': 'Africa', 'HRV': 'Europe', 'CUB': 'Americas', 'CYP': 'Europe', 'CZE': 'Europe',
        'DNK': 'Europe', 'DJI': 'Africa', 'DMA': 'Americas', 'DOM': 'Americas', 'ECU': 'Americas',
        'EGY': 'Africa', 'SLV': 'Americas', 'GNQ': 'Africa', 'ERI': 'Africa', 'EST': 'Europe',
        'ETH': 'Africa', 'FJI': 'Oceania', 'FIN': 'Europe', 'FRA': 'Europe', 'GAB': 'Africa',
        'GMB': 'Africa', 'GEO': 'Asia', 'DEU': 'Europe', 'GHA': 'Africa', 'GRC': 'Europe',
        'GRD': 'Americas', 'GTM': 'Americas', 'GIN': 'Africa', 'GNB': 'Africa', 'GUY': 'Americas',
        'HTI': 'Americas', 'HND': 'Americas', 'HUN': 'Europe', 'ISL': 'Europe', 'IND': 'Asia',
        'IDN': 'Asia', 'IRN': 'Asia', 'IRQ': 'Asia', 'IRL': 'Europe', 'ISR': 'Asia',
        'ITA': 'Europe', 'JAM': 'Americas', 'JPN': 'Asia', 'JOR': 'Asia', 'KAZ': 'Asia',
        'KEN': 'Africa', 'KIR': 'Oceania', 'PRK': 'Asia', 'KOR': 'Asia', 'KWT': 'Asia',
        'KGZ': 'Asia', 'LAO': 'Asia', 'LVA': 'Europe', 'LBN': 'Asia', 'LSO': 'Africa',
        'LBR': 'Africa', 'LBY': 'Africa', 'LIE': 'Europe', 'LTU': 'Europe', 'LUX': 'Europe',
        'MDG': 'Africa', 'MWI': 'Africa', 'MYS': 'Asia', 'MDV': 'Asia', 'MLI': 'Africa',
        'MLT': 'Europe', 'MHL': 'Oceania', 'MRT': 'Africa', 'MUS': 'Africa', 'MEX': 'Americas',
        'FSM': 'Oceania', 'MDA': 'Europe', 'MCO': 'Europe', 'MNG': 'Asia', 'MNE': 'Europe',
        'MAR': 'Africa', 'MOZ': 'Africa', 'MMR': 'Asia', 'NAM': 'Africa', 'NRU': 'Oceania',
        'NPL': 'Asia', 'NLD': 'Europe', 'NZL': 'Oceania', 'NIC': 'Americas', 'NER': 'Africa',
        'NGA': 'Africa', 'NOR': 'Europe', 'OMN': 'Asia', 'PAK': 'Asia', 'PLW': 'Oceania',
        'PSE': 'Asia', 'PAN': 'Americas', 'PNG': 'Oceania', 'PRY': 'Americas', 'PER': 'Americas',
        'PHL': 'Asia', 'POL': 'Europe', 'PRT': 'Europe', 'QAT': 'Asia', 'ROU': 'Europe',
        'RUS': 'Europe', 'RWA': 'Africa', 'KNA': 'Americas', 'LCA': 'Americas', 'VCT': 'Americas',
        'WSM': 'Oceania', 'SMR': 'Europe', 'STP': 'Africa', 'SAU': 'Asia', 'SEN': 'Africa',
        'SRB': 'Europe', 'SYC': 'Africa', 'SLE': 'Africa', 'SGP': 'Asia', 'SVK': 'Europe',
        'SVN': 'Europe', 'SLB': 'Oceania', 'SOM': 'Africa', 'ZAF': 'Africa', 'SSD': 'Africa',
        'ESP': 'Europe', 'LKA': 'Asia', 'SDN': 'Africa', 'SUR': 'Americas', 'SWZ': 'Africa',
        'SWE': 'Europe', 'CHE': 'Europe', 'SYR': 'Asia', 'TWN': 'Asia', 'TJK': 'Asia',
        'TZA': 'Africa', 'THA': 'Asia', 'TLS': 'Asia', 'TGO': 'Africa', 'TON': 'Oceania',
        'TTO': 'Americas', 'TUN': 'Africa', 'TUR': 'Asia', 'TKM': 'Asia', 'TUV': 'Oceania',
        'UGA': 'Africa', 'UKR': 'Europe', 'ARE': 'Asia', 'GBR': 'Europe', 'USA': 'Americas',
        'URY': 'Americas', 'UZB': 'Asia', 'VUT': 'Oceania', 'VEN': 'Americas', 'VNM': 'Asia',
        'YEM': 'Asia', 'ZMB': 'Africa', 'ZWE': 'Africa', 'HKG': 'Asia', 'MAC': 'Asia',
    }
    
    final['region'] = final['iso3'].map(region_mapping)
    
    # Add income classification based on GDP per capita
    gdp_col = 'gdp_per_capita_best' if 'gdp_per_capita_best' in final.columns else 'gdp_per_capita'
    if gdp_col in final.columns:
        final['income_group'] = pd.cut(
            final[gdp_col],
            bins=[0, 1085, 4255, 13205, float('inf')],
            labels=['Low', 'Lower-Middle', 'Upper-Middle', 'High']
        )
    
    print(f"   ✓ Added region and income group classifications")
except Exception as e:
    print(f"   Warning: Could not add all metadata: {e}")

# ============================================================================
# VALIDATION & QUALITY REPORT
# ============================================================================
print("\n" + "=" * 80)
print("VALIDATION & QUALITY REPORT")
print("=" * 80)

print(f"\n📊 FINAL DATASET SUMMARY")
print(f"   Shape: {final.shape[0]} rows × {final.shape[1]} columns")
print(f"   Countries: {final['iso3'].nunique()}")
print(f"   Year range: {final['year'].min()} - {final['year'].max()}")
print(f"   Total country-years: {len(final)}")

# Column coverage analysis
print(f"\n📈 COLUMN COVERAGE (% non-null values):")
coverage = (1 - final.isnull().sum() / len(final)) * 100
coverage_sorted = coverage.sort_values(ascending=False)

# Group by coverage level
high_coverage = coverage_sorted[coverage_sorted >= 80]
medium_coverage = coverage_sorted[(coverage_sorted >= 40) & (coverage_sorted < 80)]
low_coverage = coverage_sorted[coverage_sorted < 40]

print(f"\n   HIGH COVERAGE (≥80%):")
for col, pct in high_coverage.head(15).items():
    print(f"      {col}: {pct:.1f}%")
if len(high_coverage) > 15:
    print(f"      ... and {len(high_coverage) - 15} more columns")

print(f"\n   MEDIUM COVERAGE (40-80%):")
for col, pct in medium_coverage.head(10).items():
    print(f"      {col}: {pct:.1f}%")

print(f"\n   LOW COVERAGE (<40%):")
for col, pct in low_coverage.head(10).items():
    print(f"      {col}: {pct:.1f}%")

# Derived indices coverage
print(f"\n📐 DERIVED INDICES COVERAGE:")
for idx in ['DII', 'RRS', 'CRI', 'DII_normalized', 'RRS_normalized', 'CRI_normalized']:
    if idx in final.columns:
        idx_coverage = (final[idx].notna().sum() / len(final)) * 100
        print(f"   {idx}: {idx_coverage:.1f}% ({final[idx].notna().sum()} values)")

# Validate ISO3 codes
print(f"\n🌍 ISO3 CODE VALIDATION:")
try:
    import pycountry
    valid_iso3 = set(c.alpha_3 for c in pycountry.countries)
    all_codes = set(final['iso3'].unique())
    valid_codes = all_codes.intersection(valid_iso3)
    invalid_codes = all_codes - valid_iso3
    
    print(f"   Valid ISO3 codes: {len(valid_codes)}")
    if invalid_codes:
        print(f"   Non-standard codes: {len(invalid_codes)} (may be regions/territories)")
        print(f"   Examples: {list(invalid_codes)[:5]}")
except:
    pass

# Regional distribution
if 'region' in final.columns:
    print(f"\n🗺️ REGIONAL DISTRIBUTION:")
    region_counts = final.groupby('region')['iso3'].nunique()
    for region, count in region_counts.sort_values(ascending=False).items():
        print(f"   {region}: {count} countries")

# Save coverage matrix
coverage_df = pd.DataFrame({
    'column': coverage.index,
    'coverage_pct': coverage.values,
    'non_null_count': (len(final) - final.isnull().sum()).values
})
coverage_df = coverage_df.sort_values('coverage_pct', ascending=False)
coverage_df.to_csv(COVERAGE_FILE, index=False)
print(f"\n💾 Saved coverage matrix to: {COVERAGE_FILE}")

# ============================================================================
# SAVE OUTPUT FILES
# ============================================================================
print("\n" + "=" * 80)
print("SAVING OUTPUT FILES")
print("=" * 80)

# Reorder columns for better usability
key_cols = ['iso3', 'year', 'region', 'income_group']
index_cols = ['DII', 'DII_normalized', 'RRS', 'RRS_normalized', 'CRI', 'CRI_normalized']
disaster_cols = [c for c in final.columns if any(x in c for x in ['disaster', 'deaths', 'affected', 'emdat', 'gdacs', 'desinventar'])]
economic_cols = [c for c in final.columns if any(x in c for x in ['gdp', 'gini', 'inflation', 'population', 'income'])]
development_cols = [c for c in final.columns if any(x in c for x in ['hdi', 'life_expectancy', 'education', 'schooling', 'literacy', 'health'])]
governance_cols = [c for c in final.columns if 'wgi' in c]
resilience_cols = [c for c in final.columns if any(x in c for x in ['ndgain', 'inform', 'ntl'])]
funding_cols = [c for c in final.columns if 'funding' in c or 'fts' in c]

# Get all other columns
all_ordered = key_cols + index_cols + disaster_cols + economic_cols + development_cols + governance_cols + resilience_cols + funding_cols
other_cols = [c for c in final.columns if c not in all_ordered]

# Create final column order (remove duplicates while preserving order)
final_col_order = []
for col in key_cols + index_cols + disaster_cols + economic_cols + development_cols + governance_cols + resilience_cols + funding_cols + other_cols:
    if col in final.columns and col not in final_col_order:
        final_col_order.append(col)

# Reorder and save
final = final[final_col_order]

# Save main dataset
final.to_csv(OUTPUT_FILE, index=False)
print(f"\n✓ Saved unified dataset to: {OUTPUT_FILE}")
print(f"   File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.2f} MB")
print(f"   Columns: {len(final.columns)}")
print(f"   Rows: {len(final)}")

# Generate validation report
validation_report = f"""
================================================================================
GLOBAL DISASTER RESILIENCE ANALYTICS - DATA VALIDATION REPORT
================================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Pipeline Version: 2.0

DATASET OVERVIEW
----------------
Total Rows: {len(final):,}
Total Columns: {len(final.columns)}
Unique Countries: {final['iso3'].nunique()}
Year Range: {final['year'].min()} - {final['year'].max()}

DERIVED INDICES
---------------
DII (Disaster Impact Index):
  - Coverage: {(final['DII'].notna().sum() / len(final) * 100):.1f}%
  - Range: {final['DII'].min():.4f} - {final['DII'].max():.4f}
  - Mean: {final['DII'].mean():.4f}

RRS (Resilience Recovery Score):
  - Coverage: {(final['RRS'].notna().sum() / len(final) * 100):.1f}%
  - Range: {final['RRS'].min():.4f} - {final['RRS'].max():.4f}
  - Mean: {final['RRS'].mean():.4f}

CRI (Composite Resilience Index):
  - Coverage: {(final['CRI'].notna().sum() / len(final) * 100):.1f}%
  - Range: {final['CRI'].min():.4f} - {final['CRI'].max():.4f}
  - Mean: {final['CRI'].mean():.4f}

DATA SOURCES INTEGRATED
-----------------------
1. ND-GAIN Climate Resilience Index (Spine)
2. Harmonized Nighttime Lights (Economic Proxy)
3. EM-DAT International Disaster Database
4. GDACS Global Disaster Alerts
5. IMF World Economic Outlook
6. World Bank World Development Indicators
7. UNDP Human Development Reports
8. Worldwide Governance Indicators
9. INFORM Risk Index
10. FTS Humanitarian Funding
11. DesInventar Disaster Loss Records
12. Barro-Lee Educational Attainment
13. World Inequality Database (Gini)

COLUMN CATEGORIES
-----------------
Key Identifiers: {len([c for c in final.columns if c in key_cols])}
Derived Indices: {len([c for c in final.columns if c in index_cols])}
Disaster Data: {len([c for c in disaster_cols if c in final.columns])}
Economic Data: {len([c for c in economic_cols if c in final.columns])}
Development Data: {len([c for c in development_cols if c in final.columns])}
Governance Data: {len([c for c in governance_cols if c in final.columns])}
Resilience Data: {len([c for c in resilience_cols if c in final.columns])}

FORMULA REFERENCE
-----------------
DII = ((Fatalities_per_million + 4 × Affected_pct) / GDP_per_capita) × Severity_weight
RRS = (GDP_growth_change + HDI + Governance) / Recovery_factor
CRI = Adaptive_Capacity / (Exposure + Vulnerability)

================================================================================
"""

with open(VALIDATION_FILE, 'w') as f:
    f.write(validation_report)
print(f"✓ Saved validation report to: {VALIDATION_FILE}")

# Print column list for reference
print(f"\n📋 FULL COLUMN LIST ({len(final.columns)} columns):")
print("-" * 60)
for i, col in enumerate(final.columns, 1):
    coverage_val = (1 - final[col].isnull().sum() / len(final)) * 100
    print(f"   {i:2}. {col}: {coverage_val:.1f}%")

print("\n" + "=" * 80)
print("✅ PIPELINE COMPLETE")
print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
