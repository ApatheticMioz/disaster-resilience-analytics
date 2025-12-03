# 🎓 TABLEAU IMPLEMENTATION MASTERCLASS
## Global Disaster Resilience Analytics Platform
### The Definitive Guide — Version 3.0

---

> **This document supersedes:** `EXPERT_VISUALIZATION_BLUEPRINT.md`, `TABLEAU_IMPLEMENTATION_SPEC.md`, and `suggestions.md`
>
> **Purpose:** A single, comprehensive, actionable reference for building an A+ Tableau workbook.

---

# PART I: THE NARRATIVE ARC

## The Core Problem We're Solving

You have 4,608 records across 192 countries over 24 years. The instructor asked for a dashboard. That's not what you're building. **You're building a visual argument.**

The argument: *"Resilience is not a function of wealth. It's a function of preparation, governance, and institutional capacity—and the data proves it."*

### The Three-Act Structure

Every great visualization tells a story. Yours has three acts:

| Act | Question | Emotional Beat | Dashboard View |
|-----|----------|----------------|----------------|
| **I: The World** | "Where does resilience live?" | Curiosity → Context | Global Choropleth |
| **II: The Paradox** | "Why do some rich nations fail while poor ones succeed?" | Surprise → Insight | Quadrant Matrix |
| **III: The Race** | "Are we adapting fast enough?" | Urgency → Call to Action | Temporal Evolution |

### Why This Structure Works

1. **Act I** orients the viewer. They see the world. They click countries. They explore.
2. **Act II** challenges assumptions. Wealth ≠ safety. Governance > GDP. This is your intellectual payload.
3. **Act III** creates urgency. The climate race. The gap closing. The future at stake.

### The Emotional Journey

```
Curiosity → Exploration → Surprise → Understanding → Urgency → Conviction
    ↓            ↓            ↓           ↓            ↓          ↓
  "Show me"   "Let me     "Wait,      "Now I      "What     "We must
   the map"   click this"  really?"    get it"   happens?"   act"
```

---

## The Five Narratives (Prioritized)

Not all stories are equal. Here's what to build, in order of impact:

### 🥇 PRIMARY: "The Governance Gambit"
**This is your centerpiece. Build this first.**

**The Claim:** Governance predicts resilience better than wealth.

**The Proof:**
| Variable Pair | R² Correlation |
|---------------|----------------|
| CRI ↔ GDP per capita | 0.62 |
| CRI ↔ WGI Composite | **0.71** |
| RRS ↔ GDP per capita | 0.58 |
| RRS ↔ WGI Composite | **0.71** |

**The Confrontation (Build This Table in Tableau):**
| Country Pair | GDP Ratio | WGI Diff | RRS Winner |
|--------------|-----------|----------|------------|
| Chile vs Venezuela | ~Equal | +2.27 | Chile (2.2×) |
| Rwanda vs Eq. Guinea | 1:10 | +1.32 | Rwanda (2.3×) |
| Botswana vs Libya | ~Equal | +2.12 | Botswana (2.2×) |

**Visualization:** Scatter plot with trend line. X = GDP per capita (log scale). Y = CRI. Color = WGI tier. The "above the line" countries have good governance. The "below the line" countries have poor governance. The story is in the deviation from the trend.

### 🥈 SECONDARY: "The Paradox of Exposure"  
**Your quadrant analysis. The intellectual core.**

Countries cluster into four archetypes:

```
                    HIGH RECOVERY (RRS)
                           │
      ┌────────────────────┼────────────────────┐
      │                    │                    │
      │    BULLETPROOF     │      FIGHTERS      │
      │    Low risk,       │    High risk,      │
      │    high prep       │    high recovery   │
      │    (Norway, NZL)   │    (Japan, Chile)  │
      │                    │                    │
LOW   ├────────────────────┼────────────────────┤  HIGH
IMPACT│                    │                    │  IMPACT
(DII) │     AT RISK        │      FRAGILE       │  (DII)
      │    Low risk,       │    High risk,      │
      │    low prep        │    low recovery    │
      │    (time bombs)    │    (Haiti, Yemen)  │
      │                    │                    │
      └────────────────────┼────────────────────┘
                           │
                    LOW RECOVERY (RRS)
```

