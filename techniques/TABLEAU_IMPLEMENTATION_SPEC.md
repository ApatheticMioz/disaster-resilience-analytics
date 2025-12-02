# 📊 Tableau Implementation Specification
## Global Disaster Resilience Analytics Platform
### Complete Build Guide — Copy-Paste Ready

---

## Document Purpose

This specification eliminates guesswork. Every sheet, every mark, every color is defined. Follow this document step-by-step to build the dashboard in minimum time with maximum impact.

**Target:** 4 Sheets + 1 Dashboard (A3 Landscape) achieving all R1-R5 requirements from Project Statement.

---

## 📁 Data Source Configuration

### Connection Setup
```
File: unified_resilience_dataset.csv
Type: Text file (CSV)
Records: 4,608 rows
Fields: 102 columns
```

### Data Type Overrides (Set on Import)
| Field | Change To | Reason |
|-------|-----------|--------|
| `year` | Date (Year) | Enable time-series functions |
| `iso3` | Geographic Role → Country/Region (ISO 3166 Alpha-3) | Enable map plotting |
| `region` | String (Dimension) | Categorical grouping |
| `income_group` | String (Dimension) | Categorical grouping |

### Field Organization (Create Folders)
```
📁 Identifiers
   └── iso3, year, region, income_group

📁 Core Indices (Your Custom Metrics)
   └── DII, DII_normalized, RRS, RRS_normalized, CRI, CRI_normalized

📁 Disaster Impact
   └── emdat_*, gdacs_*, desinventar_*, total_disaster_*

📁 Economic
   └── gdp_*, gni_*, inflation_*, govt_*, gini_*

📁 Development
   └── hdi, life_expectancy, education_*, literacy_*, mean_years_schooling

📁 Governance
   └── wgi_*

📁 Climate & Environment
   └── ndgain_*, inform_*, forest_area_pct

📁 Infrastructure
   └── electricity_access_pct, internet_users_pct, water_access_pct, 
       sanitation_access_pct, hospital_beds_per_1k, physicians_per_1k

📁 Proxy Measures
   └── ntl_radiance, ntl_growth, humanitarian_funding_usd
```

---

## 🧮 Calculated Fields (Create These First)

### CF1: Quadrant Category
```tableau
// Name: Quadrant Category
// Purpose: Classify countries into resilience archetypes

IF [DII_normalized] < WINDOW_MEDIAN(SUM([DII_normalized])) 
   AND [RRS_normalized] >= WINDOW_MEDIAN(SUM([RRS_normalized]))
THEN "🛡️ Bulletproof"
ELSEIF [DII_normalized] >= WINDOW_MEDIAN(SUM([DII_normalized])) 
   AND [RRS_normalized] >= WINDOW_MEDIAN(SUM([RRS_normalized]))
THEN "💪 Fighters"  
ELSEIF [DII_normalized] >= WINDOW_MEDIAN(SUM([DII_normalized])) 
   AND [RRS_normalized] < WINDOW_MEDIAN(SUM([RRS_normalized]))
THEN "⚠️ Fragile"
ELSE "🎯 At Risk"
END
```

### CF2: Climate Race Status
```tableau
// Name: Climate Race Status
// Purpose: Track if readiness outpaces vulnerability

IF [ndgain_readiness] > [ndgain_vulnerability] THEN "✅ Winning"
ELSEIF [ndgain_readiness] < [ndgain_vulnerability] THEN "❌ Losing"
ELSE "➖ Even"
END
```

### CF3: Disaster Severity Tier
```tableau
// Name: Disaster Severity Tier
// Purpose: Categorize disaster impact magnitude

IF [total_disaster_deaths] >= 10000 THEN "Catastrophic (10k+)"
ELSEIF [total_disaster_deaths] >= 1000 THEN "Severe (1k-10k)"
ELSEIF [total_disaster_deaths] >= 100 THEN "Moderate (100-1k)"
ELSEIF [total_disaster_deaths] >= 1 THEN "Minor (1-100)"
ELSE "None Recorded"
END
```

### CF4: Governance Tier
```tableau
// Name: Governance Tier
// Purpose: Quartile-based governance classification

IF [wgi_composite] >= 1 THEN "Strong (+1 to +2.5)"
ELSEIF [wgi_composite] >= 0 THEN "Moderate (0 to +1)"
ELSEIF [wgi_composite] >= -1 THEN "Weak (-1 to 0)"
ELSE "Failed (<-1)"
END
```

