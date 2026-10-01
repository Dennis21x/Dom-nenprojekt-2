"""Einheitliche Fabrik für die Klassifikatoren (Stand Meilenstein 1: Baseline-Modelle).

Alle Modelle bekommen Klassengewichte ("balanced"), weil laut Bewertung die
Balanced Accuracy zählt: Jede Klasse wiegt gleich viel, egal wie selten sie ist
(Reis 93 Proben, Baumwolle/Ernte nur 11).
"""
from __future__ import annotations

from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config as C


def make_estimator(name: str, **kw):
    seed = kw.pop("random_state", C.SEED)
    if name == "dummy":
        return DummyClassifier(strategy="stratified", random_state=seed)
    if name == "logreg":
        return make_pipeline(StandardScaler(), LogisticRegression(
            C=kw.get("C", 1.0), max_iter=5000, class_weight="balanced"))
    if name == "knn":
        return make_pipeline(StandardScaler(), KNeighborsClassifier(
            n_neighbors=kw.get("n_neighbors", 5), weights="distance"))
    if name == "rf":
        return RandomForestClassifier(n_estimators=kw.get("n_estimators", 500), max_features="sqrt",
                                      class_weight="balanced_subsample", n_jobs=-1, random_state=seed)
    raise ValueError(f"unbekanntes Modell: {name}")


def factory(name: str, **kw):
    """Gibt eine parameterlose Fabrik zurück (für die Strategien)."""
    proto = make_estimator(name, **kw)
    return lambda: clone(proto)


MODEL_LABELS = {
    "dummy": "Zufall (stratifiziert)",
    "logreg": "Logistische Regression",
    "knn": "k-Nächste-Nachbarn",
    "rf": "Random Forest",
}
