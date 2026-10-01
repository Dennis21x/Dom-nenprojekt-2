"""Merkmalsbildung: Rohspektrum, Vegetationsindizes (EDA), Metadaten.

Stand Meilenstein 1: Die Baseline nutzt nur das bereinigte Rohspektrum plus
AEZ und Monat. Glättung, SNV, Ableitungen und Indizes als Modellmerkmale
werden in Meilenstein 2 systematisch verglichen.

Alle Transformationen hier sind *zeilenweise* (hängen nur vom einzelnen Spektrum
ab). Deshalb können sie vor dem Train/Test-Split angewandt werden, ohne
Information aus den Testdaten ins Training zu tragen. Alles, was Statistik über
Zeilen braucht (Skalierung, PCA, Feature-Selektion), passiert dagegen im
Modell-Pipeline-Schritt und damit nur auf den Trainingsfolds.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
from sklearn.base import BaseEstimator, TransformerMixin

from .data import segments

AEZ_LEVELS = [2, 5, 6, 7, 8, 9, 10]
MONTH_LEVELS = [5, 6, 7, 8, 9, 10]

def nearest(wl: np.ndarray, target: float) -> int:
    return int(np.argmin(np.abs(wl - target)))


def band_mean(X: np.ndarray, wl: np.ndarray, lo: float, hi: float) -> np.ndarray:
    m = (wl >= lo) & (wl <= hi)
    return X[:, m].mean(axis=1)


def sg_filter(X: np.ndarray, wl: np.ndarray, window: int = 7, deriv: int = 0,
              poly: int = 2) -> np.ndarray:
    """Savitzky-Golay je zusammenhängendem Abschnitt (nie über Lücken hinweg)."""
    out = np.empty_like(X, dtype=float)
    for seg in segments(wl):
        w = min(window, len(seg) if len(seg) % 2 else len(seg) - 1)
        if w <= poly:
            out[:, seg] = X[:, seg] if deriv == 0 else np.gradient(X[:, seg], axis=1)
            continue
        step = float(np.median(np.diff(wl[seg]))) if len(seg) > 1 else 1.0
        out[:, seg] = savgol_filter(X[:, seg], w, poly, deriv=deriv, delta=step, axis=1)
    return out


def vegetation_indices(X: np.ndarray, wl: np.ndarray) -> pd.DataFrame:
    """Etablierte Vegetationsindizes. Reflexion liegt in Prozent vor -> /100.

    Wo das Original-Band in einer entfernten Wasserdampfbande liegt, wird das
    nächstgelegene verfügbare Band genommen und der Index als *_proxy benannt.
    """
    R = lambda w: X[:, nearest(wl, w)] / 100.0  # noqa: E731
    eps = 1e-6
    b, g, r, re1, nir = R(480), R(550), R(670), R(720), R(800)
    f = {}
    f["NDVI"] = (nir - r) / (nir + r + eps)
    f["GNDVI"] = (nir - g) / (nir + g + eps)
    f["EVI"] = 2.5 * (nir - r) / (nir + 6 * r - 7.5 * b + 1)
    f["SAVI"] = 1.5 * (nir - r) / (nir + r + 0.5)
    f["OSAVI"] = (nir - r) / (nir + r + 0.16)
    f["NDRE"] = (R(790) - re1) / (R(790) + re1 + eps)
    f["CI_rededge"] = nir / (re1 + eps) - 1
    f["CI_green"] = nir / (g + eps) - 1
    mcari = ((R(700) - r) - 0.2 * (R(700) - g)) * (R(700) / (r + eps))
    tcari = 3 * ((R(700) - r) - 0.2 * (R(700) - g) * (R(700) / (r + eps)))
    f["MCARI"] = mcari
    f["TCARI_OSAVI"] = tcari / (f["OSAVI"] + eps)
    f["PRI"] = (R(531) - R(570)) / (R(531) + R(570) + eps)
    f["PSRI"] = (r - R(500)) / (R(750) + eps)            # Seneszenz
    f["CRI1"] = 1 / (R(510) + eps) - 1 / (g + eps)       # Carotinoide
    f["ARI"] = 1 / (g + eps) - 1 / (R(700) + eps)        # Anthocyane
    # Red-Edge-Position, lineare Vierpunkt-Interpolation (Guyot & Baret 1988)
    f["REP"] = 700 + 40 * (((r + R(780)) / 2) - R(700)) / (R(740) - R(700) + eps)
    f["NDWI_Gao"] = (R(860) - R(1240)) / (R(860) + R(1240) + eps)   # Blattwasser
    f["NDMI"] = (R(860) - R(1650)) / (R(860) + R(1650) + eps)
    f["MSI"] = R(1600) / (R(820) + eps)                             # Wasserstress
    f["NDTI"] = (R(1650) - R(2200)) / (R(1650) + R(2200) + eps)     # Residuen/Boden
    f["CAI_proxy"] = 0.5 * (R(2073) + R(2204)) - R(2103)            # Cellulose
    f["NDLI"] = (np.log(1 / (R(1750) + eps)) - np.log(1 / (R(1680) + eps))) / (
        np.log(1 / (R(1750) + eps)) + np.log(1 / (R(1680) + eps)) + eps)  # Lignin
    f["WBI_proxy"] = R(900) / (R(983) + eps)
    f["SWIR_ratio"] = R(1650) / (R(2200) + eps)
    # Helligkeiten der Regionen + Formmerkmale
    f["mean_VIS"] = band_mean(X, wl, 430, 700) / 100
    f["mean_NIR"] = band_mean(X, wl, 760, 900) / 100
    f["mean_SWIR1"] = band_mean(X, wl, 1500, 1800) / 100
    f["mean_SWIR2"] = band_mean(X, wl, 2000, 2400) / 100
    f["green_peak"] = g - 0.5 * (b + r)
    f["red_well"] = 0.5 * (g + R(750)) - r
    # Wendepunkt der roten Kante über das Maximum der 1. Ableitung (680-760 nm)
    d1 = sg_filter(X, wl, window=5, deriv=1)
    m = (wl >= 680) & (wl <= 760)
    f["REIP_deriv"] = wl[m][np.argmax(d1[:, m], axis=1)]
    f["max_slope_RE"] = d1[:, m].max(axis=1)
    return pd.DataFrame(f)


def meta_features(df: pd.DataFrame, mode: str) -> tuple[np.ndarray, list[str]]:
    if mode == "none":
        return np.empty((len(df), 0)), []
    cols, names = [], []
    if mode in ("onehot", "both"):
        for a in AEZ_LEVELS:
            cols.append((df["AEZ"].to_numpy() == a).astype(float)); names.append(f"AEZ_{a}")
        for m in MONTH_LEVELS:
            cols.append((df["Month"].to_numpy() == m).astype(float)); names.append(f"Month_{m}")
    if mode in ("ordinal", "both"):
        cols.append(df["AEZ"].to_numpy(float)); names.append("AEZ")
    cols.append(df["Month"].to_numpy(float)); names.append("Month")
    return np.stack(cols, axis=1), names


@dataclass
class FeatureSpec:
    """Beschreibt eine Merkmalsvariante."""
    spectrum: str = "raw"        # raw | none
    indices: bool = False        # Vegetationsindizes zusätzlich
    meta: str = "ordinal"        # none | ordinal (AEZ, Month als Zahl) | onehot | both
    name: str = field(default="")

    def label(self) -> str:
        if self.name:
            return self.name
        parts = [self.spectrum]
        if self.indices:
            parts.append("VI")
        parts.append(f"meta={self.meta}")
        return "+".join(parts)


class FeatureBuilder(BaseEstimator, TransformerMixin):
    """Zeilenweiser Merkmalsbauer (zustandslos -> fit tut nichts)."""

    def __init__(self, bands: list[str], wl: np.ndarray, spec: FeatureSpec | None = None):
        self.bands = bands
        self.wl = wl
        self.spec = spec or FeatureSpec()

    def fit(self, df, y=None):
        self.feature_names_ = self._build(df.iloc[:2])[1]
        return self

    def transform(self, df):
        return self._build(df)[0]

    def get_feature_names_out(self, input_features=None):
        return np.array(self.feature_names_)

    def _build(self, df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
        s = self.spec
        X = df[self.bands].to_numpy(float)
        wl = np.asarray(self.wl, float)
        blocks, names = [], []
        if s.spectrum == "raw":
            blocks.append(X); names += list(self.bands)
        if s.indices:
            vi = vegetation_indices(X, wl)
            blocks.append(vi.to_numpy()); names += list(vi.columns)
        m, mn = meta_features(df, s.meta)
        if m.shape[1]:
            blocks.append(m); names += mn
        return np.hstack(blocks).astype(np.float32), names