### CF5: Income-Resilience Gap
```tableau
// Name: CRI vs Income Expected
// Purpose: Identify overperformers and underperformers

IF [income_group] = "High" AND [CRI_normalized] < 50 THEN "Underperformer"
ELSEIF [income_group] = "Low" AND [CRI_normalized] >= 40 THEN "Overperformer"
ELSEIF [income_group] = "Lower-middle" AND [CRI_normalized] >= 50 THEN "Overperformer"
ELSE "Expected"
END
```

### CF6: Recovery Trend (LOD)
```tableau
// Name: CRI 5-Year Change
// Purpose: Calculate resilience trajectory

ZN([CRI_normalized]) - LOOKUP(ZN([CRI_normalized]), -5)
```

---

## 📋 SHEET 1: Global Resilience Map

### Purpose
Geographic overview answering: *"Where is resilience strong/weak globally?"*

### Configuration

| Property | Value |
|----------|-------|
| **Sheet Name** | `1. Global Resilience Map` |
| **Mark Type** | Map (Filled) |
| **Rows** | *empty* (auto-generated latitude) |
| **Columns** | *empty* (auto-generated longitude) |

### Marks Card
| Mark Property | Field | Aggregation |
|---------------|-------|-------------|
| **Geographic** | `iso3` | Dimension |
| **Color** | `CRI_normalized` | AVG |
| **Size** | `total_disaster_deaths` | SUM |
| **Detail** | `region` | Dimension |
| **Tooltip** | *see below* |

### Color Configuration
```
Palette: Red-Yellow-Green Diverging
Steps: 5
Reversed: No (Green = High CRI = Good)
Range: 0 to 100 (fixed)

Color Stops:
  0-20:   #d73027 (Dark Red - Critical)
  20-40:  #fc8d59 (Orange - Vulnerable)
  40-60:  #fee08b (Yellow - Moderate)
  60-80:  #d9ef8b (Light Green - Resilient)
  80-100: #1a9850 (Dark Green - Highly Resilient)
```

### Tooltip (Custom)
```
<b><Country></b> ([iso3])
Region: <region>
Income: <income_group>
─────────────────
Resilience (CRI): <AVG(CRI_normalized)> / 100
Impact (DII): <AVG(DII_normalized)> / 100
Recovery (RRS): <AVG(RRS_normalized)> / 100
─────────────────
Disasters: <SUM(total_disaster_events)>
Deaths: <SUM(total_disaster_deaths)>
HDI: <AVG(hdi)>
Governance: <AVG(wgi_composite)>
```

### Filters (Add to Filter Shelf)
| Filter | Type | Default |
|--------|------|---------|
| `year` | Single Value Slider | 2023 (latest) |
| `region` | Multiple Values (Dropdown) | All selected |
| `income_group` | Multiple Values (Dropdown) | All selected |

### Formatting
- Map Style: Light (Tableau default)
- Country Borders: On, Light Gray
- Coastlines: On
- Base Map: Muted gray (Settings → Map Layers → Washout 60%)
- Title: `"Global Disaster Resilience Index (CRI) — [YEAR]"` (dynamic)

---

## 📋 SHEET 2: Resilience Quadrant Matrix

### Purpose
Analytical scatter answering: *"Which countries are fighters vs fragile?"*

### Configuration

| Property | Value |
|----------|-------|
| **Sheet Name** | `2. Resilience Quadrant Matrix` |
| **Mark Type** | Circle |
| **Rows** | `AVG(RRS_normalized)` |
| **Columns** | `AVG(DII_normalized)` |

### Marks Card
| Mark Property | Field | Aggregation |
|---------------|-------|-------------|
| **Detail** | `iso3` | Dimension |
| **Color** | `region` | Dimension |
| **Size** | `AVG(hdi)` | Measure |
| **Label** | `iso3` | Dimension (show for extremes only) |
| **Tooltip** | *see below* |

### Size Legend
```
Range: 0.3 to 0.95 (HDI values)
Minimum bubble: 5px
Maximum bubble: 40px
```

### Color Configuration
```
Palette: Tableau 10 (categorical)
Assignments:
  Africa        → #e15759 (Red)
  Americas      → #4e79a7 (Blue)  
  Asia          → #f28e2b (Orange)
  Europe        → #76b7b2 (Teal)
  Oceania       → #59a14f (Green)
```

