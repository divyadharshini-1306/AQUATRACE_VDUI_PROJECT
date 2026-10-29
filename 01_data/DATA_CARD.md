# AquaTrace Modelled Dataset – Data Card

**File:** `aquatrace_dataset.csv` · 6,512 rows · 1,200 facilities · 2019–2025 · 30 columns
**Status:** Modelled estimates built on real location, climate and water-stress data and calibrated to published operator/EU figures. Every row has `Data_Basis = Modelled estimate`. Reproduce with `generate_dataset.py` (seed 42).

## 1. What is real and what is generated

| Part | Status | Source |
|---|---|---|
| Country list, facility share per country | Real (weighting only) | `SummaryByCountry.xlsx` |
| Water-stress band of each facility (0 / 1–4 / 5–8 / 9–12 months), baseline and +3 °C | Sampled from the **real country distributions** | `SummaryByCountry.xlsx` |
| Main overlapping water-user sector | Real (country level) | `SummaryByCountry.xlsx` |
| City locations, climate zone, mean temperature, humidity | Real locations; temperature/humidity values come from the uploaded file | `data_centre_wue.csv` |
| Facility type, capacity, cooling system, utilisation, AI share, PUE, WUE, daily energy/water, commissioning year, yearly panel, risk score/tier | **Modelled estimates** | rules in section 3 |
| Facility IDs and names | Invented (no real operator names are used) | – |

Check: the generated facilities reproduce the real stress shares: 24.8 % with ≥1 stress month (real 24.8 %) and 15.0 % with ≥5 months (real 14.5 %).

## 2. Sources and how each was used

**Real data inputs (your uploads)**
1. `SummaryByCountry.xlsx` – 149 countries, 9,347 data centers, facilities per water-stress band under baseline and +3 °C, overlapping sectors. The total (9,347) matches the facility count of the study *"One Quarter of Global Data Centers are Located in Water-Stressed Areas"* (ACS Environmental Science & Technology; results on Zenodo, record 22912911), so it appears to be that study's data. Confirm against your own source before citing it.
2. `data_centre_wue.csv` – 1,094 rows / 90 locations, originally from GitHub `Sarvesjr/datacenter-wue`. Only 30 of its rows are labelled real company-report values; the rest are physics-simulated. Used here for locations and climate only.

**Published figures used to calibrate the generated values** (parameters are informed by these, not copied from them)
3. Equinix reports a 2025 global WUE of 0.91 L/kWh and 1.41 L/kWh for evaporative-cooled sites (cited in the Wikipedia article "Water usage effectiveness"). → evaporative mean ≈ 1.5, fleet mean ≈ 0.7–0.8.
4. EU Energy Efficiency Directive data, 770 sites: PUE 1.36, WUE 0.58 L/kWh (as summarised in GitHub `DumitruAndriuta/data-centre-water-energy`, citing COM(2026) 500). → fleet PUE ≈ 1.3–1.36, fleet WUE ≈ 0.7.
5. Meta reports WUE 0.19 L/kWh for 2024 (greencalculus.com "Data Center Water Usage", from the open dataset `greencalculus/data-center-water-benchmarks`, CC BY 4.0). → consistent with the low WUE for air-side/liquid cooling.
6. Cooling-technology spectrum table in *AI Data Centers and the Water Use Feedback Loop* (arXiv 2606.21760, Table 3): evaporative highest water use, hybrid lower, dry cooling ≈ 0 direct water but a power penalty. → ordering of cooling systems. **My values are lower than that table's engineering ranges** because I calibrated to operator-reported fleet figures (items 3–5).
7. Wevolver, *Data Center Cooling Design* – closed-loop liquid cooling can cut water use by up to 70 %. → liquid cooling gets low WUE and low PUE.
8. US DOE/LBNL *2024 United States Data Center Energy Usage Report* – PUE and WUE depend on cooling system, space type and climate. → structure of the model (numeric ranges not copied).
9. IEA figures via gradually.ai (415 TWh in 2024, 485 TWh in 2025 for all data centers). → direction of the trend only.

**Design references (no data copied)**
10. Kaggle *Global Data Center & AI Water/Electricity Usage* (`ashyou09/global-data-center-and-ai-waterelectricity-usage`) – column design (year, PUE, WUE, daily use, stress tier, cooling type). Its own description says operational metrics are modelled.
11. WRI Aqueduct 4.0 – the concept of baseline water stress. Not used numerically.

## 3. Generation rules

