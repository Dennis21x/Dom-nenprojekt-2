"""Erzeugt und führt die Begleit-Notebooks aus (notebooks/*.ipynb).

Die Notebooks sind die lesbare Oberfläche; die eigentliche Logik liegt im Paket
src/dp2 und in den nummerierten Skripten. So bleibt alles reproduzierbar und die
Notebooks bleiben kurz.
"""
from __future__ import annotations

import sys
from pathlib import Path

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "notebooks"
NB.mkdir(exist_ok=True)

SETUP = """import sys, warnings
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, matplotlib.pyplot as plt
%matplotlib inline
from IPython.display import Image, display, Markdown
from dp2 import config as C, data as D
FIG = C.FIGURES"""


def md(s):
    return nbf.v4.new_markdown_cell(s)


def code(s):
    return nbf.v4.new_code_cell(s)


def eda():
    return [
        md("# 01 – Explorative Datenanalyse (Meilenstein 1)\n\n"
           "Hyperion-Spektren (EO-1) landwirtschaftlicher Kulturen. Ziel: Crop **und** Growth Stage "
           "bestimmen. Dieses Notebook fasst die EDA zusammen; alle Abbildungen erzeugt "
           "`scripts/01_eda.py` reproduzierbar."),
        code(SETUP),
        md("## Rohdaten"),
        code("raw_tr, raw_te = D.load_raw()\nprint(raw_tr.shape, raw_te.shape)\nraw_tr.iloc[:5, :8]"),
        code("bands = D.band_columns(raw_tr)\nempty = [b for b in bands if raw_tr[b].isna().all()]\n"
             "print(f'{len(bands)} Bandspalten, davon {len(empty)} komplett leer')\n"
             "print('leer (nm):', [int(b[1:]) for b in empty])"),
        md("Die leeren Bänder liegen exakt auf den **atmosphärischen Wasserdampfbanden** (~1130, ~1400, "
           "~1900 nm), am VNIR/SWIR-Detektorübergang und an den verrauschten Rändern – dort misst Hyperion "
           "keine verwertbare Bodenreflexion. Sie werden entfernt, 131 Bänder bleiben."),
        code("ds = D.load()\ntr = ds.train\nprint('bereinigt:', tr.shape, '| Duplikate entfernt:', ds.n_duplicates)\n"
             "pd.crosstab(tr.Crop, tr.Stage).reindex(index=C.CROPS, columns=C.STAGES).fillna(0).astype(int)"),
        md("## Klassenverteilung\n23 der 30 Crop×Stage-Kombinationen kommen vor; die kleinste "
           "(Baumwolle/Ernte) hat nur 11 Proben – Faktor > 60 zur größten. Deshalb wird überall mit "
           "Klassengewichten und Balanced Accuracy gearbeitet."),
        code("display(Image(FIG / 'eda_class_distribution.png'))"),
        md("## Metadaten: AEZ und Monat\nAEZ und Aufnahmemonat sind stark mit den Klassen verknüpft "
           "(Reis nur AEZ 7/August, Winterweizen läuft im Herbst auf). Die Aufgabenstellung erlaubt "
           "ihre Nutzung ausdrücklich."),
        code("display(Image(FIG / 'eda_metadata.png'))\ndisplay(Image(FIG / 'eda_phenology.png'))"),
        md("## Spektrale Signaturen"),
        code("display(Image(FIG / 'eda_spectra_crop.png'))\ndisplay(Image(FIG / 'eda_spectra_stage_per_crop.png'))"),
        md("Die Stadien folgen der Phänologie: im **Auflaufen** und bei der **Ernte** dominiert Boden "
           "(flacher VIS-Anstieg, kaum rote Kante, hohe SWIR-Reflexion), bei **voller Bedeckung** "
           "(Late/Critical) tiefe Chlorophyllabsorption bei 670 nm, steile rote Kante, hohes NIR-Plateau "
           "und niedrige SWIR-Werte durch Blattwasser."),
        code("display(Image(FIG / 'eda_indices.png'))"),
        md("## Überschneidungen zwischen Klassen\nMit dem Spektrum allein trennt ein 5-NN die Kulturen in "
           "den bodendominierten Stadien am schlechtesten – dort sieht der Sensor kaum Pflanze."),
        code("display(Image(FIG / 'eda_crop_separability_by_stage.png'))\ndisplay(Image(FIG / 'eda_pca_scatter.png'))"),
        md("## Redundanz\nBenachbarte Bänder sind extrem korreliert; wenige Hauptkomponenten tragen fast "
           "die gesamte Varianz → Band-Reduktion ist vielversprechend (Meilenstein 3)."),
        code("display(Image(FIG / 'eda_correlation_pca.png'))"),
        md("## Ausreißer und Plausibilität"),
        code("display(Image(FIG / 'eda_outliers.png'))\n"
             "flags = pd.read_csv(C.TABLES / 'outlier_flags.csv')\n"
             "print('LOF>2:', flags.flag_lof.sum(), '| Late/Critical mit NDVI<0,2:', flags.flag_low_ndvi.sum())"),
        md("Die markierten Spektren sind physikalisch plausibel (hellere/dunklere Bestände, Mischpixel). "
           "Ihr Entfernen aus dem Training verbessert die CV nicht (siehe `m2_preprocessing`), daher "
           "bleiben sie im Datensatz."),
        md("## Train vs. Test"),
        code("display(Image(FIG / 'eda_train_vs_test.png'))\nimport json\n"
             "f = json.load(open(C.TABLES / 'eda_facts.json'))\n"
             "print('adversarielle AUC:', round(f['adversarial_auc'], 3))"),
        md("AUC ≈ 0,5 und identische Nächste-Nachbar-Distanzen: Der Testdatensatz ist ein Zufallsausschnitt "
           "aus demselben Pool. Eine stratifizierte Kreuzvalidierung schätzt die Testnote daher gut."),
    ]


