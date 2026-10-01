"""Einheitliche Abbildungen (deutsche Beschriftung, gleiche Farben überall)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from . import config as C  # noqa: E402

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.alpha": 0.25, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
    "legend.frameon": False,
})

# atmosphärische Absorptionsbereiche, in denen die Bänder fehlen
GAPS = [(923, 983, "VNIR/SWIR-Übergang"), (1094, 1175, "H₂O 1130"), (1316, 1518, "H₂O 1400"),
        (1760, 2063, "H₂O 1900"), (2345, 2400, "")]
REGION_SPANS = [(437, 700, "VIS"), (700, 760, "Red Edge"), (760, 1300, "NIR"),
                (1500, 1800, "SWIR1"), (2000, 2400, "SWIR2")]


def savefig(fig, name: str):
    path = C.FIGURES / f"{name}.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def shade_gaps(ax, label=True):
    for a, b, txt in GAPS:
        ax.axvspan(a, b, color="#cfcfcf", alpha=0.45, lw=0)
        if label and txt:
            ax.text((a + b) / 2, 0.98, txt, transform=ax.get_xaxis_transform(), ha="center",
                    va="top", fontsize=7, color="#555", rotation=90)


def label_regions(ax):
    for a, b, txt in REGION_SPANS:
        ax.text((a + b) / 2, 1.01, txt, transform=ax.get_xaxis_transform(), ha="center",
                va="bottom", fontsize=8, color="#333")


def plot_segments(ax, wl, y, gap=15.0, **kw):
    """Linie mit Unterbrechung an fehlenden Bändern (keine Interpolation über Lücken)."""
    cuts = np.where(np.diff(wl) > gap)[0] + 1
    first = True
    for seg in np.split(np.arange(len(wl)), cuts):
        k = dict(kw)
        if not first:
            k.pop("label", None)
        ax.plot(wl[seg], y[seg], **k)
        first = False


def fill_segments(ax, wl, lo, hi, gap=15.0, **kw):
    cuts = np.where(np.diff(wl) > gap)[0] + 1
    for seg in np.split(np.arange(len(wl)), cuts):
        ax.fill_between(wl[seg], lo[seg], hi[seg], **kw)


def plot_confusion(cm, labels, title, ax=None, normalize=True, fontsize=7):
    import matplotlib.colors as mcolors
    cmn = cm / cm.sum(axis=1, keepdims=True).clip(min=1) if normalize else cm
    own = ax is None
    if own:
        fig, ax = plt.subplots(figsize=(0.42 * len(labels) + 3, 0.42 * len(labels) + 2.2))
    ax.imshow(cmn, cmap="Blues", norm=mcolors.Normalize(0, 1))
    ax.set_xticks(range(len(labels)), labels, rotation=90, fontsize=fontsize)
    ax.set_yticks(range(len(labels)), labels, fontsize=fontsize)
    ax.set_xlabel("vorhergesagt")
    ax.set_ylabel("wahr")
    ax.set_title(title)
    ax.grid(False)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if cm[i, j]:
                ax.text(j, i, f"{cmn[i, j]:.2f}" if normalize else int(cm[i, j]), ha="center",
                        va="center", fontsize=fontsize - 1,
                        color="white" if cmn[i, j] > 0.55 else "#222")
    return ax.figure
