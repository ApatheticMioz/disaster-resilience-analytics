"""
Global Disaster Resilience Analytics Platform - Data Processing Pipeline
=========================================================================
Processes 10 raw datasets into a single unified analysis-ready dataset.
Primary Key: (iso3, year) for years 2000-2024
Output: unified_resilience_dataset.csv
"""

import pandas as pd
import numpy as np
import os
import glob
import zipfile
import sqlite3
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# Base paths
DATA_DIR = Path("Data")
OUTPUT_FILE = DATA_DIR / "unified_resilience_dataset.csv"

# Target year range
YEAR_START = 2000
YEAR_END = 2024

print("=" * 70)
print("GLOBAL DISASTER RESILIENCE ANALYTICS - DATA PROCESSING PIPELINE")
print("=" * 70)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def standardize_iso3(df, iso_col='iso3'):
    """Standardize ISO3 codes: uppercase, strip whitespace, handle blanks"""
    df = df.copy()
    df[iso_col] = df[iso_col].astype(str).str.strip().str.upper()
    # Replace invalid codes
    df.loc[df[iso_col].isin(['', 'NAN', 'NONE', '-1', '   ']), iso_col] = np.nan
    return df

def country_name_to_iso3(country_name):
    """Convert country name to ISO3 code using pycountry"""
    import pycountry
    if pd.isna(country_name) or not country_name:
        return None
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
    df_long['year'] = df_long['year'].astype(int)
    return df_long

# ============================================================================
# 1. PROCESS ND-GAIN DATASETS
# ============================================================================
print("\n[1/10] Processing ND-GAIN datasets...")

ndgain_dir = DATA_DIR / "NDGain"
year_cols = [str(y) for y in range(YEAR_START, YEAR_END + 1)]

# Load main indices
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
    
    print(f"   ND-GAIN: {len(ndgain_final)} rows, {ndgain_final['iso3'].nunique()} countries")
except Exception as e:
    print(f"   ERROR processing ND-GAIN: {e}")
    ndgain_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 2. PROCESS HARMONIZED NIGHTTIME LIGHTS
# ============================================================================
print("\n[2/10] Processing Harmonized Nighttime Lights...")

ntl_dir = DATA_DIR / "HarmonizedNTL"

try:
    # Load DMSP (annual, 1992-2013)
    dmsp_df = pd.read_csv(ntl_dir / "DMSP-OLS-nighttime-lights-1992to2013-level0.csv")
    dmsp_df = dmsp_df.rename(columns={'iso': 'iso3', 'nlsum': 'ntl_radiance'})
    dmsp_df = dmsp_df[(dmsp_df['year'] >= YEAR_START) & (dmsp_df['year'] < 2013)]
    
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
    
    print(f"   NTL: {len(ntl_final)} rows, {ntl_final['iso3'].nunique()} countries")
except Exception as e:
    print(f"   ERROR processing NTL: {e}")
    ntl_final = pd.DataFrame(columns=['iso3', 'year', 'ntl_radiance'])

