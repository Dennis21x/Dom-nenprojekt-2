# Meilenstein 1 – Domäne, Data Understanding und Baseline

*Domänenprojekt 2 · Hierarchische Klassifikation von Hyperion-Hyperspektraldaten*
*Reproduzierbar mit `scripts/01_eda.py` und `scripts/02_baseline.py` (Demo: `notebooks/02_Baseline_Demo.ipynb`)*

## 1 Problemverständnis

**Domäne.** Wer weiß, *welche* Kultur auf einer Fläche steht und *in welchem
Entwicklungsstadium*, kann Ertragsprognosen erstellen, Bewässerung und Düngung
terminieren, Ernteschäden versichern oder Förderanträge (z. B. Anbaudiversifizierung)
kontrollieren. Satelliten liefern diese Information flächendeckend. Hyperspektrale
Sensoren wie **EO-1 Hyperion** (220 Bänder, 400–2500 nm, ~10 nm Bandbreite, 30 m
Pixel) messen dabei nicht nur „grün oder nicht“, sondern schmale Absorptionsmerkmale:
Chlorophyll (~670 nm), die rote Kante (700–760 nm), Blattstruktur (NIR-Plateau),
Blattwasser (~970, ~1200, ~1650 nm) sowie Cellulose/Lignin trockener Pflanzenreste
(~2100 nm).

**Aufgabe als ML-Problem.** Eingabe: ein Reflexionsspektrum (131 nutzbare Bänder)
plus agroökologische Zone (AEZ) und Aufnahmemonat. Ausgabe: Kulturpflanze (5 Klassen)
**und** Entwicklungsstadium (6 Klassen). Die Stadien hängen an der Kultur – nur 23 der
30 denkbaren Kombinationen kommen vor (z. B. gibt es Reis nur in *Early_Mid* und
*Late*). Bewertet wird primär mit **Balanced Accuracy** – jede Klasse zählt gleich,
seltene Klassen (Reis, Ernte) sind also genauso wichtig wie Mais.

**Erfolgskriterien, die wir uns setzen:** (1) deutlich über der Baseline auf allen
drei Ebenen (Crop, Stage, Crop×Stage), (2) keine Klasse „fällt aus“ (Recall je Klasse),
(3) nachvollziehbar, welche Spektralbereiche entscheiden, (4) ehrliche Aussage, wie
gut das Modell auf *neuen Feldern* wäre.

## 2 Data Understanding

| Kennzahl | Wert |
|---|---|
| Trainingsspektren | 5.591 (2 exakte Duplikate → 5.589) |
| Testspektren ohne Label | 1.397 |
| Bandspalten | 198, davon **67 komplett leer** → 131 nutzbar |
| nutzbare Bereiche | 437–923, 983–1094, 1175–1316, 1518–1760, 2063–2345 nm |
| sporadisch fehlende Werte | 48 Einzelwerte in 6 Bändern, 44 Zeilen (0,8 %); im Test 11 Zeilen |
| Reflexion | 0,25 – 93,2 % |
| Klassen | 5 Crops, 6 Stages, 23 Kombinationen |
| Ungleichgewicht | Mais : Reis = 22 : 1, größte : kleinste Kombination = 61 : 1 |

**Leere Bänder sind kein Datenfehler, sondern Physik.** Sie liegen genau auf den
atmosphärischen Wasserdampfbanden (~1130, ~1400, ~1900 nm), am Übergang der beiden
Hyperion-Detektoren (925–973 nm) und an den verrauschten Rändern. Dort erreicht kaum
Sonnenlicht den Boden – die Bänder werden standardmäßig verworfen
(`results/figures/eda_spectra_crop.png`, graue Bereiche). *Hinweis:* Abbildung 1B der
Aufgabenstellung hat eine andere Wellenlängenachse als die CSV-Spalten; wir verwenden
die Spaltennamen, weil nur sie mit den Absorptionsbanden übereinstimmen.

**Klassenverteilung** (`eda_class_distribution.png`): Mais 2.097, Soja 1.669,
Winterweizen 1.072, Baumwolle 658, Reis 93. Kleinste Kombinationen: Baumwolle/Ernte (11),
Winterweizen/Late (30), Reis/Late (41). → Klassengewichte, stratifizierte Splits,
Balanced Accuracy.

**Metadaten tragen viel Information** (`eda_metadata.png`, `eda_phenology.png`): Reis
kommt nur in AEZ 7 im August vor, Baumwolle nur in AEZ 2/5/9, Winterweizen nur in
AEZ 5/9 und läuft im **Herbst** (September/Oktober) auf. Allein durch Nachschlagen von
(AEZ, Monat) erreicht man eine Balanced Accuracy von 0,72 (Crop) bzw. 0,65 (Stage) –
AEZ und Monat werden deshalb als Merkmale genutzt (laut Aufgabenstellung erlaubt).

**Spektrale Signaturen folgen der Phänologie** (`eda_spectra_stage_per_crop.png`):
* *Emerge_VEarly* und *Harvest*: bodendominiert – flacher Anstieg im VIS, kaum rote
  Kante, hohe SWIR-Reflexion (NDVI-Median 0,07–0,15).
* *Late* und *Critical*: volle Bedeckung – tiefe Chlorophyllmulde bei 670 nm, steile
  rote Kante, NIR 50–65 %, niedriges SWIR durch Blattwasser (NDVI 0,65–0,80).
* *Mature_Senesc*: Chlorophyllabbau (höheres Rot, PSRI steigt), SWIR steigt wieder.
* Ausnahme Baumwolle: auch in *Critical* nur NDVI ≈ 0,37 – lückige Bestände auf hellen,
  trockenen Böden (AEZ 2/5).