### Reference Lines (Analytics Pane)
| Reference Line | Axis | Value | Style |
|----------------|------|-------|-------|
| Median DII | X-axis | `MEDIAN([DII_normalized])` | Dashed, Gray, 1px |
| Median RRS | Y-axis | `MEDIAN([RRS_normalized])` | Dashed, Gray, 1px |

### Quadrant Annotations (Manual)
```
Position: Center of each quadrant
Font: Tableau Medium, 12pt, Gray

Top-Left:     "🛡️ BULLETPROOF" + "Low Impact, High Recovery"
Top-Right:    "💪 FIGHTERS" + "High Impact, High Recovery"
Bottom-Right: "⚠️ FRAGILE" + "High Impact, Low Recovery"
Bottom-Left:  "🎯 AT RISK" + "Low Impact, Low Recovery"
```

### Tooltip (Custom)
```
<b><iso3></b>
<region> | <income_group>
─────────────────
DII (Impact): <AVG(DII_normalized)>
RRS (Recovery): <AVG(RRS_normalized)>
CRI (Resilience): <AVG(CRI_normalized)>
─────────────────
HDI: <AVG(hdi)>
Governance: <AVG(wgi_composite)>
GDP/capita: $<AVG(gdp_per_capita_best)>
─────────────────
Quadrant: <Quadrant Category>
```

### Axis Configuration
| Axis | Title | Range | Format |
|------|-------|-------|--------|
| X (DII) | "Disaster Impact Index (Higher = Worse)" | 0-100 | Number, 0 decimals |
| Y (RRS) | "Resilience Recovery Score (Higher = Better)" | 0-100 | Number, 0 decimals |

### Key Countries to Label
Force labels on (Right-click → Mark Label → Always Show):
- `JPN` (top-right: Fighter)
- `HTI` (bottom-right: Fragile)
- `NOR` (top-left: Bulletproof)
- `VEN` (bottom area: comparison)
- `CHL` (upper area: comparison)

---

## 📋 SHEET 3: Resilience Evolution Timeline

### Purpose
Temporal analysis answering: *"How has resilience changed over 24 years?"*

### Configuration

| Property | Value |
|----------|-------|
| **Sheet Name** | `3. Resilience Evolution Timeline` |
| **Mark Type** | Line |
| **Rows** | `AVG(CRI_normalized)` |
| **Columns** | `YEAR(year)` |

### Marks Card
| Mark Property | Field | Aggregation |
|---------------|-------|-------------|
| **Color** | `region` | Dimension |
| **Path** | `YEAR(year)` | — |
| **Detail** | `region` | Dimension |
| **Tooltip** | *see below* |

### Line Configuration
```
Line Width: 2px
Line Style: Solid
Markers: On (circle, 4px) - for individual year points
```

### Color Configuration
```
Same as Sheet 2 (Tableau 10 by region)
Apply consistent palette across all sheets
```

### Axis Configuration
| Axis | Title | Range | Format |
|------|-------|-------|--------|
| X | "Year" | 2000-2023 | Year only |
| Y | "Average Composite Resilience Index" | 0-80 (auto) | Number, 1 decimal |

### Reference Lines
| Reference Line | Purpose | Style |
|----------------|---------|-------|
| Global Average (per year) | `AVG([CRI_normalized])` | Dotted Black |
| 2010 (Haiti Earthquake) | Constant = 2010 | Vertical, Red, Labeled |
| 2020 (COVID-19) | Constant = 2020 | Vertical, Purple, Labeled |

### Tooltip
```
<b><region></b>
Year: <YEAR(year)>
─────────────────
Average CRI: <AVG(CRI_normalized)>
Countries: <COUNTD(iso3)>
─────────────────
Avg HDI: <AVG(hdi)>
Avg Governance: <AVG(wgi_composite)>
Total Deaths: <SUM(total_disaster_deaths)>
```

### Annotations (Manual - Key Events)
```
2004: "Indian Ocean Tsunami" (pointer to Asia line dip)
2008: "Cyclone Nargis / Sichuan" (pointer to Asia)
2010: "Haiti Earthquake" (pointer to Americas dip)
2011: "Tōhoku Earthquake" (pointer to Asia)
2020: "COVID-19 Global Shock" (pointer to global dip)
```

### Filters
| Filter | Configuration |
|--------|---------------|
| `region` | Apply from Sheet 1 (linked) |
| `income_group` | Apply from Sheet 1 (linked) |

