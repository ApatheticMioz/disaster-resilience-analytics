# Tableau Implementation Specification
## Global Disaster Resilience Analytics Platform

---

## Document Purpose

This specification provides the technical blueprint for building the Tableau dashboard. All values, medians, and ranges are calculated dynamically by Tableau — nothing is hard-coded.

**Alignment with Project Requirements:**
- R1 (Data Fusion): Dataset integrates 13 sources — visualizations leverage this breadth
- R4 (Comparative Analysis): Sheets enable Time, Geography, Disaster Type, Socio-economic comparison
- R5 (Analytical Storytelling): Each sheet answers one of the three core questions

---

## Data Source

```
File: unified_resilience_dataset.csv
Primary Key: (iso3, year)
```

### Data Type Configuration
| Field | Set To | Reason |
|-------|--------|--------|
| `iso3` | Geographic Role: Country/Region (ISO-3) | Enable map plotting |
| `year` | Date (Year) | Enable time-series |
| `region` | Dimension | Categorical grouping |
| `income_group` | Dimension | Categorical grouping |

### Key Fields for Visualization
| Category | Fields |
|----------|--------|
| Core Indices | `DII`, `DII_normalized`, `RRS`, `RRS_normalized`, `CRI`, `CRI_normalized` |
| Disaster Impact | `total_disaster_deaths`, `total_disaster_affected`, `total_disaster_events` |
| Risk Metrics | `inform_risk`, `inform_hazard`, `inform_vulnerability` |
| Governance | `wgi_composite`, `wgi_gov_effectiveness`, `wgi_political_stability` |
| Development | `hdi`, `gdp_per_capita_best`, `life_expectancy` |
| Climate | `ndgain_readiness`, `ndgain_vulnerability`, `ndgain_score` |

---

## Calculated Fields

### Quadrant Classification
```
// Name: Resilience Quadrant
// Purpose: Classify countries based on risk vs recovery

IF [inform_risk] < MEDIAN([inform_risk]) AND [RRS_normalized] >= MEDIAN([RRS_normalized])
  THEN "Low Risk, High Recovery"
ELSEIF [inform_risk] >= MEDIAN([inform_risk]) AND [RRS_normalized] >= MEDIAN([RRS_normalized])
  THEN "High Risk, High Recovery"
ELSEIF [inform_risk] >= MEDIAN([inform_risk]) AND [RRS_normalized] < MEDIAN([RRS_normalized])
  THEN "High Risk, Low Recovery"
ELSE "Low Risk, Low Recovery"
END
```

### Governance Category
```
// Name: Governance Tier
// Purpose: Quartile-based governance classification

IF [wgi_composite] >= PERCENTILE([wgi_composite], 0.75) THEN "Strong"
ELSEIF [wgi_composite] >= MEDIAN([wgi_composite]) THEN "Moderate"
ELSEIF [wgi_composite] >= PERCENTILE([wgi_composite], 0.25) THEN "Weak"
ELSE "Critical"
END
```

### Disaster Severity Category
```
// Name: Disaster Severity
// Purpose: Classify by death toll magnitude

IF [total_disaster_deaths] >= 10000 THEN "Catastrophic"
ELSEIF [total_disaster_deaths] >= 1000 THEN "Severe"
ELSEIF [total_disaster_deaths] >= 100 THEN "Moderate"
ELSEIF [total_disaster_deaths] > 0 THEN "Minor"
ELSE "None"
END
```

---

## Sheet Specifications

### Sheet 1: Global Resilience Map

**Analytical Purpose:** 
- R4 requirement: Geographic comparison
- R5 question: "Which nations show high exposure but low vulnerability?"

**Configuration:**
| Property | Value |
|----------|-------|
| Sheet Name | Global Resilience Map |
| Mark Type | Filled Map |
| Geographic Field | `iso3` |

**Marks Card:**
| Property | Field | Notes |
|----------|-------|-------|
| Color | `AVG(CRI_normalized)` | Diverging palette: Red (low) to Green (high) |
| Tooltip | See below | |

**Color Palette:**
- Type: Diverging (Red-Yellow-Green)
- Stepped: 5 steps
- Let Tableau determine range from data

**Tooltip:**
```
Country: <iso3>
Region: <region>
Income Group: <income_group>

Resilience (CRI): <AVG(CRI_normalized)>
Impact (DII): <AVG(DII_normalized)>
Recovery (RRS): <AVG(RRS_normalized)>

Disasters: <SUM(total_disaster_events)>
Deaths: <SUM(total_disaster_deaths)>
Governance: <AVG(wgi_composite)>
```

**Filters:**
- `year` — Single value slider
- `region` — Multi-select dropdown
- `income_group` — Multi-select dropdown

---

### Sheet 2: Risk vs Recovery Matrix

