# Disaster Resilience Analytics

A comprehensive data analytics platform for quantifying and visualizing global disaster resilience at national and regional scales.

[![Status](https://img.shields.io/badge/Status-Archived%20%2F%20Refactored-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)]()

## Overview

The **Disaster Resilience Analytics** platform is a data intelligence system designed to integrate historical disaster data, socio-economic indicators, and environmental information to reveal how societies prepare for, absorb, and recover from disasters. Developed for the Global Disaster and Humanitarian Response Agency (GDHRA), this platform enables decision-makers to:

- Identify which countries are most vulnerable to disasters
- Analyze recovery speed and patterns
- Understand what socio-economic and governance factors drive resilience

### Key Features

- **ETL Pipeline**: Comprehensive data processing pipeline integrating 13 heterogeneous datasets
- **Derived Indices**: Three novel composite indices for disaster resilience analysis
  - **DII** (Disaster Impact Index): Measures disaster disruption relative to a country's wealth and size
  - **RRS** (Resilience Recovery Score): Quantifies recovery capacity
  - **CRI** (Composite Resilience Index): Combines adaptive capacity, exposure, and vulnerability
- **Interactive Dashboard**: 5-view Tableau dashboard with LOD expressions and Set Actions
- **191 Countries**: Analysis spanning 2000-2024 with 4,500+ country-year records

## Project Structure

```
disaster-resilience-analytics/
├── build_unified_dataset.py    # Main ETL pipeline (~1,750 lines)
├── run_diagnostics.py          # Data quality diagnostics and validation
├── Book2.twb                   # Tableau workbook (source)
├── Book2.twbx                  # Tableau packaged workbook
├── Data/                       # Data sources (13 datasets)
│   ├── emdat/                  # EM-DAT disaster database
│   ├── NDGain/                 # ND-GAIN climate resilience index
│   ├── WDI/                    # World Bank Development Indicators
│   ├── WGI/                    # Worldwide Governance Indicators
│   ├── HDR/                    # Human Development Reports
│   ├── GDACS/                  # Global Disaster Alert Coordination
│   ├── IMFWEO/                 # IMF World Economic Outlook
│   ├── FTS/                    # Financial Tracking Service
│   ├── IINFORMRisk/            # INFORM Risk Index
│   ├── desinventarSandai/      # DesInventar granular losses
│   ├── HarmonizedNTL/          # Nighttime lights (economic proxy)
│   ├── barrolee/               # Educational attainment data
│   └── unified_resilience_dataset.csv  # Output dataset
├── report/                     # Technical report (LaTeX)
│   └── main.tex                # IEEE-format report
├── techniques/                 # Visualization techniques documentation
├── ProjectInstructions/        # Original project requirements
├── authors.txt                 # Contribution statement
├── LICENSE                     # MIT License
├── CONTRIBUTING.md             # Contribution guidelines
└── CHANGELOG.md                # Version history
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ApatheticMioz/DAV_Project_Semester_5.git
   cd DAV_Project_Semester_5
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install pandas numpy pycountry
   ```

## Usage

### Build Unified Dataset

Run the ETL pipeline to process all data sources and generate the unified resilience dataset:

```bash
python build_unified_dataset.py
```

**Output:**
- `Data/unified_resilience_dataset.csv` - Main dataset with derived indices
- `Data/coverage_matrix.csv` - Variable-level coverage statistics
- `Data/validation_report.txt` - Detailed validation report

### Run Diagnostics

Generate data quality diagnostics and validation reports:

```bash
python run_diagnostics.py
```

### Tableau Dashboard

1. Open `Book2.twbx` in Tableau Desktop or Tableau Public
2. The dashboard includes 5 coordinated analytical views:
   - Geographic choropleth map of CRI
   - Temporal evolution of resilience indices
   - Factor analysis scatterplots
   - Country comparison views
   - Disaster type breakdown

## Data Sources

| Source | Description | Key Variables |
|--------|-------------|---------------|
| ND-GAIN | Climate Resilience Index | `ndgain_score`, `ndgain_readiness` |
| EM-DAT | Disaster Impact Database | `disaster_count`, `disaster_deaths` |
| World Bank WDI | Development Indicators | `gdp_per_capita`, `population` |
| WGI | Governance Indicators | `wgi_rule_of_law`, `wgi_gov_effectiveness` |
| HDR | Human Development | `hdi` |
| INFORM Risk | Risk Assessment | `inform_risk`, `inform_vulnerability` |
| IMF WEO | Economic Outlook | `gdp_growth`, `inflation_rate` |

## Authors

- **M. Abdullah Ali** (23i-2523) - ETL Pipeline & Feature Engineering
- **M. Abdullah Aamir** (23i-2538) - Tableau Dashboard & Data Collection

See [authors.txt](authors.txt) for detailed contribution breakdown.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- FAST-NUCES, Department of Data Science
- Global Disaster and Humanitarian Response Agency (GDHRA) for the project framework
- All open data providers: EM-DAT, World Bank, UNDP, ND-GAIN, and others

---

**Status:** Archived / Refactored