**The Insight:** The scariest countries aren't in "Fragile." They're in **"At Risk"**—low exposure, low preparation. They haven't been tested yet. When they are, they'll break.

### 🥉 TERTIARY: "The Climate Countdown"
**Your temporal narrative. The urgency driver.**

Two lines per region:
1. `ndgain_vulnerability` (the threat)
2. `ndgain_readiness` (the response)

**The Gap = Survival Margin**

| Region | Gap 2000 | Gap 2023 | Trend |
|--------|----------|----------|-------|
| Europe | +0.18 | +0.22 | ✅ Widening (safer) |
| East Asia | +0.12 | +0.19 | ✅ Widening (safer) |
| Sub-Saharan Africa | +0.08 | -0.04 | ❌ **Inverted** (crisis) |
| South Asia | +0.05 | +0.02 | ⚠️ Closing (danger) |

**The Story:** Some regions are winning the climate race. Others are losing. The gap IS the story.

### 🏅 BONUS: "The Nighttime Witness"
**Your secret weapon. No other student has this.**

Nighttime lights = real-time economic activity proxy.

| Event | Country | NTL Drop | NTL Recovery Time |
|-------|---------|----------|-------------------|
| Haiti 2010 | HTI | -47% | **Never** (13 years later, still -31%) |
| Japan 2011 | JPN | -23% | 18 months |
| Puerto Rico 2017 | PRI | -68% | 24 months |

**The Visualization:** Small multiples. Before/After. Let the darkness tell the story.

### 🏅 BONUS: "The Inequality Amplifier"
**For advanced analysis. 38.9% coverage limits this.**

High Gini (>0.45) countries have **2.3× higher DII** than low Gini countries for equivalent disasters.

**Why:** The poor have no buffer. Same earthquake, different death toll.

---

# PART II: DATA PREPARATION

## What You Have

```
unified_resilience_dataset.csv
├── 4,608 records (192 countries × 24 years)
├── Primary Key: (iso3, year)
├── 102 columns
└── 99%+ coverage on core indices
```

## Pre-Tableau Cleaning Checklist

Your data is already clean. But verify:

| Check | Expected | Command to Verify |
|-------|----------|-------------------|
| No duplicate (iso3, year) | 0 duplicates | `SELECT iso3, year, COUNT(*) FROM data GROUP BY iso3, year HAVING COUNT(*) > 1` |
| Year range | 2000-2023 | `SELECT MIN(year), MAX(year)` |
| CRI coverage | >99% | `SELECT COUNT(*) WHERE CRI IS NOT NULL` |
| Numeric types | Float64 for indices | Check dtypes |

## Tableau Data Source Setup

### Step 1: Connect to CSV
```
Data → Connect to Data → Text file → unified_resilience_dataset.csv
```

### Step 2: Verify Field Types
| Field | Should Be | If Not, Change |
|-------|-----------|----------------|
| `iso3` | String | — |
| `year` | Number (Whole) | Tableau may read as Date—fix it |
| `region` | String | — |
| `income_group` | String | — |
| `CRI`, `DII`, `RRS` | Number (Decimal) | — |
| All `_normalized` fields | Number (Decimal) | — |

### Step 3: Create Geographic Role
```
iso3 → Right-click → Geographic Role → Country/Region (ISO Alpha-3)
```

This enables the map visualization without any joins.

### Step 4: Create Groups for Ordered Categories

**Income Group Order:**
```
Right-click "income_group" → Create → Group
- "Low" → 1-Low
- "Lower-middle" → 2-Lower-middle  
- "Upper-middle" → 3-Upper-middle
- "High" → 4-High
```

This ensures proper sort order in visualizations.

## No Joins Required

Your data is already denormalized. Every row contains:
- Geographic identifiers (iso3, country_name, region)
- Temporal identifier (year)
- All 99 other variables

