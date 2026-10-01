#!/usr/bin/env bash
# Meilenstein 1: EDA, Baseline und Begleit-Notebooks (Laufzeit wenige Minuten).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
export PYTHONWARNINGS=ignore

$PY scripts/01_eda.py          # EDA-Abbildungen + Fakten
$PY scripts/02_baseline.py     # Baseline (70/30, stratifiziert + Cluster)
$PY scripts/make_notebooks.py  # Notebooks neu ausführen
