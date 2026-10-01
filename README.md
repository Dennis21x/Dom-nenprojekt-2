# Domänenprojekt 2 – Hierarchische Klassifikation von Hyperion-Hyperspektraldaten

**Stand: Meilenstein 1 (Domain & Baseline, 08.10.2026)**

Kulturpflanze (**Crop**, 5 Klassen) **und** Entwicklungsstadium (**Growing Stage**,
6 Klassen) aus satellitengestützten EO-1-Hyperion-Spektren bestimmen.

## Stand Meilenstein 1

**Neu im Projekt? → zuerst [`ANLEITUNG.md`](ANLEITUNG.md) lesen** (Begriffe, Bedienung, Erkenntnisse, typische Fragen).

| Bestandteil | Wo |
|---|---|
| Kurzreport (Problemverständnis, Data Understanding, Pipeline, Baseline) | `reports/Meilenstein1_Kurzreport.md` |
| Offene Fragen zur Aufgabenstellung | `reports/Fragen_fuer_Kickoff.md` |
| Explorative Datenanalyse | `scripts/01_eda.py`, `notebooks/01_EDA.ipynb` |
| Erste Pre-Processing-Pipeline | `src/dp2/data.py` |
| Baseline-Klassifikator (70/30, stratifiziert + Cluster-Split) | `scripts/02_baseline.py` |
| Demo-Run | `notebooks/02_Baseline_Demo.ipynb` (unter einer Minute) |

**Baseline** – Random Forest (500 Bäume, Klassengewichte) auf 131 Bändern + AEZ + Monat,
Zielklasse Crop×Stage, stratifizierter 70/30-Split:

| Ebene | Balanced Accuracy |
|---|---|
| Crop | 0,827 |
| Stage | 0,829 |
| Crop×Stage | 0,692 |
| Samples-F1 | 0,858 |

Beim Cluster-Split (ganze Gruppen spektral ähnlicher Pixel ≈ Felder zurückgehalten)
sinkt die Crop×Stage-BAcc auf 0,39 – Details im Kurzreport.

## Schnellstart

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
bash scripts/run_all.sh
```

## Aufbau

```
data/raw/               train.csv, test.csv (unverändert)
src/dp2/
  config.py             Pfade, Saat, Klassenreihenfolge, Farben
  data.py               Laden, leere Bänder entfernen, Lücken interpolieren, Duplikate
  features.py           Rohspektrum + AEZ/Monat, Vegetationsindizes (für die EDA)
  models.py             Baseline-Modelle (Zufall, Random Forest, LogReg, kNN)
  strategies.py         Flat (Crop×Stage) und Separate (zwei Modelle)
  evaluation.py         70/30-Splits: stratifiziert und Cluster-Split
  metrics.py            Balanced Accuracy, Macro-F1, Samples-F1 (alle Ebenen)
  viz.py                Abbildungs-Helfer
scripts/
  01_eda.py             EDA-Abbildungen und Kennzahlen
  02_baseline.py        Baseline
  make_notebooks.py     Begleit-Notebooks erzeugen und ausführen
  run_all.sh            alles in der richtigen Reihenfolge
notebooks/              01_EDA, 02_Baseline_Demo
results/figures|tables  Abbildungen und Tabellen (werden erzeugt)
reports/                Kurzreport Meilenstein 1, offene Fragen
```

## Nächste Schritte (Meilenstein 2, 15.10.2026)

* Vorverarbeitung systematisch vergleichen: Glättung, SNV, Ableitungen,
  Vegetationsindizes als Merkmale, Umgang mit den markierten Ausreißern
* Modellvergleich: tabellarisch (Boosting, SVM, MLP) vs. sequenziell (1D-CNN, RNN)
* Strategievergleich: flach / getrennt / hierarchisch / Multi-Task
* Validierung auf 5-fach stratifizierte Kreuzvalidierung umstellen, Cluster-Split als Gegenprobe
* Fehleranalyse je Klasse

## Reproduzierbarkeit

* Feste Saat (`SEED = 42`), identische Splits für alle Varianten.
* Alle Bereinigungsschritte sind zeilenweise (keine Statistik über andere Zeilen) und
  werden identisch auf Training und Test angewandt.
* Exakte Paketversionen in `requirements.txt`.
