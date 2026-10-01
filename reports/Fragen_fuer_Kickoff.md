# Offene Punkte zur Vorabversion der Aufgabenstellung – für den Kickoff am 28.09.2026

Beim Durcharbeiten der Vorabversion sind folgende Stellen aufgefallen, die man im
Kickoff kurz klären sollte. Die Arbeit ist so aufgebaut, dass jede Antwort ohne
Umbau berücksichtigt werden kann.

1. **Auf welcher Klassenebene wird die Balanced Accuracy berechnet?**
   Crop (5 Klassen), Stage (6 Klassen) oder die Kombination Crop×Stage (23 Klassen)?
   Oder als Mittel aus Crop und Stage? Wir berichten alle drei Ebenen und wählen
   Modelle über ihren Mittelwert.

2. **Samples-F1 (Multi-Label):** Ist die Label-Menge je Probe {Crop, Stage}?
   Dann ist F1 je Probe 1, 0,5 oder 0 (beides / eins / nichts richtig). So ist es
   implementiert (`src/dp2/metrics.py`).

3. **„70/30 Clusterplot-Split“ (Meilenstein 1):** Was ist genau gemeint? Die Daten
   enthalten weder Koordinaten noch Feld- oder Szenen-IDs. Wir haben zwei Varianten
   umgesetzt: (a) stratifiziert zufällig, (b) einen Cluster-Split, der spektral
   ähnliche Pixel innerhalb jeder Gruppe (AEZ, Monat, Crop, Stage) nur geschlossen
   einer Seite zuteilt – als Ersatz für einen Feld-/Plot-Split.

4. **Meilenstein 3 („1–2-jährige Sequenzen, Sommerfenster, wenige Zeitstempel“)**
   passt zu einem Zeitreihen-Datensatz. Hier gibt es je Probe genau ein Spektrum.
   Wir haben „Input minimieren“ als Reduktion der **Spektralbänder** (Anzahl,
   Bereiche, Auflösung, Multispektral-Sensoren), der **Metadaten**, der
   **Trainingsmenge** und als Genauigkeit **je Aufnahmemonat** umgesetzt. Passt das?

5. **Ist der Datensatz `test.csv` bereits der spätere Validierungsdatensatz**, oder
   kommt noch ein weiterer? Unser Vorhersageskript nimmt jede Datei im gleichen
   Format: `python scripts/09_predict.py pfad/zur/datei.csv`.

6. **Format der Abgabe-CSV:** Reicht `id, Crop, Stage`? Die Schreibweise der Labels
   ist exakt wie in `train.csv` (z. B. `winter_wheat`, `Mature_Senesc`).

7. **Abbildung 1B der Aufgabenstellung:** Die Wellenlängenachse dort weicht von den
   Spaltennamen der CSV ab (die Lücken liegen in der Abbildung bei ~920–970,
   ~1110–1320 und ~1550–1860 nm). Die Spaltennamen sind physikalisch plausibel:
   die komplett leeren Bänder liegen genau auf den atmosphärischen
   Wasserdampfbanden (~1130, ~1400, ~1900 nm). Wir verwenden die Spaltennamen.

8. **Datum Meilenstein 1** steht als „08.10.25“ – vermutlich 08.10.2026.

9. **Metadaten AEZ und Monat** dürfen laut Text verwendet werden – gilt das auch
   für den Validierungsdatensatz (sind die Spalten dort sicher enthalten)?