---

## 📋 SHEET 4: Governance vs Wealth Analysis

### Purpose
Correlation analysis answering: *"Does money or governance drive resilience?"*

### Configuration

| Property | Value |
|----------|-------|
| **Sheet Name** | `4. Governance vs Wealth` |
| **Mark Type** | Circle |
| **Rows** | `AVG(CRI_normalized)` |
| **Columns** | `AVG(wgi_composite)` |

### Marks Card
| Mark Property | Field | Aggregation |
|---------------|-------|-------------|
| **Detail** | `iso3` | Dimension |
| **Color** | `income_group` | Dimension |
| **Size** | `AVG(gdp_per_capita_best)` | Measure |
| **Tooltip** | *see below* |

### Color Configuration (Income Groups)
```
Palette: Sequential Blues (4 steps)
Assignments:
  Low           → #c6dbef (Light Blue)
  Lower-middle  → #6baed6 (Medium Blue)
  Upper-middle  → #2171b5 (Blue)
  High          → #08306b (Dark Blue)
```

### Trend Line (Analytics Pane)
```
Type: Linear
Scope: Entire Table
Show Confidence Bands: Yes (95%)
Show R-squared: Yes (display in annotation)
Color: Gray, Dashed
```

### Axis Configuration
| Axis | Title | Range | Format |
|------|-------|-------|--------|
| X | "Governance Quality (WGI Composite)" | -2.5 to +2.5 | Number, 2 decimals |
| Y | "Resilience Index (CRI)" | 0-100 | Number, 0 decimals |

### Annotations
```
Top annotation:
"R² = 0.50 (Governance explains 50% of resilience variance)"

Label quadrants:
Top-Right: "Strong Governance + High Resilience"
Bottom-Left: "Weak Governance + Low Resilience"
Top-Left: "Wealth Without Governance" (highlight exceptions)
```

### Tooltip
```
<b><iso3></b>
<region> | <income_group>
─────────────────
CRI: <AVG(CRI_normalized)> / 100
Governance (WGI): <AVG(wgi_composite)>
GDP/capita: $<AVG(gdp_per_capita_best)>
─────────────────
HDI: <AVG(hdi)>
RRS: <AVG(RRS_normalized)>
─────────────────
The Insight: 
<IF governance high AND CRI high>
"Governance drives resilience"
<ELSE IF gdp high AND CRI low>
"Wealth alone isn't enough"
```

### Key Comparisons to Highlight
```
Chile (CHL) vs Venezuela (VEN):
- Similar GDP range (~$10-15k)
- Opposite governance scores
- Opposite CRI outcomes
→ Add annotation: "Same wealth, different governance, different resilience"

Rwanda (RWA) vs Equatorial Guinea (GNQ):
- Rwanda: Low GDP, improving governance, rising CRI
- Eq Guinea: High GDP (oil), poor governance, low CRI
→ Add annotation: "Oil doesn't buy resilience"
```

---

## 📐 DASHBOARD: Main Dashboard

### Canvas Configuration

| Property | Value |
|----------|-------|
| **Dashboard Name** | `Global Disaster Resilience Analytics` |
| **Size** | Custom: 1400 × 900 px (A3 Landscape ratio) |
| **Device Layout** | Desktop (primary) |
| **Background** | #f5f5f5 (Light Gray) |

