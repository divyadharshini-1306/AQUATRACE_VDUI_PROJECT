#!/usr/bin/env python3
"""
AquaTrace - Member 3 pipeline (AI + XAI).  All data are MODELLED ESTIMATES.

Run from anywhere:   python member3_pipeline.py
Options:             --model gb|xgboost   --n-boot 300   --skip-shap   --skip-embed

Steps
  1  Audit the existing model + build a stratified, facility-grouped out-of-fold (OOF) model
  2  Explainability: SHAP (OOF), permutation importance (held-out), comparison with EDA
  3  PCA + UMAP (t-SNE fallback) 2-D coordinates
  4  Drift test: train 2019-2023, test 2024-2025
  5  Limitations and bias panel: per-region metrics with facility-level bootstrap CIs,
     calibration, low-confidence share, error clusters
Outputs go to ./outputs (CSVs for Power BI, figures/ for PPT + paper, member3_summary.md).
"""
import argparse, sys, warnings, traceback
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.metrics import (balanced_accuracy_score, f1_score, average_precision_score, roc_auc_score,
                             brier_score_loss, confusion_matrix, precision_recall_curve)
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

SEED = 42
TARGET = "High_Risk"
CAT = ["Cooling_System", "Climate_Zone", "Facility_Type"]
NUM = ["IT_Capacity_MW", "Utilization_Pct", "AI_Workload_Share_Pct", "Ambient_Temp_C", "PUE", "Stress_Tier_Order"]
FEATURES = CAT + NUM                      # same 9 inputs as Member 1's model, so results reconcile
LEAKY = ["WUE_L_per_kWh", "Daily_Water_Use_m3", "Stress_Weight", "Water_Risk_Score"]  # define the target
assert not set(FEATURES) & set(LEAKY)

# Okabe-Ito based colour-blind-safe colours (suggestion for Member 4's theme as well)
TIER_COL = {"Low": "#0072B2", "Medium": "#F0E442", "High": "#D55E00"}
COOL_COL = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#000000", "#D55E00", "#999999"]
UP, DOWN = "#D55E00", "#0072B2"
FOOT = "Modelled estimates (locations and water stress are real; cooling, capacity, PUE, WUE, water use are modelled)"

HERE = Path(__file__).resolve().parent


class Tee:
    """Print to the terminal AND to a log file, so no shell redirection is needed."""
    def __init__(self, *streams): self.streams = streams
    def write(self, text):
        for st in self.streams: st.write(text)
    def flush(self):
        for st in self.streams: st.flush()
    def isatty(self): return False
    def __getattr__(self, name): return getattr(self.streams[0], name)
sec = lambda n, t: print(f"\n=== STEP {n}: {t} ===")


# ------------------------------------------------------------------ helpers
def make_model(kind):
    if kind == "xgboost":
        from xgboost import XGBClassifier
        return XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.1, subsample=0.8,
                             random_state=SEED, eval_metric="logloss", n_jobs=-1)
    return GradientBoostingClassifier(random_state=SEED)       # what Member 1 used


def col_groups(X):
    g = {c: [k for k in X.columns if k.startswith(c + "_")] for c in CAT}
    g.update({c: [c] for c in NUM})
    return g


def metrics(y, p, thr=0.5):
    y = np.asarray(y); p = np.asarray(p); pred = (p >= thr).astype(int)
    ok = len(np.unique(y)) == 2
    return dict(n=len(y), high_share=y.mean(), accuracy=(pred == y).mean(),
                majority_baseline_acc=max(y.mean(), 1 - y.mean()),
                balanced_accuracy=balanced_accuracy(y, pred),
                precision_high=_div(((pred == 1) & (y == 1)).sum(), (pred == 1).sum()),
                recall_high=_div(((pred == 1) & (y == 1)).sum(), (y == 1).sum()),
                f1_high=f1_score(y, pred, zero_division=0),
                pr_auc=average_precision_score(y, p) if y.sum() else np.nan,
                pr_auc_baseline=y.mean(),
                roc_auc=roc_auc_score(y, p) if ok else np.nan,
                brier=brier_score_loss(y, p))


def balanced_accuracy(y, pred):
    return balanced_accuracy_score(y, pred) if len(np.unique(y)) == 2 else np.nan


def _div(a, b):
    return a / b if b else np.nan


