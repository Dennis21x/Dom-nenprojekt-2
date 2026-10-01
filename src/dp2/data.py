"""Laden und Bereinigen der Hyperion-Spektren.

Befunde aus der EDA, die hier umgesetzt werden:
* 67 der 198 Bänder sind in Train UND Test vollständig leer. Sie liegen exakt auf
  den atmosphärischen Wasserdampf-Absorptionsbanden (~1130, ~1400, ~1900 nm), am
  VNIR/SWIR-Detektorübergang (925-973 nm) und an den rauschigen Rändern
  (427 nm, >= 2355 nm). Sie werden entfernt -> 131 nutzbare Bänder.
* Einzelne Werte fehlen sporadisch (X1306, X1316, X1760, X2063, X2335, X2345,
  44 von 5.591 Zeilen). Sie werden je Spektrum linear über die Wellenlänge
  interpoliert - das nutzt die Glattheit eines Reflexionsspektrums und braucht
  keine Statistik aus anderen Zeilen (keine Leakage zwischen Train und Test).
* 2 exakte Duplikate im Training werden entfernt.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import config as C

META_COLS = ["AEZ", "Month"]
LABEL_COLS = ["Crop", "Stage"]


def band_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("X") and c[1:].isdigit()]


def wavelengths(cols: list[str]) -> np.ndarray:
    return np.array([int(c[1:]) for c in cols], dtype=float)


def segments(wl: np.ndarray, gap: float = 15.0) -> list[np.ndarray]:
    """Zusammenhängende Spektralabschnitte (Indexlisten) - getrennt an Lücken > gap nm."""
    cuts = np.where(np.diff(wl) > gap)[0] + 1
    return np.split(np.arange(len(wl)), cuts)


def interpolate_row_nans(X: np.ndarray, wl: np.ndarray) -> np.ndarray:
    """Fehlende Einzelwerte je Spektrum linear über die Wellenlänge schließen."""
    X = X.copy()
    bad_rows = np.where(np.isnan(X).any(axis=1))[0]
    for r in bad_rows:
        ok = ~np.isnan(X[r])
        X[r, ~ok] = np.interp(wl[~ok], wl[ok], X[r, ok])
    return X


@dataclass
class Dataset:
    train: pd.DataFrame          # bereinigt, mit Spalte Combo
    test: pd.DataFrame           # bereinigt
    bands: list[str]             # nutzbare Bänder (131)
    wl: np.ndarray               # deren Wellenlängen
    dropped_bands: list[str]     # vollständig leere Bänder
    n_duplicates: int

    @property
    def X_train(self) -> np.ndarray:
        return self.train[self.bands].to_numpy(float)

    @property
    def X_test(self) -> np.ndarray:
        return self.test[self.bands].to_numpy(float)


def combo(crop, stage):
    return pd.Series(crop).astype(str).str.cat(pd.Series(stage).astype(str), sep=C.SEP).to_numpy()


def split_combo(labels) -> tuple[np.ndarray, np.ndarray]:
    parts = pd.Series(labels).str.split(C.SEP, n=1, expand=True)
    return parts[0].to_numpy(), parts[1].to_numpy()


def load_raw() -> tuple[pd.DataFrame, pd.DataFrame]:
    tr = pd.read_csv(C.TRAIN_CSV)
    te = pd.read_csv(C.TEST_CSV)
    for df in (tr, te):
        if "Unnamed: 0" in df.columns:
            df.drop(columns="Unnamed: 0", inplace=True)
    return tr, te


def load(drop_duplicates: bool = True) -> Dataset:
    tr, te = load_raw()
    all_bands = band_columns(tr)
    empty = [b for b in all_bands if tr[b].isna().all() and te[b].isna().all()]
    bands = [b for b in all_bands if b not in empty]
    wl = wavelengths(bands)

    for df in (tr, te):
        df[bands] = interpolate_row_nans(df[bands].to_numpy(float), wl)
        df.drop(columns=empty, inplace=True)

    n_dup = int(tr.duplicated(subset=bands + META_COLS + LABEL_COLS).sum())
    if drop_duplicates and n_dup:
        tr = tr.drop_duplicates(subset=bands + META_COLS + LABEL_COLS).reset_index(drop=True)

    tr = tr.copy()  # entfragmentieren
    tr["Combo"] = combo(tr["Crop"], tr["Stage"])
    return Dataset(train=tr, test=te.reset_index(drop=True), bands=bands, wl=wl,
                   dropped_bands=empty, n_duplicates=n_dup)


def valid_pairs(train: pd.DataFrame) -> list[tuple[str, str]]:
    """Im Training vorkommende (Crop, Stage)-Kombinationen - 23 Stück."""
    pairs = train[["Crop", "Stage"]].drop_duplicates().itertuples(index=False, name=None)
    order = {s: i for i, s in enumerate(C.STAGES)}
    return sorted(pairs, key=lambda p: (C.CROPS.index(p[0]), order[p[1]]))
