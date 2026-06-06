# Power BI Build Guide

## 1. Source File
Use this file:

`data/clean/primary_skills_powerbi.csv`

## 2. Import Steps
1. Open Power BI Desktop.
2. Click `Get data`.
3. Choose `Text/CSV`.
4. Select `data/clean/primary_skills_powerbi.csv`.
5. Click `Transform Data`.
6. In Power Query, verify the column types:
   - `job_id` as Text
   - `skill` as Text
   - `skill_category` as Text
   - `skill_level` as Text
   - `job_match_method` as Text
   - `job_id_job` as Text
   - `job_title` as Text
   - `company_type` as Text
   - `industry` as Text
   - `country` as Text
   - `city` as Text
   - `remote_type` as Text
   - `experience_level` as Text
   - `min_experience_years` as Decimal Number
   - `salary_min_usd` as Decimal Number
   - `salary_max_usd` as Decimal Number
   - `employment_type` as Text
   - `posted_year` as Whole Number
   - `company_size` as Text
   - `source` as Text
   - `month` as Text
   - `quarter` as Text
7. Click `Close and Apply`.

## 3. Rename the Table
Rename the imported table to:

`SkillFacts`

## 4. Theme
Import this file:

`dashboards/future_fit_powerbi_theme.json`

Recommended theme colors:
- Background: `#120a22`
- Surface: `#1b122f`
- Surface Alt: `#26173f`
- Text: `#f6e7bf`
- Accent Gold: `#d7b15a`
- Accent Purple: `#a67cff`

## 5. Calculated Columns
Create these columns first.

### 5.1 Experience Sort
Modeling > New column:

```DAX
Experience Sort =
SWITCH(
    'SkillFacts'[experience_level],
    "entry", 1,
    "mid", 2,
    "senior", 3,
    99
)
```

Then select `experience_level` and choose `Sort by column` > `Experience Sort`.

### 5.2 Year Label
If Power BI reads `posted_year` as a decimal, create:

```DAX
Year = INT('SkillFacts'[posted_year])
```

Use `Year` in the slicer and charts instead of `posted_year` if needed.

## 6. Measures
Copy these into Modeling > New measure, one measure at a time.

See [powerbi_measures.dax](powerbi_measures.dax) for the full measure set.

## 7. Page Layout
Create one report page named:

`Future Fit Skill Trends`

Set the page size to:
- Type: 16:9
- Canvas background: `#120a22`

### Recommended layout
- Top row: 3 card visuals
- Middle left: bar chart
- Middle right: line chart
- Bottom: matrix visual
- Top of page or far right: year slicer

## 8. Visual 1 - Top 20 Skills Bar Chart
Visual type: Clustered bar chart

Field mapping:
- Y-axis: `skill`
- X-axis: `Total Skill Mentions`

Visual-level filter:
- `skill` > Top N > 20 by `Total Skill Mentions`

Formatting:
- Sort descending by `Total Skill Mentions`
- Data labels on
- Title: `Top 20 Most In-Demand Skills (2020-2026)`
- Bar color: gold

## 9. Visual 2 - Skill Trend Line Chart
Visual type: Line chart

Field mapping:
- X-axis: `Year`
- Y-axis: `Total Skill Mentions`
- Legend: `skill`

Visual-level filter:
- `skill` > Top N > 5 by `Total Skill Mentions`

Formatting:
- Markers on
- Title: `Skill Demand Trend by Year (Top 5 Skills)`
- Use gold and purple line colors

## 10. Visual 3 - Skill by Experience Level Matrix
Visual type: Matrix

Field mapping:
- Rows: `experience_level`
- Columns: `skill`
- Values: `Total Skill Mentions`

Visual-level filter:
- `skill` > Top N > 10 by `Total Skill Mentions`

Formatting:
- Row headers sorted by `Experience Sort`
- Conditional formatting: background color scale from deep purple to gold
- Title: `Skill Demand by Experience Level`

## 11. Visual 4 - KPI Cards
Create three separate Card visuals.

Card 1:
- Field: `Total Skill Mentions`
- Title: `Total Skill Mentions`

Card 2:
- Field: `Unique Skills`
- Title: `Unique Skills`

Card 3:
- Field: `Year Span Text`
- Title: `Year Span`

## 12. Slicer
Create a `Between` slicer using `Year`.

Important:
- Select the slicer.
- Go to `Format` > `Edit interactions`.
- Set the slicer to `Filter` for the bar chart, line chart, and matrix.
- Set the slicer to `None` for the three card visuals so the KPI cards stay as overall totals.

## 13. Export
Save the PBIX as:

`dashboards/skill_trend_powerbi.pbix`

Then export the PDF as:

`dashboards/skill_trend_dashboard.pdf`

## 14. Final Checks
- Page loads without missing data
- All three charts respond to the year slicer
- KPI cards do not change with the slicer
- Report title and theme match `Future Fit`
- PDF export is not blank

