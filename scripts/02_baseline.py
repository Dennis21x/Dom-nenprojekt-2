"""Meilenstein 1 - Baseline-Klassifikator mit 70/30-Split.

Baseline = Random Forest auf den 131 bereinigten Bändern + AEZ + Monat,
kombinierte Zielklasse Crop×Stage (Flat). Bewusst ohne Tuning und ohne
Feature Engineering - das ist der Referenzpunkt für alle späteren Verbesserungen.

Zwei 70/30-Splits (siehe dp2.evaluation):
  * stratifiziert zufällig  (entspricht dem Testdatensatz)
  * Cluster-Split           (strenger: ganze Spektral-Cluster ≈ Felder getrennt)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import confusion_matrix  # noqa: E402

from dp2 import config as C  # noqa: E402
from dp2 import data as D  # noqa: E402
from dp2 import viz as V  # noqa: E402
from dp2.evaluation import holdout_cluster, holdout_eval, holdout_stratified  # noqa: E402
from dp2.features import FeatureBuilder, FeatureSpec  # noqa: E402
from dp2.metrics import fmt, per_class_report  # noqa: E402
from dp2.models import factory  # noqa: E402
from dp2.strategies import Flat, Separate  # noqa: E402

ds = D.load()
tr = ds.train
pairs = D.valid_pairs(tr)
crop, stage = tr.Crop.to_numpy(object), tr.Stage.to_numpy(object)

fb = FeatureBuilder(ds.bands, ds.wl, FeatureSpec(spectrum="raw", meta="ordinal")).fit(tr)
X = fb.transform(tr)
X_spec_only = FeatureBuilder(ds.bands, ds.wl, FeatureSpec(spectrum="raw", meta="none")).fit(tr).transform(tr)

splits = {
    "stratifiziert 70/30": holdout_stratified(tr.Combo.values),
    "Cluster 70/30": holdout_cluster(tr, ds.X_train)[:2],
}
for name, (a, b) in splits.items():
    print(f"{name}: train={len(a)} test={len(b)} Klassen im Test={tr.Combo.iloc[b].nunique()}")

candidates = {
    "Zufall (stratifiziert)": (lambda: Flat(factory("dummy"), pairs), X),
    "RF nur Spektrum": (lambda: Flat(factory("rf"), pairs), X_spec_only),
    "RF Spektrum+AEZ+Monat (Baseline)": (lambda: Flat(factory("rf"), pairs), X),
    "RF getrennt (2 Modelle)": (lambda: Separate(factory("rf"), factory("rf"), pairs, constrained=False), X),
}

rows = []
store = {}
for split_name, (a, b) in splits.items():
    for cname, (make, Xc) in candidates.items():
        m, c, s, strat = holdout_eval(make, Xc, crop, stage, a, b)
        rows.append({"Split": split_name, "Modell": cname, **m})
        store[(split_name, cname)] = (b, c, s)
        print(f"[{split_name}] {cname:35s} {fmt(m)}")

res = pd.DataFrame(rows)
res.to_csv(C.TABLES / "m1_baseline_results.csv", index=False)

# Konfusionsmatrizen der Baseline (stratifizierter Split)
b, c, s = store[("stratifiziert 70/30", "RF Spektrum+AEZ+Monat (Baseline)")]
import matplotlib.pyplot as plt  # noqa: E402
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
V.plot_confusion(confusion_matrix(crop[b], c, labels=C.CROPS), [C.CROP_DE[x] for x in C.CROPS],
                 "Baseline: Crop", ax=axes[0], fontsize=9)
V.plot_confusion(confusion_matrix(stage[b], s, labels=C.STAGES), [C.STAGE_DE[x] for x in C.STAGES],
                 "Baseline: Stage", ax=axes[1], fontsize=9)
V.savefig(fig, "m1_baseline_confusion")
labels = [p[0] + C.SEP + p[1] for p in pairs]
yt = crop[b] + C.SEP + stage[b]
yp = c + C.SEP + s
fig = V.plot_confusion(confusion_matrix(yt, yp, labels=labels), labels,
                       "Baseline: Crop×Stage (Zeilen normiert = Recall)")
V.savefig(fig, "m1_baseline_confusion_combo")
per_class_report(yt, yp, labels).round(3).to_csv(C.TABLES / "m1_baseline_per_class.csv")

summary = res.pivot_table(index="Modell", columns="Split",
                          values=["bacc_crop", "bacc_stage", "bacc_combo", "f1_samples"]).round(4)
print(summary)
with open(C.TABLES / "m1_baseline_summary.json", "w") as f:
    json.dump(res.to_dict(orient="records"), f, indent=1, default=float)
