"""Bewertungsmaße laut Aufgabenstellung.

* Balanced Accuracy  BAcc = 1/K * sum_c TP_c / (TP_c + FN_c)   (mittlerer Recall)
* Macro-F1           F1_macro = 1/K * sum_c F1_c
* Samples-F1         F1_samples = 1/n * sum_i F1_i, wobei jede Probe die
  Label-Menge {Crop, Stage} trägt (Multi-Label). Mit je zwei wahren und zwei
  vorhergesagten Labels ist F1_i = |Y_i ∩ Ŷ_i| / 2, also 1 (beides richtig),
  0,5 (eins richtig) oder 0.

Die Aufgabenstellung legt nicht fest, auf welcher Klassenebene BAcc und
Macro-F1 gerechnet werden. Wir berichten deshalb alle drei Ebenen:
Crop (5 Klassen), Stage (6 Klassen) und die Kombination Crop×Stage (23 Klassen).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, f1_score,
                             precision_recall_fscore_support)

from .config import SEP


def samples_f1(crop_true, stage_true, crop_pred, stage_pred) -> float:
    ct = np.asarray(crop_true) == np.asarray(crop_pred)
    st = np.asarray(stage_true) == np.asarray(stage_pred)
    return float(((ct.astype(float) + st.astype(float)) / 2.0).mean())


def evaluate(crop_true, stage_true, crop_pred, stage_pred) -> dict[str, float]:
    ct, st = np.asarray(crop_true, dtype=object), np.asarray(stage_true, dtype=object)
    cp, sp = np.asarray(crop_pred, dtype=object), np.asarray(stage_pred, dtype=object)
    comb_t = ct + SEP + st
    comb_p = cp + SEP + sp
    return {
        "bacc_crop": balanced_accuracy_score(ct, cp),
        "bacc_stage": balanced_accuracy_score(st, sp),
        "bacc_combo": balanced_accuracy_score(comb_t, comb_p),
        "f1_crop": f1_score(ct, cp, average="macro"),
        "f1_stage": f1_score(st, sp, average="macro"),
        "f1_combo": f1_score(comb_t, comb_p, average="macro", labels=np.unique(comb_t)),
        "f1_samples": samples_f1(ct, st, cp, sp),
        "acc_crop": accuracy_score(ct, cp),
        "acc_stage": accuracy_score(st, sp),
        "acc_combo": accuracy_score(comb_t, comb_p),
    }


# Hauptkennzahl für die Modellauswahl: Mittel der drei Balanced Accuracies.
# So wird kein Teilziel geopfert, egal auf welcher Ebene später gewertet wird.
def score(m: dict[str, float]) -> float:
    return (m["bacc_crop"] + m["bacc_stage"] + m["bacc_combo"]) / 3.0


def per_class_report(y_true, y_pred, labels=None) -> pd.DataFrame:
    labels = labels if labels is not None else np.unique(np.asarray(y_true))
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return pd.DataFrame({"precision": p, "recall": r, "f1": f, "support": s}, index=labels)


def fmt(m: dict[str, float], keys=("bacc_crop", "bacc_stage", "bacc_combo", "f1_combo", "f1_samples")) -> str:
    return "  ".join(f"{k}={m[k]:.4f}" for k in keys)
