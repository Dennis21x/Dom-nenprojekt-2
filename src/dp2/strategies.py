"""Modellierungsstrategien mit einheitlicher Schnittstelle (Stand Meilenstein 1).

Jede Strategie liefert `pair_proba(X)`: eine Wahrscheinlichkeit für jede der
23 im Training beobachteten (Crop, Stage)-Kombinationen. Daraus entsteht die
Vorhersage - so kann keine unmögliche Kombination (z. B. "Reis/Ernte")
herauskommen, außer bei der absichtlich unbeschränkten Variante.

* Flat      - Crop×Stage als eine Zielklasse (23 Klassen)  -> Baseline
* Separate  - zwei unabhängige Modelle; optional mit Konsistenzschritt

Geplant für Meilenstein 2: hierarchisch (Crop -> Stage), Multi-Task, Ensemble.
"""
from __future__ import annotations

from typing import Callable

import numpy as np

from .config import SEP

Pairs = list[tuple[str, str]]


def _proba_for(model, X, labels: list[str]) -> np.ndarray:
    """predict_proba auf eine feste Klassenreihenfolge bringen (fehlende = 0)."""
    p = model.predict_proba(X)
    out = np.zeros((len(X), len(labels)))
    idx = {c: i for i, c in enumerate(model.classes_)}
    for j, lab in enumerate(labels):
        if lab in idx:
            out[:, j] = p[:, idx[lab]]
    return out


def _norm(P: np.ndarray) -> np.ndarray:
    s = P.sum(axis=1, keepdims=True)
    return np.divide(P, s, out=np.full_like(P, 1.0 / P.shape[1]), where=s > 0)


class Strategy:
    name = "strategy"
    pairs: Pairs

    def fit(self, X, crop, stage):
        raise NotImplementedError

    def pair_proba(self, X) -> np.ndarray:
        raise NotImplementedError

    def predict(self, X) -> tuple[np.ndarray, np.ndarray]:
        P = self.pair_proba(X)
        best = np.argmax(P, axis=1)
        crop = np.array([self.pairs[i][0] for i in best], dtype=object)
        stage = np.array([self.pairs[i][1] for i in best], dtype=object)
        return crop, stage


class Flat(Strategy):
    name = "Flat (Crop×Stage, 23 Klassen)"

    def __init__(self, make: Callable, pairs: Pairs):
        self.make, self.pairs = make, pairs

    def fit(self, X, crop, stage):
        y = np.asarray(crop, dtype=object) + SEP + np.asarray(stage, dtype=object)
        self.model_ = self.make().fit(X, y)
        return self

    def pair_proba(self, X):
        return _proba_for(self.model_, X, [c + SEP + s for c, s in self.pairs])


class Separate(Strategy):
    """Zwei unabhängige Modelle. constrained=False gibt die rohe, unabhängige
    Vorhersage aus (kann unmögliche Paare liefern); constrained=True wählt das
    wahrscheinlichste *gültige* Paar unter P(c)·P(s)."""

    def __init__(self, make_crop: Callable, make_stage: Callable, pairs: Pairs, constrained=True):
        self.make_crop, self.make_stage, self.pairs = make_crop, make_stage, pairs
        self.constrained = constrained
        self.name = "Separate + Konsistenz" if constrained else "Separate (unabhängig)"

    def fit(self, X, crop, stage):
        self.crops_ = sorted({c for c, _ in self.pairs})
        self.stages_ = sorted({s for _, s in self.pairs})
        self.mc_ = self.make_crop().fit(X, np.asarray(crop))
        self.ms_ = self.make_stage().fit(X, np.asarray(stage))
        return self

    def marginals(self, X):
        return _proba_for(self.mc_, X, self.crops_), _proba_for(self.ms_, X, self.stages_)

    def pair_proba(self, X):
        pc, ps = self.marginals(X)
        ci = {c: i for i, c in enumerate(self.crops_)}
        si = {s: i for i, s in enumerate(self.stages_)}
        P = np.stack([pc[:, ci[c]] * ps[:, si[s]] for c, s in self.pairs], axis=1)
        return _norm(P)

    def predict(self, X):
        if self.constrained:
            return super().predict(X)
        pc, ps = self.marginals(X)
        return (np.array(self.crops_, dtype=object)[pc.argmax(1)],
                np.array(self.stages_, dtype=object)[ps.argmax(1)])
