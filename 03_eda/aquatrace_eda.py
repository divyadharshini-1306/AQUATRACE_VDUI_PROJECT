"""
AquaTrace - Exploratory Data Analysis (Member 1)
Run:  python aquatrace_eda.py  [path_to_aquatrace_powerbi.csv]
Needs: pandas, numpy, scipy, matplotlib
Outputs: printed findings + CSV tables + PNG charts in ./eda_output/

NOTE: the data are MODELLED ESTIMATES (see DATA_CARD.md). Findings describe the model,
not measured facilities. Cooling -> WUE and stress -> risk are built into the generator.
"""
import sys, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

PATH = sys.argv[1] if len(sys.argv) > 1 else "aquatrace_powerbi.csv"
OUT = "eda_output"
os.makedirs(OUT, exist_ok=True)
d = pd.read_csv(PATH)
NOTE = "Modelled estimates"

def section(t):
    print("\n" + "=" * 70 + "\n" + t + "\n" + "=" * 70)

# ---------------------------------------------------------------- 1. data checks
section("1. DATA CHECKS")
print("shape:", d.shape)
print("null cells:", int(d.isna().sum().sum()))
print("duplicate rows:", int(d.duplicated().sum()))
print("duplicate (Facility_ID, Year):", int(d.duplicated(["Facility_ID", "Year"]).sum()))
print("facilities:", d.Facility_ID.nunique(), "| years:", d.Year.min(), "-", d.Year.max())
print("WUE range:", d.WUE_L_per_kWh.min(), "-", d.WUE_L_per_kWh.max(),
      "| PUE range:", d.PUE.min(), "-", d.PUE.max())
print("risk tier share (%):\n", (d.Water_Risk_Tier.value_counts(normalize=True) * 100).round(1).to_string())

# ---------------------------------------------------------------- 2. trends
section("2. TREND BY YEAR")
d["IT_MWh"] = d.Daily_Electricity_MWh / d.PUE
yr = d.groupby("Year").agg(
    facility_rows=("Facility_ID", "count"),
    total_water_m3=("Daily_Water_Use_m3", "sum"),
    total_electricity_MWh=("Daily_Electricity_MWh", "sum"),
    it_mwh=("IT_MWh", "sum"),
    avg_ai_share=("AI_Workload_Share_Pct", "mean"),
    high_risk_pct=("High_Risk", lambda x: 100 * x.mean()))
yr["weighted_WUE"] = yr.total_water_m3 / yr.it_mwh
yr["water_per_facility_m3"] = yr.total_water_m3 / yr.facility_rows
yr = yr.drop(columns="it_mwh").round(3)
print(yr.to_string())
g_w = yr.total_water_m3.iloc[-1] / yr.total_water_m3.iloc[0]
g_f = yr.facility_rows.iloc[-1] / yr.facility_rows.iloc[0]
g_p = yr.water_per_facility_m3.iloc[-1] / yr.water_per_facility_m3.iloc[0]
print(f"\n2019->2025: total water x{g_w:.2f} | facilities in panel x{g_f:.2f} | water per facility x{g_p:.2f}")
print("=> part of the rise is simply more facilities being added (stylised, not a real growth rate).")
yr.to_csv(f"{OUT}/trend_by_year.csv")

# ---------------------------------------------------------------- 3. cooling
section("3. WUE BY COOLING SYSTEM")
cool = d.groupby("Cooling_System").agg(
    rows=("WUE_L_per_kWh", "size"), mean_WUE=("WUE_L_per_kWh", "mean"),
    median_WUE=("WUE_L_per_kWh", "median"), mean_PUE=("PUE", "mean"),
    high_risk_pct=("High_Risk", lambda x: 100 * x.mean())).sort_values("mean_WUE", ascending=False).round(3)
print(cool.to_string())
cool.to_csv(f"{OUT}/wue_by_cooling.csv")
ratio = cool.mean_WUE.max() / cool.mean_WUE.min()
print(f"\nhighest / lowest mean WUE = {ratio:.1f}x")

# ---------------------------------------------------------------- 4. correlations
section("4. CORRELATION WITH WATER-RISK SCORE AND WITH WUE")
nums = ["IT_Capacity_MW", "Utilization_Pct", "AI_Workload_Share_Pct", "Ambient_Temp_C",
        "Relative_Humidity_Pct", "PUE", "Stress_Tier_Order"]