def savefig(fig, name, fig_dir, foot_y=-0.035):
    fig.text(0.01, foot_y, FOOT, fontsize=7, color="#555555")
    fig.savefig(fig_dir / name, dpi=200, bbox_inches="tight"); plt.close(fig)


# ------------------------------------------------------------------ STEP 1/2 cross-validation
def run_cv(d, X, y, groups, kind, cg, do_perm=False, do_shap=False):
    """Stratified, facility-grouped 5-fold CV. Same facility never in train and test of one fold."""
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    oof = np.zeros(len(d)); fold = np.zeros(len(d), int)
    perm_rows, sv_all, base_all = [], None, np.zeros(len(d))
    rng = np.random.default_rng(SEED)
    if do_shap:
        import shap
        sv_all = np.zeros(X.shape)
    for k, (tr, te) in enumerate(sgkf.split(X, y, groups)):
        m = make_model(kind).fit(X.iloc[tr], y.iloc[tr])
        Xte, yte = X.iloc[te], y.iloc[te]
        oof[te] = m.predict_proba(Xte)[:, 1]; fold[te] = k
        if do_perm:                                            # grouped permutation importance, held-out fold
            base = average_precision_score(yte, oof[te]); row = {}
            for g, cols in cg.items():
                drops = []
                for _ in range(5):
                    Xp = Xte.copy(); Xp[cols] = Xte[cols].values[rng.permutation(len(Xte))]
                    drops.append(base - average_precision_score(yte, m.predict_proba(Xp)[:, 1]))
                row[g] = np.mean(drops)
            perm_rows.append(row)
        if do_shap:                                            # SHAP from the model that never saw these rows
            ex = shap.TreeExplainer(m); sv = ex.shap_values(Xte)
            if isinstance(sv, list): sv = sv[-1]
            sv_all[te] = np.asarray(sv); base_all[te] = float(np.ravel(ex.expected_value)[-1])
    return oof, fold, (pd.DataFrame(perm_rows) if do_perm else None), sv_all, base_all


# ------------------------------------------------------------------ plots for steps 1-2
def plot_audit(y, p, thr, fig_dir):
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    cm = confusion_matrix(y, (p >= thr).astype(int)); rn = cm / cm.sum(1, keepdims=True)
    ax[0].imshow(rn, cmap="Blues", vmin=0, vmax=1)
    for i in range(2):
        for j in range(2):
            ax[0].text(j, i, f"{cm[i, j]:,}\n({rn[i, j]:.0%} of row)", ha="center", va="center",
                       color="white" if rn[i, j] > .5 else "black")
    ax[0].set_xticks([0, 1], ["Pred: not High", "Pred: High"]); ax[0].set_yticks([0, 1], ["Actual: not High", "Actual: High"])
    ax[0].set_title(f"Confusion matrix (OOF, threshold {thr})")
    pr, rc, _ = precision_recall_curve(y, p)
    ax[1].plot(rc, pr, color=DOWN, lw=2, label=f"Model (PR-AUC {average_precision_score(y, p):.2f})")
    ax[1].axhline(y.mean(), color="#555", ls="--", label=f"Baseline = prevalence ({y.mean():.2f})")
    ax[1].set_xlabel("Recall (High risk)"); ax[1].set_ylabel("Precision (High risk)")
    ax[1].set_title("Precision-recall curve"); ax[1].legend(); ax[1].set_ylim(0, 1.02)
    savefig(fig, "01_confusion_pr.png", fig_dir)


def plot_shap_bar(grp_abs, fig_dir):
    s = grp_abs.sort_values()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(s.index, s.values, color=DOWN)
    for i, v in enumerate(s.values): ax.text(v, i, f" {v:.3f}", va="center", fontsize=8)
    ax.set_xlabel("Mean |SHAP value| (log-odds of High risk)")
    ax.set_title("Global feature importance (SHAP, out-of-fold)")
    savefig(fig, "02_shap_global_bar.png", fig_dir)


def plot_local(contrib, base, prob, title, shown, path_name, fig_dir):
    c = contrib.reindex(contrib.abs().sort_values(ascending=False).index)[:8][::-1]
    fig, ax = plt.subplots(figsize=(7.5, 4))
    ax.barh([f"{k} = {shown[k]}" for k in c.index], c.values, color=[UP if v > 0 else DOWN for v in c.values])
    for i, v in enumerate(c.values): ax.text(v, i, f" {v:+.2f}", va="center", ha="left" if v > 0 else "right", fontsize=8)
    ax.axvline(0, color="k", lw=.8); ax.margins(x=.15)
    ax.set_xlabel("SHAP contribution (log-odds). Red raises, blue lowers P(High risk)")
    ax.set_title(f"{title}\nPredicted P(High) = {prob:.2f}  (average model output {base:+.2f} log-odds)", fontsize=10)
    savefig(fig, path_name, fig_dir)


