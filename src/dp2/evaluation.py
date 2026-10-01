"""Validierungsdesign Meilenstein 1: zwei 70/30-Holdouts.

Warum zwei Split-Arten?
* **Stratifiziert zufällig**: Der mitgelieferte Testdatensatz ist statistisch ein
  Zufallsausschnitt aus demselben Pool wie das Training (gleiche AEZ-/Monats-
  anteile, identische Nächste-Nachbar-Distanzen, adversarielle AUC ≈ 0,5 -> siehe
  EDA). Diese Validierung schätzt also die Note auf dem Testdatensatz.
* **Cluster-Split**: Benachbarte Pixel desselben Feldes/derselben Szene sind fast
  identisch. Liegen sie auf beiden Seiten des Splits, misst man teils
  "Wiedererkennen" statt Generalisieren. Beim Cluster-Split werden spektral
  ähnliche Proben *innerhalb* jeder Gruppe (AEZ, Monat, Crop, Stage) mit KMeans
  zusammengefasst und nur als ganze Cluster verteilt. Das ist eine strengere
  Schätzung für neue Felder (die Daten enthalten keine Feld-/Szenen-IDs; die
  Cluster sind ein Ersatz dafür).
"""
from __future__ import annotations

import time
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.model_selection import train_test_split

from . import config as C
from .metrics import evaluate, score


def holdout_stratified(y, test_size=0.3, seed=C.SEED):
    idx = np.arange(len(y))
    tr, te = train_test_split(idx, test_size=test_size, stratify=y, random_state=seed)
    return np.sort(tr), np.sort(te)


def cluster_groups(df: pd.DataFrame, X: np.ndarray, per_cluster: int = 20, seed=C.SEED) -> np.ndarray:
    """Cluster-ID je Probe: KMeans innerhalb jeder (AEZ, Monat, Crop, Stage)-Gruppe."""
    groups = np.zeros(len(df), dtype=int)
    Z = (X - X.mean(0)) / (X.std(0) + 1e-9)
    gid = 0
    for _, idx in df.groupby(["AEZ", "Month", "Crop", "Stage"]).indices.items():
        k = max(1, int(round(len(idx) / per_cluster)))
        if k == 1 or len(idx) < 6:
            # kleine Gruppe: in Mini-Cluster aus je ~3 Proben teilen
            k = max(1, len(idx) // 3)
            if k == 1:
                groups[idx] = gid; gid += 1
                continue
        lab = KMeans(n_clusters=k, n_init=4, random_state=seed).fit_predict(Z[idx])
        groups[idx] = gid + lab
        gid += k
    return groups


def holdout_cluster(df: pd.DataFrame, X: np.ndarray, test_size=0.3, seed=C.SEED):
    """70/30-Split, bei dem ganze Spektral-Cluster auf eine Seite fallen.
    Je Crop×Stage-Klasse werden Cluster zufällig in den Test gelegt, bis ~30 %
    der Klasse erreicht sind (mindestens ein Cluster bleibt im Training)."""
    rng = np.random.default_rng(seed)
    groups = cluster_groups(df, X, seed=seed)
    test = np.zeros(len(df), bool)
    for _, idx in df.groupby("Combo").indices.items():
        cl = np.unique(groups[idx])
        if len(cl) < 2:
            # nur ein Cluster -> zufällig teilen, sonst fehlte die Klasse ganz
            pick = rng.choice(idx, int(round(len(idx) * test_size)), replace=False)
            test[pick] = True
            continue
        rng.shuffle(cl)
        target, n = test_size * len(idx), 0
        for c in cl[:-1]:
            members = idx[groups[idx] == c]
            if n + len(members) > target * 1.25 and n > 0:
                continue
            test[members] = True
            n += len(members)
            if n >= target:
                break
    return np.where(~test)[0], np.where(test)[0], groups


def holdout_eval(make_strategy: Callable, X, crop, stage, tr, te):
    crop, stage = np.asarray(crop, dtype=object), np.asarray(stage, dtype=object)
    t0 = time.time()
    strat = make_strategy().fit(X[tr], crop[tr], stage[tr])
    c, s = strat.predict(X[te])
    m = evaluate(crop[te], stage[te], c, s)
    m["score"] = score(m)
    m["seconds"] = time.time() - t0
    return m, c, s, strat