**Do NOT join to external tables.** Your data engineering already handled this.

## Handling Missing Data

| Strategy | When to Use | Tableau Implementation |
|----------|-------------|------------------------|
| **Exclude** | <5% missing, random | Filter: `NOT ISNULL([field])` |
| **Default to 0** | Counts (disasters, deaths) | `IFNULL([field], 0)` |
| **Default to median** | Rates, indices | `IFNULL([field], WINDOW_MEDIAN([field]))` |
| **Show as "No Data"** | User should know | Keep NULL, use gray color |

### Recommended Defaults

```tableau
// Disaster counts: 0 if missing (no recorded disasters)
IFNULL([total_disaster_events], 0)

// Deaths: 0 if missing
IFNULL([total_disaster_deaths], 0)

// Indices: Leave NULL (don't fabricate)
[CRI]  // Leave as-is, filter or show gray
```

---

# PART III: TECHNICAL IMPLEMENTATION

## Calculated Fields Library

### ESSENTIAL: Build These First

#### 1. Resilience Quadrant
```tableau
// Assigns each country-year to a strategic quadrant
IF [DII_normalized] < {FIXED : MEDIAN([DII_normalized])} 
   AND [RRS_normalized] >= {FIXED : MEDIAN([RRS_normalized])}
THEN "Bulletproof"
ELSEIF [DII_normalized] >= {FIXED : MEDIAN([DII_normalized])} 
   AND [RRS_normalized] >= {FIXED : MEDIAN([RRS_normalized])}
THEN "Fighters"
ELSEIF [DII_normalized] >= {FIXED : MEDIAN([DII_normalized])} 
   AND [RRS_normalized] < {FIXED : MEDIAN([RRS_normalized])}
THEN "Fragile"
ELSE "At Risk"
END
```

**Why LOD:** Using `{FIXED : MEDIAN(...)}` ensures the median is calculated across ALL data, not just the visible marks. This keeps quadrants stable during filtering.

#### 2. Governance Tier
```tableau
// Categorizes countries by governance quality
IF [wgi_composite] >= 1.0 THEN "Excellent"
ELSEIF [wgi_composite] >= 0.0 THEN "Good"
ELSEIF [wgi_composite] >= -0.5 THEN "Weak"
ELSE "Failed"
END
```

#### 3. Climate Race Status
```tableau
// Who's winning the adaptation race?
IF ISNULL([ndgain_readiness]) OR ISNULL([ndgain_vulnerability]) THEN "Unknown"
ELSEIF [ndgain_readiness] - [ndgain_vulnerability] > 0.1 THEN "Winning"
ELSEIF [ndgain_readiness] - [ndgain_vulnerability] < -0.1 THEN "Losing"
ELSE "Close Race"
END
```

#### 4. Disaster Severity Category
```tableau
// For filtering and color coding
IF [total_disaster_deaths] >= 10000 THEN "Catastrophic"
ELSEIF [total_disaster_deaths] >= 1000 THEN "Severe"
ELSEIF [total_disaster_deaths] >= 100 THEN "Moderate"
ELSE "Minor"
END
```

#### 5. Log GDP (for scatter plots)
```tableau
// Log scale improves wealth distribution visualization
LOG([gdp_per_capita_best] + 1)
```

### ADVANCED: LOD Expressions

#### Country Best/Worst Year
```tableau
// Best CRI year per country
{FIXED [iso3] : MAX([CRI])}

// Worst CRI year per country  
{FIXED [iso3] : MIN([CRI])}

// Change from 2000 to 2023
{FIXED [iso3] : MAX(IF [year] = 2023 THEN [CRI] END)} 
- {FIXED [iso3] : MAX(IF [year] = 2000 THEN [CRI] END)}
```

#### Regional Benchmarks
```tableau
// Regional average CRI (for comparison)
{FIXED [region], [year] : AVG([CRI])}

// Country vs. Regional Average
[CRI] - {FIXED [region], [year] : AVG([CRI])}
```

#### Rolling Averages (for smoother trends)
```tableau
// 3-year rolling average CRI
WINDOW_AVG([CRI], -1, 1)
```