**Analytical Purpose:**
- R5 question: "Which nations show high exposure but low vulnerability?"
- Scatter plot as suggested in Project Statement

**Configuration:**
| Property | Value |
|----------|-------|
| Sheet Name | Risk vs Recovery Matrix |
| Mark Type | Circle |
| Columns | `AVG(inform_risk)` |
| Rows | `AVG(RRS_normalized)` |

**Marks Card:**
| Property | Field | Notes |
|----------|-------|-------|
| Detail | `iso3` | One point per country |
| Color | `region` | Categorical palette |
| Size | `AVG(hdi)` | Larger = higher development |
| Label | `iso3` | Show for selected/filtered only |

**Reference Lines (from Analytics Pane):**
| Line | Axis | Computation |
|------|------|-------------|
| Median | X-axis | Median of `inform_risk` |
| Median | Y-axis | Median of `RRS_normalized` |

**Axis Titles:**
- X: "INFORM Risk Index (Higher = More Exposed)"
- Y: "Resilience Recovery Score (Higher = Better Recovery)"

**Quadrant Interpretation:**
- Top-Left: Low Risk, High Recovery — stable nations
- Top-Right: High Risk, High Recovery — resilient despite exposure
- Bottom-Right: High Risk, Low Recovery — fragile, need intervention
- Bottom-Left: Low Risk, Low Recovery — underdeveloped capacity

**Tooltip:**
```
<iso3>
Region: <region> | Income: <income_group>

INFORM Risk: <AVG(inform_risk)>
Recovery Score: <AVG(RRS_normalized)>
Resilience (CRI): <AVG(CRI_normalized)>

HDI: <AVG(hdi)>
Governance: <AVG(wgi_composite)>
GDP per capita: <AVG(gdp_per_capita_best)>
```

---

### Sheet 3: Resilience Evolution Timeline

**Analytical Purpose:**
- R4 requirement: Temporal evolution of resilience
- R5 question: "How does resilience evolve alongside climate risk?"

**Configuration:**
| Property | Value |
|----------|-------|
| Sheet Name | Resilience Timeline |
| Mark Type | Line |
| Columns | `YEAR(year)` |
| Rows | `AVG(CRI_normalized)` |

**Marks Card:**
| Property | Field | Notes |
|----------|-------|-------|
| Color | `region` | Same palette as Sheet 2 |
| Path | `YEAR(year)` | Connect points chronologically |
| Detail | `region` | One line per region |

**Alternative View — Country Level:**
Add `iso3` to Detail and filter to specific countries for drill-down.

**Axis Configuration:**
- X: Year (Tableau auto-determines range from data)
- Y: Let Tableau auto-scale based on data

**Filters:**
- `region` — Linked to dashboard filter
- `income_group` — Linked to dashboard filter
- `iso3` — Optional, for country-specific analysis

**Tooltip:**
```
<region>
Year: <YEAR(year)>

Average CRI: <AVG(CRI_normalized)>
Average HDI: <AVG(hdi)>
Average Governance: <AVG(wgi_composite)>
Total Deaths (this year): <SUM(total_disaster_deaths)>
```

---

### Sheet 4: Governance vs Resilience

**Analytical Purpose:**
- R5 question: "Do wealthier nations recover faster, or does governance matter more?"
- Scatter plot as suggested in Project Statement

**Configuration:**
| Property | Value |
|----------|-------|
| Sheet Name | Governance vs Resilience |
| Mark Type | Circle |
| Columns | `AVG(wgi_composite)` |
| Rows | `AVG(CRI_normalized)` |

**Marks Card:**
| Property | Field | Notes |
|----------|-------|-------|
| Detail | `iso3` | One point per country |
| Color | `income_group` | Shows wealth dimension |
| Size | `AVG(gdp_per_capita_best)` | Bubble size = wealth |

**Reference Lines:**
| Line | Type | Purpose |
|------|------|---------|
| Trend Line | Linear | Show correlation, display R-squared |

**Axis Titles:**
- X: "Governance Quality (WGI Composite)"
- Y: "Composite Resilience Index"

**Key Insight:**
The trend line R-squared value answers the question directly — if governance explains more variance than GDP (visible in bubble sizes not aligning with Y position), governance matters more.

**Tooltip:**
```
<iso3>
Region: <region> | Income: <income_group>

CRI: <AVG(CRI_normalized)>
Governance (WGI): <AVG(wgi_composite)>
GDP per capita: <AVG(gdp_per_capita_best)>
HDI: <AVG(hdi)>
```

---

## Dashboard Specification

### Layout

**Size:** 1400 x 900 pixels (16:10 aspect ratio, suitable for presentation)