def shap_section(d, X, cg, sv_all, base_all, oof, out, fig_dir, S):
    grp = pd.DataFrame({g: sv_all[:, [X.columns.get_loc(c) for c in cols]].sum(1) for g, cols in cg.items()})
    ex = pd.concat([d[["Facility_ID", "Year"]], pd.Series(base_all, name="SHAP_BaseValue")], axis=1)
    ex = pd.concat([ex, grp.add_prefix("SHAP_"), pd.Series(oof.round(4), name="M3_Pred_High_Risk_Prob")], axis=1)
    ex.round(4).to_csv(out / "shap_values.csv", index=False)
    mean_abs = grp.abs().mean()
    plot_shap_bar(mean_abs, fig_dir)
    try:                                                         # beeswarm on one-hot columns (standard shap API)
        import shap
        plt.figure(); shap.summary_plot(sv_all, X, max_display=15, show=False)
        plt.title("SHAP beeswarm (out-of-fold; red = high feature value)")
        plt.gcf().text(0.01, -0.02, FOOT, fontsize=7, color="#555555")
        plt.gcf().savefig(fig_dir / "03_shap_beeswarm.png", dpi=200, bbox_inches="tight"); plt.close("all")
    except Exception:
        print("  beeswarm failed (bar chart + local plots still made):"); traceback.print_exc()
    pred_c = (oof >= 0.5).astype(int); yy = d[TARGET].values; stress = d.Stress_Tier_Order.values
    def first(mask, fn):
        ix = np.where(mask)[0]; return fn(ix) if len(ix) else None
    tp = (yy == 1) & (pred_c == 1)
    cases = [("1_correct_High", "Correct High", first(tp & (stress < 4) if (tp & (stress < 4)).any() else tp, lambda ix: ix[np.argmax(oof[ix])])),
             ("2_missed_High", "Missed High (false negative)", first((yy == 1) & (pred_c == 0), lambda ix: ix[np.argmin(oof[ix])])),
             ("3_false_alarm", "False alarm (false positive)", first((yy == 0) & (pred_c == 1), lambda ix: ix[np.argmax(oof[ix])])),
             ("4_borderline", "Borderline", first(np.ones(len(d), bool), lambda ix: ix[np.argmin(np.abs(oof[ix] - 0.5))])),
             ("5_correct_not_High_Extreme_stress", "Correct not-High at Extreme stress", first((yy == 0) & (pred_c == 0) & (stress == 4), lambda ix: ix[np.argmax(oof[ix])]))]
    rec = []
    for old in fig_dir.glob("04_shap_local_*.png"):   # remove plots from earlier runs
        old.unlink()
    for tag, label, i in cases:
        if i is None: continue
        row = d.loc[i]; shown = {g: (row[g] if g in CAT else round(row[g], 2)) for g in cg}
        ttl = f"{label}: {row.Facility_ID} ({row.City}, {row.Year})\nActual: {'High' if yy[i] else 'not High'}; model says {'High' if pred_c[i] else 'not High'}"
        plot_local(grp.loc[i], base_all[i], oof[i], ttl, shown, f"04_shap_local_{tag}_{row.Facility_ID}_{row.Year}.png", fig_dir)
        rec.append(dict(Case=label, Facility_ID=row.Facility_ID, Year=row.Year, City=row.City, Actual_High=int(yy[i]), M3_Pred_Prob=round(float(oof[i]), 4)))
    pd.DataFrame(rec).to_csv(out / "shap_local_cases.csv", index=False)
    S["shap_top_features"] = mean_abs.sort_values(ascending=False).round(3).to_dict()
    return mean_abs