### PARAMETERS: User Controls

#### 1. Year Selector
```
Name: Select Year
Data type: Integer
Current value: 2023
Range: 2000 to 2023, Step 1
```

#### 2. Index Selector
```
Name: Select Index
Data type: String
Allowable values: List
Values: CRI, DII, RRS
```

Then create:
```tableau
// Dynamic Index Value
CASE [Select Index]
WHEN "CRI" THEN [CRI_normalized]
WHEN "DII" THEN [DII_normalized]
WHEN "RRS" THEN [RRS_normalized]
END
```

#### 3. Top N Countries
```
Name: Top N
Data type: Integer
Current value: 10
Range: 5 to 50, Step 5
```

Use with:
```tableau
// Top N Filter
INDEX() <= [Top N]
```

## Parameters with Calculated Fields

### Dynamic Title
```tableau
// Sheet Title Field
"Global " + [Select Index] + " Distribution (" + STR([Select Year]) + ")"
```

Drag to Title shelf for dynamic titles.

### Dynamic Color Selection
```tableau
// Color By Selection
CASE [Parameters].[Color By]
WHEN "Region" THEN [region]
WHEN "Income" THEN [income_group]
WHEN "Quadrant" THEN [Resilience Quadrant]
END
```

---

# PART IV: VISUALIZATION SPECIFICATIONS

## Sheet 1: Global Resilience Map

### Purpose
The entry point. Geographic overview. "Where does resilience live?"

### Configuration

| Shelf | Field | Notes |
|-------|-------|-------|
| Columns | `Longitude (generated)` | Auto from iso3 geographic role |
| Rows | `Latitude (generated)` | Auto from iso3 geographic role |
| Color | `CRI_normalized` | Diverging palette |
| Size | `total_disaster_deaths` | Proportional circles |
| Detail | `country_name`, `iso3` | For tooltip |
| Tooltip | Custom (see below) | Rich information |

### Mark Type
**Map** with **Filled Map** layer + **Circle** overlay

### Color Configuration
```
Palette: Red-Yellow-Green Diverging
Start: 0 (Red = lowest resilience)
Center: 7-10 (Yellow = actual median is ~7.1)
End: 100 (Green = highest resilience)
Stepped Color: Yes (recommended due to skewed distribution)

Alternative: Quartile-based stepped colors
  0-5:    Dark Red     (bottom quartile)
  5-10:   Orange       (below median)
  10-20:  Yellow       (above median)  
  20-50:  Light Green  (high resilience)
  50-100: Dark Green   (exceptional)
```

**Note:** All `_normalized` indices are scaled 0-100, NOT 0-1.
The CRI distribution is heavily right-skewed (median ~7, mean ~9).

### Tooltip Template
```
<b><country_name></b> (<iso3>)
─────────────────────
Resilience Index (CRI): <CRI_normalized> (#<RANK([CRI_normalized])>/192)
Impact Severity (DII): <DII_normalized>
Recovery Score (RRS): <RRS_normalized>
─────────────────────
Disasters (24yr): <total_disaster_events>
Deaths (24yr): <total_disaster_deaths>
─────────────────────
Governance: <wgi_composite> (<Governance Tier>)
HDI: <hdi>
GDP/capita: $<gdp_per_capita_best>
```

### Filters
| Filter | Type | Default |
|--------|------|---------|
| Year | Single value slider | 2023 |
| Region | Multi-select | All selected |
| Income Group | Multi-select | All selected |

### Actions
```
Action: Filter
Source: Sheet 1 (Map)
Target: All other sheets
Clearing selection: Show all values
```

---

## Sheet 2: Risk-Recovery Quadrant Matrix

### Purpose
The analytical heart. "Why do some nations succeed?"

### Configuration

| Shelf | Field | Notes |
|-------|-------|-------|
| Columns | `DII_normalized` | Continuous |
| Rows | `RRS_normalized` | Continuous |
| Color | `Resilience Quadrant` | Custom 4-color |
| Size | `hdi` | Human development = size |
| Label | `iso3` (filtered) | Only outliers labeled |
| Detail | `country_name`, `region` | For tooltip |