# ============================================================================
# 3. PROCESS GDACS DISASTER DATA
# ============================================================================
print("\n[3/10] Processing GDACS disaster data...")

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
            df.columns = df.columns.str.lower()
            
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
            
            # Add deaths/displaced if available
            if 'death' in df.columns:
                cols_to_keep.append('death')
            if 'displaced' in df.columns:
                cols_to_keep.append('displaced')
            if 'people affected' in df.columns:
                df = df.rename(columns={'people affected': 'affected'})
                cols_to_keep.append('affected')
            
            available_cols = [c for c in cols_to_keep if c in df.columns]
            all_disasters.append(df[available_cols])
    
    # Combine all disaster types
    if all_disasters:
        gdacs_combined = pd.concat(all_disasters, ignore_index=True)
        gdacs_combined = standardize_iso3(gdacs_combined)
        
        # Filter year range
        gdacs_combined = gdacs_combined[(gdacs_combined['year'] >= YEAR_START) & 
                                         (gdacs_combined['year'] <= YEAR_END)]
        
        # Count red alerts
        gdacs_combined['is_red_alert'] = gdacs_combined['alertlevel'].str.upper().str.contains('RED', na=False).astype(int)
        
        # Aggregate by country-year
        gdacs_agg = gdacs_combined.groupby(['iso3', 'year']).agg({
            'disaster_type': 'count',  # Total disaster events
            'is_red_alert': 'sum',     # Red alert count
            'alertscore': 'mean'       # Average severity
        }).reset_index()
        
        gdacs_agg = gdacs_agg.rename(columns={
            'disaster_type': 'disaster_count',
            'is_red_alert': 'red_alerts',
            'alertscore': 'avg_alert_score'
        })
        
        # Add deaths/displaced aggregation if available
        if 'death' in gdacs_combined.columns:
            deaths_agg = gdacs_combined.groupby(['iso3', 'year'])['death'].sum().reset_index()
            deaths_agg = deaths_agg.rename(columns={'death': 'disaster_deaths'})
            gdacs_agg = gdacs_agg.merge(deaths_agg, on=['iso3', 'year'], how='left')
        
        if 'displaced' in gdacs_combined.columns:
            displaced_agg = gdacs_combined.groupby(['iso3', 'year'])['displaced'].sum().reset_index()
            displaced_agg = displaced_agg.rename(columns={'displaced': 'disaster_displaced'})
            gdacs_agg = gdacs_agg.merge(displaced_agg, on=['iso3', 'year'], how='left')
        
        gdacs_final = gdacs_agg.dropna(subset=['iso3'])
        print(f"   GDACS: {len(gdacs_final)} rows, {gdacs_final['iso3'].nunique()} countries")
    else:
        gdacs_final = pd.DataFrame(columns=['iso3', 'year'])
        
except Exception as e:
    print(f"   ERROR processing GDACS: {e}")
    import traceback
    traceback.print_exc()
    gdacs_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 4. PROCESS IMF WEO DATA
# ============================================================================
print("\n[4/10] Processing IMF WEO data...")

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
            'NGDP_RPCH': 'gdp_growth_imf',      # Real GDP growth
            'NGDPDPC': 'gdp_per_capita_imf',   # GDP per capita (current prices)
            'PCPIPCH': 'inflation_rate',        # Inflation
            'LP': 'population_imf'              # Population
        }
        
        # Filter for target indicators
        weo_filtered = weo_df[weo_df['indicator'].isin(target_indicators.keys())].copy()
        
        # Get year columns (they start from column 66 onwards based on exploration)
        year_cols_weo = [str(y) for y in range(YEAR_START, YEAR_END + 1)]
        available_year_cols = [c for c in year_cols_weo if c in weo_filtered.columns]
        
        # Melt to long format
        weo_long = weo_filtered.melt(
            id_vars=['iso3', 'indicator'],
            value_vars=available_year_cols,
            var_name='year',
            value_name='value'
        )
        
        # Clean values (handle empty strings)
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
        print(f"   IMF WEO: {len(weo_final)} rows, {weo_final['iso3'].nunique()} countries")
    else:
        weo_final = pd.DataFrame(columns=['iso3', 'year'])
        print("   IMF WEO: No files found")
        
except Exception as e:
    print(f"   ERROR processing IMF WEO: {e}")
    import traceback
    traceback.print_exc()
    weo_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 5. PROCESS WORLD BANK WDI
# ============================================================================
print("\n[5/10] Processing World Bank WDI (large file, using chunks)...")

wdi_dir = DATA_DIR / "worldBankWDI"
wdi_file = wdi_dir / "WDICSV.csv"