# ------------------------------------------------------------------ importance comparison
def importance_table(cg, perm_mean, shap_abs, mi_path, fig_dir, out):
    t = pd.DataFrame({"Feature": list(cg)})
    t["Perm_Importance_OOF"] = t.Feature.map(perm_mean)
    if shap_abs is not None: t["SHAP_MeanAbs"] = t.Feature.map(shap_abs)
    mi = pd.read_csv(mi_path).set_index("Feature")
    t["Member1_InSample_Importance"] = t.Feature.map(mi.Model_Importance)
    rho, eta = t.Feature.map(mi.EDA_Spearman_with_Risk_Score), t.Feature.map(mi.EDA_Variance_Explained)
    t["EDA_Strength"] = np.where(rho.notna(), rho ** 2, eta)          # rho^2 and eta^2 are both "share explained"
    t["EDA_Strength_Basis"] = np.where(rho.notna(), "Spearman rho^2", "eta^2")
    basis = "SHAP_MeanAbs" if shap_abs is not None else "Perm_Importance_OOF"
    t["Model_Rank"] = t[basis].rank(ascending=False, method="min").astype(int)
    t["EDA_Rank"] = t.EDA_Strength.rank(ascending=False, method="min").astype(int)
    diff = t.Model_Rank - t.EDA_Rank
    t["Verdict"] = np.select([diff.abs() <= 1, diff.abs() >= 3], ["Agree", "Diverge"], "Partly agree")
    t["Divergence_Direction"] = np.where(t.Verdict == "Diverge", np.where(diff > 0, "EDA ranks it higher", "Model ranks it higher"), "")
    t = t.sort_values("Model_Rank").round(4); t.to_csv(out / "feature_importance_comparison.csv", index=False)
    cols = [basis, "Perm_Importance_OOF", "Member1_InSample_Importance", "EDA_Strength"]
    cols = list(dict.fromkeys(cols)); lab = {basis: basis.replace("_", " "), "Perm_Importance_OOF": "Permutation (held-out)",
            "Member1_InSample_Importance": "Member 1 (in-sample perm.)", "EDA_Strength": "EDA (rho^2 / eta^2)"}
    fig, ax = plt.subplots(figsize=(9, 5)); h = .8 / len(cols); y0 = np.arange(len(t))
    for j, c in enumerate(cols):
        v = t[c].clip(lower=0) / t[c].clip(lower=0).max()
        ax.barh(y0 + j * h, v, h, label=lab[c], color=COOL_COL[j])
    ax.set_yticks(y0 + .4 - h / 2, t.Feature); ax.invert_yaxis(); ax.set_xlabel("Importance, scaled so each method's top feature = 1")
    ax.set_title("Do the model and the EDA agree on what matters?"); ax.legend(fontsize=8)
    savefig(fig, "05_importance_comparison.png", fig_dir)
    return t


# ------------------------------------------------------------------ STEP 3 embeddings
def embeddings(d, out, fig_dir, S):
    Z = np.hstack([StandardScaler().fit_transform(d[NUM]), pd.get_dummies(d[CAT], dtype=float).values])
    pca = PCA(2, random_state=SEED); P = pca.fit_transform(Z)
    S["pca_explained_var"] = pca.explained_variance_ratio_.round(3).tolist()
    try:
        import umap
        E = umap.UMAP(n_neighbors=30, min_dist=.1, random_state=SEED).fit_transform(Z); nm = "UMAP"
    except ImportError:
        from sklearn.manifold import TSNE
        print("  umap-learn not installed -> using t-SNE (pip install umap-learn to get UMAP)")
        E = TSNE(2, perplexity=30, init="pca", random_state=SEED).fit_transform(Z); nm = "TSNE"
    S["embed_method"] = nm
    emb = d[["Facility_ID", "Year"]].copy()
    emb["PC1"], emb["PC2"], emb[nm + "1"], emb[nm + "2"] = P[:, 0], P[:, 1], E[:, 0], E[:, 1]
    emb.round(4).to_csv(out / "embeddings.csv", index=False)
    fig, ax = plt.subplots(2, 2, figsize=(12, 10))
    for r, (xy, nmx) in enumerate([(P, "PCA"), (E, nm)]):
        for t, c in TIER_COL.items():
            m = (d.Water_Risk_Tier == t).values
            ax[r, 0].scatter(xy[m, 0], xy[m, 1], s=6, c=c, alpha=.6 if t != "High" else .9, label=t, edgecolors="none")
        for k, cs in enumerate(sorted(d.Cooling_System.unique())):
            m = (d.Cooling_System == cs).values
            ax[r, 1].scatter(xy[m, 0], xy[m, 1], s=6, c=COOL_COL[k], alpha=.6, label=cs, edgecolors="none")
        ax[r, 0].set_title(f"{nmx}, coloured by risk tier"); ax[r, 1].set_title(f"{nmx}, coloured by cooling system")
        for a in ax[r]: a.set_xlabel(f"{nmx} 1"); a.set_ylabel(f"{nmx} 2"); a.legend(markerscale=3, fontsize=8)
    fig.suptitle("2-D views of the facility-years. Shapes reflect how the data were modelled, not proof of real-world structure.\n"
                 f"PCA: PC1 + PC2 explain {pca.explained_variance_ratio_.sum():.0%} of the variance. Tight UMAP streaks are likely the same facility across years.", y=.99)
    savefig(fig, "06_embeddings.png", fig_dir)
    return pca