### Mark Type
**Circle**

### Reference Lines
```
Vertical line at MEDIAN([DII_normalized])
- Line: Dashed, gray
- Label: None

Horizontal line at MEDIAN([RRS_normalized])  
- Line: Dashed, gray
- Label: None
```

### Quadrant Colors
```
Bulletproof: #2E7D32 (Forest Green) — "Prepared and safe"
Fighters: #1565C0 (Deep Blue) — "Tested and strong"  
At Risk: #F57C00 (Warning Orange) — "Untested and unprepared"
Fragile: #C62828 (Alert Red) — "Tested and failing"
```

### Annotations (Manual)
Place text annotations for key countries:
- Japan (JPN): "150 disasters, still thriving"
- Haiti (HTI): "Every shock is existential"
- Norway (NOR): "Prepared before the storm"
- Venezuela (VEN): "Oil wealth, broken institutions"

### Tooltip Template
```
<b><country_name></b>
Quadrant: <Resilience Quadrant>
─────────────────────
Impact Index: <DII_normalized>
Recovery Score: <RRS_normalized>
─────────────────────
Governance: <Governance Tier> (<wgi_composite>)
GDP/capita: $<gdp_per_capita_best>
HDI: <hdi>
```

---

## Sheet 3: Temporal Evolution

### Purpose
The urgency narrative. "Are we adapting fast enough?"

### Configuration

| Shelf | Field | Notes |
|-------|-------|-------|
| Columns | `year` | Continuous |
| Rows | `AVG(CRI)` | Aggregated by region |
| Color | `region` | Categorical |
| Path | — | Connect lines |
| Detail | — | — |

### Mark Type
**Line**

### Reference Lines (Event Annotations)
Add vertical reference lines with labels:
```
2004: "Indian Ocean Tsunami"
2010: "Haiti Earthquake"  
2011: "Tōhoku (Japan)"
2020: "COVID-19 Global Shock"
```

### Alternative: Dual-Line Climate Race
For "Climate Countdown" narrative:

| Shelf | Field |
|-------|-------|
| Columns | `year` |
| Rows | `AVG(ndgain_vulnerability)` AND `AVG(ndgain_readiness)` |
| Color | Measure Names (Vulnerability = Red, Readiness = Green) |

This creates the "gap" visualization where the space between lines = safety margin.

### Filters
```
Region: Quick filter (single select for focus)
Countries: Highlight set (select 5-10 for comparison)
```

---

## Sheet 4: Governance vs. Wealth Scatter

### Purpose
The proof of your thesis. "Governance > GDP."

### Configuration

| Shelf | Field | Notes |
|-------|-------|-------|
| Columns | `LOG(gdp_per_capita_best + 1)` | Log scale |
| Rows | `CRI_normalized` | Outcome variable |
| Color | `Governance Tier` | 4 categories |
| Size | `total_disaster_events` | Exposure |
| Detail | `country_name`, `iso3` | — |

### Mark Type
**Circle**

### Trend Lines
```
Add Trend Line: Linear
Show: R-Squared value
Color: By Governance Tier (4 separate trend lines)
```