**Structure:**
```
+------------------------------------------------------------------+
| HEADER: Title + Subtitle                                          |
+------------------------------------------------------------------+
| FILTER BAR: [Year] [Region] [Income Group]                        |
+---------------------------+--------------------------------------+
|                           |                                      |
|  Sheet 1: Map             |  Sheet 2: Risk vs Recovery           |
|  (Primary geographic      |  (Quadrant analysis)                 |
|   overview)               |                                      |
|                           |                                      |
+---------------------------+--------------------------------------+
|                           |                                      |
|  Sheet 3: Timeline        |  Sheet 4: Governance                 |
|  (Temporal evolution)     |  (Correlation analysis)              |
|                           |                                      |
+---------------------------+--------------------------------------+
| FOOTER: Data sources, formula references                          |
+------------------------------------------------------------------+
```

### Dashboard Actions

**Action 1: Filter by Country Selection**
- Source: Sheet 1 (Map)
- Target: Sheets 2, 3, 4
- Trigger: Select
- Action: Filter on `iso3`
- Clear: Shows all values

**Action 2: Highlight by Region**
- Source: Sheet 2 (Scatter)
- Target: All sheets
- Trigger: Hover
- Action: Highlight on `region`

**Action 3: Filter by Year**
- Source: Sheet 3 (Timeline)
- Target: Sheets 1, 2, 4
- Trigger: Select
- Action: Filter on `year`

### Global Filters

| Filter | Type | Apply To |
|--------|------|----------|
| `year` | Single Value Slider | All sheets |
| `region` | Multi-select Dropdown | All sheets |
| `income_group` | Multi-select Dropdown | All sheets |

### Header Content
```
Title: "Global Disaster Resilience Analytics"
Subtitle: "Exploring Risk, Recovery, and Resilience Across Nations"
```

### Footer Content
```
Data Sources: EM-DAT, ND-GAIN, WGI, HDR, WDI, GDACS, INFORM Risk, IMF WEO
Indices: CRI = Adaptive Capacity / (Exposure + Vulnerability)
```

---

## Color Standards

**Maintain consistency across all sheets:**

| Variable | Palette Type | Notes |
|----------|--------------|-------|
| `CRI_normalized` | Diverging (Red-Yellow-Green) | Red = low resilience, Green = high |
| `region` | Categorical (Tableau 10) | Same color per region in all sheets |
| `income_group` | Sequential (Blues) | Light = Low income, Dark = High income |

---

## Storytelling Flow

The dashboard is designed to answer the three R5 questions in sequence:

1. **Map (Sheet 1):** "Where are the resilient vs vulnerable nations?"
   - User sees global distribution, identifies geographic patterns
   
2. **Scatter (Sheet 2):** "Which nations show high exposure but low vulnerability?"
   - Quadrant analysis reveals countries that defy expectations
   - Click on a country to filter other views

3. **Timeline (Sheet 3):** "How does resilience evolve over time?"
   - Shows trajectory by region
   - Reveals trends, potential inflection points

4. **Governance (Sheet 4):** "Does governance matter more than wealth?"
   - Trend line shows correlation strength
   - Bubble size (GDP) vs Y-position (CRI) answers the question

---

## Implementation Checklist

### Data Preparation
- [ ] Import CSV, verify all rows load
- [ ] Set `iso3` geographic role
- [ ] Set `year` as date type
- [ ] Create calculated fields
- [ ] Organize fields into folders

### Sheet Building
- [ ] Sheet 1: Map with CRI color
- [ ] Sheet 2: Scatter with median reference lines
- [ ] Sheet 3: Line chart by region
- [ ] Sheet 4: Scatter with trend line

### Dashboard Assembly
- [ ] Create dashboard at specified size
- [ ] Place 4 sheets in grid layout
- [ ] Add filter controls to top
- [ ] Configure dashboard actions
- [ ] Add header and footer text

### Validation
- [ ] All filters work across sheets
- [ ] Click on map filters other views
- [ ] Trend line shows R-squared
- [ ] Colors are consistent across sheets

---

## Alignment with Project Statement

| Requirement | How Dashboard Addresses It |
|-------------|---------------------------|
| R4: Time comparison | Sheet 3 (Timeline) |
| R4: Geography comparison | Sheet 1 (Map) |
| R4: Socio-economic groups | `income_group` filter + Sheet 4 coloring |
| R4: Disaster types | Available via disaster count fields, can add filter |
| R5: High exposure, low vulnerability | Sheet 2 (Quadrant analysis) |
| R5: Wealth vs governance | Sheet 4 (Trend line + bubble size) |
| R5: Resilience evolution | Sheet 3 (Timeline) |
| Suggested: Geo-maps | Sheet 1 |
| Suggested: Time-series | Sheet 3 |
| Suggested: Scatter/bubble plots | Sheets 2 and 4 |
| Suggested: Interactive filters | Year, Region, Income Group |
| At least 3 analytical views | 4 sheets provided |

---

*Specification aligned with Project Statement requirements.*
*All computations performed dynamically by Tableau.*