# ------------------------------------------------------------------ STEP 4 drift
def psi(a, b, eps=1e-4):
    cats = sorted(set(a) | set(b))
    pa = np.array([(a == c).mean() for c in cats]).clip(eps); pb = np.array([(b == c).mean() for c in cats]).clip(eps)
    return float(((pb - pa) * np.log(pb / pa)).sum())


def psi_numeric(a, b, bins=10):
    edges = np.unique(np.quantile(a, np.linspace(0, 1, bins + 1))); edges[0], edges[-1] = -np.inf, np.inf
    pa = np.histogram(a, edges)[0] / len(a); pb = np.histogram(b, edges)[0] / len(b)
    pa, pb = pa.clip(1e-4), pb.clip(1e-4)
    return float(((pb - pa) * np.log(pb / pa)).sum())


def drift(d, X, y, kind, oof, thr, out, fig_dir, S):
    tr, te = (d.Year <= 2023).values, (d.Year >= 2024).values
    rows = []
    for f in FEATURES:
        a, b = d.loc[tr, f], d.loc[te, f]
        if f in CAT or f == "Stress_Tier_Order":
            rows.append(dict(Feature=f, Type="categorical/ordinal", PSI=psi(a.values, b.values), KS_stat=np.nan, KS_p=np.nan))
        else:
            ks = stats.ks_2samp(a, b)
            rows.append(dict(Feature=f, Type="numeric", PSI=psi_numeric(a.values, b.values), KS_stat=ks.statistic, KS_p=ks.pvalue))
    dr = pd.DataFrame(rows)
    dr["PSI_Status"] = pd.cut(dr.PSI, [-1, .1, .25, 99], labels=["Stable (<0.1)", "Moderate (0.1-0.25)", "Major (>0.25)"])
    dr["Train_High_Share"] = y[tr].mean(); dr["Test_High_Share"] = y[te].mean()
    dr.round(4).to_csv(out / "drift_results.csv", index=False)
    m = make_model(kind).fit(X[tr], y[tr]); p = m.predict_proba(X[te])[:, 1]
    first_year = d.groupby("Facility_ID").Year.transform("min")
    unseen = (first_year[te] >= 2024).values                       # facilities the training years never saw
    ev = {"OOF predictions on the same 2024-25 rows": metrics(y[te], oof[te], thr),
          "Temporal split: all 2024-25 rows": metrics(y[te], p, thr)}
    if unseen.sum() > 20 and y[te][unseen].sum() > 0:
        ev["Temporal split: only facilities first seen in 2024-25"] = metrics(y[te][unseen], p[unseen], thr)
    mm = pd.DataFrame(ev).T.reset_index().rename(columns={"index": "Evaluation"})
    mm.round(4).to_csv(out / "drift_model_metrics.csv", index=False)
    S["drift_metrics"] = mm[["Evaluation", "n", "high_share", "pr_auc", "recall_high", "precision_high", "f1_high"]].round(3)
    S["drift_psi"] = dr[["Feature", "PSI", "PSI_Status"]].round(3)
    S["drift_high_share"] = (round(y[tr].mean(), 3), round(y[te].mean(), 3))
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    s = dr.sort_values("PSI")
    ax[0].barh(s.Feature, s.PSI, color=DOWN); ax[0].axvline(.1, ls="--", c="#555"); ax[0].axvline(.25, ls="--", c="#D55E00")
    ax[0].set_xlabel("PSI, train 2019-23 vs test 2024-25 (dashed: 0.1 and 0.25)"); ax[0].set_title("Feature drift")
    w = mm.set_index("Evaluation")[["pr_auc", "recall_high", "precision_high"]]
    w.index = [i.replace(": ", ":\n").replace("predictions on", "pred. on") for i in w.index]
    w.plot.bar(ax=ax[1], color=[DOWN, "#E69F00", "#009E73"], rot=0); ax[1].set_ylim(0, 1.15); ax[1].set_yticks([0, .2, .4, .6, .8, 1.0]); ax[1].set_ylabel("Score (High-risk class)")
    ax[1].set_title("Does performance hold on later years?"); ax[1].tick_params(axis="x", labelsize=7)
    ax[1].legend(["PR-AUC", "Recall", "Precision"], fontsize=8, loc="upper center", ncol=3)
    savefig(fig, "07_drift.png", fig_dir)