rows = []
for c in nums:
    rows.append(dict(feature=c,
                     spearman_with_risk_score=spearmanr(d[c], d.Water_Risk_Score)[0],
                     spearman_with_WUE=spearmanr(d[c], d.WUE_L_per_kWh)[0]))
corr = pd.DataFrame(rows).round(3).sort_values("spearman_with_risk_score", key=abs, ascending=False)
print(corr.to_string(index=False))
corr.to_csv(f"{OUT}/spearman_correlations.csv", index=False)

def eta2(col, target):
    gm = d.groupby(col)[target].transform("mean")
    return ((gm - d[target].mean()) ** 2).sum() / ((d[target] - d[target].mean()) ** 2).sum()

cats = ["Cooling_System", "Climate_Zone", "Facility_Type", "Region", "Stress_Tier_Baseline"]
eta = pd.DataFrame({"feature": cats,
                    "eta2_risk_score": [eta2(c, "Water_Risk_Score") for c in cats],
                    "eta2_WUE": [eta2(c, "WUE_L_per_kWh") for c in cats]}).round(3)
print("\nShare of variance explained (eta squared):")
print(eta.sort_values("eta2_risk_score", ascending=False).to_string(index=False))
eta.to_csv(f"{OUT}/eta_squared.csv", index=False)
print("\nCaution: risk score is built from stress, WUE and water volume, so stress and cooling")
print("correlate with it by construction. Use WUE-based columns to see the cooling effect alone.")

# ---------------------------------------------------------------- 5. risk by region / stress / cooling
section("5. HIGH-RISK SHARE BY REGION, STRESS AND COOLING")
reg = (pd.crosstab(d.Region, d.Water_Risk_Tier, normalize="index") * 100).round(1)
print(reg.to_string())
reg.to_csv(f"{OUT}/risk_tier_by_region.csv")
st = d.groupby("Stress_Tier_Baseline").High_Risk.mean().mul(100).round(1)
print("\nHigh-risk % by baseline stress tier:\n", st.to_string())
heat = (d.pivot_table(index="Cooling_System", columns="Stress_Tier_Baseline", values="High_Risk",
                      aggfunc="mean") * 100).round(1)
heat = heat[[c for c in ["Low", "Moderate", "High", "Extreme"] if c in heat.columns]]
cnt = d.pivot_table(index="Cooling_System", columns="Stress_Tier_Baseline", values="High_Risk",
                    aggfunc="size")
print("\nHigh-risk % by cooling x stress tier:\n", heat.to_string())
print("\nRows in each cell (small cells are unreliable):\n", cnt.to_string())
heat.to_csv(f"{OUT}/high_risk_cooling_x_stress.csv")
hs = d[d.Stress_Months_Baseline >= 5]
ev = hs[hs.Cooling_System.isin(["Evaporative", "Chilled Water"])]
print(f"\nFacility-years with >=5 stress months: {len(hs)} | "
      f"of those on Evaporative or Chilled Water: {len(ev)} ({100*len(ev)/max(len(hs),1):.0f}%)")
print(f"High-risk share in that group: {100*ev.High_Risk.mean():.1f}% "
      f"vs {100*d.High_Risk.mean():.1f}% overall")

# ---------------------------------------------------------------- 6. outliers
section("6. WUE OUTLIERS (Tukey rule on log WUE, within cooling system)")
lw = np.log(d.WUE_L_per_kWh)
g = lw.groupby(d.Cooling_System)
q1, q3 = g.transform(lambda x: x.quantile(.25)), g.transform(lambda x: x.quantile(.75))
iqr = q3 - q1
d["out_high"] = (lw > q3 + 1.5 * iqr).astype(int)
d["out_low"] = (lw < q1 - 1.5 * iqr).astype(int)
print("matches WUE_Outlier_Flag in the file:",
      bool(((d.out_high | d.out_low) == d.WUE_Outlier_Flag).all()))
out = d.groupby("Cooling_System").agg(rows=("out_high", "size"), high=("out_high", "sum"),
                                      low=("out_low", "sum")).assign(
    outlier_pct=lambda x: (100 * (x.high + x.low) / x.rows).round(2))