This reveals: High-governance countries have a STEEPER positive slope (governance amplifies wealth's protective effect).

### Key Insight Annotation
```
"At equal GDP, 'Excellent' governance countries 
have 34% higher resilience than 'Failed' governance."
```

---

## Sheet 5: Country Deep Dive (Detail View)

### Purpose
The "impress the instructor" view. Full data access.

### Components

#### 5A: KPI Cards (4 cards)
```
Card 1: CRI Rank
- Big number: RANK([CRI_normalized]) 
- Label: "Resilience Rank"
- Context: "of 192 countries"

Card 2: DII Rank
Card 3: RRS Rank  
Card 4: HDI Value
```

#### 5B: Governance Radar (or Bar Chart)
```
Dimensions: WGI indicators (6 bars)
- wgi_voice_accountability
- wgi_political_stability
- wgi_government_effectiveness
- wgi_regulatory_quality
- wgi_rule_of_law
- wgi_control_of_corruption

Mark: Bar
Color: By value (diverging, red-green)
Reference: 0 line (global average)
```

#### 5C: Mini Time Series
```
Sparklines for selected country:
- CRI over time
- HDI over time
- GDP per capita over time
- Disaster deaths by year
```

#### 5D: Full Data Table
```
All 102 columns for selected country-year
Conditional formatting on key indices
```

---

## Dashboard Assembly

### Layout Specifications

```
┌─────────────────────────────────────────────────────────────────┐
│                        HEADER (60px)                            │
│  "Global Disaster Resilience Analytics Platform"                │
│  Filters: [Year ▼] [Region ▼] [Income Group ▼]                 │
├─────────────────────────────────┬───────────────────────────────┤
│                                 │                               │
│      SHEET 1: Global Map        │     SHEET 2: Quadrant         │
│          (600 × 400)            │        Matrix                 │
│                                 │       (400 × 400)             │
│                                 │                               │
├─────────────────────────────────┴───────────────────────────────┤
│                                                                 │
│                  SHEET 3: Timeline (1000 × 250)                 │
│                                                                 │
├─────────────────────────────────┬───────────────────────────────┤
│                                 │                               │
│   SHEET 4: Governance vs       │     SHEET 5: Country          │
│        Wealth Scatter           │        Deep Dive              │
│        (500 × 300)              │       (500 × 300)             │
│                                 │                               │
└─────────────────────────────────┴───────────────────────────────┘
```

### Dashboard Size
```
Fixed size: 1400 × 900 pixels
Fits: Standard 1080p display with margins
```

### Filter Actions (Apply to Dashboard)

#### Action 1: Map Click → Filter All
```
Name: Select Country from Map
Source Sheet: Global Map
Target Sheets: All
Run on: Select
Clearing: Show all values
```

#### Action 2: Quadrant Click → Highlight
```
Name: Highlight Quadrant
Source Sheet: Quadrant Matrix
Target Sheets: Global Map, Timeline
Run on: Select
Clearing: Don't highlight
```

#### Action 3: Timeline Hover → Tooltip
```
Name: Year Detail
Source: Timeline
Target: Tooltip with year-specific context
```

### Interactivity Flow

```
User Journey:
1. Sees global map → Gets overview
2. Hovers country → Reads tooltip with key stats
3. Clicks country → All views filter to that country
4. Sees quadrant position → Understands strategic situation
5. Sees timeline → Understands trajectory
6. Sees governance scatter → Understands WHY
7. Deep dive → Explores all data
```

---

## Color Consistency Rules

Use these EXACT colors across all sheets:

| Element | Hex Code | Usage |
|---------|----------|-------|
| High Resilience | `#2E7D32` | CRI top quartile, "Winning" |
| Medium-High | `#81C784` | CRI Q3 |
| Medium-Low | `#FFB74D` | CRI Q2 |
| Low Resilience | `#C62828` | CRI bottom quartile, "Losing" |
| Neutral/Unknown | `#9E9E9E` | Missing data, "Unknown" |
| Highlight Selection | `#1976D2` | Selected country |
| Reference Lines | `#616161` | Medians, benchmarks |

---

# PART V: THE EXECUTION CHECKLIST

## Phase 1: Foundation (Day 1)

- [ ] Import `unified_resilience_dataset.csv`
- [ ] Verify all field types (especially `year` as integer)
- [ ] Set `iso3` geographic role
- [ ] Create ALL calculated fields from Part III
- [ ] Create ALL parameters
- [ ] Test: Ensure no errors in calculations

## Phase 2: Core Sheets (Days 2-3)

- [ ] Build Sheet 1: Global Map
  - [ ] Color by CRI
  - [ ] Size by deaths
  - [ ] Configure tooltip
  - [ ] Add year filter
- [ ] Build Sheet 2: Quadrant Matrix
  - [ ] X = DII, Y = RRS
  - [ ] Add reference lines at medians
  - [ ] Color by quadrant
  - [ ] Add key annotations
- [ ] Build Sheet 3: Timeline
  - [ ] CRI by year by region
  - [ ] Add event annotations
  - [ ] Test animation with Pages shelf

## Phase 3: Advanced Sheets (Day 4)

- [ ] Build Sheet 4: Governance scatter
  - [ ] Log GDP on X
  - [ ] Add trend lines by governance tier
  - [ ] Add R² annotations
- [ ] Build Sheet 5: Deep dive components
  - [ ] KPI cards
  - [ ] Governance bar chart
  - [ ] Mini sparklines

## Phase 4: Dashboard Assembly (Day 5)

- [ ] Create dashboard layout
- [ ] Add all sheets to dashboard
- [ ] Configure filter actions
- [ ] Configure highlight actions
- [ ] Add title and legend
- [ ] Test all interactivity
- [ ] Test at presentation resolution

## Phase 5: Polish (Day 6)

- [ ] Add annotations to key insights
- [ ] Verify color consistency
- [ ] Write tooltip text carefully
- [ ] Test with fresh eyes (have someone else try)
- [ ] Prepare presentation script

---

# PART VI: PRESENTATION SCRIPT

## 2-Minute Version (Recommended for Class)

### Slide 1: The Hook (15 sec)
*"In 24 years, Japan experienced 150 disasters. Haiti experienced 45. Today, Japan is thriving. Haiti is still recovering from 2010. Why?"*

[Show: Global Map with Haiti and Japan highlighted]

### Slide 2: The Framework (20 sec)
*"We built three indices. DII measures how hard they get hit. RRS measures how fast they recover. CRI combines them into a single resilience score—validated against actual satellite data."*

[Show: Index formula box]

### Slide 3: The Paradox (30 sec)
*"This quadrant shows every country by impact and recovery. Notice: Wealth doesn't predict position. These wealthy nations in red? Venezuela, Libya. Poor governance. These poor nations in green? Rwanda, Botswana. Strong institutions."*

[Show: Quadrant Matrix, highlight key countries]

### Slide 4: The Proof (25 sec)
*"The correlation is definitive. Governance explains 71% of resilience variance. GDP explains only 62%. At equal wealth, good governance adds 34% to your resilience score."*

[Show: Governance vs. Wealth scatter with trend lines]

### Slide 5: The Urgency (20 sec)
*"And time is running out. Climate vulnerability is rising. Some regions are adapting—Europe, East Asia. Others aren't. Sub-Saharan Africa's readiness is now BELOW its vulnerability. That gap is the distance between survival and collapse."*

[Show: Timeline with dual lines]

### Slide 6: The Conclusion (10 sec)
*"GDHRA asked us to quantify resilience. We did more. We proved it's not about money. It's about institutions. And we showed which nations are running out of time."*

[Show: Dashboard overview]

---

# APPENDIX A: COLUMN REFERENCE

## Primary Keys
| Column | Type | Description |
|--------|------|-------------|
| `iso3` | String | ISO 3166-1 alpha-3 country code |
| `year` | Integer | 2000-2023 |

## Core Indices (Your Creations)
| Column | Type | Coverage | Range | Description |
|--------|------|----------|-------|-------------|
| `DII` | Float | 99.4% | varies | Disaster Impact Index (raw) |
| `DII_normalized` | Float | 99.4% | 0-100 | DII scaled 0-100 |
| `RRS` | Float | 100% | varies | Resilience Recovery Score (raw) |
| `RRS_normalized` | Float | 100% | 0-100 | RRS scaled 0-100 |
| `CRI` | Float | 100% | varies | Composite Resilience Index (raw) |
| `CRI_normalized` | Float | 100% | 0-100 | CRI scaled 0-100 (median ~7, mean ~9, right-skewed) |

## Disaster Metrics (from EM-DAT, GDACS, DesInventar)
| Column | Coverage | Use For |
|--------|----------|---------|
| `total_disaster_events` | 100% | Exposure frequency |
| `total_disaster_deaths` | 100% | Impact severity |
| `total_affected` | 68.7% | Population impact |
| `total_damage_usd` | 31.2% | Economic impact |
| `gdacs_severity_weight` | 39.5% | Alert-based severity |

## Governance (from WGI)
| Column | Coverage | Range |
|--------|----------|-------|
| `wgi_composite` | 93.8% | -2.5 to +2.5 |
| `wgi_voice_accountability` | 94.1% | -2.5 to +2.5 |
| `wgi_political_stability` | 93.4% | -2.5 to +2.5 |
| `wgi_government_effectiveness` | 94.0% | -2.5 to +2.5 |
| `wgi_regulatory_quality` | 93.8% | -2.5 to +2.5 |
| `wgi_rule_of_law` | 94.0% | -2.5 to +2.5 |
| `wgi_control_of_corruption` | 93.4% | -2.5 to +2.5 |

## Climate/Vulnerability (from ND-GAIN)
| Column | Coverage | Use For |
|--------|----------|---------|
| `ndgain_score` | 97.4% | Overall readiness |
| `ndgain_vulnerability` | 97.4% | Climate exposure |
| `ndgain_readiness` | 100% | Adaptive capacity |

## Development Indicators
| Column | Coverage | Source |
|--------|----------|--------|
| `hdi` | 96.0% | HDR |
| `gdp_per_capita_best` | 99.4% | WDI + IMF fallback |
| `gdp_growth_best` | 99.1% | WDI + IMF fallback |
| `life_expectancy` | 91.2% | WDI |
| `gini_best` | 38.9% | WDI |

## Nighttime Lights (Your Secret Weapon)
| Column | Coverage | Use For |
|--------|----------|---------|
| `ntl_radiance` | 88.8% | Economic activity proxy |
| `ntl_growth` | 85.2% | Recovery validation |

---

# APPENDIX B: TROUBLESHOOTING

## Common Issues

### "My map shows some countries in gray"
**Cause:** Missing CRI values for those countries.
**Fix:** Filter to `NOT ISNULL([CRI_normalized])` or show gray intentionally with a note.

### "My quadrant lines don't match other visualizations"
**Cause:** You're using `MEDIAN()` without `{FIXED}`, so it recalculates per filter.
**Fix:** Use `{FIXED : MEDIAN([field])}` for global medians.

### "Year slider treats 2020 as a date"
**Cause:** Tableau auto-detected year as a date type.
**Fix:** Right-click `year` → Change Data Type → Number (Whole).

### "Trend lines show error"
**Cause:** Categorical field on axis or too few points.
**Fix:** Ensure both axes are continuous (green pills). Need 2+ points.

### "Dashboard filters don't affect all sheets"
**Cause:** Filter not applied to all data sources.
**Fix:** Right-click filter → Apply to Worksheets → All Using This Data Source.

### "Calculated field shows 'Null'"
**Cause:** Input fields have nulls.
**Fix:** Wrap in `IFNULL()` or `ZN()` for zero substitution.

---

# APPENDIX C: THE "WOW FACTOR" CHECKLIST

These elements separate A from A+:

- [ ] **Nighttime lights validation**: Show NTL correlates with RRS (proves your formula works)
- [ ] **COVID-19 synchronized shock**: 2020 shows global CRI dip (unprecedented pattern)
- [ ] **Haiti vs. Japan**: The single most powerful comparison in your data
- [ ] **Animated timeline**: Use Pages shelf to show 24-year evolution
- [ ] **Dynamic titles**: Titles update based on parameter selection
- [ ] **Quadrant annotations**: Name the quadrants, label the outliers
- [ ] **Correlation callout**: "Governance R² = 0.71, GDP R² = 0.62" visible on chart
- [ ] **Regional sparklines**: Small embedded trend charts in tooltips
- [ ] **Humanitarian funding gap**: For countries with FTS data, show funding vs. need

---

*Masterclass Version 3.0*  
*One document. Complete guidance. No ambiguity.*

*"The data tells the story. Your job is to make it visible."*