# ------------------------------------------------------------------ STEP 5 limitations + bias
def _m(y, p, thr):
    pred = p >= thr; tp = (pred & (y == 1)).sum()
    return dict(recall=_div(tp, (y == 1).sum()), precision=_div(tp, pred.sum()),
                pr_auc=average_precision_score(y, p) if y.sum() else np.nan, accuracy=(pred == y).mean())


def boot_ci(fac_ids, y, p, thr, n_boot, seed):
    """Facility-level (cluster) bootstrap: rows of one facility are correlated, so resample whole facilities."""
    idx = list(pd.Series(np.arange(len(y))).groupby(np.asarray(fac_ids)).apply(lambda s: s.values))
    rng = np.random.default_rng(seed); res = {k: [] for k in ["recall", "precision", "pr_auc", "accuracy"]}
    for _ in range(n_boot):
        pick = np.concatenate([idx[i] for i in rng.integers(0, len(idx), len(idx))])
        for k, v in _m(y[pick], p[pick], thr).items(): res[k].append(v)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return {k: (np.nanpercentile(v, 2.5), np.nanpercentile(v, 97.5)) if not np.all(np.isnan(v)) else (np.nan, np.nan) for k, v in res.items()}


def group_table(d, col, p, thr, n_boot, min_high_rows=30, min_high_fac=10):
    rows = []
    for g, sub in d.groupby(col):
        ii = sub.index.values; y = sub[TARGET].values; pp = p[ii]; pred = pp >= thr
        nh, nhf = int(y.sum()), sub.loc[sub[TARGET] == 1, "Facility_ID"].nunique()
        r = {col: g, "n_rows": len(sub), "n_facilities": sub.Facility_ID.nunique(),
             "n_countries": sub.Country.nunique(), "n_high_rows": nh, "n_high_facilities": nhf,
             "false_positives": int((pred & (y == 0)).sum()), "false_negatives": int((~pred & (y == 1)).sum()),
             "error_rate": round((pred != y).mean(), 4), "low_confidence_share": round((np.maximum(pp, 1 - pp) < .8).mean(), 4)}
        if nh < min_high_rows or nhf < min_high_fac:
            r["status"] = f"Insufficient data ({nh} High rows from {nhf} facilities)"
        else:
            r["status"] = "OK"; pt = _m(y, pp, thr); ci = boot_ci(sub.Facility_ID.values, y, pp, thr, n_boot, SEED)
            for k in pt: r[k] = round(pt[k], 4); r[k + "_lo"] = round(ci[k][0], 4); r[k + "_hi"] = round(ci[k][1], 4)
        rows.append(r)
    return pd.DataFrame(rows)


def plot_bias(reg, fig_dir):
    reg = reg.sort_values("n_rows"); fig, ax = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for a, k, t in [(ax[0], "recall", "Recall: share of true High found"), (ax[1], "precision", "Precision: share of flagged that are High")]:
        for i, (_, r) in enumerate(reg.iterrows()):
            lab = f"{r.Region}\n({r.n_high_rows} High rows)"
            if r.status == "OK":
                a.errorbar(r[k], i, xerr=[[r[k] - r[k + "_lo"]], [r[k + "_hi"] - r[k]]], fmt="o", color=DOWN, capsize=4)
                a.text(r[k + "_hi"] + .02, i, f"{r[k]:.2f}", va="center", fontsize=8)
            else:
                a.text(.02, i, "Insufficient data", va="center", fontsize=9, style="italic", color="#444")
        a.set_yticks(range(len(reg)), [f"{r.Region}\n({r.n_high_rows} High rows)" for _, r in reg.iterrows()])
        a.set_xlim(0, 1.15); a.set_ylim(-.6, len(reg) - .4); a.set_xlabel("Score with 95% CI (facility bootstrap)"); a.set_title(t)
    fig.suptitle("Model performance by region (out-of-fold)", y=1.02)
    savefig(fig, "08_bias_by_region.png", fig_dir)


