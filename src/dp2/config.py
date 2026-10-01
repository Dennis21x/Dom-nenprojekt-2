"""Zentrale Konfiguration: Pfade, Zufallssaat, Klassenreihenfolgen."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
TRAIN_CSV = DATA_RAW / "train.csv"
TEST_CSV = DATA_RAW / "test.csv"

RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
TABLES = RESULTS / "tables"

for _p in (FIGURES, TABLES):
    _p.mkdir(parents=True, exist_ok=True)

SEED = 42

CROPS = ["corn", "cotton", "rice", "soybean", "winter_wheat"]

# Phänologische Reihenfolge (GHISA-Nomenklatur):
# Auflaufen/sehr früh -> früh/mittel vegetativ -> spät vegetativ ->
# kritisch (reproduktiv, Blüte) -> Reife/Seneszenz -> Ernte
STAGES = ["Emerge_VEarly", "Early_Mid", "Late", "Critical", "Mature_Senesc", "Harvest"]

CROP_DE = {
    "corn": "Mais",
    "cotton": "Baumwolle",
    "rice": "Reis",
    "soybean": "Sojabohne",
    "winter_wheat": "Winterweizen",
}
STAGE_DE = {
    "Emerge_VEarly": "Auflaufen/sehr früh",
    "Early_Mid": "früh/mittel veg.",
    "Late": "spät vegetativ",
    "Critical": "kritisch (Blüte)",
    "Mature_Senesc": "Reife/Seneszenz",
    "Harvest": "Ernte",
}

CROP_COLORS = {
    "corn": "#E8743B",
    "cotton": "#3BA5A0",
    "rice": "#2E7D32",
    "soybean": "#C9A227",
    "winter_wheat": "#3F5E78",
}
STAGE_COLORS = {
    "Emerge_VEarly": "#8C6D46",
    "Early_Mid": "#9CCC65",
    "Late": "#2E7D32",
    "Critical": "#1565C0",
    "Mature_Senesc": "#F9A825",
    "Harvest": "#6D4C41",
}

SEP = "__"  # Trennzeichen für kombinierte Klassen, z. B. "corn__Critical"