def baseline():
    return [
        md("# 02 – Baseline-Demo (Meilenstein 1)\n\nRandom Forest auf 131 Bändern + AEZ + Monat, "
           "Zielklasse Crop×Stage, 70/30-Split. Läuft in unter einer Minute."),
        code(SETUP),
        code("from dp2.features import FeatureBuilder, FeatureSpec\nfrom dp2.models import factory\n"
             "from dp2.strategies import Flat\nfrom dp2.evaluation import holdout_stratified, holdout_cluster, holdout_eval\n"
             "from dp2.metrics import fmt\n"
             "ds = D.load(); tr = ds.train; pairs = D.valid_pairs(tr)\n"
             "X = FeatureBuilder(ds.bands, ds.wl, FeatureSpec(meta='ordinal')).fit(tr).transform(tr)\n"
             "crop, stage = tr.Crop.to_numpy(object), tr.Stage.to_numpy(object)\nX.shape"),
        md("## Pipeline\n1. Leere Bänder entfernen, Einzellücken je Spektrum linear interpolieren, Duplikate entfernen\n"
           "2. Merkmale: 131 Reflexionswerte + AEZ + Monat\n3. Random Forest (500 Bäume, Klassengewichte)"),
        code("a, b = holdout_stratified(tr.Combo.values)\n"
             "m, c, s, model = holdout_eval(lambda: Flat(factory('rf'), pairs), X, crop, stage, a, b)\n"
             "print('stratifiziert 70/30:', fmt(m))\n"
             "a2, b2, _ = holdout_cluster(tr, ds.X_train)\n"
             "m2, *_ = holdout_eval(lambda: Flat(factory('rf'), pairs), X, crop, stage, a2, b2)\n"
             "print('Cluster 70/30:     ', fmt(m2))"),
        md("Der **Cluster-Split** hält ganze Gruppen spektral ähnlicher Pixel (≈ dasselbe Feld) zurück. "
           "Die große Lücke zeigt: Ein Teil der Leistung beim Zufallssplit ist 'Wiedererkennen' "
           "benachbarter Pixel. Für den offiziellen Test (ebenfalls Zufallsausschnitt) ist der "
           "stratifizierte Split die richtige Schätzung, für neue Felder der Cluster-Split."),
        code("display(Image(FIG / 'm1_baseline_confusion.png'))"),
    ]


def build(name, cells, run=True):
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    path = NB / name
    if run:
        ExecutePreprocessor(timeout=1200, kernel_name="python3").preprocess(nb, {"metadata": {"path": str(NB)}})
    nbf.write(nb, path)
    print("geschrieben:", path)


if __name__ == "__main__":
    which = sys.argv[1:] or ["eda", "baseline"]
    if "eda" in which:
        build("01_EDA.ipynb", eda())
    if "baseline" in which:
        build("02_Baseline_Demo.ipynb", baseline())