try:
    # Target indicators
    target_wdi_indicators = [
        'NY.GDP.MKTP.KD.ZG',  # GDP growth (annual %)
        'NY.GDP.PCAP.KD',     # GDP per capita (constant 2015 US$)
        'SI.POV.GINI',        # Gini Index
        'SH.MED.BEDS.ZS',     # Hospital beds per 1,000
        'IT.NET.USER.ZS',     # Internet users (% of population)
        'SE.ADT.LITR.ZS',     # Adult literacy rate
        'SP.POP.TOTL',        # Total population
        'SH.XPD.CHEX.GD.ZS',  # Health expenditure (% of GDP)
    ]
    
    indicator_names = {
        'NY.GDP.MKTP.KD.ZG': 'gdp_growth',
        'NY.GDP.PCAP.KD': 'gdp_per_capita',
        'SI.POV.GINI': 'gini_index',
        'SH.MED.BEDS.ZS': 'hospital_beds_per_1k',
        'IT.NET.USER.ZS': 'internet_users_pct',
        'SE.ADT.LITR.ZS': 'literacy_rate',
        'SP.POP.TOTL': 'population',
        'SH.XPD.CHEX.GD.ZS': 'health_expenditure_pct_gdp',
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
        print(f"   WDI: {len(wdi_final)} rows, {wdi_final['iso3'].nunique()} entities")
    else:
        wdi_final = pd.DataFrame(columns=['iso3', 'year'])
        print("   WDI: No matching indicators found")
        
except Exception as e:
    print(f"   ERROR processing WDI: {e}")
    import traceback
    traceback.print_exc()
    wdi_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 6. PROCESS HDR (Human Development Report)
# ============================================================================
print("\n[6/10] Processing HDR (Human Development Index)...")

hdr_dir = DATA_DIR / "HDR"

try:
    # First try the time-series CSV (preferred)
    hdr_timeseries = hdr_dir / "HDR25_Composite_indices_complete_time_series.csv"
    
    if hdr_timeseries.exists():
        # This file has columns: iso3, country, hdicode, region, hdi_1990, hdi_1991, ..., hdi_2023
        # Also has hdi_f_YYYY (female) and hdi_m_YYYY (male) - we only want the base hdi_YYYY
        hdr_df = pd.read_csv(hdr_timeseries, encoding='latin-1')
        
        # Get ONLY base HDI year columns (hdi_YYYY format, not hdi_f_YYYY or hdi_m_YYYY)
        import re
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
        
        # Also extract life expectancy if available (base le_YYYY only, not le_f_ or le_m_)
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
        
        hdr_final = standardize_iso3(hdr_long)
        hdr_final = hdr_final.dropna(subset=['iso3'])
        
        print(f"   HDR: {len(hdr_final)} rows, {hdr_final['iso3'].nunique()} countries")
        print(f"   HDR year range: {hdr_final['year'].min()} - {hdr_final['year'].max()}")
    else:
        # Fallback to Excel file (single year)
        hdr_file = hdr_dir / "HDR25_Statistical_Annex_HDI_Table.xlsx"
        if hdr_file.exists():
            hdr_df = pd.read_excel(hdr_file, sheet_name=0, header=5)
            cols = list(hdr_df.columns)
            country_col = cols[1] if len(cols) > 1 else None
            hdi_col = cols[2] if len(cols) > 2 else None
            
            if country_col and hdi_col:
                hdr_processed = hdr_df[[country_col, hdi_col]].copy()
                hdr_processed.columns = ['country_name', 'hdi']
                hdr_processed['hdi'] = pd.to_numeric(hdr_processed['hdi'], errors='coerce')
                hdr_processed = hdr_processed.dropna(subset=['hdi'])
                hdr_processed['iso3'] = hdr_processed['country_name'].apply(country_name_to_iso3)
                hdr_processed['year'] = 2023
                hdr_final = hdr_processed[['iso3', 'year', 'hdi']].dropna(subset=['iso3'])
                hdr_final = standardize_iso3(hdr_final)
                print(f"   HDR (Excel fallback): {len(hdr_final)} rows")
            else:
                hdr_final = pd.DataFrame(columns=['iso3', 'year', 'hdi'])
        else:
            hdr_final = pd.DataFrame(columns=['iso3', 'year', 'hdi'])
            print("   HDR: No files found")
        
except Exception as e:
    print(f"   ERROR processing HDR: {e}")
    import traceback
    traceback.print_exc()
    hdr_final = pd.DataFrame(columns=['iso3', 'year', 'hdi'])

# ============================================================================
# 7. PROCESS WGI (Worldwide Governance Indicators)
# ============================================================================
print("\n[7/10] Processing WGI (Governance Indicators)...")

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
        
        wgi_final = standardize_iso3(wgi_pivot)
        wgi_final = wgi_final.dropna(subset=['iso3'])
        print(f"   WGI: {len(wgi_final)} rows, {wgi_final['iso3'].nunique()} countries")
    else:
        print(f"   WGI file not found")
        wgi_final = pd.DataFrame(columns=['iso3', 'year'])
        
except Exception as e:
    print(f"   ERROR processing WGI: {e}")
    import traceback
    traceback.print_exc()
    wgi_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 8. PROCESS INFORM RISK INDEX
# ============================================================================
print("\n[8/10] Processing INFORM Risk Index...")

inform_dir = DATA_DIR / "IINFORMRisk"

try:
    # Use the TREND file which has historical data 2016-2025
    trend_file = inform_dir / "INFORM2024_TREND_2015_2024_v70_ALL.xlsx"
    
    if trend_file.exists():
        inform_df = pd.read_excel(trend_file, sheet_name=0)
        
        # Structure: Iso3, IndicatorId, IndicatorName, IndicatorScore, INFORMYear
        # Filter for main INFORM Risk indicator
        inform_risk = inform_df[inform_df['IndicatorId'] == 'INFORM'].copy()
        
        # Select and rename columns
        inform_risk = inform_risk[['Iso3', 'INFORMYear', 'IndicatorScore']].copy()
        inform_risk.columns = ['iso3', 'year', 'inform_risk']
        
        # Also get sub-components if available
        hazard_df = inform_df[inform_df['IndicatorId'] == 'HA'][['Iso3', 'INFORMYear', 'IndicatorScore']].copy()
        hazard_df.columns = ['iso3', 'year', 'inform_hazard']
        
        vuln_df = inform_df[inform_df['IndicatorId'] == 'VU'][['Iso3', 'INFORMYear', 'IndicatorScore']].copy()
        vuln_df.columns = ['iso3', 'year', 'inform_vulnerability']
        
        coping_df = inform_df[inform_df['IndicatorId'] == 'CC'][['Iso3', 'INFORMYear', 'IndicatorScore']].copy()
        coping_df.columns = ['iso3', 'year', 'inform_coping_capacity']
        
        # Merge components
        inform_final = inform_risk.merge(hazard_df, on=['iso3', 'year'], how='left')
        inform_final = inform_final.merge(vuln_df, on=['iso3', 'year'], how='left')
        inform_final = inform_final.merge(coping_df, on=['iso3', 'year'], how='left')
        
        # Filter year range
        inform_final = inform_final[(inform_final['year'] >= YEAR_START) & (inform_final['year'] <= YEAR_END)]
        
        inform_final = standardize_iso3(inform_final)
        inform_final = inform_final.dropna(subset=['iso3'])
        
        print(f"   INFORM: {len(inform_final)} rows, {inform_final['iso3'].nunique()} countries")
        print(f"   INFORM year range: {inform_final['year'].min()} - {inform_final['year'].max()}")
    else:
        print(f"   INFORM TREND file not found")
        inform_final = pd.DataFrame(columns=['iso3', 'year'])
        
except Exception as e:
    print(f"   ERROR processing INFORM: {e}")
    import traceback
    traceback.print_exc()
    inform_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# 9. PROCESS FTS HUMANITARIAN FUNDING
# ============================================================================
print("\n[9/10] Processing FTS humanitarian funding...")

fts_dir = DATA_DIR / "FTS"

try:
    fts_files = list(fts_dir.glob("*.csv"))
    
    if fts_files:
        fts_all = []
        
        for fts_file in fts_files:
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
        
        if fts_all:
            fts_combined = pd.concat(fts_all, ignore_index=True)
            
            # Aggregate by country-year
            fts_agg = fts_combined.groupby(['iso3', 'year']).agg({
                'funding_usd': 'sum'
            }).reset_index()
            
            fts_agg = fts_agg.rename(columns={'funding_usd': 'humanitarian_funding_usd'})
            fts_final = standardize_iso3(fts_agg)
            fts_final = fts_final[(fts_final['year'] >= YEAR_START) & (fts_final['year'] <= YEAR_END)]
            
            print(f"   FTS: {len(fts_final)} rows, {fts_final['iso3'].nunique()} countries")
            print(f"   FTS year range: {fts_final['year'].min()} - {fts_final['year'].max()}")
        else:
            fts_final = pd.DataFrame(columns=['iso3', 'year', 'humanitarian_funding_usd'])
    else:
        fts_final = pd.DataFrame(columns=['iso3', 'year', 'humanitarian_funding_usd'])
        print("   FTS: No files found")
        
except Exception as e:
    print(f"   ERROR processing FTS: {e}")
    import traceback
    traceback.print_exc()
    fts_final = pd.DataFrame(columns=['iso3', 'year', 'humanitarian_funding_usd'])

# ============================================================================
# 10. PROCESS DESINVENTAR (Disaster Loss Records)
# ============================================================================
print("\n[10/10] Processing DesInventar disaster loss records...")

desinventar_dir = DATA_DIR / "desinventarSandai"

try:
    import xml.etree.ElementTree as ET
    
    zip_files = list(desinventar_dir.glob("*.zip"))
    print(f"   Found {len(zip_files)} DesInventar ZIP files")
    
    if zip_files:
        desinventar_all = []
        processed_count = 0
        
        for zip_file in zip_files:
            try:
                # Extract ISO3 from filename (DI_export_XXX.zip)
                filename_parts = zip_file.stem.split('_')
                country_code = filename_parts[-1].upper()
                
                # Some codes need mapping
                code_mapping = {
                    'AR2': 'ARM',  # Armenia
                    'NG_OY': 'NGA',  # Nigeria
                    'LAO2': 'LAO',  # Laos
                    'PAC': 'PCN',  # Pacific (approximate)
                }
                country_code = code_mapping.get(country_code, country_code)
                
                with zipfile.ZipFile(zip_file, 'r') as z:
                    xml_files = [n for n in z.namelist() if n.endswith('.xml')]
                    
                    for xml_file in xml_files:
                        try:
                            with z.open(xml_file) as f:
                                tree = ET.parse(f)
                                root = tree.getroot()
                                
                                # Find fichas (disaster records)
                                fichas = root.find('fichas')
                                if fichas is not None:
                                    records = list(fichas.findall('TR'))
                                    
                                    # Extract data from each record
                                    for record in records:
                                        try:
                                            year_elem = record.find('fechano')
                                            year = int(year_elem.text) if year_elem is not None and year_elem.text else None
                                            
                                            if year and YEAR_START <= year <= YEAR_END:
                                                deaths = record.find('muertos')
                                                affected = record.find('afectados')
                                                houses_dest = record.find('vivdest')
                                                
                                                desinventar_all.append({
                                                    'iso3': country_code,
                                                    'year': year,
                                                    'deaths': int(deaths.text) if deaths is not None and deaths.text else 0,
                                                    'affected': int(affected.text) if affected is not None and affected.text else 0,
                                                    'houses_destroyed': int(houses_dest.text) if houses_dest is not None and houses_dest.text else 0,
                                                    'event_count': 1
                                                })
                                        except:
                                            continue
                                    
                                    processed_count += 1
                        except ET.ParseError:
                            continue
            except Exception as zip_error:
                continue
        
        if desinventar_all:
            desinventar_df = pd.DataFrame(desinventar_all)
            
            # Aggregate by country-year
            desinventar_agg = desinventar_df.groupby(['iso3', 'year']).agg({
                'event_count': 'sum',
                'deaths': 'sum',
                'affected': 'sum',
                'houses_destroyed': 'sum'
            }).reset_index()
            
            # Rename columns with prefix
            desinventar_agg = desinventar_agg.rename(columns={
                'event_count': 'desinventar_events',
                'deaths': 'desinventar_deaths',
                'affected': 'desinventar_affected',
                'houses_destroyed': 'desinventar_houses_destroyed'
            })
            
            desinventar_final = standardize_iso3(desinventar_agg)
            print(f"   DesInventar: {len(desinventar_final)} rows from {processed_count} countries")
        else:
            desinventar_final = pd.DataFrame(columns=['iso3', 'year'])
            print("   DesInventar: No data extracted")
    else:
        desinventar_final = pd.DataFrame(columns=['iso3', 'year'])
        print("   DesInventar: No ZIP files found")
        
except Exception as e:
    print(f"   ERROR processing DesInventar: {e}")
    import traceback
    traceback.print_exc()
    desinventar_final = pd.DataFrame(columns=['iso3', 'year'])

# ============================================================================
# FINAL MERGE
# ============================================================================
print("\n" + "=" * 70)
print("MERGING ALL DATASETS")
print("=" * 70)

# Use ND-GAIN as the spine (most complete country-year coverage)
print(f"\nStarting with ND-GAIN spine: {len(ndgain_final)} rows")
final = ndgain_final.copy()

# Define merge datasets
merge_datasets = [
    (ntl_final, 'Nighttime Lights'),
    (gdacs_final, 'GDACS Disasters'),
    (weo_final, 'IMF WEO'),
    (wdi_final, 'World Bank WDI'),
    (hdr_final, 'HDR'),
    (wgi_final, 'WGI Governance'),
    (inform_final, 'INFORM Risk'),
    (fts_final, 'FTS Funding'),
    (desinventar_final, 'DesInventar'),
]

for df, name in merge_datasets:
    if len(df) > 0 and 'iso3' in df.columns and 'year' in df.columns:
        # Ensure year is int
        df = df.copy()
        df['year'] = df['year'].astype(int)
        
        # Get columns to merge (excluding iso3 and year)
        merge_cols = [c for c in df.columns if c not in ['iso3', 'year']]
        
        if merge_cols:
            before_len = len(final)
            final = final.merge(df, on=['iso3', 'year'], how='left')
            print(f"   Merged {name}: +{len(merge_cols)} columns")
        else:
            print(f"   Skipped {name}: No data columns")
    else:
        print(f"   Skipped {name}: Empty or missing key columns")

# ============================================================================
# POST-PROCESSING
# ============================================================================
print("\n" + "=" * 70)
print("POST-PROCESSING")
print("=" * 70)

# Filter to target year range
final = final[(final['year'] >= YEAR_START) & (final['year'] <= YEAR_END)]

# Remove rows with no iso3
final = final.dropna(subset=['iso3'])

# Sort by iso3 and year
final = final.sort_values(['iso3', 'year']).reset_index(drop=True)

# ============================================================================
# VALIDATION
# ============================================================================
print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"\nFinal dataset shape: {final.shape}")
print(f"Countries: {final['iso3'].nunique()}")
print(f"Year range: {final['year'].min()} - {final['year'].max()}")
print(f"Total rows: {len(final)}")

print("\nColumn coverage (non-null %):")
coverage = (1 - final.isnull().sum() / len(final)) * 100
for col in coverage.sort_values(ascending=False).items():
    print(f"   {col[0]}: {col[1]:.1f}%")

# Validate ISO3 codes
try:
    import pycountry
    valid_iso3 = set(c.alpha_3 for c in pycountry.countries)
    invalid_codes = final[~final['iso3'].isin(valid_iso3)]['iso3'].unique()
    if len(invalid_codes) > 0:
        print(f"\nNote: {len(invalid_codes)} non-standard ISO3 codes found (may be regions/territories):")
        print(f"   {list(invalid_codes[:10])}...")
except:
    pass

# ============================================================================
# SAVE OUTPUT
# ============================================================================
print("\n" + "=" * 70)
print("SAVING OUTPUT")
print("=" * 70)

final.to_csv(OUTPUT_FILE, index=False)
print(f"\nSaved unified dataset to: {OUTPUT_FILE}")
print(f"File size: {OUTPUT_FILE.stat().st_size / (1024*1024):.2f} MB")

print("\n" + "=" * 70)
print("PIPELINE COMPLETE")
print("=" * 70)
