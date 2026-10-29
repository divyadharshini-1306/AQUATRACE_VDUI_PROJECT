# AquaTrace – Handoff for Member 1 (Data & EDA lead)

**Load this file into Power BI:** `aquatrace_powerbi.csv` (6,512 rows · 1,200 facilities · 2019–2025 · 43 columns).
Read `DATA_CARD.md` once before you start. It explains what is real and what is modelled.

## 1. Your checklist against the dataset

| Your task | Status in the file |
|---|---|
| Confirm columns (city, country, lat/long, cooling, PUE, WUE, stress index, year) | All present: `City`, `Country`, `Latitude`, `Longitude`, `Cooling_System`, `PUE`, `WUE_L_per_kWh`, `Water_Stress_Index` (0–1) and `Stress_Months_Baseline` (0–12), `Year` |
| Clean in Power Query (types, nulls, duplicates, outliers, names) | Already checked: 0 nulls, 0 duplicate rows, 0 duplicate (Facility_ID, Year). You still do the steps and document them (set types, confirm, trim text). Outliers: use the ready-made `WUE_Outlier_Flag`. Country names follow the stress spreadsheet ("USA", "The Netherlands"), so keep them as they are |
| Lat/long lookup for cities | **Not needed.** Every row has `Latitude` and `Longitude`. Use them on the map (not the city names, which Power BI can misplace). They are city-level with about 5 km jitter, not real facility addresses |
| Define the water-risk score | **Already defined. Do not change it** (see section 2) |
| DAX measures, Page 2 EDA visuals, EDA findings note | Yours. Suggestions in section 3 |
| "Misleading visuals" notes | Yours. Suggestions in section 4 |

## 2. The risk score (write this into your notes)

`Water_Risk_Score = 100 × (0.25 + 0.75 × stress weight) × (0.5 × WUE percentile + 0.5 × daily-water-volume percentile)`

- Stress weight comes from `Stress_Tier_Baseline`: Low 0, Moderate 0.35, High 0.7, Extreme 1.0.
- Tiers: Low < 20, Medium 20–35, High ≥ 35 (`Water_Risk_Tier`, and `High_Risk` = 1 for High).
- **Why:** raw WUE ignores where the water comes from. A litre in a water-stressed region matters more than a litre in a wet one, so stress scales the score. The 0.25 floor means unstressed sites still differ by how much water they use. Without it the score tracks stress almost perfectly (correlation 0.99) and cooling and capacity look irrelevant.
- The model columns (`Pred_High_Risk_Prob` etc.) were built on this tier. **If you want to change the formula, tell the dataset owner first**, because the model columns must be rebuilt.
- You can recompute the score as a DAX check, but don't overwrite the column.

## 3. Suggested measures and EDA visuals

- Measures: total daily water (m³), average WUE, average PUE, high-risk share (%), share of facilities with 5+ stress months, AI share, facility count.
- EDA ideas: WUE by cooling system (bars from zero), risk-tier share by region, correlation of numeric fields with `Water_Risk_Score`, WUE outliers by cooling type, trend by `Year`.
- Findings note: trends (water and AI share by year), correlations, outliers. `model_importance.csv` already puts the model's ranking next to the EDA statistics.

## 4. Rules to keep the project honest

1. Call the data **modelled estimates** wherever it appears (subtitles, footnotes, PPT). Locations and water-stress exposure are real; cooling, capacity, PUE, WUE and water use are modelled. Never say "real facility records" or "measured".
2. Key Influencers: analyse `High_Risk` (is 1) using cooling, climate, facility type, capacity, utilisation, AI share, temperature, PUE, region and `Stress_Tier_Baseline`. **Exclude** `WUE_L_per_kWh`, `Daily_Water_Use_m3`, `Stress_Weight`, `Water_Risk_Score` and the `Pred_*` columns, because they define or come from the target.
3. Use the `*_Order` columns to sort tiers and cooling types, and `Region` for drill-down.
4. The `Year` trend is stylised. Total water grows faster than published global estimates, so don't quote it as a real growth rate.
5. Keep to **5 visuals** in the .pbix (the brief's maximum). Confirm with the teacher whether slicers count.
6. The Epoch AI files are real data and are **separate** from the modelled table. Don't merge them. Cite Epoch as: *Epoch AI, 'AI data centers', epoch.ai, retrieved October 2026* (CC BY 4.0).

## 5. Files in this package

| File | Use |
|---|---|
| `aquatrace_powerbi.csv` | Main table for Power BI |
| `model_importance.csv` | Model vs EDA ranking, for the insight slide |
| `epoch_ai_data_centers.csv` | 95 real AI data centers (Meta, OpenAI case study) |
| `epoch_ai_capacity_by_year.csv` | Real tracked AI capacity by year, for the Hook chart |
| `DATA_CARD.md` | Sources, generation rules, limits, wording for slides |
| `generate_dataset.py`, `prepare_powerbi.py` | Reference only. They show how the data was built and need the original input files to rerun |

## 6. Review 2 (3 Nov 2026)

The PPT needs the title, dataset, one paper per student, a SWOT analysis and part of the implementation. For the dataset slide, use the wording in section 6 of `DATA_CARD.md`.
