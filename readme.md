# AquaTrace

### A Data-Driven Framework for Diagnosing and Prioritizing Data Center Water-Risk

Mini Project, Visualization of Data, Understanding and Interpretation (VDUI), PES University. Team 5.

**Live dashboard:** [ADD LINK AFTER DEPLOYMENT]
**Final presentation:** [ADD LINK OR FILE NAME]

---

## Problem statement

Data centers use large volumes of water for cooling, but facility-level water-use reporting is limited. This makes it hard for regulators, communities and sustainability planners to see where water risk is concentrated and what drives it.

AquaTrace focuses on **diagnosing and communicating** water risk. It does not try to reduce consumption directly.

**Research question:** Which characteristics most strongly predict high water risk? We look at cooling technology, geographic region, facility type and capacity.

## Dataset: AquaTrace Modelled Facility Panel

Facility-level water data is rarely disclosed, so we modelled operations on real locations and real water stress.

- 6,512 facility-year rows covering 1,200 facilities
- 2019 to 2025 (7 years), 43 columns

| Status | Fields | Basis |
| --- | --- | --- |
| Real | Countries and facility share, water-stress band, main competing water user | Global study of 9,347 data centres (country level) |
| Real | City locations, climate zone, temperature, humidity | Public location and climate data |
| Modelled | Facility type, capacity, cooling system, utilisation, AI share, commissioning year | Rules by facility type, climate and local stress |
| Modelled | PUE, WUE (litres per kWh of IT energy), daily electricity and water use | Calibrated to published Equinix, EU directive and Meta figures |
| Derived | Water-risk score and tier, model probabilities | Stress-weighted formula; out-of-fold model |

**Important:** operating values are modelled estimates, not measurements. The results demonstrate the method on realistic structure. They are not facts about individual facilities.

## Headline findings

These come from the Python exploratory analysis in `03_eda/`.

- Cooling system explains about **68%** of the variance in WUE.
- **40.6%** of Middle East and Africa facility-years are High risk, versus **5.5%** in Europe.
- **94%** of evaporative and chilled-water facility-years with 5 or more stress months are High risk.

## Dashboard

The Power BI dashboard is in `02_pbix/`. It follows a **martini glass** structure (Segel and Heer, 2010): a guided story first (hook, build-up, insight, conclusion), then slicers for free exploration.
<img width="1320" height="737" alt="image" src="https://github.com/user-attachments/assets/436a24ea-8183-434e-af13-4cf2fffd22f1" />
<img width="1332" height="762" alt="image" src="https://github.com/user-attachments/assets/a2af78cf-82e9-4558-8930-c4a6f3cb91aa" />
<img width="1310" height="742" alt="image" src="https://github.com/user-attachments/assets/d2096429-88f3-4339-8d2e-185473bebe42" />









## Design and accessibility

- **Shared theme** (`05_theme/aquatrace-theme.json`): Okabe-Ito colour-blind-safe palette and Segoe UI fonts, imported by every page author for consistency.
- **Risk tiers:** Low is blue (#0072B2), Medium is orange (#E69F00), High is vermillion (#D55E00). Tiers are never shown by colour alone: data labels and legends carry the same information.
- **Insight-sentence titles** state the finding, and subtitles say "modelled estimates" and give hints.
- **Alt text** on every visual and slicer.
- **Tab order** follows the reading order: headline numbers, then charts, then filters.
- **Contrast:** label text is white on blue and black on orange and vermillion.
- Review checklist: see `04_notes/accessibility-and-review-checklist.md`.


## Limitations

- All operating values are modelled estimates, not measured data.
- WUE counts on-site water only, so total water footprint (including the water used to generate electricity) may be understated.
- Air-cooled sites use less water but more electricity. The dataset does not capture this trade-off.
- SHAP values explain what the model learned, not real-world causes, because the data contains built-in rules.
- Correlated inputs (for example cooling and temperature, or region and stress) can distort feature attributions.


## Tech stack

- **Python:** data analysis and preprocessing (Pandas, NumPy, SciPy)
- **Matplotlib:** exploratory visualisation
- **Power BI:** interactive dashboard (DAX measures, Smart Narrative, bookmarks and page navigation)
- **Git and GitHub:** version control

## Folder structure

```
AQUATRACE_VDUI_PROJECT/
|
|-- 01_data/        Dataset and data files
|-- 02_pbix/        Power BI dashboard
|-- 03_eda/         Exploratory data analysis and visualizations
|-- 04_notes/       Project notes, accessibility and review checklist
|-- 05_theme/       Shared Power BI theme (aquatrace-theme.json)
|-- 06_usability/   Usability test kit and findings
|-- review_ppts/    Project presentation files
`-- readme.md       Project documentation
```

**Institution:** PES University

## References

1. Ristic, B., Madani, K. and Makuch, Z. (2015). The Water Footprint of Data Centers. *Sustainability*, 7.
2. Golebiowska, I., Opach, T. and Rod, J. K. (2020). Breaking the Eyes: How Do Users Get Started with a Coordinated and Multiple View Geovisualization Tool? *The Cartographic Journal*, 57(3).
3. Lundberg, S. M. and Lee, S.-I. (2017). A Unified Approach to Interpreting Model Predictions. *NIPS*.
4. Segel, E. and Heer, J. (2010). Narrative Visualization: Telling Stories with Data. *IEEE Transactions on Visualization and Computer Graphics*, 16(6).
5. Okabe, M. and Ito, K. Color Universal Design (colour-blind-safe palette).