def calibration(y, p, out, fig_dir):
    qb = pd.qcut(p, 10, duplicates="drop"); c = pd.DataFrame({"y": y, "p": p, "bin": qb}).groupby("bin", observed=True).agg(
        mean_predicted=("p", "mean"), fraction_high=("y", "mean"), n=("y", "size")).reset_index(drop=True)
    c.round(4).to_csv(out / "calibration.csv", index=False)
    ub = np.minimum((p * 10).astype(int), 9); ece = sum((ub == b).mean() * abs(y[ub == b].mean() - p[ub == b].mean()) for b in range(10) if (ub == b).any())
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].plot([0, 1], [0, 1], "--", c="#555", label="Perfect calibration"); ax[0].plot(c.mean_predicted, c.fraction_high, "o-", c=DOWN, label="Model (decile bins)")
    ax[0].set_xlabel("Mean predicted P(High)\n(most rows sit near 0 or 1, so the middle rests on few points)"); ax[0].set_ylabel("Observed share High"); ax[0].legend(); ax[0].set_title(f"Reliability (ECE {ece:.3f})")
    conf = np.maximum(p, 1 - p); ax[1].hist(conf, bins=30, color=DOWN); ax[1].axvline(.8, ls="--", c="#D55E00")
    ax[1].set_xlabel("Model confidence (dashed = 0.8 low-confidence cut-off)"); ax[1].set_ylabel("Facility-years")
    ax[1].set_title(f"{(conf < .8).mean():.1%} of rows are low-confidence")
    fig.subplots_adjust(wspace=0.3)
    savefig(fig, "09_calibration.png", fig_dir, foot_y=-0.14)
    return ece  
# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE.parent / "01_data" / "aquatrace_powerbi.csv"))
    ap.add_argument("--importance", default=str(HERE.parent / "01_data" / "model_importance.csv"))
    ap.add_argument("--out", default=str(HERE / "outputs"))
    ap.add_argument("--model", default="gb", choices=["gb", "xgboost"])
    ap.add_argument("--n-boot", type=int, default=300)
    ap.add_argument("--thr", type=float, default=0.5)
    ap.add_argument("--skip-shap", action="store_true"); ap.add_argument("--skip-embed", action="store_true")
    a = ap.parse_args()
    out = Path(a.out); fig_dir = out / "figures"; fig_dir.mkdir(parents=True, exist_ok=True)
    log = open(out / "run_log.txt", "w")
    sys.stdout, sys.stderr = Tee(sys.__stdout__, log), Tee(sys.__stderr__, log)
    d = pd.read_csv(a.data).reset_index(drop=True); S = {}
    assert not d.duplicated(["Facility_ID", "Year"]).any()
    X = pd.get_dummies(d[FEATURES], dtype=float); y = d[TARGET]; cg = col_groups(X)
    try:
        import shap; have_shap = not a.skip_shap
    except ImportError:
        have_shap = False; print("NOTE: 'shap' not installed -> SHAP outputs skipped. Run: pip install shap")

    sec(1, "Audit + stratified, facility-grouped out-of-fold model")
    print(f"rows {len(d)}, facilities {d.Facility_ID.nunique()}, High share {y.mean():.3f}")
    oof, fold, perm, sv_all, base_all = run_cv(d, X, y, d.Facility_ID, a.model, cg, do_perm=True, do_shap=have_shap)
    rows = {"Member 1 column (GroupKFold)": metrics(y, d.Pred_High_Risk_Prob, a.thr),
            f"Member 3 OOF (StratifiedGroupKFold, {a.model})": metrics(y, oof, a.thr)}
    leak = X.copy()
    for c in ["WUE_L_per_kWh", "Daily_Water_Use_m3", "Stress_Weight"]: leak[c] = d[c]
    lo, *_ = run_cv(d, leak, y, d.Facility_ID, a.model, {})
    rows["DEMO ONLY: with WUE + water use + stress weight (target leakage)"] = metrics(y, lo, a.thr)
    so, *_ = run_cv(d, X[["Stress_Tier_Order"]], y, d.Facility_ID, a.model, {})
    rows["Ablation: Stress_Tier_Order ONLY"] = metrics(y, so, a.thr)
    ns, *_ = run_cv(d, X.drop(columns=["Stress_Tier_Order"]), y, d.Facility_ID, a.model, {})
    rows["Ablation: everything EXCEPT Stress_Tier_Order"] = metrics(y, ns, a.thr)
    aud = pd.DataFrame(rows).T.reset_index().rename(columns={"index": "Model"}); aud.round(4).to_csv(out / "audit_metrics.csv", index=False)
    print(aud[["Model", "accuracy", "majority_baseline_acc", "balanced_accuracy", "recall_high", "precision_high", "pr_auc", "roc_auc"]].round(3).to_string(index=False))
    S["audit"] = aud[["Model", "accuracy", "majority_baseline_acc", "balanced_accuracy", "recall_high", "precision_high", "f1_high", "pr_auc", "roc_auc", "brier"]].round(3)
    pr, rc, th = precision_recall_curve(y, oof); f1s = 2 * pr * rc / (pr + rc + 1e-12)
    S["best_f1_threshold"] = (round(float(th[np.nanargmax(f1s[:-1])]), 3), round(float(np.nanmax(f1s[:-1])), 3))
    pred = pd.DataFrame({"Facility_ID": d.Facility_ID, "Year": d.Year, "M3_Fold": fold,
                         "M3_Pred_High_Risk_Prob": oof.round(4), "M3_Pred_High_Risk": (oof >= a.thr).astype(int),
                         "M3_Model_Confidence": np.maximum(oof, 1 - oof).round(4)})
    pred["M3_Low_Confidence_Flag"] = (pred.M3_Model_Confidence < .8).astype(int)
    pred["M3_Prediction_Error_Flag"] = (pred.M3_Pred_High_Risk != y).astype(int)
    pred.to_csv(out / "oof_predictions.csv", index=False)
    plot_audit(y.values, oof, a.thr, fig_dir)

    sec(2, "Explainability: SHAP, permutation importance, EDA comparison")
    shap_abs = None
    if have_shap:
        try: shap_abs = shap_section(d, X, cg, sv_all, base_all, oof, out, fig_dir, S)
        except Exception: print("  SHAP section failed:"); traceback.print_exc()
    imp = importance_table(cg, perm.mean(), shap_abs, a.importance, fig_dir, out)
    print(imp[[c for c in ["Feature", "SHAP_MeanAbs", "Perm_Importance_OOF", "EDA_Strength", "Model_Rank", "EDA_Rank", "Verdict"] if c in imp]].to_string(index=False))
    S["importance"] = imp[["Feature", "Perm_Importance_OOF"] + (["SHAP_MeanAbs"] if shap_abs is not None else []) + ["EDA_Strength", "Model_Rank", "EDA_Rank", "Verdict", "Divergence_Direction"]]

    sec(3, "PCA + UMAP/t-SNE")
    if a.skip_embed: print("skipped")
    else: embeddings(d, out, fig_dir, S)

    sec(4, "Drift: train 2019-2023, test 2024-2025")
    drift(d, X, y.values, a.model, oof, a.thr, out, fig_dir, S)
    print(S["drift_metrics"].to_string(index=False)); print(S["drift_psi"].to_string(index=False))

    sec(5, "Limitations and bias")
    reg = group_table(d, "Region", oof, a.thr, a.n_boot); reg.to_csv(out / "bias_by_region.csv", index=False)
    oth = pd.concat([group_table(d, c, oof, a.thr, a.n_boot).rename(columns={c: "Group"}).assign(Dimension=c)
                     for c in ["Cooling_System", "Facility_Type", "Stress_Tier_Baseline"]])
    oth.to_csv(out / "bias_by_other_groups.csv", index=False)
    ece = calibration(y.values, oof, out, fig_dir); plot_bias(reg, fig_dir)
    S["bias_region"] = reg; S["bias_other"] = oth; S["ece"] = round(ece, 4)
    S["low_conf"] = round(pred.M3_Low_Confidence_Flag.mean(), 4); S["errors"] = int(pred.M3_Prediction_Error_Flag.sum())
    print(reg[["Region", "n_rows", "n_facilities", "n_high_rows", "status", "recall", "precision"]].to_string(index=False))

    # ---- summary file
    with open(out / "member3_summary.md", "w") as f:
        f.write("# Member 3 results (modelled estimates)\n\n")
        for k, v in S.items():
            f.write(f"## {k}\n```\n{v.to_string(index=False) if isinstance(v, pd.DataFrame) else v}\n```\n")
    print(f"\nDone. Outputs in {out}"); log.flush()


if __name__ == "__main__":
    main()