### Layout Grid (12-Column System)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  HEADER (Full Width)                                                    │
│  Title: "Global Disaster Resilience Analytics Platform"                │
│  Subtitle: "192 Countries | 2000-2023 | 13 Data Sources"               │
├─────────────────────────────────────────────────────────────────────────┤
│  FILTERS BAR (Full Width)                                               │
│  [Year Slider] [Region Dropdown] [Income Group Dropdown]               │
├────────────────────────────────────┬────────────────────────────────────┤
│                                    │                                    │
│  SHEET 1: Global Map               │  SHEET 2: Quadrant Matrix          │
│  (8 columns)                       │  (4 columns)                       │
│                                    │                                    │
│  Primary view - geographic         │  Analytical view - classification  │
│  overview of CRI worldwide         │  of countries into archetypes      │
│                                    │                                    │
├────────────────────────────────────┴────────────────────────────────────┤
│                                                                          │
│  SHEET 3: Timeline (6 columns)     │  SHEET 4: Governance (6 columns)  │
│                                    │                                    │
│  Temporal evolution by region      │  Governance vs Resilience          │
│                                    │  correlation with wealth           │
│                                    │                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  FOOTER: Data Sources + Formula Summary                                 │
│  "Data: EM-DAT, ND-GAIN, WGI, HDR, WDI, GDACS, INFORM | CRI = A/(E+V)" │
└─────────────────────────────────────────────────────────────────────────┘
```

### Exact Pixel Dimensions

| Element | Position (x, y) | Size (w × h) |
|---------|-----------------|--------------|
| Header | (0, 0) | 1400 × 60 |
| Filters Bar | (0, 60) | 1400 × 50 |
| Sheet 1 (Map) | (10, 120) | 850 × 380 |
| Sheet 2 (Quadrant) | (870, 120) | 520 × 380 |
| Sheet 3 (Timeline) | (10, 510) | 685 × 340 |
| Sheet 4 (Governance) | (705, 510) | 685 × 340 |
| Footer | (0, 860) | 1400 × 40 |

### Interactive Actions

#### Action 1: Map → Filter All
```
Name: "Select Country from Map"
Source: Sheet 1 (Global Resilience Map)
Target: All sheets (Sheet 2, 3, 4)
Run on: Select
Clear selection: Show all values
Fields: iso3
```

#### Action 2: Quadrant → Highlight
```
Name: "Highlight Quadrant Selection"
Source: Sheet 2 (Resilience Quadrant Matrix)
Target: Sheet 1, Sheet 3
Run on: Hover
Highlight: region, income_group
```

#### Action 3: Timeline → Filter Year
```
Name: "Focus Year from Timeline"
Source: Sheet 3 (Timeline)
Target: Sheet 1, Sheet 2, Sheet 4
Run on: Select
Fields: year
```

### Filter Configuration

#### Year Filter
```
Type: Single Value Slider
Range: 2000-2023
Default: 2023
Apply to: All sheets using this data source
Position: Filters Bar, Left
Width: 400px
```

#### Region Filter
```
Type: Multiple Values (Dropdown)
Values: Africa, Americas, Asia, Europe, Oceania
Default: All
Apply to: All sheets
Position: Filters Bar, Center
Width: 200px
```

#### Income Group Filter
```
Type: Multiple Values (Dropdown)  
Values: Low, Lower-middle, Upper-middle, High
Default: All
Apply to: All sheets
Position: Filters Bar, Right
Width: 200px
```

### Header Design

```
Background: #2c3e50 (Dark Blue-Gray)
Height: 60px

Title:
  Text: "Global Disaster Resilience Analytics Platform"
  Font: Tableau Bold, 24pt, White
  Position: Left-aligned, 20px padding

Subtitle:
  Text: "Quantifying National Resilience | 192 Countries | 2000-2023"
  Font: Tableau Regular, 12pt, #bdc3c7 (Light Gray)
  Position: Below title

Logo Area (Right):
  Text: "GDHRA" (or university logo)
  Position: Right-aligned, 20px padding
```

### Footer Design

```
Background: #ecf0f1 (Light Gray)
Height: 40px

Left Section:
  Text: "Data Sources: EM-DAT | ND-GAIN | WGI | HDR | WDI | GDACS | INFORM Risk | IMF WEO"
  Font: Tableau Regular, 9pt, #7f8c8d

Right Section:
  Text: "CRI = Adaptive Capacity / (Exposure + Vulnerability) | © 2025"
  Font: Tableau Regular, 9pt, #7f8c8d