- **Facilities:** 1,200, allocated to countries in proportion to (real data-center count)^0.85. A city is chosen from that country's real locations; coordinates get ±0.05° (about 5 km) jitter, so map points are city-level, not real facility addresses.
- **Type mix:** Hyperscale 22 %, Colocation 33 %, Enterprise 24 %, Edge 13 %, AI/HPC Campus 8 % (assumption). Capacity is log-normal per type (median IT MW: 60 / 15 / 4 / 1.2 / 120).
- **Commissioning year:** random, weighted toward recent years (AI/HPC from 2020). Rows exist only from 2019 on and only once a facility is commissioned, so the panel is unbalanced. New sites ramp up over three years.
- **Cooling system:** depends on type, climate (cold → more air-side; hot → more evaporative/chilled) and local water stress (stressed sites favour hybrid/liquid). From 2022, 6 %/year of evaporative/chilled-water sites in stressed regions retrofit to hybrid.
- **WUE:** base by cooling (Evaporative 1.45, Chilled 0.85, Hybrid 0.55, Air-side 0.15, Liquid 0.20 L/kWh) × temperature effect × type factor × AI-load effect, −2 %/year efficiency drift, plus facility-level and yearly noise.
- **PUE:** base by cooling (1.14–1.45) + type offset + temperature effect − 0.004/year + noise.
- **Daily values:** IT energy = capacity × utilisation × 24 h; electricity = IT energy × PUE; water (m³) = IT energy (MWh) × WUE.
- **Risk:** `Water_Risk_Score = 100 × (0.25 + 0.75 × stress weight) × (0.5·WUE percentile + 0.5·water-volume percentile)`, stress weight Low 0, Moderate 0.35, High 0.7, Extreme 1.0. The 0.25 floor keeps facilities in unstressed places distinguishable by how much water they use. Tiers: Low < 20, Medium 20–35, High ≥ 35. This is the "water-stress-weighted tier" rather than a raw WUE threshold.

## 4. Column dictionary

`Facility_ID`, `Facility_Name`, `Year`, `Country`, `City`, `Latitude`, `Longitude`, `Climate_Zone`, `Facility_Type`, `Year_Commissioned`, `Cooling_System`, `IT_Capacity_MW`, `Utilization_Pct`, `AI_Workload_Share_Pct`, `Ambient_Temp_C`, `Relative_Humidity_Pct`, `PUE`, `WUE_L_per_kWh` (on-site, L per kWh IT), `Daily_Electricity_MWh`, `Daily_Water_Use_m3`, `Stress_Months_Baseline`, `Stress_Tier_Baseline` (Low/Moderate/High/Extreme), `Stress_Months_3C`, `Stress_Tier_3C`, `Main_Overlap_Sector`, `Data_Basis`, `Stress_Weight`, `Water_Risk_Score`, `Water_Risk_Tier`, `High_Risk` (1 = High tier).

## 5. Known limits (state these in your project)

1. **Modelled operational data.** PUE, WUE, capacity, cooling system and the yearly panel are model estimates, not measurements. Findings describe this model, not real facilities.
2. **Built-in relationships.** Cooling → WUE, and stress → risk, are written into the rules. Feature importances partly recover them. Frame the model as a *method demonstration*.
3. **Trend is stylised.** Total electricity grows about 3.6× from 2019 to 2025 in this 1,200-facility panel (partly because facilities are added over time). That is steeper than published global estimates, so do not quote it as a real growth rate.
4. **Stress is country-level.** Facilities get a band sampled from their country's distribution, not a basin-level value.
5. **Class balance.** About 71 % Low / 17 % Medium / 11 % High, because about 75 % of facilities sit in unstressed countries. Use stratified splits or class weights.
6. **Not an official statistic.** Do not describe it as "18,110 real facility records" or as measured data.

## 6. Suggested wording for your slides

> "We built a 6,512-row facility-year panel (1,200 facilities, 2019–2025). Facility locations, climate and water-stress exposure come from real data (global data-center water-stress study, 9,347 facilities); operational metrics (cooling system, capacity, PUE, WUE, daily use) are modelled estimates calibrated to published operator and EU averages. The dashboard demonstrates the diagnostic method; results are estimates, not measurements of individual facilities."

## 7. Power BI preparation (`prepare_powerbi.py` → `aquatrace_powerbi.csv`)

Load **`aquatrace_powerbi.csv`** into Power BI (43 columns). It adds to the base file:

| Column(s) | Purpose |
|---|---|
| `Region` | Region → Country → City drill-down |
| `Water_Stress_Index`, `Water_Stress_Index_3C` | Stress months ÷ 12 (0 to 1), a normalised version of the stress months for the risk-score slide |
| `Risk_Tier_Order`, `Stress_Tier_Order`, `Stress_Tier_3C_Order`, `Cooling_Order` | Sort Low/Medium/High (and stress tiers, cooling by WUE) correctly instead of alphabetically |
| `WUE_Outlier_Flag` | EDA: WUE outside the Tukey fence (1.5 × IQR on log WUE) within its cooling system |
| `Pred_High_Risk_Prob`, `Pred_High_Risk`, `Model_Confidence`, `Low_Confidence_Flag` (< 0.8), `Prediction_Error_Flag` | Model output. Probabilities are out-of-fold (5-fold, grouped by facility, so no facility is scored by a model that saw it) |

`model_importance.csv` holds grouped permutation importance from the model next to the EDA statistics (Spearman correlation or variance explained), for the "do the two methods agree?" slide.

**Model inputs exclude** `WUE_L_per_kWh`, `Daily_Water_Use_m3`, `Stress_Weight` and `Water_Risk_Score`, because those define the target. Do the same in Power BI's Key Influencers visual: analyse `High_Risk` (is 1) using Cooling_System, Climate_Zone, Facility_Type, IT_Capacity_MW, Utilization_Pct, AI_Workload_Share_Pct, Ambient_Temp_C, PUE, Region/Country and Stress_Tier_Baseline.

The model is scikit-learn GradientBoosting, not XGBoost (not installed here). Swap in `xgboost.XGBClassifier` in your own notebook if your deck says XGBoost.
