"""Meilenstein 1 - Explorative Datenanalyse.

Erzeugt alle EDA-Abbildungen (results/figures/eda_*.png), Tabellen und eine
Faktensammlung (results/tables/eda_facts.json), auf die sich der Bericht stützt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.stats import chi2  # noqa: E402
from sklearn.covariance import MinCovDet  # noqa: E402
from sklearn.decomposition import PCA  # noqa: E402
from sklearn.ensemble import RandomForestClassifier  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import StratifiedKFold, cross_val_predict  # noqa: E402
from sklearn.neighbors import KNeighborsClassifier, NearestNeighbors  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from dp2 import config as C  # noqa: E402
from dp2 import data as D  # noqa: E402
from dp2 import viz as V  # noqa: E402
from dp2.features import vegetation_indices  # noqa: E402

facts: dict = {}
raw_tr, raw_te = D.load_raw()
ds = D.load()
tr, te, bands, wl = ds.train, ds.test, ds.bands, ds.wl
X, T = ds.X_train, ds.X_test

# ---------------------------------------------------------------- Überblick
all_bands = D.band_columns(raw_tr)
facts["n_train_raw"], facts["n_test"] = len(raw_tr), len(raw_te)
facts["n_train"] = len(tr)
facts["n_bands_total"], facts["n_bands_used"] = len(all_bands), len(bands)
facts["dropped_bands_nm"] = [int(b[1:]) for b in ds.dropped_bands]
facts["n_duplicates"] = ds.n_duplicates
partial = {b: int(raw_tr[b].isna().sum()) for b in bands if raw_tr[b].isna().any()}
facts["sporadic_missing_train"] = partial
facts["sporadic_missing_test"] = {b: int(raw_te[b].isna().sum()) for b in bands if raw_te[b].isna().any()}
facts["valid_ranges_nm"] = [[int(wl[s[0]]), int(wl[s[-1]])] for s in D.segments(wl)]
facts["reflectance_range"] = [float(X.min()), float(X.max())]

counts = pd.crosstab(tr.Crop, tr.Stage).reindex(index=C.CROPS, columns=C.STAGES).fillna(0).astype(int)
counts.to_csv(C.TABLES / "class_counts_crop_stage.csv")
facts["crop_counts"] = tr.Crop.value_counts().reindex(C.CROPS).to_dict()
facts["stage_counts"] = tr.Stage.value_counts().reindex(C.STAGES).to_dict()
facts["n_combo_classes"] = int((counts > 0).sum().sum())
facts["smallest_combos"] = tr.Combo.value_counts().tail(5).to_dict()
facts["imbalance_ratio_crop"] = float(tr.Crop.value_counts().max() / tr.Crop.value_counts().min())
facts["imbalance_ratio_combo"] = float(tr.Combo.value_counts().max() / tr.Combo.value_counts().min())

# ---------------------------------------------------------------- 1 Klassenverteilung
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), gridspec_kw={"width_ratios": [1, 1.1, 1.6]})
vc = tr.Crop.value_counts().reindex(C.CROPS)
axes[0].bar([C.CROP_DE[c] for c in C.CROPS], vc.values, color=[C.CROP_COLORS[c] for c in C.CROPS])
axes[0].set_title("Kulturpflanzen (Crop)")
plt.setp(axes[0].get_xticklabels(), rotation=30, ha="right")
for i, v in enumerate(vc.values):
    axes[0].text(i, v + 20, str(v), ha="center", fontsize=8)
vs = tr.Stage.value_counts().reindex(C.STAGES)
axes[1].bar([C.STAGE_DE[s] for s in C.STAGES], vs.values, color=[C.STAGE_COLORS[s] for s in C.STAGES])
axes[1].set_title("Entwicklungsstadien (Stage)")
plt.setp(axes[1].get_xticklabels(), rotation=35, ha="right")
for i, v in enumerate(vs.values):
    axes[1].text(i, v + 20, str(v), ha="center", fontsize=8)
im = axes[2].imshow(np.where(counts.values > 0, counts.values, np.nan), cmap="YlGn", aspect="auto")
axes[2].set_xticks(range(len(C.STAGES)), [C.STAGE_DE[s] for s in C.STAGES], rotation=35, ha="right")
axes[2].set_yticks(range(len(C.CROPS)), [C.CROP_DE[c] for c in C.CROPS])
axes[2].grid(False)
for i in range(len(C.CROPS)):
    for j in range(len(C.STAGES)):
        v = counts.values[i, j]
        axes[2].text(j, i, str(v) if v else "–", ha="center", va="center", fontsize=9,
                     color="#c62828" if 0 < v < 60 else ("white" if v > 350 else "#222"),
                     fontweight="bold" if 0 < v < 60 else "normal")
axes[2].set_title("Crop × Stage: 23 von 30 Kombinationen belegt (rot: < 60 Proben)")
fig.subplots_adjust(wspace=0.42)
V.savefig(fig, "eda_class_distribution")

# ---------------------------------------------------------------- 2 Metadaten
fig, axes = plt.subplots(1, 3, figsize=(15, 3.8))
for ax, (a, b, title) in zip(axes, [("Crop", "AEZ", "Crop × agroökologische Zone"),
                                    ("Crop", "Month", "Crop × Aufnahmemonat"),
                                    ("Stage", "Month", "Stage × Aufnahmemonat")]):
    ct = pd.crosstab(tr[a], tr[b])
    ct = ct.reindex(C.CROPS if a == "Crop" else C.STAGES)
    ax.imshow(np.log1p(ct.values), cmap="Greens", aspect="auto")
    ax.set_xticks(range(ct.shape[1]), ct.columns)
    lab = [C.CROP_DE[c] for c in ct.index] if a == "Crop" else [C.STAGE_DE[s] for s in ct.index]
    ax.set_yticks(range(ct.shape[0]), lab)
    ax.set_xlabel(b)
    ax.set_title(title)
    ax.grid(False)
    for i in range(ct.shape[0]):
        for j in range(ct.shape[1]):
            ax.text(j, i, int(ct.values[i, j]) or "·", ha="center", va="center", fontsize=8)
V.savefig(fig, "eda_metadata")
facts["crop_aez"] = {c: sorted(tr.loc[tr.Crop == c, "AEZ"].unique().tolist()) for c in C.CROPS}
facts["crop_month"] = {c: sorted(tr.loc[tr.Crop == c, "Month"].unique().tolist()) for c in C.CROPS}

# Wie viel verraten die Metadaten allein? (Obergrenze durch Nachschlagen)
meta_key = tr.AEZ.astype(str) + "_" + tr.Month.astype(str)
for target in ("Crop", "Stage", "Combo"):
    ct = pd.crosstab(meta_key, tr[target])
    majority = ct.idxmax(axis=1)
    pred = meta_key.map(majority)
    from sklearn.metrics import balanced_accuracy_score
    facts[f"meta_only_lookup_bacc_{target.lower()}"] = float(balanced_accuracy_score(tr[target], pred))

# ---------------------------------------------------------------- 3 Spektren je Crop
fig, ax = plt.subplots(figsize=(11, 4.6))
V.shade_gaps(ax)
for c in C.CROPS:
    m = tr.Crop == c
    q25, q50, q75 = np.percentile(X[m.values], [25, 50, 75], axis=0)
    V.fill_segments(ax, wl, q25, q75, color=C.CROP_COLORS[c], alpha=0.12, lw=0)
    V.plot_segments(ax, wl, q50, color=C.CROP_COLORS[c], lw=2, label=f"{C.CROP_DE[c]} (n={m.sum()})")
V.label_regions(ax)
ax.set_xlabel("Wellenlänge [nm]")
ax.set_ylabel("Reflexion [%]")
ax.set_title("Median-Spektren je Kulturpflanze (Band: Interquartilsabstand)", pad=16)
ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.14))
ax.set_xlim(420, 2420)
V.savefig(fig, "eda_spectra_crop")

# ---------------------------------------------------------------- 4 Spektren je Stage innerhalb Crop
fig, axes = plt.subplots(2, 3, figsize=(15, 7.5), sharex=True, sharey=True)
for ax, c in zip(axes.flat, C.CROPS):
    V.shade_gaps(ax, label=False)
    for s in C.STAGES:
        m = ((tr.Crop == c) & (tr.Stage == s)).values
        if m.sum() == 0:
            continue
        V.plot_segments(ax, wl, np.median(X[m], axis=0), color=C.STAGE_COLORS[s], lw=1.8,
                        label=f"{C.STAGE_DE[s]} ({m.sum()})")
    ax.set_title(C.CROP_DE[c])
    ax.legend(fontsize=7, loc="upper right")
    ax.set_xlim(420, 2420)
ax = axes.flat[-1]
V.shade_gaps(ax, label=False)
for s in C.STAGES:
    m = (tr.Stage == s).values
    V.plot_segments(ax, wl, np.median(X[m], axis=0), color=C.STAGE_COLORS[s], lw=1.8, label=C.STAGE_DE[s])
ax.set_title("alle Kulturen")
ax.legend(fontsize=7)
for ax in axes[-1]:
    ax.set_xlabel("Wellenlänge [nm]")
for ax in axes[:, 0]:
    ax.set_ylabel("Reflexion [%] (Median)")
fig.suptitle("Phänologie im Spektrum: vom bodendominierten Auflaufen über die Vollbedeckung zur Seneszenz",
             fontweight="bold")
V.savefig(fig, "eda_spectra_stage_per_crop")

# ---------------------------------------------------------------- 5 Vegetationsindizes
VI = vegetation_indices(X, wl)
VI["Crop"], VI["Stage"] = tr.Crop.values, tr.Stage.values
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=False)
for ax, idx, ttl in zip(axes, ["NDVI", "NDMI", "PSRI"],
                        ["NDVI (Grünbiomasse)", "NDMI (Blattwasser, 860/1650 nm)", "PSRI (Seneszenz)"]):
    data, pos, cols = [], [], []
    for j, s in enumerate(C.STAGES):
        for i, c in enumerate(C.CROPS):
            v = VI.loc[(VI.Crop == c) & (VI.Stage == s), idx].values
            if len(v):
                data.append(v); pos.append(j * 6 + i); cols.append(C.CROP_COLORS[c])
    bp = ax.boxplot(data, positions=pos, widths=0.8, patch_artist=True, showfliers=False)
    for patch, col in zip(bp["boxes"], cols):
        patch.set_facecolor(col); patch.set_alpha(0.75)
    ax.set_xticks([j * 6 + 2 for j in range(len(C.STAGES))], [C.STAGE_DE[s] for s in C.STAGES],
                  rotation=30, ha="right")
    ax.set_title(ttl)
handles = [plt.Rectangle((0, 0), 1, 1, color=C.CROP_COLORS[c]) for c in C.CROPS]
fig.legend(handles, [C.CROP_DE[c] for c in C.CROPS], ncol=5, loc="lower center", bbox_to_anchor=(0.5, -0.08))
V.savefig(fig, "eda_indices")
facts["ndvi_median_by_combo"] = VI.groupby(["Crop", "Stage"]).NDVI.median().round(3).unstack().to_dict()

# ---------------------------------------------------------------- 6 Korrelation der Bänder + PCA
corr = np.corrcoef(X.T)
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
im = axes[0].imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
ticks = np.linspace(0, len(wl) - 1, 10).astype(int)
axes[0].set_xticks(ticks, wl[ticks].astype(int), rotation=90)
axes[0].set_yticks(ticks, wl[ticks].astype(int))
axes[0].grid(False)
axes[0].set_title("Korrelation der 131 Bänder")
fig.colorbar(im, ax=axes[0], fraction=0.046)
Z = StandardScaler().fit_transform(X)
pca = PCA(n_components=20, random_state=C.SEED).fit(Z)
cum = np.cumsum(pca.explained_variance_ratio_)
axes[1].bar(range(1, 21), pca.explained_variance_ratio_, color="#607D8B", label="je Komponente")
axes[1].plot(range(1, 21), cum, "o-", color="#E8743B", label="kumuliert")
axes[1].axhline(0.99, ls="--", color="#999", lw=1)
axes[1].set_xlabel("Hauptkomponente")
axes[1].set_ylabel("erklärte Varianz")
axes[1].set_title("PCA: wenige Komponenten tragen fast die ganze Varianz")
axes[1].legend()
V.savefig(fig, "eda_correlation_pca")
facts["pca_cumvar"] = {int(k): float(cum[k - 1]) for k in (1, 2, 3, 5, 10, 20)}
adj = np.array([corr[i, i + 1] for i in range(len(wl) - 1)])
facts["median_adjacent_band_corr"] = float(np.median(adj))

P2 = pca.transform(Z)[:, :2]
fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
for c in C.CROPS:
    m = (tr.Crop == c).values
    axes[0].scatter(P2[m, 0], P2[m, 1], s=5, alpha=0.5, color=C.CROP_COLORS[c], label=C.CROP_DE[c])
for s in C.STAGES:
    m = (tr.Stage == s).values
    axes[1].scatter(P2[m, 0], P2[m, 1], s=5, alpha=0.5, color=C.STAGE_COLORS[s], label=C.STAGE_DE[s])
for ax, t in zip(axes, ["nach Crop", "nach Stage"]):
    ax.set_xlabel(f"PC1 ({pca.explained_variance_ratio_[0]:.0%})")
    ax.set_ylabel(f"PC2 ({pca.explained_variance_ratio_[1]:.0%})")
    ax.set_title(f"PCA der Spektren {t}")
    ax.legend(markerscale=3, fontsize=8)
V.savefig(fig, "eda_pca_scatter")

# ---------------------------------------------------------------- 7 Klassenüberlappung (nur Spektren)
# 5-NN in standardisiertem Spektralraum, leave-one-out über Kreuzvalidierung:
# Wie gut trennt das Spektrum *allein* die Kulturen innerhalb jedes Stadiums?
skf = StratifiedKFold(5, shuffle=True, random_state=C.SEED)
knn = KNeighborsClassifier(n_neighbors=5)
pred_crop = cross_val_predict(knn, Z, tr.Crop.values, cv=skf)
sep = []
for s in C.STAGES:
    m = (tr.Stage == s).values
    sep.append((s, (pred_crop[m] == tr.Crop.values[m]).mean(), m.sum()))
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.bar([C.STAGE_DE[s] for s, _, _ in sep], [a for _, a, _ in sep],
       color=[C.STAGE_COLORS[s] for s, _, _ in sep])
for i, (_, a, n) in enumerate(sep):
    ax.text(i, a + 0.01, f"{a:.0%}", ha="center", fontsize=9)
ax.set_ylim(0, 1.05)
ax.set_ylabel("Crop-Trefferquote (5-NN, nur Spektrum)")
ax.set_title("Kulturen sind im Spektrum am schwersten zu trennen, wenn Boden dominiert")
ax.tick_params(axis="x", rotation=20)
V.savefig(fig, "eda_crop_separability_by_stage")
facts["knn_crop_acc_by_stage"] = {s: float(a) for s, a, _ in sep}
facts["knn_crop_acc_overall_spectra_only"] = float((pred_crop == tr.Crop.values).mean())

# Crop-Verwechslungen des Spektrum-kNN
from sklearn.metrics import confusion_matrix  # noqa: E402
cm = confusion_matrix(tr.Crop, pred_crop, labels=C.CROPS)
fig = V.plot_confusion(cm, [C.CROP_DE[c] for c in C.CROPS], "5-NN nur Spektrum: Crop-Verwechslungen",
                       fontsize=9)
V.savefig(fig, "eda_knn_crop_confusion")

# ---------------------------------------------------------------- 8 Ausreißer
# (a) Robuste Mahalanobis-Distanz je Klasse: nur zur Begründung, warum sie hier
#     NICHT taugt - die Klassen sind multimodal (mehrere Felder/Szenen je Klasse),
#     die robuste Kovarianz passt nur den Hauptmodus an und markiert ~1/3 der Daten.
P10 = PCA(n_components=10, random_state=C.SEED).fit_transform(Z)
n_mcd = 0
for cls, idx in tr.groupby("Combo").indices.items():
    if len(idx) >= 30:
        d2 = MinCovDet(random_state=C.SEED).fit(P10[idx]).mahalanobis(P10[idx])
        n_mcd += int((d2 > chi2.ppf(0.999, df=10)).sum())
facts["outliers_mcd_naive"] = n_mcd
# (b) Local Outlier Factor je Crop×Stage (dichtebasiert, verträgt mehrere Modi):
#     LOF > 2 heißt: Punkt liegt in einer mehr als doppelt so dünn besetzten
#     Umgebung wie seine Nachbarn.
from sklearn.neighbors import LocalOutlierFactor  # noqa: E402
lof = np.zeros(len(tr))
for cls, idx in tr.groupby("Combo").indices.items():
    lo = LocalOutlierFactor(n_neighbors=min(20, len(idx) - 1)).fit(P10[idx])
    lof[idx] = -lo.negative_outlier_factor_
flag = lof > 2.0
# (c) physikalisch unplausibel: "Late"/"Critical" (volle Bedeckung) mit NDVI < 0.2
implaus = (VI.Stage.isin(["Late", "Critical"]) & (VI.NDVI < 0.2)).values
facts["outliers_lof"] = int(flag.sum())
facts["outliers_lof_by_combo"] = tr.loc[flag, "Combo"].value_counts().head(10).to_dict()
facts["implausible_low_ndvi_vegetative"] = int(implaus.sum())
facts["implausible_by_combo"] = tr.loc[implaus, "Combo"].value_counts().to_dict()
facts["outliers_union"] = int((flag | implaus).sum())
pd.DataFrame({"id": tr.id, "Combo": tr.Combo, "lof": lof.round(3), "flag_lof": flag,
              "NDVI": VI.NDVI.round(3), "flag_low_ndvi": implaus}).to_csv(
    C.TABLES / "outlier_flags.csv", index=False)

fig, axes = plt.subplots(1, 2, figsize=(14, 4.4))
ax = axes[0]
V.shade_gaps(ax, label=False)
cls = tr.loc[flag, "Combo"].value_counts().index[0]
m = (tr.Combo == cls).values
q = np.percentile(X[m & ~flag], [5, 50, 95], axis=0)
V.fill_segments(ax, wl, q[0], q[2], color="#90A4AE", alpha=0.35, lw=0)
V.plot_segments(ax, wl, q[1], color="#37474F", lw=2, label=f"{cls}: Median (5–95 %)")
for i in np.where(m & flag)[0][:12]:
    V.plot_segments(ax, wl, X[i], color="#D32F2F", lw=0.8, alpha=0.7)
ax.plot([], [], color="#D32F2F", label=f"markierte Ausreißer ({(m & flag).sum()})")
ax.set_title(f"Ausreißer (Local Outlier Factor > 2) – Beispielklasse {cls}")
ax.set_xlabel("Wellenlänge [nm]"); ax.set_ylabel("Reflexion [%]")
ax.legend(fontsize=8)
ax = axes[1]
V.shade_gaps(ax, label=False)
for i in np.where(implaus)[0][:40]:
    V.plot_segments(ax, wl, X[i], color="#8D6E63", lw=0.7, alpha=0.6)
mm = (VI.Stage.isin(["Late", "Critical"]) & (VI.NDVI >= 0.5)).values
V.plot_segments(ax, wl, np.median(X[mm], axis=0), color="#2E7D32", lw=2.5, label="typisch Late/Critical")
ax.plot([], [], color="#8D6E63", label=f"Late/Critical mit NDVI < 0,2 ({implaus.sum()})")
ax.set_title("Plausibilitätsprüfung: 'volle Bedeckung' mit Bodenspektrum")
ax.set_xlabel("Wellenlänge [nm]")
ax.legend(fontsize=8)
V.savefig(fig, "eda_outliers")

# ---------------------------------------------------------------- 9 Train vs. Test
# (a) adversarielle Validierung: lässt sich Train von Test unterscheiden?
XA = np.vstack([np.c_[X, tr[["AEZ", "Month"]].values], np.c_[T, te[["AEZ", "Month"]].values]])
ya = np.r_[np.zeros(len(X)), np.ones(len(T))]
proba = cross_val_predict(RandomForestClassifier(300, n_jobs=-1, random_state=C.SEED), XA, ya,
                          cv=StratifiedKFold(5, shuffle=True, random_state=C.SEED),
                          method="predict_proba")[:, 1]
facts["adversarial_auc"] = float(roc_auc_score(ya, proba))
# (b) Abstand zum nächsten Trainingsspektrum
nn_ = NearestNeighbors(n_neighbors=2).fit(Z)
d_tr = nn_.kneighbors(Z)[0][:, 1]
Zt = StandardScaler().fit(X).transform(T)
d_te = NearestNeighbors(n_neighbors=1).fit(Z).kneighbors(Zt)[0][:, 0]
facts["nn_dist_median_train_train"] = float(np.median(d_tr))
facts["nn_dist_median_test_train"] = float(np.median(d_te))
facts["test_share"] = {"AEZ": (te.AEZ.value_counts() / (tr.AEZ.value_counts() + te.AEZ.value_counts())).round(3).to_dict(),
                       "Month": (te.Month.value_counts() / (tr.Month.value_counts() + te.Month.value_counts())).round(3).to_dict()}
fig, axes = plt.subplots(1, 2, figsize=(12, 3.8))
bins = np.linspace(0, np.percentile(d_tr, 99), 50)
axes[0].hist(d_tr, bins, alpha=0.6, density=True, label="Train → nächstes Train (ohne sich selbst)")
axes[0].hist(d_te, bins, alpha=0.6, density=True, label="Test → nächstes Train")
axes[0].set_xlabel("Abstand zum nächsten Nachbarn (standardisiert)")
axes[0].set_title("Abstand zum nächsten Trainingsspektrum")
axes[0].legend(fontsize=8)
share = pd.DataFrame({"Train": tr.Month.value_counts(normalize=True), "Test": te.Month.value_counts(normalize=True)}).sort_index()
share.plot.bar(ax=axes[1], color=["#607D8B", "#E8743B"])
axes[1].set_title(f"Monatsanteile (adversarielle AUC = {facts['adversarial_auc']:.2f})")
axes[1].set_xlabel("Monat")
axes[1].tick_params(axis="x", rotation=0)
V.savefig(fig, "eda_train_vs_test")

# ---------------------------------------------------------------- 10 Phänologie je Crop (Stage × Monat)
fig, axes = plt.subplots(1, 5, figsize=(17, 3.4), sharey=True)
for ax, c in zip(axes, C.CROPS):
    ct = pd.crosstab(tr.loc[tr.Crop == c, "Stage"], tr.loc[tr.Crop == c, "Month"]).reindex(
        index=C.STAGES, columns=[5, 6, 7, 8, 9, 10]).fillna(0)
    ax.imshow(np.log1p(ct.values), cmap="Greens", aspect="auto")
    ax.set_xticks(range(6), [5, 6, 7, 8, 9, 10])
    ax.set_yticks(range(6), [C.STAGE_DE[s] for s in C.STAGES])
    ax.set_title(C.CROP_DE[c])
    ax.grid(False)
    for i in range(6):
        for j in range(6):
            if ct.values[i, j]:
                ax.text(j, i, int(ct.values[i, j]), ha="center", va="center", fontsize=7)
    ax.set_xlabel("Monat")
fig.suptitle("Phänologie: Stadium je Aufnahmemonat (Winterweizen: Auflaufen im Herbst)", fontweight="bold")
V.savefig(fig, "eda_phenology")

# 912/915 nm: Überlappung von VNIR- und SWIR-Detektor
i1, i2 = bands.index("X912"), bands.index("X915")
facts["corr_912_915"] = float(np.corrcoef(X[:, i1], X[:, i2])[0, 1])

with open(C.TABLES / "eda_facts.json", "w") as f:
    json.dump(facts, f, indent=2, ensure_ascii=False, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps({k: facts[k] for k in ["n_train", "n_test", "n_bands_used", "n_duplicates",
                                         "adversarial_auc", "outliers_lof", "outliers_mcd_naive",
                                         "implausible_low_ndvi_vegetative", "knn_crop_acc_by_stage",
                                         "meta_only_lookup_bacc_crop", "meta_only_lookup_bacc_stage",
                                         "meta_only_lookup_bacc_combo", "pca_cumvar",
                                         "nn_dist_median_train_train", "nn_dist_median_test_train"]},
                 indent=1, ensure_ascii=False, default=str))