```

---

## 🎨 Global Formatting Standards

### Typography
| Element | Font | Size | Color |
|---------|------|------|-------|
| Dashboard Title | Tableau Bold | 24pt | White (#ffffff) |
| Sheet Titles | Tableau Semibold | 14pt | Dark Gray (#2c3e50) |
| Axis Titles | Tableau Medium | 11pt | Gray (#5d6d7e) |
| Axis Labels | Tableau Regular | 10pt | Gray (#7f8c8d) |
| Tooltips | Tableau Regular | 10pt | Black (#000000) |
| Annotations | Tableau Light | 9pt | Gray (#95a5a6) |
| Data Labels | Tableau Regular | 9pt | Varies by background |

### Color Consistency

**CRI Gradient (Use Everywhere for Resilience)**
```
Critical:    #d73027 (0-20)
Vulnerable:  #fc8d59 (20-40)
Moderate:    #fee08b (40-60)
Resilient:   #d9ef8b (60-80)
Excellent:   #1a9850 (80-100)
```

**Region Colors (Use Everywhere for Region)**
```
Africa:   #e15759
Americas: #4e79a7
Asia:     #f28e2b
Europe:   #76b7b2
Oceania:  #59a14f
```

**Income Colors (Use Everywhere for Income)**
```
Low:          #c6dbef
Lower-middle: #6baed6
Upper-middle: #2171b5
High:         #08306b
```

### Borders & Spacing
```
Sheet Borders: None (clean look)
Sheet Padding: 10px all sides
Dashboard Padding: 10px outer margin
Element Spacing: 10px between sheets
Shadow: None (flat design)
```

---

## ✅ Pre-Submission Checklist

### Data Validation
- [ ] All 4,608 records loading correctly
- [ ] No null values breaking visualizations
- [ ] ISO3 codes recognized as geographic
- [ ] Year field recognized as date

### Sheet Validation
- [ ] Sheet 1: Map shows all 192 countries with color
- [ ] Sheet 2: Scatter has 4 clear quadrants with reference lines
- [ ] Sheet 3: Lines show 5 regions over 24 years
- [ ] Sheet 4: Trend line displays with R² value

### Dashboard Validation
- [ ] All filters work across all sheets
- [ ] Click on map filters other views
- [ ] Tooltips display correctly formatted
- [ ] No overlapping elements
- [ ] Title and footer visible

### Storytelling Validation
- [ ] Can answer "Which country is most resilient?" in 3 seconds (Map)
- [ ] Can identify Haiti vs Japan difference (Quadrant + Timeline)
- [ ] Can see governance matters more than wealth (Governance chart)
- [ ] Year slider reveals meaningful changes (2010, 2020 events visible)

### Export Checklist
- [ ] Save as Tableau Packaged Workbook (.twbx)
- [ ] Publish to Tableau Public (if required)
- [ ] Test all interactions after publish
- [ ] Take screenshots for report (4 sheets + 1 dashboard = 5 images)

---

## 📸 Screenshots Needed for Report

| Screenshot | Purpose | Resolution |
|------------|---------|------------|
| Full Dashboard | Main deliverable image | 1400 × 900 |
| Map Close-up | Geographic analysis evidence | 850 × 400 |
| Quadrant with Labels | Archetype classification | 600 × 500 |
| Timeline with Annotations | Temporal analysis | 700 × 350 |
| Governance Scatter with Trend | Correlation evidence | 700 × 350 |

---

## 🚀 Build Order (Recommended Sequence)

### Phase 1: Foundation (30 min)
1. Import CSV
2. Set data types (iso3 → geographic, year → date)
3. Create all 6 calculated fields
4. Organize into folders

### Phase 2: Sheet 1 - Map (20 min)
1. Drag iso3 to canvas (auto-generates map)
2. Drag CRI_normalized to Color
3. Configure color palette (Red-Yellow-Green)
4. Add total_disaster_deaths to Size
5. Build tooltip
6. Add filters

### Phase 3: Sheet 2 - Quadrant (25 min)
1. Create scatter (DII vs RRS)
2. Add iso3 to Detail
3. Add region to Color
4. Add hdi to Size
5. Add reference lines (median X, median Y)
6. Label key countries
7. Add quadrant annotations

### Phase 4: Sheet 3 - Timeline (20 min)
1. Create line chart (Year vs CRI)
2. Add region to Color
3. Add reference lines for key events
4. Add annotations for disasters
5. Link filters

### Phase 5: Sheet 4 - Governance (20 min)
1. Create scatter (WGI vs CRI)
2. Add income_group to Color
3. Add GDP to Size
4. Add trend line with R²
5. Highlight key comparisons

### Phase 6: Dashboard Assembly (30 min)
1. Create dashboard canvas (1400 × 900)
2. Add header container
3. Add filters bar
4. Place sheets in grid layout
5. Configure filter actions
6. Add highlight actions
7. Add footer
8. Final formatting pass

### Phase 7: Polish & Export (15 min)
1. Test all interactions
2. Fix any tooltip issues
3. Ensure color consistency
4. Export .twbx
5. Capture screenshots

**Total Estimated Time: 2.5 - 3 hours**

---

*Specification Version 1.0*  
*Ready for Implementation*  
*102 variables → 4 sheets → 1 dashboard → Infinite insight*