print(out.to_string())
out.to_csv(f"{OUT}/outliers_by_cooling.csv")
o = d[d.WUE_Outlier_Flag == 1]
print(f"\nTotal outliers: {len(o)} ({100*len(o)/len(d):.2f}% of rows)")
if len(o):
    print("Mean temp / humidity: outliers", round(o.Ambient_Temp_C.mean(), 1), "/",
          round(o.Relative_Humidity_Pct.mean(), 1), "| all rows",
          round(d.Ambient_Temp_C.mean(), 1), "/", round(d.Relative_Humidity_Pct.mean(), 1))
    print("Outliers by climate zone:\n", o.Climate_Zone.value_counts().to_string())
    print("Outliers by year:\n", o.Year.value_counts().sort_index().to_string())

# ---------------------------------------------------------------- 7. model vs EDA
section("7. DO MODEL AND EDA AGREE? (from model_importance.csv)")
mp_path = os.path.join(os.path.dirname(os.path.abspath(PATH)), "model_importance.csv")
if os.path.exists(mp_path):
    mp = pd.read_csv(mp_path)
    mp["model_rank"] = mp.Model_Importance.rank(ascending=False, method="min").astype(int)
    mp["eda_strength"] = mp.EDA_Spearman_with_Risk_Score.abs().fillna(mp.EDA_Variance_Explained)
    mp["eda_rank"] = mp.eda_strength.rank(ascending=False, method="min").astype(int)
    print(mp[["Feature", "Model_Importance", "model_rank", "eda_strength", "eda_rank"]].to_string(index=False))
    print("\nNote: eda_strength mixes |Spearman| (numeric) and eta squared (categorical).")
    print("Treat the ranks as a rough guide. Both methods put water stress first.")
else:
    print("model_importance.csv not found next to the data file - skipped.")

# ---------------------------------------------------------------- 8. charts
section("8. CHARTS")
plt.rcParams.update({"font.size": 11})

# a) WUE by cooling (box, log axis)
order = cool.index.tolist()
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.boxplot([d.loc[d.Cooling_System == c, "WUE_L_per_kWh"] for c in order], vert=False,
           labels=order, showfliers=True)
ax.set_xscale("log"); ax.invert_yaxis()
ax.set_xlabel("WUE (litres per kWh of IT energy, log scale)")
ax.set_title(f"WUE spread by cooling system ({NOTE})")
fig.tight_layout(); fig.savefig(f"{OUT}/wue_by_cooling_box.png", dpi=160); plt.close(fig)

# b) correlations with risk score
c2 = corr.sort_values("spearman_with_risk_score")
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.barh(c2.feature, c2.spearman_with_risk_score, color="#2a78d6")
ax.axvline(0, color="grey", lw=0.8)
ax.set_xlabel("Spearman correlation with water-risk score")
ax.set_title(f"Numeric drivers of water-risk score ({NOTE})")
fig.tight_layout(); fig.savefig(f"{OUT}/correlations.png", dpi=160); plt.close(fig)

# c) high-risk % cooling x stress heatmap
fig, ax = plt.subplots(figsize=(7, 4.2))
im = ax.imshow(heat.values, cmap="Reds", aspect="auto", vmin=0, vmax=100)
ax.set_xticks(range(heat.shape[1])); ax.set_xticklabels(heat.columns)
ax.set_yticks(range(heat.shape[0])); ax.set_yticklabels(heat.index)
for i in range(heat.shape[0]):
    for j in range(heat.shape[1]):
        v = heat.values[i, j]
        if not np.isnan(v):
            ax.text(j, i, f"{v:.0f}%", ha="center", va="center", color="white" if v > 50 else "black")
ax.set_xlabel("Baseline water-stress tier"); ax.set_title(f"High-risk share by cooling and stress ({NOTE})")
fig.colorbar(im, ax=ax, label="% High risk"); fig.tight_layout()
fig.savefig(f"{OUT}/high_risk_heatmap.png", dpi=160); plt.close(fig)

# d) trend
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(yr.index, yr.total_water_m3 / 1e3, marker="o", color="#2a78d6", label="Total daily water (thousand m3)")
ax.plot(yr.index, yr.water_per_facility_m3 / 10, marker="s", color="#eb6834", label="Water per facility (x10 m3)")
ax.set_ylim(bottom=0); ax.set_xlabel("Year"); ax.legend()
ax.set_title(f"Stylised trend, fleet grows as facilities are added ({NOTE})")
fig.tight_layout(); fig.savefig(f"{OUT}/trend.png", dpi=160); plt.close(fig)
print("saved charts and CSV tables in", OUT)
