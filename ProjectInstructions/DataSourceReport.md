# Global Disaster Resilience Analytics Platform: Data Source Report

**To:** Senior Data Engineer / Policy Researcher  
**From:** AI Research Agent  
**Date:** December 2, 2025  
**Subject:** Final Open-Source Datasets for Resilience Indices (DII, RRS, CRI)

The following report outlines the high-quality, open-source datasets selected for your "Global Disaster Resilience Analytics Platform." All selected sources prioritize ISO 3166-1 alpha-3 compatibility to ensure seamless fusion by **Country** and **Year**. This version of the report designates primary sources for impact, inequality, and education data to ensure the robust calculation of the DII, RRS, and CRI indices.

---

## 1. Primary Disaster & Impact Data

These datasets form the core of the **Exposure (E)** and **Vulnerability (V)** components for the resilience indices.

### EM-DAT International Disaster Database (Primary Source)

- **Description:** The globally recognized gold-standard for validated disaster data, maintained by the Centre for Research on the Epidemiology of Disasters (CRED). It provides verified, cross-referenced data on disaster occurrences, fatalities, affected populations, and economic losses, and serves as the definitive source for calculating disaster impact.
- **Data Content:** Total Deaths, Total Affected, Total Damage, Adjusted ('000 US$).
- **Granularity:** Event-level, aggregated to Country-Year.
- **Access:** [https://www.emdat.be/](https://www.emdat.be/) (Academic registration required).
- **Folder:** `Data/emdat`

### GDACS (Global Disaster Alert and Coordination System) (Secondary Source)

- **Description:** Archives of real-time alerts and impact estimations. Useful for the **Severity (S)** weight in the DII formula, based on its algorithmic alert scores (Green/Orange/Red), which provide a consistent measure of an event's initial intensity.
- **Data Content:** Event severity scores, disaster type, population exposure estimates.
- **Granularity:** Event-level.
- **Access:** [https://www.gdacs.org/](https://www.gdacs.org/) (Archives) | [Kaggle Mirror](https://www.kaggle.com/datasets/elvinrustam/global-disaster-events-20002025).
- **Folder:** `Data/GDACS`

### DesInventar Sendai (Tertiary/Contextual Source)

- **Description:** The official UNDRR repository for historical disaster loss data, valuable for its inclusion of small-to-medium scale "extensive risk" events not always captured in global databases.
- **Data Content:** Granular data on fatalities, affected people, and economic/infrastructure losses.
- **Granularity:** Sub-national (District/Province) and National.
- **Access:** [https://www.desinventar.net/](https://www.desinventar.net/).
- **Folder:** `Data/desinventarSandai`

---

## 2. Primary Socio-Economic & Governance Data

These datasets form the core of the **Adaptive Capacity (A)** and **Resilience Recovery Score (RRS)** components.

### World Bank World Development Indicators (WDI)

- **Description:** The primary source for harmonized global macro-economic and development metrics.
- **Data Content:** GDP per capita, GDP growth (annual %), Health expenditure, Internet penetration.
- **Granularity:** Annual, Country-level.
- **Access:** [https://databank.worldbank.org/source/world-development-indicators](https://databank.worldbank.org/source/world-development-indicators).
- **Folder:** `Data/worldBankWDI`

### UNDP Human Development Reports (HDR)

- **Description:** The definitive source for the Human Development Index (HDI) and its components, a critical measure of a nation's social resilience and well-being.
- **Data Content:** Human Development Index (HDI), Life Expectancy, Mean Years of Schooling.
- **Granularity:** Annual, Country-level.
- **Access:** [https://hdr.undp.org/data-center/](https://hdr.undp.org/data-center/).
- **Folder:** `Data/HDR`

### Worldwide Governance Indicators (WGI)

- **Description:** The standard for quantifying institutional strength and stability, crucial for the GovIndex component of the RRS.
- **Data Content:** Political Stability, Government Effectiveness, Rule of Law, Control of Corruption.
- **Granularity:** Annual, Country-level.
- **Access:** [https://www.worldbank.org/en/publication/worldwide-governance-indicators](https://www.worldbank.org/en/publication/worldwide-governance-indicators).
- **Folder:** `Data/WGI`

---

## 3. Enhanced Datasets for Coverage & Quality

These sources are designated as primary replacements for sparse variables identified in the initial data validation.

### World Inequality Database (WID.world) (Primary Inequality Source)

- **Description:** The leading academic database for global income and wealth distribution. It provides robust, annual inequality estimates, replacing the sparse World Bank Gini data.
- **Data Content:** Gini coefficient, Top 10% income share.
- **Granularity:** Annual, Country-level.
- **Access:** [https://wid.world/data/](https://wid.world/data/).
- **Folder:** `Data/WDIworld`

### Barro-Lee Educational Attainment Dataset (Primary Education Source)

- **Description:** The most widely cited cross-country dataset on human capital. Its Mean Years of Schooling variable serves as a comprehensive and well-covered proxy for literacy and educational capacity.
- **Data Content:** Mean Years of Schooling.
- **Granularity:** 5-year intervals (interpolated to annual).
- **Access:** [https://barrolee.github.io/BarroLeeDataSet/OUPdownload.html](https://barrolee.github.io/BarroLeeDataSet/OUPdownload.html).
- **Folder:** `Data/barrolee`

---

## 4. Advanced & Proxy Datasets

These datasets provide composite metrics or high-frequency proxies for resilience modeling.

### ND-GAIN Country Index

- **Description:** The University of Notre Dame's index measuring a country's climate change vulnerability and its readiness to improve resilience. Its components are key inputs for the CRI.
- **Data Content:** ND-GAIN Score, Readiness, Vulnerability (including sub-components for food, water, health).
- **Granularity:** Annual, Country-level.
- **Access:** [https://gain.nd.edu/our-work/country-index/download-data/](https://gain.nd.edu/our-work/country-index/download-data/).
- **Folder:** `Data/NDGain`

### Harmonized Nighttime Lights (NTL)

- **Description:** A harmonized dataset integrating DMSP-OLS and VIIRS satellite data, serving as a high-frequency proxy for economic activity and recovery.
- **Data Content:** Annual average radiance values, aggregated at the country level.
- **Granularity:** Annual, Country-level.
- **Access:** [https://sites.google.com/site/jiaxiongyao16/nighttime-lights-data](https://sites.google.com/site/jiaxiongyao16/nighttime-lights-data) (Aggregated) | [Figshare](https://figshare.com/articles/dataset/Harmonization_of_DMSP_and_VIIRS_nighttime_light_data_from_1992-2018_at_the_global_scale/9828827) (Raw Rasters).
- **Folder:** `Data/HarmonizedNTL`

### INFORM Risk Index

- **Description:** A composite index that fuses Hazard, Vulnerability, and Coping Capacity. Excellent for benchmarking and as a risk variable from 2016 onwards.
- **Data Content:** INFORM Risk score and its three core dimensions.
- **Granularity:** Annual, Country-level (since 2016).
- **Access:** [https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Results-and-data](https://drmkc.jrc.ec.europa.eu/inform-index/INFORM-Risk/Results-and-data).
- **Folder:** `Data/IINFORMRisk`

### IMF World Economic Outlook (WEO)

- **Description:** Provides historical and projected macroeconomic data, serving as a validation source for WDI economic figures.
- **Data Content:** GDP growth, inflation, and other macroeconomic variables.
- **Granularity:** Annual, Country-level.
- **Access:** [https://www.imf.org/en/publications/weo/weo-database](https://www.imf.org/en/publications/weo/weo-database).
- **Folder:** `Data/IMFWEO`