**Klassenüberlappung** (`eda_crop_separability_by_stage.png`): Ein 5-NN auf dem
Spektrum allein erkennt die Kultur bei voller Bedeckung zu 87–90 %, beim Auflaufen nur
zu 71 % und bei der Ernte zu 63 %. **Wo der Sensor Boden sieht, ist die Kultur kaum
unterscheidbar** – das ist die zentrale Schwierigkeit und ein Argument dafür, das
Stadium mitzudenken (hierarchisch/gemeinsam).

**Redundanz** (`eda_correlation_pca.png`): Benachbarte Bänder korrelieren im Median mit
r = 0,999; 3 Hauptkomponenten erklären 96 %, 10 erklären 99,7 % der Varianz →
Band-Reduktion (Meilenstein 3) ist vielversprechend.

**Ausreißer** (`eda_outliers.png`): Eine robuste Mahalanobis-Distanz je Klasse
markiert 2.013 Proben (!) – die Klassen sind **multimodal** (mehrere Felder/Szenen je
Klasse), das Verfahren passt nicht. Der dichtebasierte **Local Outlier Factor** (> 2)
markiert 39 Proben, eine Plausibilitätsregel („volle Bedeckung, aber NDVI < 0,2“)
weitere 33 (27 davon Baumwolle/Critical). Die markierten Spektren sind physikalisch
plausibel (hellere Bestände, Mischpixel, lückige Baumwolle) → **nicht blind löschen**,
sondern in Meilenstein 2 per CV prüfen.

**Train vs. Test** (`eda_train_vs_test.png`): Ein Klassifikator, der Train von Test
unterscheiden soll, erreicht AUC = 0,50 (Zufall); die Distanz zum nächsten
Trainingsnachbarn ist für Test- und Trainingsspektren gleich (Median 1,28 vs. 1,27).
**Der Testdatensatz ist ein Zufallsausschnitt aus demselben Pool** – eine stratifizierte
Kreuzvalidierung schätzt die Testnote realistisch.

## 3 Pre-Processing-Pipeline (Version 1)

1. `Unnamed: 0` (Zeilenindex) entfernen, `id` nur für die Abgabe behalten.
2. 67 leere Bänder entfernen.
3. Einzelne Fehlwerte je Spektrum linear über die Wellenlänge interpolieren – nutzt die
   Glattheit des Spektrums, braucht keine Statistik anderer Zeilen (keine Leakage).
4. 2 exakte Duplikate entfernen.
5. Merkmale: 131 Reflexionswerte + AEZ + Monat.

Alle Schritte stecken in `src/dp2/data.py` und werden identisch auf Training und Test
angewandt.

## 4 Baseline: Random Forest, 70/30

Random Forest (500 Bäume, Klassengewichte), Zielklasse = Crop×Stage (23 Klassen).
Zwei Splits:
* **stratifiziert 70/30** – entspricht dem Testdatensatz;
* **Cluster-Split 70/30** – spektral ähnliche Pixel innerhalb jeder Gruppe (AEZ,
  Monat, Crop, Stage) werden per KMeans zusammengefasst und nur geschlossen einer
  Seite zugeteilt. Die Daten enthalten keine Feld-IDs; das ist unser Ersatz für einen
  Feld-/Plot-Split und schätzt die Leistung auf *neuen* Feldern.

| Modell | Split | BAcc Crop | BAcc Stage | BAcc Crop×Stage | Samples-F1 |
|---|---|---|---|---|---|
| Zufall (stratifiziert) | stratifiziert | 0,197 | 0,152 | 0,040 | 0,232 |
| RF nur Spektrum | stratifiziert | 0,782 | 0,765 | 0,601 | 0,808 |
| **RF Spektrum + AEZ + Monat (Baseline)** | stratifiziert | **0,827** | **0,829** | **0,692** | **0,858** |
| RF, zwei getrennte Modelle | stratifiziert | 0,823 | 0,786 | 0,623 | 0,841 |
| RF Spektrum + AEZ + Monat | **Cluster** | 0,652 | 0,598 | 0,390 | 0,699 |

**Lesart.**
* Die Metadaten bringen +0,09 Balanced Accuracy auf der Kombi-Ebene.
* Zwei getrennte Modelle sind schlechter als ein gemeinsames: Crop und Stage
  unabhängig zu raten ignoriert, dass die Stadien je Kultur anders aussehen.
* Der Cluster-Split kostet 0,30 Punkte. Ein erheblicher Teil der Leistung beim
  Zufallssplit entsteht, weil fast identische Nachbarpixel desselben Feldes auf beiden
  Seiten liegen. Für die Projektbewertung (Zufallsausschnitt) ist die stratifizierte
  Schätzung die richtige – für eine echte Anwendung auf neuen Feldern muss man mit
  deutlich weniger rechnen. Das berichten wir in jedem Meilenstein mit.

Konfusionsmatrizen: `results/figures/m1_baseline_confusion.png`,
`m1_baseline_confusion_combo.png`. Häufigste Fehler: Auflaufen/Ernte zwischen den
Kulturen und benachbarte Stadien (Early_Mid ↔ Late, Critical ↔ Mature_Senesc).

## 5 Nächste Schritte (Meilenstein 2)

Vorverarbeitung systematisch prüfen (Glättung, SNV, Ableitungen,
Vegetationsindizes, Ausreißer), Modellvergleich (tabellarisch vs. 1D-CNN),
Strategievergleich (flach / getrennt / hierarchisch / Multi-Task), 5-fach
stratifizierte CV plus Cluster-Gegenprobe.
